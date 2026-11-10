"""Unit tests for drg.query (parsing and where-clause building). No index needed."""
import json
from pathlib import Path

import pytest

from drg import acl
from drg.query import build_where, clean_query, company_periods, load_periods, parse_query

ROOT = Path(__file__).resolve().parent.parent

# Expected parse of every dev question (checked by hand against the question text).
DEV_EXPECTED = {
    "fb_00735": ({"PepsiCo"}, 2022),            # FY2022 and FY2021 -> max
    "fb_04171": ({"MGM Resorts"}, 2018),
    "fb_00603": ({"Ulta Beauty"}, 2023),
    "fb_00499": ({"3M"}, 2022),
    "fb_10285": ({"Boeing"}, 2018),
    "fb_00494": ({"Boeing"}, 2023),
    "fb_00215": ({"Verizon"}, 2022),            # "FY 2022"
    "fb_10130": ({"Corning"}, 2020),            # FY2020 and FY2019 -> max
    "fb_00757": ({"AMD"}, 2022),                # "FY22"
    "fb_01275": ({"Best Buy"}, 2023),
    "fb_04980": ({"PepsiCo"}, 2021),
    "fb_00407": ({"MGM Resorts"}, 2023),        # "MGM", "H1 FY2023"
    "fb_00941": ({"3M"}, 2023),                 # "Q2 of 2023"
    "fb_03029": ({"3M"}, 2018),
    "fb_01484": ({"Johnson & Johnson"}, 2022),  # "JnJ"
    "fb_00005": ({"Corning"}, 2022),
    "fb_03069": ({"AMD"}, 2015),
    "fb_00591": ({"Adobe"}, 2022),
    "fb_01254": ({"MGM Resorts"}, 2022),
    "fb_02608": ({"Best Buy"}, 2017),           # FY2015 - FY2017 -> max
}


def _dev_questions():
    p = ROOT / "dev_questions.jsonl"
    if not p.exists():
        pytest.skip("dev_questions.jsonl missing")
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def test_every_dev_question_parse():
    qs = _dev_questions()
    assert {q["id"] for q in qs} == set(DEV_EXPECTED), "dev set changed; update DEV_EXPECTED"
    for q in qs:
        assert parse_query(q["question"]) == DEV_EXPECTED[q["id"]], q["id"]


@pytest.mark.parametrize("text,expected", [
    ("AMD FY22 revenue", ({"AMD"}, 2022)),
    ("Best Buy margin 2015 - 2017", ({"Best Buy"}, 2017)),
    ("no year here", (set(), None)),
    ("MGM H1 FY2023 debt", ({"MGM Resorts"}, 2023)),
    ("3M or MMM, Q2 2023", ({"3M"}, 2023)),
    ("Pepsi versus Best Buy in fiscal 2021", ({"PepsiCo", "Best Buy"}, 2021)),
    ("J&J, JnJ and Johnson  &  Johnson", ({"Johnson & Johnson"}, None)),
    ("Pepsico's pepsi cola sales", ({"PepsiCo"}, None)),
    ("fiscal 2019 compared with fiscal year 2021", (set(), 2021)),
    ("Spent $2020.5 million; FY1999 and FY35 are out of range", (set(), None)),
    ("AMDX and Adobes are not matches", (set(), None)),
    ("FY2024 guidance vs FY2026 outlook", (set(), 2026)),
    ("ulta beauty fy 2023", ({"Ulta Beauty"}, 2023)),
])
def test_tricky_parses(text, expected):
    assert parse_query(text) == expected


def test_company_periods():
    assert company_periods({"2021", "2022"}, 2022) == ["2022"]
    assert company_periods({"2023", "2024"}, 2022) == ["2023", "2024"]
    assert company_periods({"2024"}, 2022) == ["2024"]
    assert company_periods({"2015", "2016"}, 2023) is None


def _strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    else:
        yield x


