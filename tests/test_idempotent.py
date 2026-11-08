"""Idempotency of ingest. Uses the real embedding model (downloaded on first run)."""
import csv
import shutil
from pathlib import Path

import pytest

from drg import ingest as ing

ROOT = Path(__file__).resolve().parent.parent
SMALL = "ULTABEAUTY_2024Q2_EARNINGS"  # 10 pages
SRC_PDF = ROOT / "pdfs" / f"{SMALL}.pdf"
SRC_MANIFEST = ROOT / "manifest.csv"

pytestmark = pytest.mark.skipif(
    not (SRC_PDF.exists() and SRC_MANIFEST.exists()), reason="corpus files not present")


def _setup(tmp_path):
    corpus = tmp_path / "corpus dir"  # space in path on purpose
    corpus.mkdir()
    # lower-case filename: must still match the manifest's doc_id spelling
    shutil.copy(SRC_PDF, corpus / f"{SMALL.lower()}.pdf")
    with open(SRC_MANIFEST, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r["doc_id"] == SMALL]
    assert len(rows) == 1
    manifest = tmp_path / "manifest.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    # an unlisted PDF that must never be indexed
    shutil.copy(SRC_PDF, corpus / "NOT_IN_MANIFEST.pdf")
    return corpus, manifest, tmp_path / "cache", tmp_path / "index"


def _run(corpus, manifest, cache, index):
    assert ing.ingest(corpus, manifest, cache, index, workers=1) == 0


def test_ingest_idempotent_and_replace(tmp_path):
    corpus, manifest, cache, index = _setup(tmp_path)
    run = lambda: _run(corpus, manifest, cache, index)

    run()
    coll = ing.open_collection(index)
    n1 = coll.count()
    assert n1 > 0
    got = coll.get(include=["metadatas"])
    assert {m["doc_id"] for m in got["metadatas"]} == {SMALL}  # manifest spelling
    assert min(m["page"] for m in got["metadatas"]) >= 1
    assert (cache / f"{SMALL}.jsonl").exists()

    # sentinel: same doc_id, so it is deleted only if the doc is re-ingested
    coll.add(ids=["sentinel"], documents=["stale"], embeddings=[[0.0] * 384],
             metadatas=[{"doc_id": SMALL, "page": 0}])
    assert coll.count() == n1 + 1

    # 1) unchanged -> skipped, sentinel untouched
    run()
    assert ing.open_collection(index).count() == n1 + 1

    # 2) byte-modified copy under the same doc_id -> old chunks removed, new added
    pdf = corpus / f"{SMALL.lower()}.pdf"
    pdf.write_bytes(pdf.read_bytes() + b"\n% modified\n")
    run()
    coll = ing.open_collection(index)
    assert coll.count() == n1  # same count; sentinel (old chunk) gone
    assert coll.get(ids=["sentinel"])["ids"] == []
    assert ing.load_hashes(index)[SMALL] == ing.sha256_file(pdf)
