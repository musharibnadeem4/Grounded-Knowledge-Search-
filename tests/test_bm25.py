"""drg/bm25.py: tokenizer, fusion, and that BM25 only ever scores/returns chunks allowed by the filter."""
import chromadb
import pytest
from chromadb.config import Settings

from drg import bm25

DOCS = [  # (id, company, text)
    ("a1", "AMD", "Research and development expenses were 5,005 million"),
    ("a2", "AMD", "Marketing general and administrative expenses"),
    ("p1", "Pfizer", "Research and development expenses were 11,428 million"),
    ("p2", "Pfizer", "Research and development research and development research and development"),
    ("b1", "Boeing", "Research and development expense decreased"),
]


@pytest.fixture
def built(tmp_path, monkeypatch):
    monkeypatch.setattr(bm25, "_state", {})
    idx = tmp_path / "idx"
    coll = chromadb.PersistentClient(path=str(idx), settings=Settings(anonymized_telemetry=False)
                                     ).create_collection("chunks", metadata={"hnsw:space": "cosine"})
    coll.add(ids=[d[0] for d in DOCS], documents=[d[2] for d in DOCS],
             embeddings=[[1.0, 0.0, float(i)] for i in range(len(DOCS))],
             metadatas=[{"company": d[1], "page_header": "Statements", "chunk_id": d[0]} for d in DOCS])
    bm25.build(idx)
    return idx, coll


def test_tokenize_stops_and_plurals():
    assert bm25.tokenize("The Research and Development expenses of AMD") == \
        ["research", "development", "expense", "amd"]


def test_rrf():
    s = bm25.rrf([["a", "b"], ["b", "c"]], k=60)
    assert s["b"] > s["a"] > s["c"]


def test_top_only_returns_allowed_chunks(built):
    idx, coll = built
    allowed = bm25.top(idx, coll, {"company": {"$in": ["AMD"]}}, "research and development", 10)
    assert {i for i, _ in allowed} <= {"a1", "a2"} and allowed[0][0] == "a1"
    both = bm25.top(idx, coll, {"company": {"$in": ["AMD", "Boeing"]}}, "research and development", 10)
    assert {i for i, _ in both} <= {"a1", "a2", "b1"}
    assert bm25.top(idx, coll, {"company": {"$in": ["Corning"]}}, "research and development", 10) == []


def test_statistics_come_from_candidates_only(built):
    """The score of an AMD chunk must not change when other companies' chunks exist: idf/avgdl are computed
    on the filtered candidates only, so out-of-scope documents cannot influence it."""
    idx, coll = built
    s_amd_only = dict(bm25.top(idx, coll, {"company": {"$in": ["AMD"]}}, "research development", 10))
    # same AMD candidates, but the collection also holds Pfizer/Boeing chunks (outside the filter)
    assert s_amd_only["a1"] == pytest.approx(
        dict(bm25.top(idx, coll, {"$and": [{"company": {"$in": ["AMD", "Pfizer"]}}, {"company": "AMD"}]},
                      "research development", 10))["a1"])


def test_retrieve_hybrid_returns_k_hits():
    """Regression: hybrid fusion looks at HYBRID_DEPTH candidates but retrieve() must return exactly k."""
    import copy
    from pathlib import Path
    from types import SimpleNamespace

    from drg import config
    from drg.retrieve import retrieve

    root = Path(__file__).resolve().parent.parent
    if not (root / "index_bm25" / "meta.json").exists() or not (root / "index" / "chroma.sqlite3").exists():
        pytest.skip("index / index_bm25 not built")
    cfg = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.INDEX_DIR, cfg.MANIFEST_PATH = root / "index", root / "manifest.csv"
    cfg.HYBRID_BM25 = True
    for k in (3, 8, 20):
        assert len(retrieve("AMD research and development 2022", "lead", k, cfg)) == k
