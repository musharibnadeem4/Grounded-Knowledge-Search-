"""Export the embedding model to ONNX (fp32) and verify it against sentence-transformers.

Used by scripts/export_onnx.py and, automatically, at the end of `ingest` when models/bge-small-en-v1.5-onnx is
missing. Needs torch / transformers / onnx at export time only; the query-time encoder (drg/onnx_encoder.py) needs
onnxruntime + tokenizers. Nothing here ever raises into the caller of ensure_onnx(): failures are logged and the
sentence-transformers fallback in drg.retrieve keeps working.
"""
import json
import os
import shutil
import sys
from pathlib import Path

from . import config, hf

VERIFY_TEXTS = [
    "What was AMD's research and development expense in 2022?",
    "Research and development 5,005 2,845 1,983",
    "Net revenues were $5,162,082 thousand in 2020 compared with $12,899,672 thousand in 2019.",
    "Purchases of property, plant and equipment (1,603) (1,501) (1,699)",
    "Consolidated Statements of Cash Flows (In millions)",
    "Has the company reported any material ongoing legal proceedings?",
    "As of December 2, 2016, we employed 15,706 people.",
    "Item 3. Legal Proceedings. We are party to a variety of litigation.",
    "Operating income 6,098 5,802 4,237",
    "Total current assets less total current liabilities equals working capital.",
    "Johnson & Johnson completed its split-off exchange offer of Kenvue shares.",
    "Gross profit rate was 23.2 percent compared with 22.1 percent last year.",
    "Which segment had the highest revenue growth in the second quarter?",
    "Diluted earnings per share were $1.25 versus $1.35 a year ago.",
    "The Board increased the number of directors from eleven to twelve.",
    "Boeing expects to gradually increase the 737 production rate to 50 per month.",
    "Customer concentration: one customer accounted for 16% of consolidated net revenue.",
    "Dividends declared per share were $2.585 in 2022.",
    "Free cash flow conversion improved from 143% to 156%.",
    "short",
]


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def export(out_dir):
    """Write model.onnx + tokenizer.json + export_meta.json into out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hf.prefer_offline(config.EMBED_MODEL)
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoModel, AutoTokenizer

    src = snapshot_download(config.EMBED_MODEL)
    tok = AutoTokenizer.from_pretrained(src)
    model = AutoModel.from_pretrained(src).eval()

    class Wrap(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.m(input_ids=input_ids, attention_mask=attention_mask,
                          token_type_ids=token_type_ids).last_hidden_state

    enc = tok(["export example sentence", "another, longer example sentence for the dummy batch"],
              padding=True, return_tensors="pt")
    args = (enc["input_ids"], enc["attention_mask"], enc["token_type_ids"])
    axes = {k: {0: "batch", 1: "seq"} for k in ("input_ids", "attention_mask", "token_type_ids")}
    axes["last_hidden_state"] = {0: "batch", 1: "seq"}
    torch.onnx.export(Wrap(model), args, str(out / "model.onnx"),
                      input_names=["input_ids", "attention_mask", "token_type_ids"],
                      output_names=["last_hidden_state"], dynamic_axes=axes, opset_version=17, dynamo=False)
    shutil.copy(Path(src) / "tokenizer.json", out / "tokenizer.json")
    (out / "export_meta.json").write_text(json.dumps({
        "source": config.EMBED_MODEL, "pooling": "cls", "normalize": True, "max_seq_length": 512,
        "precision": "fp32", "torch": torch.__version__}, indent=1), encoding="utf-8")


def verify(out_dir, texts=None, threshold=0.999):
    """-> minimum cosine between the sentence-transformers and the ONNX embeddings of `texts`."""
    texts = texts or VERIFY_TEXTS
    from sentence_transformers import SentenceTransformer

    from .onnx_encoder import OnnxEncoder

    a = SentenceTransformer(config.EMBED_MODEL).encode(texts, normalize_embeddings=True, show_progress_bar=False,
                                                       convert_to_numpy=True)
    b = OnnxEncoder(out_dir).encode(texts, normalize_embeddings=True)
    return float((a * b).sum(axis=1).min())


def ensure_onnx(model_dir=None, exporter=None, verifier=None):
    """Make sure the ONNX export exists and is valid. -> True if usable afterwards, False otherwise (warned).
    Exports into '<dir>.tmp', verifies cosine > 0.999 on 20 texts, then renames to '<dir>'. A failed export is
    kept as '<dir>.failed' (never deleted) and the sentence-transformers fallback stays in use."""
    model_dir = Path(model_dir or config.ONNX_DIR)
    if (model_dir / "model.onnx").exists():
        return True
    exporter, verifier = exporter or export, verifier or verify
    tmp = model_dir.with_name(model_dir.name + ".tmp")
    failed = model_dir.with_name(model_dir.name + ".failed")
    try:
        log(f"onnx: {model_dir} missing; exporting the query encoder (one-off, ~1 min)")
        if tmp.exists():  # leftover of an interrupted export: park it, never delete
            tmp.rename(tmp.with_name(tmp.name + f".old{os.getpid()}"))
        exporter(tmp)
        cos = verifier(tmp)
        if not cos > 0.999:
            raise RuntimeError(f"ONNX embeddings differ from the torch embeddings (min cosine {cos:.5f} <= 0.999)")
        model_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(tmp, model_dir)
        log(f"onnx: export verified (min cosine {cos:.6f} on {len(VERIFY_TEXTS)} texts); wrote {model_dir}")
        return True
    except Exception as e:  # noqa: BLE001 - export is optional; never break ingest
        log(f"WARN onnx export failed ({type(e).__name__}: {e}). Queries will use sentence-transformers "
            f"(slower cold start, identical results). Fix and retry with: python scripts/export_onnx.py")
        if tmp.exists():
            try:
                tmp.rename(failed if not failed.exists() else failed.with_name(failed.name + f".{os.getpid()}"))
            except OSError:
                pass
        return False
