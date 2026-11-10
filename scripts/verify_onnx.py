#!/usr/bin/env python
"""Check the ONNX encoder against the torch (SentenceTransformer) embeddings on 200 sample texts.

  python scripts/verify_onnx.py [--n 200]

Texts: random chunk texts from ./index (read-only), plus the tune/holdout-free dev questions. Adoption criterion:
minimum cosine > 0.999. Output goes to stdout.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drg import config, hf  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    import chromadb
    from chromadb.config import Settings

    coll = chromadb.PersistentClient(path=str(ROOT / "index"),
                                     settings=Settings(anonymized_telemetry=False)).get_collection(config.COLLECTION)
    rng = random.Random(7)
    total = coll.count()
    offs = sorted(rng.sample(range(total), a.n - 20))
    texts = []
    for o in offs:
        texts += coll.get(limit=1, offset=o, include=["documents"])["documents"]
    texts += [json.loads(l)["question"] for l in open(ROOT / "eval" / "questions.jsonl", encoding="utf-8")]
    print(f"{len(texts)} texts, chars min/median/max = {min(map(len, texts))}/"
          f"{int(np.median(list(map(len, texts))))}/{max(map(len, texts))}")

    hf.prefer_offline(config.EMBED_MODEL)
    from sentence_transformers import SentenceTransformer

    from drg.onnx_encoder import OnnxEncoder

    st = SentenceTransformer(config.EMBED_MODEL)
    ox = OnnxEncoder(ROOT / "models" / "bge-small-en-v1.5-onnx")
    t0 = time.perf_counter()
    a_emb = st.encode(texts, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
    t1 = time.perf_counter()
    b_emb = ox.encode(texts, normalize_embeddings=True)
    t2 = time.perf_counter()
    cos = (a_emb * b_emb).sum(axis=1)
    print(f"cosine torch vs onnx: min={cos.min():.6f} mean={cos.mean():.6f} max={cos.max():.6f}; "
          f"n below 0.999: {(cos < 0.999).sum()}")
    print(f"batch encode time: torch {t1 - t0:.1f}s, onnx {t2 - t1:.1f}s")
    one = [texts[-1]]
    t = time.perf_counter(); st.encode(one, normalize_embeddings=True); ts = time.perf_counter() - t
    t = time.perf_counter(); ox.encode(one, normalize_embeddings=True); to = time.perf_counter() - t
    print(f"single query warm: torch {ts * 1000:.1f} ms, onnx {to * 1000:.1f} ms")
    return 0 if cos.min() > 0.999 else 1


if __name__ == "__main__":
    sys.exit(main())
