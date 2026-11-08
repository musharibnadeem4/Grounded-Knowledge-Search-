"""Hugging Face cache helpers. Import-light on purpose: must run before
transformers / huggingface_hub / sentence_transformers are imported, because
huggingface_hub reads HF_HUB_OFFLINE once, at import time."""
import os
from pathlib import Path

_REQUIRED = ("config.json", "modules.json", "tokenizer.json")
_WEIGHTS = ("model.safetensors", "pytorch_model.bin")
_TOKENIZERS = ("tokenizer.json", "vocab.txt", "sentencepiece.bpe.model", "spiece.model")


def _hub_cache():
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "huggingface" / "hub"


def is_cached(model_id, need_modules=True):
    """need_modules=True: a sentence-transformers model (modules.json + tokenizer.json).
    False: a plain transformers model such as a cross-encoder reranker
    (config + weights + some tokenizer file)."""
    snaps = _hub_cache() / ("models--" + model_id.replace("/", "--")) / "snapshots"
    if not snaps.is_dir():
        return False
    for s in snaps.iterdir():
        if not any((s / w).exists() for w in _WEIGHTS):
            continue
        if need_modules:
            if all((s / f).exists() for f in _REQUIRED):
                return True
        elif (s / "config.json").exists() and any((s / t).exists() for t in _TOKENIZERS):
            return True
    return False


def prefer_offline(model_id, *rerankers):
    """Set HF_HUB_OFFLINE=1 if the embedding model (and any reranker given) is fully
    cached and the user hasn't set it. If anything isn't cached (e.g. first ingest, or a
    reranker's first use), leave the environment alone so it can download."""
    if "HF_HUB_OFFLINE" in os.environ:
        return
    if is_cached(model_id) and all(is_cached(r, need_modules=False) for r in rerankers):
        os.environ["HF_HUB_OFFLINE"] = "1"


def offline_enabled():
    """True if Hugging Face offline mode is on (set by us or by the user)."""
    return os.environ.get("HF_HUB_OFFLINE", "").strip().upper() in ("1", "ON", "YES", "TRUE")
