"""The ONLY path to the index.

Access control is applied inside the Chroma query (`where`), never after it.

RULE FOR ANY FUTURE RETRIEVAL PATH (BM25, reranker, hybrid, query expansion...):
its candidates must come from the same allowed-company set *before* scoring.
Never retrieve unfiltered and filter afterwards, and never rank/score documents
the role may not see, because scores, counts and ordering can leak them.
"""
import sys
import time
from dataclasses import dataclass

from . import acl

_state = {}  # per-process cache: model, collections, manifest check


@dataclass
class Hit:
    doc_id: str
    page: int
    chunk_id: str
    score: float  # cosine similarity = 1 - Chroma cosine distance
    text: str
    company: str


def _model(config):
    if "model" not in _state:
        t0 = time.perf_counter()
        from . import hf

        hf.prefer_offline(config.EMBED_MODEL)  # must precede the transformers import
        from sentence_transformers import SentenceTransformer
        from transformers.utils import logging as hf_logging

        hf_logging.disable_progress_bar()  # hides "Loading weights" in search/ask
        _state["model"] = SentenceTransformer(config.EMBED_MODEL)
        print(f"loaded embedding model in {time.perf_counter() - t0:.1f}s",
              file=sys.stderr, flush=True)
    return _state["model"]


def _collection(config):
    key = str(config.INDEX_DIR)
    if key not in _state:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=key, settings=Settings(anonymized_telemetry=False))
        _state[key] = client.get_collection(config.COLLECTION)
    return _state[key]


def retrieve(question, role, k, config):
    allowed = acl.allowed_companies(role)  # raises acl.UnknownRole
    if "manifest_ok" not in _state:
        acl.check_manifest(config.MANIFEST_PATH)
        _state["manifest_ok"] = True

    t0 = time.perf_counter()
    model = _model(config)
    t1 = time.perf_counter()
    q = model.encode([config.QUERY_PREFIX + question], normalize_embeddings=True,
                     show_progress_bar=False, convert_to_numpy=True).tolist()
    t2 = time.perf_counter()
    res = _collection(config).query(
        query_embeddings=q,
        n_results=k,
        where={"company": {"$in": allowed}},  # ACL: inside the query
        include=["documents", "metadatas", "distances"],
    )
    t3 = time.perf_counter()
    print(f"query latency: model_load={t1 - t0:.3f}s embed={t2 - t1:.3f}s "
          f"chroma={t3 - t2:.3f}s total={t3 - t0:.3f}s", file=sys.stderr, flush=True)

    hits = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append(Hit(doc_id=meta["doc_id"], page=int(meta["page"]),
                        chunk_id=meta["chunk_id"], score=1.0 - float(dist),
                        text=doc, company=meta["company"]))
    return hits  # Chroma returns nearest first
