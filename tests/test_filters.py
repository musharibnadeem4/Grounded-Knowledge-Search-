"""MIN_CHUNK_CHARS and QUERY_CLEAN against the real index (skipped if ./index is missing)."""
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

BASE = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
BASE.INDEX_DIR = INDEX
BASE.MANIFEST_PATH = ROOT / "manifest.csv"

QUERIES = [("consumer", "PepsiCo net revenue FY2021"), ("consumer", "Pfizer revenue 2022"),
           ("tech_telecom", "AMD gross margin. Answer in percent."),
           ("lead", "Which company reported the highest backlog?")]


def test_defaults_are_off():
    assert config.MIN_CHUNK_CHARS == 0 and config.QUERY_CLEAN is False


def test_min_chunk_chars_drops_short_hits_and_keeps_acl():
    cfg = copy.copy(BASE)
    cfg.MIN_CHUNK_CHARS = 400
    for role, q in QUERIES:
        hits = retrieve(q, role, 10, cfg)
        assert hits and len(hits) <= 10
        assert all(len(h.text.strip()) >= 400 for h in hits)
        assert {h.company for h in hits} <= set(acl.allowed_companies(role))


def test_min_chunk_chars_results_come_from_unfiltered_candidates():
    cfg = copy.copy(BASE)
    cfg.MIN_CHUNK_CHARS = 400
    wide = {h.chunk_id for h in retrieve("PepsiCo net revenue FY2021", "consumer",
                                         10 * cfg.MIN_CHUNK_OVERFETCH, BASE)}
    got = {h.chunk_id for h in retrieve("PepsiCo net revenue FY2021", "consumer", 10, cfg)}
    assert got <= wide


def test_query_clean_keeps_acl_and_returns_hits():
    cfg = copy.copy(BASE)
    cfg.QUERY_CLEAN = True
    for role, q in QUERIES:
        hits = retrieve(q, role, 10, cfg)
        assert hits
        assert {h.company for h in hits} <= set(acl.allowed_companies(role))
