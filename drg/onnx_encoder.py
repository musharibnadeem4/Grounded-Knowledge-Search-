"""Query-time embedding with onnxruntime + tokenizers only (no torch / transformers / sentence-transformers import).

Same model as the index (bge-small-en-v1.5): CLS pooling, L2-normalised, max 512 tokens. Created by
scripts/export_onnx.py; adopted only if scripts/verify_onnx.py confirms cosine > 0.999 against the torch embeddings
(config.ONNX_ENCODER).
"""
import json
from pathlib import Path

import numpy as np


class OnnxEncoder:
    def __init__(self, model_dir):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        d = Path(model_dir)
        if not (d / "model.onnx").exists():
            raise FileNotFoundError(f"{d / 'model.onnx'} missing; run: python scripts/export_onnx.py")
        meta = json.loads((d / "export_meta.json").read_text(encoding="utf-8"))
        self.max_len = int(meta.get("max_seq_length", 512))
        self.tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.tok.enable_truncation(max_length=self.max_len)
        self.tok.enable_padding()  # pad to the longest in the batch
        so = ort.SessionOptions()
        so.log_severity_level = 3
        self.sess = ort.InferenceSession(str(d / "model.onnx"), sess_options=so,
                                         providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True,
               batch_size=32):
        """Same call shape as SentenceTransformer.encode as used in drg.retrieve."""
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.tok.encode_batch(list(texts[i:i + batch_size]))
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, feed)[0]
            vec = hidden[:, 0, :]  # CLS pooling
            if normalize_embeddings:
                vec = vec / np.maximum(np.linalg.norm(vec, axis=1, keepdims=True), 1e-12)
            out.append(vec.astype(np.float32))
        return np.concatenate(out, axis=0)
