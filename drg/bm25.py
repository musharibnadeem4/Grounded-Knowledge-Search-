"""Optional BM25 side of hybrid retrieval (config.HYBRID_BM25). OFF by default (rejected, X1); see EXPERIMENTS.md.

Access control: candidates are the chunk ids that Chroma returns for the SAME `where` filter used by the dense
query (role / company / year, computed in retrieve()). BM25 statistics (document frequency, average length,
collection size) are computed over those candidates only, so nothing about chunks the role may not see
influences a score. The persisted matrix only maps chunk ids to term counts; it is never scanned unfiltered.

Persisted next to (not inside) the index:  <index_dir>_bm25/{meta.json, tf.npz, dl.npy}
Build:  python -m drg.bm25 build --index-dir index
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

K1, B = 1.2, 0.75
_STOP = frozenset("a an and are as at be by for from has have in is it its of on or that the to was were will with "
                  "what which who how did do does".split())
_TOK = re.compile(r"[a-z0-9]+")
_state = {}


def tokenize(text):
    out = []
    for t in _TOK.findall(text.lower()):
        if t in _STOP:
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]  # crude plural stripping: expenses -> expense
        out.append(t)
    return out


def bm25_dir(index_dir):
    p = Path(index_dir)
    return p.parent / (p.name + "_bm25")


def build(index_dir, collection="chunks"):
    import chromadb
    from chromadb.config import Settings

    t0 = time.perf_counter()
    coll = chromadb.PersistentClient(path=str(index_dir),
                                     settings=Settings(anonymized_telemetry=False)).get_collection(collection)
    ids, docs = [], []
    off = 0
    while True:
        r = coll.get(limit=5000, offset=off, include=["documents", "metadatas"])
        if not r["ids"]:
            break
        for i, d, m in zip(r["ids"], r["documents"], r["metadatas"]):
            ids.append(i)
            docs.append((m.get("page_header", "") + "\n" + d))
        off += len(r["ids"])
    vocab, rows, cols, vals, dl = {}, [], [], [], np.zeros(len(ids), dtype=np.float32)
    for n, text in enumerate(docs):
        toks = tokenize(text)
        dl[n] = len(toks)
        counts = {}
        for t in toks:
            counts[t] = counts.get(t, 0) + 1
        for t, c in counts.items():
            j = vocab.setdefault(t, len(vocab))
            rows.append(n)
            cols.append(j)
            vals.append(c)
    tf = sp.csc_matrix((np.array(vals, dtype=np.float32), (rows, cols)), shape=(len(ids), len(vocab)))
    out = bm25_dir(index_dir)
    out.mkdir(parents=True, exist_ok=True)
    sp.save_npz(out / "tf.npz", tf)
    np.save(out / "dl.npy", dl)
    (out / "meta.json").write_text(json.dumps({"ids": ids, "vocab": vocab, "k1": K1, "b": B,
                                               "built_from": str(index_dir)}), encoding="utf-8")
    print(f"bm25: {len(ids)} chunks, vocab {len(vocab)}, wrote {out} in {time.perf_counter() - t0:.1f}s",
          file=sys.stderr)


def _load(index_dir):
    key = ("bm25", str(index_dir))
    if key not in _state:
        d = bm25_dir(index_dir)
        if not (d / "meta.json").exists():
            raise FileNotFoundError(f"{d} missing; build it with: python -m drg.bm25 build --index-dir {index_dir}")
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        _state[key] = {"tf": sp.load_npz(d / "tf.npz").tocsc(), "dl": np.load(d / "dl.npy"),
                       "ids": meta["ids"], "row": {i: n for n, i in enumerate(meta["ids"])},
                       "vocab": meta["vocab"]}
    return _state[key]


def candidate_ids(coll, where):
    """Chunk ids allowed by `where` (same filter as the dense query), cached per filter in this process."""
    key = ("cand", id(coll), json.dumps(where, sort_keys=True))
    if key not in _state:
        _state[key] = coll.get(where=where, include=[])["ids"]
    return _state[key]


def top(index_dir, coll, where, text, n):
    """-> [(chunk_id, bm25_score)] best first, among chunks allowed by `where`. Scores only the candidates."""
    st = _load(index_dir)
    cand = [st["row"][i] for i in candidate_ids(coll, where) if i in st["row"]]
    terms = [t for t in dict.fromkeys(tokenize(text)) if t in st["vocab"]]
    if not cand or not terms:
        return []
    cand = np.array(cand, dtype=np.int64)
    cols = [st["vocab"][t] for t in terms]
    tf = st["tf"][:, cols][cand].toarray()          # (n_cand, n_terms) raw counts, candidates only
    dl = st["dl"][cand]
    N = len(cand)
    df = (tf > 0).sum(axis=0)
    idf = np.log(1.0 + (N - df + 0.5) / (df + 0.5))
    avgdl = max(float(dl.mean()), 1.0)
    denom = tf + K1 * (1.0 - B + B * dl[:, None] / avgdl)
    score = (idf[None, :] * tf * (K1 + 1.0) / np.where(denom == 0, 1.0, denom)).sum(axis=1)
    order = np.argsort(-score, kind="stable")[:n]
    return [(st["ids"][cand[i]], float(score[i])) for i in order if score[i] > 0]


def rrf(rank_lists, k=60):
    """Reciprocal rank fusion of several ranked id lists -> {id: score}."""
    out = {}
    for lst in rank_lists:
        for r, i in enumerate(lst, 1):
            out[i] = out.get(i, 0.0) + 1.0 / (k + r)
    return out


if __name__ == "__main__":  # pragma: no cover
    ap = argparse.ArgumentParser(prog="python -m drg.bm25")
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--index-dir", default="index")
    a = ap.parse_args()
    build(a.index_dir)
