"""drg/onnx_export.ensure_onnx: auto-export at the end of ingest, with verification and a safe failure mode."""
from drg import onnx_export as OX


def _fake_export(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "model.onnx").write_bytes(b"x")


def test_existing_export_is_left_alone(tmp_path):
    d = tmp_path / "m"
    d.mkdir()
    (d / "model.onnx").write_bytes(b"x")
    assert OX.ensure_onnx(d, exporter=lambda p: (_ for _ in ()).throw(AssertionError("must not export"))) is True


def test_missing_export_is_created_and_verified(tmp_path, capsys):
    d = tmp_path / "m"
    assert OX.ensure_onnx(d, exporter=_fake_export, verifier=lambda p: 0.99999) is True
    assert (d / "model.onnx").exists() and not (tmp_path / "m.tmp").exists()
    assert "export verified" in capsys.readouterr().err


def test_low_cosine_keeps_fallback_and_parks_the_export(tmp_path, capsys):
    d = tmp_path / "m"
    assert OX.ensure_onnx(d, exporter=_fake_export, verifier=lambda p: 0.95) is False
    assert not d.exists() and (tmp_path / "m.failed" / "model.onnx").exists()   # kept, not deleted
    assert "WARN onnx export failed" in capsys.readouterr().err


def test_export_exception_warns_and_never_raises(tmp_path, capsys):
    def boom(p):
        p.mkdir(parents=True)
        raise RuntimeError("no onnx module")
    assert OX.ensure_onnx(tmp_path / "m", exporter=boom, verifier=lambda p: 1.0) is False
    err = capsys.readouterr().err
    assert "WARN onnx export failed" in err and "sentence-transformers" in err


def test_twenty_verification_texts():
    assert len(OX.VERIFY_TEXTS) == 20
