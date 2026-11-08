#!/usr/bin/env python
"""Time the cold-start path of `search`, step by step. Output goes to stderr.

Each run is a fresh subprocess (so imports are really cold for that process);
the parent reports per-run values and the median over --runs.
Run from the project root with the project's venv python.
"""
import argparse
import json
import statistics
import subprocess
import sys
import time

STEPS = ["import torch", "import sentence_transformers", "import chromadb",
         "model load", "chroma client open", "first query", "second query"]
Q1 = "Pfizer revenue 2022"
Q2 = "What was Boeing's backlog at year end?"


def child():
    t = {}

    def step(name, fn):
        t0 = time.perf_counter()
        r = fn()
        t[name] = time.perf_counter() - t0
        return r

    step("import torch", lambda: __import__("torch"))
    step("import sentence_transformers", lambda: __import__("sentence_transformers"))
    step("import chromadb", lambda: __import__("chromadb"))

    from drg import acl, config  # light; not timed

    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings

    model = step("model load", lambda: SentenceTransformer(config.EMBED_MODEL))

    def open_client():
        client = chromadb.PersistentClient(
            path=str(config.INDEX_DIR), settings=Settings(anonymized_telemetry=False))
        return client.get_collection(config.COLLECTION)

    coll = step("chroma client open", open_client)
    allowed = acl.allowed_companies("consumer")

    def query(q):
        emb = model.encode([config.QUERY_PREFIX + q], normalize_embeddings=True,
                           show_progress_bar=False, convert_to_numpy=True).tolist()
        return coll.query(query_embeddings=emb, n_results=10,
                          where={"company": {"$in": allowed}},
                          include=["documents", "metadatas", "distances"])

    step("first query", lambda: query(Q1))
    step("second query", lambda: query(Q2))
    print(json.dumps(t))


def fmt(t):
    return "  ".join(f"{k}={t[k]:.3f}" for k in STEPS) + f"  total={sum(t.values()):.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    if a.child:
        return child()

    runs = []
    for i in range(1, a.runs + 1):
        p = subprocess.run([sys.executable, __file__, "--child"],
                           capture_output=True, text=True)
        if p.returncode:
            print(p.stderr[-2000:], file=sys.stderr)
            sys.exit(p.returncode)
        t = json.loads(p.stdout.strip().splitlines()[-1])
        runs.append(t)
        print(f"run {i}: {fmt(t)}", file=sys.stderr)
    med = {k: statistics.median(r[k] for r in runs) for k in STEPS}
    print("\nmedian of %d runs (seconds):" % len(runs), file=sys.stderr)
    for k in STEPS:
        print(f"  {k:<30}{med[k]:8.3f}", file=sys.stderr)
    print(f"  {'sum of medians':<30}{sum(med.values()):8.3f}", file=sys.stderr)


if __name__ == "__main__":
    main()