def test_build_where_never_widens():
    periods = load_periods(ROOT / "manifest.csv")
    for role in ("consumer", "health_industrials", "tech_telecom", "lead"):
        allowed = acl.allowed_companies(role)
        for companies in (set(), {"Pfizer"}, {"PepsiCo", "Boeing"}, set(allowed), {"nobody"}):
            for year in (None, 2022, 2023, 2030):
                where, chosen = build_where(allowed, companies, year, periods)
                assert set(chosen) <= set(allowed)
                assert where["$and"][0] == {"company": {"$in": allowed}} if "$and" in where \
                    else where == {"company": {"$in": allowed}}
                named = {s for s in _strings(where) if s in acl.DESK_COMPANIES["lead"]}
                assert named <= set(allowed), (role, companies, year, named - set(allowed))


def test_build_where_empty_intersection_falls_back_to_role():
    periods = load_periods(ROOT / "manifest.csv")
    allowed = acl.allowed_companies("consumer")
    where, chosen = build_where(allowed, {"Pfizer"}, None, periods)
    assert chosen == allowed
    assert where == {"company": {"$in": allowed}}


def test_build_where_year_rules():
    periods = {"A": {"2022", "2023"}, "B": {"2023", "2024"}, "C": {"2015"}}
    where, chosen = build_where(["A", "B", "C"], {"A", "B", "C"}, 2022, periods)
    clauses = where["$and"][1]["$or"]
    assert clauses[0] == {"$and": [{"company": "A"}, {"period": {"$in": ["2022"]}}]}
    assert clauses[1] == {"$and": [{"company": "B"}, {"period": {"$in": ["2023", "2024"]}}]}
    assert clauses[2] == {"company": "C"}  # no 2022 / 2023 / 2024 filing -> no year filter


def test_clean_query_all_dev_questions():
    """Prints original -> cleaned (run pytest -s to see) and checks nothing comes out empty."""
    for q in _dev_questions():
        cleaned = clean_query(q["question"])
        print(f"{q['id']}: {q['question']!r} -> {cleaned!r}")
        assert cleaned.strip(), q["id"]


@pytest.mark.parametrize("text,expected", [
    # keeps '?' sentences and company/year sentences, drops filler
    ("You are an analyst. Be precise. What was Boeing's backlog?", "What was Boeing's backlog?"),
    ("Pfizer reported results in 2022. Please answer briefly.", "Pfizer reported results in 2022."),
    # nothing qualifies -> original
    ("Tell me about revenue. Be brief.", "Tell me about revenue. Be brief."),
    ("", ""),
    # single question sentence unchanged
    ("Did AMD report customer concentration in FY22?", "Did AMD report customer concentration in FY22?"),
])
def test_clean_query_cases(text, expected):
    assert clean_query(text) == expected


# ------------------------------------------------------------ expand_query (QUERY_EXPAND)
import pytest as _pytest  # noqa: E402
from drg.query import expand_query  # noqa: E402


@_pytest.mark.parametrize("q,expect", [
    ("Compare R&D spending at AMD and Pfizer in 2022.", "research and development"),
    ("What share of 3M's sales did it reinvest in capex?", "purchases of property, plant and equipment"),
    ("How did the bottom line change?", "net income"),
    ("What was Adobe's headcount in fiscal 2016?", "number of employees"),
    ("What was SG&A?", "selling, general and administrative"),
    ("Show the balance sheet totals", "statement of financial position"),
    ("Look at the P&L", "statements of operations"),
])
def test_expand_query_adds_formal_terms(q, expect):
    out, added = expand_query(q)
    assert out.startswith(q) and expect in out and added


def test_expand_query_noop_without_shorthand():
    q = "Who joined the board in March 2023?"
    assert expand_query(q) == (q, [])


# ------------------------------------------------------- forward-looking years (FORECAST_PRIOR_YEAR)
from drg.query import company_periods, is_forward_looking  # noqa: E402


def test_is_forward_looking():
    assert is_forward_looking("What production rate changes is Boeing forecasting for FY2023?")
    assert is_forward_looking("What is PepsiCo's guidance for 2023?")
    assert not is_forward_looking("What was Boeing's revenue in 2022?")
    assert not is_forward_looking("Did the project finish on time?")


def test_company_periods_forward():
    assert company_periods({"2021", "2022"}, 2023) is None                       # unchanged default
    assert company_periods({"2021", "2022"}, 2023, forward=True) == ["2022"]     # prior-year filing
    assert company_periods({"2022", "2023"}, 2023, forward=True) == ["2023"]     # exact period still wins
    assert company_periods({"2024"}, 2023, forward=True) == ["2024"]             # falls back to later filings
