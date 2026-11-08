"""Hugging Face cache helpers. Import-light on purpose: must run before
transformers / huggingface_hub / sentence_transformers are imported, because
huggingface_hub reads HF_HUB_OFFLINE once, at import time."""
import os
from pathlib import Path

_REQUIRED = ("config.json", "modules.json", "tokenizer.json")
_WEIGHTS = ("model.safetensors", "pytorch_model.bin")


def _hub_cache():
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "huggingface" / "hub"


def is_cached(model_id):
    snaps = _hub_cache() / ("models--" + model_id.replace("/", "--")) / "snapshots"
    if not snaps.is_dir():
        return False
    for s in snaps.iterdir():
        if all((s / f).exists() for f in _REQUIRED) and any((s / w).exists() for w in _WEIGHTS):
            return True
    return False


def prefer_offline(model_id):
    """Set HF_HUB_OFFLINE=1 if the model is fully cached and the user hasn't set it.
    If it isn't cached (e.g. first ingest), leave the environment alone so it downloads."""
    if "HF_HUB_OFFLINE" in os.environ:
        return
    if is_cached(model_id):
        os.environ["HF_HUB_OFFLINE"] = "1"
