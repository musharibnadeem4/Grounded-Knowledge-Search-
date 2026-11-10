"""ingest --context-header (E1): embedded text gets a header, stored text stays original."""
import csv
import shutil
from pathlib import Path

import numpy as np
import pytest

from drg import config
from drg import ingest as ing

ROOT = Path(__file__).resolve().parent.parent
SMALL = "ULTABEAUTY_2024Q2_EARNINGS"  # 10 pages
SRC_PDF = ROOT / "pdfs" / f"{SMALL}.pdf"
SRC_MANIFEST = ROOT / "manifest.csv"

META = {"company": "Ulta Beauty", "doc_type": "Earnings", "period": "2024", "page": 3,
        "page_header": "Condensed Statements\n(In millions)"}


# ------------------------------------------------------------------ pure functions
def test_context_prefix_format():
    assert ing.context_prefix(META) == \
        "Ulta Beauty | Earnings | FY2024 | p.3 | Condensed Statements\n(In millions)\n"


def test_embed_inputs():
    docs = ["alpha", "beta"]
    metas = [META, dict(META, page=4, page_header="H")]
    assert ing.embed_inputs(docs, metas, False) == docs
    out = ing.embed_inputs(docs, metas, True)
    assert out[0] == ing.context_prefix(metas[0]) + "alpha"
    assert out[1] == "Ulta Beauty | Earnings | FY2024 | p.4 | H\nbeta"
    assert docs == ["alpha", "beta"]  # inputs untouched


def test_read_index_meta_missing(tmp_path):
    assert ing.read_index_meta(tmp_path) is None


# ------------------------------------------------------------------------ guards
def test_context_header_is_default():
    import argparse
    import inspect
    assert inspect.signature(ing.ingest).parameters["context_header"].default is True
    captured = {}
    orig = ing.ingest
    ing.ingest = lambda *a, **k: captured.update(k) or 0
    try:
        ing.main(["x"])
        assert captured["context_header"] is True
        ing.main(["x", "--no-context-header"])
        assert captured["context_header"] is False
    finally:
        ing.ingest = orig


def test_refuses_plain_chunks_into_header_index(tmp_path):
    idx = tmp_path / "idx"
    idx.mkdir()
    (idx / config.HASHES_FILE).write_text("{}")
    (idx / config.INDEX_META_FILE).write_text('{"context_header": true}')
    with pytest.raises(SystemExit) as e:
        ing.ingest(tmp_path, SRC_MANIFEST, tmp_path / "cache", idx, context_header=False)
    assert "context_header=True" in str(e.value)


def test_refuses_to_mix_chunk_styles(tmp_path):
    idx = tmp_path / "idx"
    idx.mkdir()
    (idx / config.HASHES_FILE).write_text("{}")
    (idx / config.INDEX_META_FILE).write_text('{"context_header": false}')
    with pytest.raises(SystemExit) as e:
        ing.ingest(tmp_path, SRC_MANIFEST, tmp_path / "cache", idx, context_header=True)
    assert "context_header=False" in str(e.value)
    # an old index with no meta file counts as context_header=False too
    (idx / config.INDEX_META_FILE).unlink()
    with pytest.raises(SystemExit):
        ing.ingest(tmp_path, SRC_MANIFEST, tmp_path / "cache", idx, context_header=True)


# ------------------------------------------------------------------- integration
@pytest.mark.skipif(not (SRC_PDF.exists() and SRC_MANIFEST.exists()), reason="corpus not present")
def test_context_header_changes_embeddings_not_stored_text(tmp_path):
    corpus = tmp_path / "corpus dir"
    corpus.mkdir()
    shutil.copy(SRC_PDF, corpus / f"{SMALL}.pdf")
    with open(SRC_MANIFEST, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["doc_id"] == SMALL]
    manifest = tmp_path / "manifest.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cache = tmp_path / "cache"  # shared: the second ingest reuses the parse cache

    plain, ch = tmp_path / "plain", tmp_path / "ch"
    assert ing.ingest(corpus, manifest, cache, plain, workers=1, context_header=False) == 0
    assert (cache / f"{SMALL}.jsonl").exists()
    assert ing.ingest(corpus, manifest, cache, ch, workers=1, context_header=True) == 0

    assert ing.read_index_meta(plain)["context_header"] is False
    assert ing.read_index_meta(ch)["context_header"] is True

    a = ing.open_collection(plain).get(include=["documents", "embeddings", "metadatas"])
    b = ing.open_collection(ch).get(include=["documents", "embeddings", "metadatas"])
    assert sorted(a["ids"]) == sorted(b["ids"]) and len(a["ids"]) > 0

    docs_a, docs_b = dict(zip(a["ids"], a["documents"])), dict(zip(b["ids"], b["documents"]))
    assert docs_a == docs_b  # stored chunk text is identical and prefix-free
    assert all("| FY2024 |" not in d.split("\n", 1)[0] for d in docs_b.values())

    emb_a, emb_b = dict(zip(a["ids"], a["embeddings"])), dict(zip(b["ids"], b["embeddings"]))
    cos = [float(np.dot(emb_a[i], emb_b[i])) for i in a["ids"]]  # both L2-normalised
    assert max(cos) < 0.9999, "embedding input must differ when the header is added"
    assert np.mean(cos) < 0.99
