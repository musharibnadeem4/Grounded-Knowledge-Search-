"""ACL tests against the real index (skipped if ./index is missing)."""
import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from drg import acl, config
from drg.retrieve import retrieve

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index"

pytestmark = pytest.mark.skipif(not (INDEX / "chroma.sqlite3").exists(),
                                reason="./index is missing; run ingest first")

CFG = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
CFG.INDEX_DIR = INDEX
CFG.MANIFEST_PATH = ROOT / "manifest.csv"

BM25_BUILT = (ROOT / "index_bm25" / "meta.json").exists()


@pytest.fixture(params=[(False, False), (True, False), (False, True), (True, True)],
                ids=["filter_off", "filter_on", "hybrid_filter_off", "hybrid_filter_on"])
def cfg(request):
    """Every retrieval test runs with YEAR_COMPANY_FILTER off/on and with HYBRID_BM25 off/on."""
    year_filter, hybrid = request.param
    if hybrid and not BM25_BUILT:
        pytest.skip("./index_bm25 missing; python -m drg.bm25 build --index-dir index")
    c = copy.copy(CFG)
    c.YEAR_COMPANY_FILTER = year_filter
    c.HYBRID_BM25 = hybrid
    return c


OFF_DESK_QUERIES = {
    "consumer": ["Pfizer revenue 2022", "AMD R&D expense", "Boeing commercial airplanes backlog",
                 "Verizon wireless subscribers", "Johnson & Johnson litigation talc"],
    "health_industrials": ["PepsiCo net revenue 2021", "Best Buy domestic comparable sales",
                           "AMD data center segment revenue", "Verizon total debt",
                           "Ulta Beauty store count"],
    "tech_telecom": ["Pfizer vaccine revenue", "Boeing 737 MAX deliveries",
                     "3M restructuring charges", "PepsiCo Frito-Lay operating profit",
                     "MGM Resorts Las Vegas Strip revenue"],
}

LEAD_QUERIES = [
    "PepsiCo net revenue", "Best Buy gross profit rate", "MGM Resorts casino revenue",
    "Ulta Beauty net sales", "Johnson & Johnson pharmaceutical sales",
    "Pfizer research and development", "3M operating income", "Boeing backlog",
    "AMD gross margin", "Adobe subscription revenue",
    "Corning optical communications sales", "Verizon wireline revenue",
]


def test_manifest_matches_acl():
    acl.check_manifest(ROOT / "manifest.csv")
    assert len(acl.allowed_companies("lead")) == 12


def test_unknown_role():
    with pytest.raises(acl.UnknownRole):
        acl.allowed_companies("intern")


@pytest.mark.parametrize("role", sorted(OFF_DESK_QUERIES))
def test_off_desk_queries_never_leak(role, cfg):
    allowed = set(acl.allowed_companies(role))
    for q in OFF_DESK_QUERIES[role]:
        hits = retrieve(q, role, 20, cfg)
        assert hits, f"no results for {q!r}"
        assert {h.company for h in hits} <= allowed, (
            role, q, {h.company for h in hits} - allowed)


def test_lead_sees_many_companies(cfg):
    seen = set()
    for q in LEAD_QUERIES:
        seen |= {h.company for h in retrieve(q, "lead", 10, cfg)}
    assert len(seen) >= 10, seen


def test_consumer_naming_pfizer_and_year_stays_on_desk():
    cfg = copy.copy(CFG)
    cfg.YEAR_COMPANY_FILTER = True
    allowed = set(acl.allowed_companies("consumer"))
    for q in ("Pfizer revenue 2022", "What was Pfizer's FY2022 revenue?"):
        hits = retrieve(q, "consumer", 20, cfg)
        assert hits
        assert {h.company for h in hits} <= allowed


def test_flag_narrows_to_named_company():
    cfg = copy.copy(CFG)
    cfg.YEAR_COMPANY_FILTER = True
    hits = retrieve("PepsiCo net revenue in FY2021", "consumer", 20, cfg)
    assert hits and {h.company for h in hits} == {"PepsiCo"}


# ------------------------------------------- ask-time paths: expansion, per-page cap, ONNX encoder, sub-queries
from drg import answer as _answer  # noqa: E402
from drg.query import parse_query  # noqa: E402

ONNX_BUILT = (ROOT / "models" / "bge-small-en-v1.5-onnx" / "model.onnx").exists()


@pytest.fixture(params=["expand_cap", "expand_cap_onnx"])
def ask_cfg(request):
    c = copy.copy(CFG)
    c.YEAR_COMPANY_FILTER = True
    c.QUERY_EXPAND = True
    c.ASK_MAX_CHUNKS_PER_PAGE = 1
    if request.param.endswith("onnx"):
        if not ONNX_BUILT:
            pytest.skip("ONNX export missing")
        c.ONNX_ENCODER = True
    return c


@pytest.mark.parametrize("role", sorted(OFF_DESK_QUERIES))
def test_ask_context_never_leaks(role, ask_cfg):
    """The exact retrieval `ask` uses (gather: sub-queries per company, expansion, page cap) stays on the desk,
    even when the question names companies of other desks (ask itself refuses those before retrieval)."""
    allowed = set(acl.allowed_companies(role))
    for q in OFF_DESK_QUERIES[role] + ["Compare R&D spending at AMD and Pfizer in 2022 and the capex of Boeing"]:
        companies, _ = parse_query(q)
        hits = _answer.gather(q, role, companies, ask_cfg)
        assert {h.company for h in hits} <= allowed, (role, q, {h.company for h in hits} - allowed)


def test_ask_refuses_off_desk_before_any_retrieval(ask_cfg, monkeypatch):
    monkeypatch.setattr(_answer, "retrieve", lambda *a, **k: pytest.fail("retrieve() must not be called"))
    r = _answer.answer("Pfizer R&D expense 2022", "consumer", ask_cfg)
    assert r["status"] == "refused" and r["citations"] == []
