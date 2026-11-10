#!/usr/bin/env python
"""One-off: export the embedding model (bge-small-en-v1.5, CLS pooling) to ONNX (fp32, dynamic batch / length).

  python scripts/export_onnx.py [--out models/bge-small-en-v1.5-onnx] [--no-verify]

Thin wrapper over drg/onnx_export.py (the same code `ingest` runs automatically when the export is missing).
Writes model.onnx + tokenizer.json + export_meta.json; verifies cosine > 0.999 vs sentence-transformers on 20 texts.
Never touches ./index.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drg import onnx_export  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "models" / "bge-small-en-v1.5-onnx"))
    ap.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()
    onnx_export.export(a.out)
    if not a.no_verify:
        cos = onnx_export.verify(a.out)
        print(f"min cosine vs sentence-transformers on {len(onnx_export.VERIFY_TEXTS)} texts: {cos:.6f}", file=sys.stderr)
        return 0 if cos > 0.999 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
