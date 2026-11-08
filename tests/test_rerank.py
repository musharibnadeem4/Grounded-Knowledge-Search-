"""Reranker tests against the real index. Needs the reranker model (downloaded on first use);
skipped if the index is missing or the model cannot be loaded."""
import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from drg import acl, config
from drg.retrieve import _reranker, retrieve

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index"
RERANKER = config.RERANKERS_ALLOWED[0]  # cross-encoder/ms-marco-MiniLM-L-6-v2 (smaller)

pytestmark = pytest.mark.skipif(not (INDEX / "chroma.sqlite3").exists(),
                                reason="./index is missing; run ingest first")

BASE = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
BASE.INDEX_DIR = INDEX
BASE.MANIFEST_PATH = ROOT / "manifest.csv"

QUERIES = [
    ("consumer", "What drove the increase in Ulta Beauty's merchandise inventories in FY2023?"),
    ("consumer", "Pfizer revenue 2022"),  # off-desk company named
    ("health_industrials", "Is 3M a capital-intensive business based on FY2022 data?"),
    ("tech_telecom", "Did AMD report customer concentration in FY22?"),
    ("lead", "Which company reported the highest backlog?"),
]


@pytest.fixture(scope="module")
def reranker_cfg():
    c = copy.copy(BASE)
    c.RERANKER = RERANKER
    try:
        _reranker(c)
    except Exception as e:  # no network / model not cached
        pytest.skip(f"cannot load reranker {RERANKER}: {e}")
    return c


@pytest.mark.parametrize("year_company_filter", [False, True], ids=["filter_off", "filter_on"])
def test_reranked_results_are_subset_of_unreranked_depth_candidates(
        reranker_cfg, year_company_filter):
    plain = copy.copy(BASE)  # RERANKER = None
    plain.YEAR_COMPANY_FILTER = year_company_filter
    rr = copy.copy(reranker_cfg)
    rr.YEAR_COMPANY_FILTER = year_company_filter
    rr.RERANK_DEPTH = 50
    for role, q in QUERIES:
        candidates = {h.chunk_id for h in retrieve(q, role, rr.RERANK_DEPTH, plain)}
        hits = retrieve(q, role, 10, rr)
        assert hits and len(hits) <= 10
        assert {h.chunk_id for h in hits} <= candidates, (role, q)
        assert {h.company for h in hits} <= set(acl.allowed_companies(role)), (role, q)
        scores = [h.score for h in hits]
        assert scores == sorted(scores, reverse=True), "must be sorted by reranker score"


def test_rejects_unlisted_reranker():
    c = copy.copy(BASE)
    c.RERANKER = "some/other-model"
    with pytest.raises(ValueError):
        retrieve("anything", "lead", 3, c)
