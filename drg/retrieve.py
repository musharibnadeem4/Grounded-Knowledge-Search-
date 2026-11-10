"""The ONLY path to the index.

Access control is applied inside the Chroma query (`where`), never after it.

RULE FOR ANY FUTURE RETRIEVAL PATH (BM25, reranker, hybrid, query expansion...):
its candidates must come from the same allowed-company set *before* scoring.
Never retrieve unfiltered and filter afterwards, and never rank/score documents
the role may not see, because scores, counts and ordering can leak them.
"""
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import acl, boilerplate, query

_state = {}  # per-process cache: model, collections, manifest check


@dataclass
class Hit:
    doc_id: str
    page: int
    chunk_id: str
    score: float  # cosine similarity = 1 - Chroma cosine distance (reranker score if RERANKER is set)
    text: str
    company: str
    page_header: str = ""  # first lines of the page (statement name, units)
    period: str = ""


def _model(config):
    if "model" not in _state and getattr(config, "ONNX_ENCODER", False):
        if (Path(config.ONNX_DIR) / "model.onnx").exists():
            # onnxruntime + tokenizers only: no torch / transformers / sentence-transformers import
            t0 = time.perf_counter()
            from .onnx_encoder import OnnxEncoder

            _state["model"] = OnnxEncoder(config.ONNX_DIR)
            print(f"onnx query encoder loaded in {time.perf_counter() - t0:.2f}s", file=sys.stderr, flush=True)
        else:  # not exported on this machine: same embeddings, just slower to start
            print(f"WARN ONNX_ENCODER is on but {config.ONNX_DIR}/model.onnx is missing "
                  f"(python scripts/export_onnx.py); using sentence-transformers", file=sys.stderr, flush=True)
    if "model" not in _state:
        t0 = time.perf_counter()
        from . import hf

        rr = getattr(config, "RERANKER", None)
        hf.prefer_offline(config.EMBED_MODEL, *([rr] if rr else []))  # before transformers import
        from sentence_transformers import SentenceTransformer
        from transformers.utils import logging as hf_logging

        hf_logging.disable_progress_bar()  # hides "Loading weights" in search/ask
        # In offline mode huggingface_hub warns "Could not reach the Hub ... Using cached
        # commit hash"; that is expected, so keep only errors from it.
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
        _state["model"] = SentenceTransformer(config.EMBED_MODEL)
        took = time.perf_counter() - t0
        if hf.offline_enabled():
            print(f"embedding model loaded from local cache (offline) in {took:.1f}s",
                  file=sys.stderr, flush=True)
        else:
            print(f"loaded embedding model in {took:.1f}s", file=sys.stderr, flush=True)
    return _state["model"]


def _reranker(config):  # OFF by default (RERANKER=None; e3a-e3c rejected): see EXPERIMENTS.md
    name = config.RERANKER
    if name not in config.RERANKERS_ALLOWED:
        raise ValueError(f"RERANKER {name!r} not allowed; expected None or one of "
                         f"{list(config.RERANKERS_ALLOWED)}")
    key = ("reranker", name)
    if key not in _state:
        t0 = time.perf_counter()
        from . import hf

        hf.prefer_offline(config.EMBED_MODEL, name)
        from sentence_transformers import CrossEncoder

        _state[key] = CrossEncoder(name)
        print(f"loaded reranker {name} in {time.perf_counter() - t0:.1f}s",
              file=sys.stderr, flush=True)
    return _state[key]


def last_timings():
    """Timings (seconds) of the most recent retrieve() call in this process."""
    return dict(_state.get("timings", {}))


def _collection(config):
    key = str(config.INDEX_DIR)
    if key not in _state:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=key, settings=Settings(anonymized_telemetry=False))
        _state[key] = client.get_collection(config.COLLECTION)
    return _state[key]


