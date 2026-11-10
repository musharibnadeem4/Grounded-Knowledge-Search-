"""ONNX_ENCODER on without an export: falls back to sentence-transformers (runs even when models/ is absent)."""

def test_missing_onnx_export_falls_back_to_sentence_transformers(tmp_path, monkeypatch, capsys):
    """ONNX_ENCODER on but no export on disk: warn and use sentence-transformers instead of failing."""
    import types

    from drg import config
    from drg import retrieve as R

    cfg = types.SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.ONNX_ENCODER, cfg.ONNX_DIR = True, tmp_path / "nope"
    monkeypatch.setattr(R, "_state", {})
    m = R._model(cfg)
    assert m.__class__.__name__ == "SentenceTransformer"
    assert "model.onnx is missing" in capsys.readouterr().err
