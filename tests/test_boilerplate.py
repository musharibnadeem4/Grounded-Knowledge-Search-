"""DROP_BOILERPLATE and PREFER_10K_OVER_ANNUALREPORT."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from drg import acl, boilerplate, config
from drg.ingest import clean_page
from drg.query import annualreport_exclusions
from drg.retrieve import retrieve

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "pages"
INDEX = ROOT / "index"


def cached_page(doc_id, page):
    p = CACHE / f"{doc_id}.jsonl"
    if not p.exists():
        pytest.skip(f"{p} not in cache")
    with open(p, encoding="utf-8") as f:
        f.readline()  # meta
        for line in f:
            r = json.loads(line)
            if r["page"] == page:
                body, header = clean_page(r["text"])
                return header, body
    pytest.fail(f"{doc_id} has no page {page}")


# --------------------------------------------------------------- exhibit detector
@pytest.mark.parametrize("doc_id,page", [
    ("AMD_2022_10K", 104), ("AMD_2022_10K", 105), ("AMD_2022_10K", 106),
    ("PEPSICO_2022_10K", 128),
])
def test_detector_fires_on_exhibit_index_pages(doc_id, page):
    header, body = cached_page(doc_id, page)
    assert boilerplate.exhibit_page(header, body), (doc_id, page, header[:60])


@pytest.mark.parametrize("doc_id,page", [("3M_2018_10K", 60), ("BOEING_2018_10K", 52)])
def test_detector_does_not_fire_on_statement_pages(doc_id, page):
    header, body = cached_page(doc_id, page)
    assert not boilerplate.exhibit_page(header, body), (doc_id, page)
    assert boilerplate.is_boilerplate(header, body) is None


# ---------------------------------------------------------------- synthetic cases
@pytest.mark.parametrize("header", [
    "Exhibit Index", "EXHIBIT 21", "Item 15. Exhibits and Financial Statement Schedules",
    "ITEM 15", "SIGNATURES", "  Signatures\nPursuant to the requirements",
])
def test_header_rule(header):
    assert boilerplate.exhibit_page(header, "some ordinary text\nmore text")


@pytest.mark.parametrize("header", ["Item 1A. Risk Factors", "Exhibition of results", "Signature bank loans"])
def test_header_rule_negative(header):
    assert not boilerplate.exhibit_page(header, "some ordinary text")


def test_forty_percent_rule():
    lines = ["10.19 Plan", "*10.25 Agreement", "31.1 Certification", "32.2 Certification", "x", "y"]
    assert boilerplate.exhibit_page("Header", "\n".join(lines))           # 4/6
    assert not boilerplate.exhibit_page("Header", "\n".join(lines[:2] + ["a", "b", "c", "d", "e"]))  # 2/7


def test_numeric_continuation_page_is_not_an_exhibit_page():
    text = "3.5 billion in revenue grew\nthe company said\nand more text here\nanother line"
    header = "3.5 billion in revenue grew\nthe company said"
    assert not boilerplate.exhibit_page(header, text)  # header looks numbered but only 1 line matches


def test_short_chunks():
    assert boilerplate.is_boilerplate("h", "x" * 79) == "short"
    assert boilerplate.is_boilerplate("h", "  " + "x" * 80 + "  ") is None
    assert boilerplate.is_boilerplate("SIGNATURES", "x" * 200) == "exhibit"


# ---------------------------------------------------------------- annual reports
def test_annualreport_exclusions_from_manifest():
    assert annualreport_exclusions(ROOT / "manifest.csv") == ["AMD_2022_annualreport"]


# ------------------------------------------------------- against the real index
needs_index = pytest.mark.skipif(not (INDEX / "chroma.sqlite3").exists(),
                                 reason="./index is missing; run ingest first")


def _cfg(**flags):
    c = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    c.INDEX_DIR = INDEX
    c.MANIFEST_PATH = ROOT / "manifest.csv"
    for k, v in flags.items():
        setattr(c, k, v)
    return c


def test_flags_default_off():
    assert config.DROP_BOILERPLATE is False and config.PREFER_10K_OVER_ANNUALREPORT is True
    assert config.YEAR_COMPANY_FILTER is True and config.RERANKER is None


@needs_index
def test_drop_boilerplate_removes_short_and_exhibit_chunks_and_keeps_acl(capsys):
    cfg = _cfg(DROP_BOILERPLATE=True)
    queries = [("tech_telecom", "AMD 2022 exhibits incorporated by reference stock purchase plan"),
               ("consumer", "PepsiCo Executive Incentive Compensation Plan exhibit 10.19"),
               ("lead", "signatures pursuant to the requirements of the Securities Exchange Act")]
    for role, q in queries:
        hits = retrieve(q, role, 10, cfg)
        assert hits
        assert all(boilerplate.is_boilerplate(h.page_header, h.text) is None for h in hits), q
        assert {h.company for h in hits} <= set(acl.allowed_companies(role))
    assert "drop_boilerplate: dropped" in capsys.readouterr().err  # logged per query


@needs_index
def test_prefer_10k_excludes_annual_report_doc():
    q = "AMD FY2022 revenue and gross margin"
    on = retrieve(q, "tech_telecom", 40, _cfg(PREFER_10K_OVER_ANNUALREPORT=True))
    assert on and all(h.doc_id != "AMD_2022_annualreport" for h in on)
    off = retrieve(q, "tech_telecom", 40, _cfg(PREFER_10K_OVER_ANNUALREPORT=False))
    assert any(h.doc_id == "AMD_2022_annualreport" for h in off), \
        "sanity: the annual report is retrievable when the flag is off"


@needs_index
def test_prefer_10k_keeps_acl_with_other_filters():
    cfg = _cfg(PREFER_10K_OVER_ANNUALREPORT=True, YEAR_COMPANY_FILTER=True, DROP_BOILERPLATE=True)
    hits = retrieve("Pfizer revenue 2022", "consumer", 20, cfg)
    assert hits and {h.company for h in hits} <= set(acl.allowed_companies("consumer"))
