"""eval/answer_metrics.py: numeric matching and per-question / aggregate answer scoring."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
import answer_metrics as M  # noqa: E402


@pytest.mark.parametrize("text,spec,ok", [
    ("AMD spent $5.0 billion on R&D.", {"kind": "usd_m", "values": [5005]}, True),
    ("R&D was $5,005 million.", {"kind": "usd_m", "values": [5005]}, True),
    ("R&D was $5,005.", {"kind": "usd_m", "values": [5005]}, True),
    ("Net revenues were 5,162,082 thousand.", {"kind": "usd_m", "values": [5162.08]}, True),
    ("Accounts payable $303.00", {"kind": "usd_m", "values": [303]}, True),
    ("PP&E was 1577.00", {"kind": "usd_m", "values": [1577]}, True),
    ("capex of $4.6 billion", {"kind": "usd_m", "values": [4600]}, True),
    ("revenue was $4.0 billion", {"kind": "usd_m", "values": [5005]}, False),
    ("about 4.5% of sales", {"kind": "pct", "values": [4.53]}, True),
    ("10.3 percent decline", {"kind": "pct", "values": [10.29]}, True),
    ("a 10% decline", {"kind": "pct", "values": [10.29]}, True),       # rounding-aware
    ("a 9% decline", {"kind": "pct", "values": [10.29]}, False),
    ("AMD net income was $1.3 billion", {"kind": "usd_m", "values": [1320]}, True),
    ("Verizon 21,748 and AMD 1,320", {"kind": "usd_m", "values": [[21256, 21748], [1320]], "mode": "all"}, True),
    ("Verizon 21,256 and AMD 1,320", {"kind": "usd_m", "values": [[21256, 21748], [1320]], "mode": "all"}, True),
    ("Verizon 20,000 and AMD 1,320", {"kind": "usd_m", "values": [[21256, 21748], [1320]], "mode": "all"}, False),
    ("approximately 134,500 employees", {"kind": "count", "values": [134500]}, True),
    ("134.5 thousand employees", {"kind": "count", "values": [134500]}, True),
    ("both: AMD $5,005M and Pfizer $11,428M", {"kind": "usd_m", "values": [5005, 11428], "mode": "all"}, True),
    ("only AMD $5,005M", {"kind": "usd_m", "values": [5005, 11428], "mode": "all"}, False),
    ("either: 46,298", {"kind": "usd_m", "values": [51761, 46298], "mode": "any"}, True),
    ("$5,005 million\u202f", {"kind": "usd_m", "values": [5005]}, True),
])
def test_numeric_match(text, spec, ok):
    assert M.numeric_match(text, spec) is ok


def _q(type_="answerable", **kw):
    return dict(type=type_, gold=[{"doc_id": "D", "pages": [3]}], alt_gold=[{"doc_id": "D", "pages": [4]}], **kw)


def test_score_answer_answerable():
    q = _q(numeric={"kind": "usd_m", "values": [100]})
    res = {"status": "answered", "answer": "It was $100 million [C1].",
           "citations": [{"doc_id": "D", "page": 4}, {"doc_id": "X", "page": 1}]}
    m = M.score_answer(q, res, 2.0, True, 1)
    assert m["status_ok"] and m["numeric_ok"] and m["cite_hit"] and m["cite_precision"] == 0.5
    assert m["answer_ok"] is True and m["ungrounded_warnings"] == 1


def test_score_answer_refusals():
    off = _q("off_desk")
    assert M.score_answer(off, {"status": "refused", "answer": "x", "citations": []}, 0.1, False, 0)["answer_ok"]
    assert not M.score_answer(off, {"status": "answered", "answer": "x", "citations": []}, 0.1, True, 0)["answer_ok"]
    q = _q(numeric={"kind": "pct", "values": [5]})   # answerable but refused -> wrong
    m = M.score_answer(q, {"status": "refused", "answer": "no", "citations": []}, 0.1, True, 0)
    assert m["status_ok"] is False and m["answer_ok"] is False
    manual = M.score_answer(_q(), {"status": "answered", "answer": "yes", "citations": []}, 0.1, True, 0)
    assert manual["answer_ok"] is None  # no numeric spec: manual review


def test_summarize_refusal_precision_recall():
    def row(type_, got):
        return {"type": type_, "answer_metrics": {
            "status_ok": (got == "answered") == (type_ == "answerable"), "got": got, "numeric_ok": None,
            "cite_hit": None, "cite_precision": None, "ungrounded_warnings": 0, "seconds": 1.0}}
    rows = [row("answerable", "answered"), row("answerable", "refused"), row("off_desk", "refused"),
            row("unanswerable", "answered")]
    s = M.summarize(rows)
    assert s["refusal_recall"] == 0.5          # 1 of 2 negatives refused
    assert s["refusal_precision"] == 0.5       # 2 refusals, 1 correct
    assert s["status_accuracy"] == 0.5


def test_confident_error_rate_and_refusal_rates():
    def row(type_, got, num_ok):
        return {"type": type_, "answer_metrics": {
            "status_ok": True, "got": got, "numeric_ok": num_ok, "cite_hit": None, "cite_precision": None,
            "ungrounded_warnings": 0, "seconds": 1.0}}
    rows = [row("answerable", "answered", True),    # right
            row("answerable", "answered", False),   # confident error
            row("answerable", "answered", False),   # confident error
            row("answerable", "refused", False),    # refused numeric question: not a confident error
            row("answerable", "answered", None),    # no numeric gold: outside the population
            row("off_desk", "refused", None)]
    s = M.summarize(rows)
    assert s["n_numeric"] == 4 and s["n_confident_errors"] == 2
    assert s["confident_error_rate"] == 0.5            # 2 of 4 numeric-gold questions
    assert s["numeric_accuracy"] == 0.25               # 1 of 4
    assert s["refusal_rate_numeric"] == 0.25           # 1 of 4 refused
    assert s["refusal_rate_on_answerable"] == pytest.approx(0.2)   # 1 of 5 answerable refused
    assert M.confident_error_rate([row("off_desk", "answered", False)]) is None
