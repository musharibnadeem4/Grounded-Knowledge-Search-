"""ACL tests against the real index (skipped if ./index is missing)."""
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
def test_off_desk_queries_never_leak(role):
    allowed = set(acl.allowed_companies(role))
    for q in OFF_DESK_QUERIES[role]:
        hits = retrieve(q, role, 20, CFG)
        assert hits, f"no results for {q!r}"
        assert {h.company for h in hits} <= allowed, (
            role, q, {h.company for h in hits} - allowed)


def test_lead_sees_many_companies():
    seen = set()
    for q in LEAD_QUERIES:
        seen |= {h.company for h in retrieve(q, "lead", 10, CFG)}
    assert len(seen) >= 10, seen