def retrieve(question, role, k, config, companies=None):
    """`companies` (optional) narrows the search to those companies within the role's
    allowed set; it can only narrow, never widen."""
    allowed = acl.allowed_companies(role)  # raises acl.UnknownRole
    if companies is not None:
        allowed = [c for c in allowed if c in set(companies)]
        if not allowed:
            return []
    if "manifest_ok" not in _state:
        acl.check_manifest(config.MANIFEST_PATH)
        _state["manifest_ok"] = True

    where = {"company": {"$in": allowed}}  # ACL: inside the query
    if getattr(config, "YEAR_COMPANY_FILTER", False):
        # The result is always AND-ed with the role filter, so it can only narrow.
        if "periods" not in _state:
            _state["periods"] = query.load_periods(config.MANIFEST_PATH)
        companies, year = query.parse_query(question)
        forward = getattr(config, "FORECAST_PRIOR_YEAR", False) and query.is_forward_looking(question)
        where, chosen = query.build_where(allowed, companies, year, _state["periods"], forward)
        print(f"query parse: companies={sorted(companies)} year={year} "
              f"searching={chosen} where={json.dumps(where)}", file=sys.stderr, flush=True)

    reranker = _reranker(config) if getattr(config, "RERANKER", None) else None
    # With a reranker, fetch RERANK_DEPTH candidates through the very same query + where.
    n_fetch = max(k, config.RERANK_DEPTH) if reranker else k
    min_chars = getattr(config, "MIN_CHUNK_CHARS", 0)
    drop_bp = getattr(config, "DROP_BOILERPLATE", False)
    overfetch = max(config.MIN_CHUNK_OVERFETCH if min_chars > 0 else 1,
                    config.DROP_BOILERPLATE_OVERFETCH if drop_bp else 1)
    n_fetch *= overfetch  # extra candidates to absorb the dropped ones

    if getattr(config, "PREFER_10K_OVER_ANNUALREPORT", False):
        if "ar_excl" not in _state:
            _state["ar_excl"] = query.annualreport_exclusions(config.MANIFEST_PATH)
        if _state["ar_excl"]:  # only narrows: AND-ed onto the role / company / year filter
            where = {"$and": [where, {"doc_id": {"$nin": _state["ar_excl"]}}]}

    hybrid = getattr(config, "HYBRID_BM25", False)
    n_out = n_fetch  # how many candidates the rest of the pipeline wants
    if hybrid:  # both rankers need enough candidates to fuse
        n_fetch = max(n_fetch, getattr(config, "HYBRID_DEPTH", 50))

    search_text = question  # what gets embedded; `question` itself is never altered
    if getattr(config, "QUERY_CLEAN", False):
        search_text = query.clean_query(question)
        print(f"query clean: {search_text!r}", file=sys.stderr, flush=True)

    if getattr(config, "QUERY_EXPAND", False):
        search_text, added = query.expand_query(search_text)
        if added:
            print(f"query expand: +{added}", file=sys.stderr, flush=True)

    t0 = time.perf_counter()
    model = _model(config)
    t1 = time.perf_counter()
    q = model.encode([config.QUERY_PREFIX + search_text], normalize_embeddings=True,
                     show_progress_bar=False, convert_to_numpy=True).tolist()
    t2 = time.perf_counter()
    res = _collection(config).query(
        query_embeddings=q,
        n_results=n_fetch,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    t3 = time.perf_counter()
    print(f"query latency: model_load={t1 - t0:.3f}s embed={t2 - t1:.3f}s "
          f"chroma={t3 - t2:.3f}s total={t3 - t0:.3f}s", file=sys.stderr, flush=True)

    def _hit(doc, meta, score):
        return Hit(doc_id=meta["doc_id"], page=int(meta["page"]), chunk_id=meta["chunk_id"], score=score,
                   text=doc, company=meta["company"], page_header=meta.get("page_header", ""),
                   period=str(meta.get("period", "")))

    hits = [_hit(doc, meta, 1.0 - float(dist))
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])]

    if hybrid:
        from . import bm25  # lazy: numpy/scipy are not needed unless hybrid is on

        # BM25 over the chunks allowed by the very same `where`, fused with the dense ranking (RRF).
        tb = time.perf_counter()
        coll = _collection(config)
        depth = getattr(config, "HYBRID_DEPTH", 50)
        lex = bm25.top(config.INDEX_DIR, coll, where, search_text, depth)
        fused = bm25.rrf([[h.chunk_id for h in hits[:depth]], [i for i, _ in lex]],
                         getattr(config, "RRF_K", 60))
        by_id = {h.chunk_id: h for h in hits}
        missing = [i for i in fused if i not in by_id]
        if missing:  # lexical-only hits: fetched through the same filter (ids AND where)
            got = coll.get(ids=missing, where=where, include=["documents", "metadatas"])
            for doc, meta in zip(got["documents"], got["metadatas"]):
                by_id[meta["chunk_id"]] = _hit(doc, meta, 0.0)
        for i, sc in fused.items():
            if i in by_id:
                by_id[i].score = sc  # RRF score replaces the cosine similarity
        hits = sorted((by_id[i] for i in fused if i in by_id), key=lambda h: h.score, reverse=True)
        hits = hits[:n_out]  # fusion looked at HYBRID_DEPTH per ranker; return what was asked for
        print(f"hybrid: dense={min(depth, len(res['ids'][0]))} bm25={len(lex)} lexical-only={len(missing)} "
              f"bm25_time={time.perf_counter() - tb:.3f}s", file=sys.stderr, flush=True)
        t3 = time.perf_counter()

    if min_chars > 0 or drop_bp:
        fetched = len(hits)
        if min_chars > 0:
            kept = [h for h in hits if len(h.text.strip()) >= min_chars]
            print(f"min_chunk_chars={min_chars}: dropped {len(hits) - len(kept)} of "
                  f"{len(hits)} candidates", file=sys.stderr, flush=True)
            hits = kept
        if drop_bp:
            kept, n_short, n_exhibit = [], 0, 0
            for h in hits:
                why = boilerplate.is_boilerplate(h.page_header, h.text)
                if why == "short":
                    n_short += 1
                elif why == "exhibit":
                    n_exhibit += 1
                else:
                    kept.append(h)
            print(f"drop_boilerplate: dropped {len(hits) - len(kept)} of {len(hits)} candidates "
                  f"(short={n_short}, exhibit/signature={n_exhibit})",
                  file=sys.stderr, flush=True)
            hits = kept
        # back to the normal candidate count (k, or RERANK_DEPTH with a reranker)
        hits = hits[:max(k, config.RERANK_DEPTH) if reranker else k]

    rerank_s = None
    if reranker and hits:
        # Reorders only the candidates above; never adds documents.
        t4 = time.perf_counter()
        scores = reranker.predict([(question, h.text) for h in hits],
                                  show_progress_bar=False, convert_to_numpy=True)
        for h, sc in zip(hits, scores):
            h.score = float(sc)  # reranker score replaces the cosine similarity
        hits.sort(key=lambda h: h.score, reverse=True)
        hits = hits[:k]
        rerank_s = time.perf_counter() - t4
        print(f"rerank latency: {rerank_s:.3f}s for {len(scores)} candidates "
              f"({config.RERANKER})", file=sys.stderr, flush=True)
    _state["timings"] = {"embed_s": t2 - t1, "chroma_s": t3 - t2, "rerank_s": rerank_s}
    return hits  # nearest first, or best reranker score first
