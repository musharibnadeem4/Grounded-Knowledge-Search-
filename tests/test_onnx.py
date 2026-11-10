"""ONNX query encoder: same embeddings as sentence-transformers (skipped if the export is missing)."""
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
ONNX_DIR = ROOT / "models" / "bge-small-en-v1.5-onnx"
pytestmark = pytest.mark.skipif(not (ONNX_DIR / "model.onnx").exists(),
                                reason="run scripts/export_onnx.py first")

TEXTS = ["What was AMD's research and development expense in 2022?",
         "Research and development 5,005 2,845 1,983",
         "short", "A " * 400]  # the last one is truncated at 512 tokens


def test_onnx_matches_torch():
    from drg import config, hf
    from drg.onnx_encoder import OnnxEncoder

    hf.prefer_offline(config.EMBED_MODEL)
    from sentence_transformers import SentenceTransformer

    a = SentenceTransformer(config.EMBED_MODEL).encode(TEXTS, normalize_embeddings=True, convert_to_numpy=True,
                                                       show_progress_bar=False)
    b = OnnxEncoder(ONNX_DIR).encode(TEXTS, normalize_embeddings=True)
    assert b.shape == a.shape == (4, 384)
    assert np.allclose(np.linalg.norm(b, axis=1), 1.0, atol=1e-5)
    assert ((a * b).sum(axis=1) > 0.999).all()


def test_onnx_batching_is_consistent():
    from drg.onnx_encoder import OnnxEncoder

    enc = OnnxEncoder(ONNX_DIR)
    together = enc.encode(TEXTS, batch_size=4)
    one_by_one = np.concatenate([enc.encode([t]) for t in TEXTS])
    assert np.allclose(together, one_by_one, atol=1e-4)

