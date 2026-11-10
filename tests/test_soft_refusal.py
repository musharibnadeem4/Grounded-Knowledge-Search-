"""Soft refusals: the five-way numeric outcome (eval scorer) and the PROMPT_VERSION=4 post-check in ask."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import answer_metrics as M  # noqa: E402
from drg import answer as A  # noqa: E402
from drg import config, llm, unavailable  # noqa: E402
from drg.retrieve import Hit  # noqa: E402

# real answers from the first runs (shortened)
DPO = ("The balance sheet provides accounts payable of $1,174 million for FY2020 and $1,587 million for FY2019 [C2]. "
       "The average accounts payable is therefore (1,174 + 1,587) / 2 = 1,380.5 million. However, the FY2020 cost of goods "
       "sold (COGS) figure required for the denominator of the DPO formula is not present in the provided filings, "
       "so the DPO cannot be computed from the available data.")
DPO_Q = "what is FY2020 days payable outstanding (DPO) for Corning? Round your answer to two decimal places."
AMD_PFE = ("AMD reported research and development expenses of $5.0 billion in 2022 (reported as $5,005 million) [C5]. "
           "The filings provided do not contain a specific figure for Pfizer's total R&D spending in 2022.")
WRONG = "PepsiCo's organic sales grew 10 % in the first quarter of 2023 [C2]."
CAVEAT = "Revenue was $5,005 million in 2022 [C1]. The 2021 figure is not in the provided filings."


# ---------------------------------------------------------------- detector
def test_soft_refusal_single_company_with_inputs_listed():
    assert unavailable.soft_refusal(DPO_Q, DPO, 1) is True          # inputs listed, asked figure unavailable


def test_partial_multi_company_stays_answered():
    assert unavailable.soft_refusal("Compare R&D spending at AMD and Pfizer in 2022.", AMD_PFE, 2) is False


def test_multi_company_with_no_figure_at_all_is_a_soft_refusal():
    t = "The provided documents do not contain research and development figures for AMD or Pfizer."
    assert unavailable.soft_refusal("Compare R&D spending at AMD and Pfizer in 2022.", t, 2) is True


def test_wrong_figure_and_plain_answers_are_not_soft_refusals():
    assert unavailable.soft_refusal("How fast did PepsiCo's organic sales grow?", WRONG, 1) is False
    assert unavailable.soft_refusal("What was revenue in 2022?", "Revenue was $5,005 million [C1].", 1) is False


def test_unrelated_caveat_does_not_trigger_when_it_shares_no_word_with_the_question():
    assert unavailable.soft_refusal("What was Adobe's operating profit?", CAVEAT, 1) is False


# ---------------------------------------------------------------- scorer outcomes
SPEC1 = {"kind": "pct", "values": [14.3], "mode": "any"}
SPEC2 = {"kind": "usd_m", "values": [5005, 11428], "mode": "all"}


@pytest.mark.parametrize("text,spec,got,ok,outcome", [
    ("It was 14.3% [C1].", SPEC1, "answered", True, "correct"),
    ("It was 10 % [C1].", SPEC1, "answered", False, "confident_error"),
    ("The organic growth figure is not disclosed in the provided filings.", SPEC1, "answered", False, "soft_refusal"),
    (DPO, {"kind": "count", "values": [63.86]}, "answered", False, "soft_refusal"),
    (AMD_PFE, SPEC2, "answered", False, "partial"),
    ("AMD $5,005 million and Pfizer $9,000 million [C1].", SPEC2, "answered", False, "confident_error"),
    ("not disclosed in the filings", SPEC2, "answered", False, "soft_refusal"),   # no expected figure at all
    ("REFUSE", SPEC1, "refused", False, "refused"),
])
def test_classify_numeric(text, spec, got, ok, outcome):
    assert M.classify_numeric(text, spec, got, ok) == outcome


def test_summarize_reports_five_rates_that_sum_to_one():
    def row(outcome):
        got = "refused" if outcome == "refused" else "answered"
        return {"type": "answerable", "answer_metrics": {
            "status_ok": True, "got": got, "numeric_ok": outcome == "correct", "outcome": outcome, "cite_hit": None,
            "cite_precision": None, "ungrounded_warnings": 0, "seconds": 1.0}}
    rows = [row(o) for o in ("correct", "correct", "partial", "soft_refusal", "refused", "confident_error")]
    s = M.summarize(rows)
    assert (s["correct_rate"], s["partial_rate"], s["soft_refusal_rate"], s["refused_rate"], s["confident_error_rate"]) == \
        pytest.approx((2 / 6, 1 / 6, 1 / 6, 1 / 6, 1 / 6))
    assert sum(s[f"{o}_rate"] for o in M.OUTCOMES) == pytest.approx(1.0)
    assert s["n_confident_errors"] == 1 and s["answered_wrong_rate"] == pytest.approx(3 / 6)   # old two-way reading


def test_score_answer_stores_the_outcome():
    q = {"type": "answerable", "numeric": SPEC1, "gold": [], "alt_gold": []}
    m = M.score_answer(q, {"status": "answered", "answer": "not disclosed in the filings", "citations": []}, 1.0, True, 0)
    assert m["outcome"] == "soft_refusal" and m["numeric_ok"] is False


# ---------------------------------------------------------------- ask: PROMPT_VERSION = 4
def hit(n):
    return Hit(doc_id=f"DOC_{n}", page=n, chunk_id=f"chunk{n}", score=0.5, text="Net revenue was 2,415 million.",
               company="PepsiCo", page_header="Statement (In millions)", period="2022")


def cfg(version):
    class C:
        pass
    for k in dir(config):
        if k.isupper():
            setattr(C, k, getattr(config, k))
    C.PROMPT_VERSION = version
    return C


@pytest.fixture(autouse=True)
def _pin(monkeypatch):
    monkeypatch.setattr(config, "MANIFEST_PATH", ROOT / "manifest.csv")
    A._periods_cache.clear()
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])


def _reply(monkeypatch, payload):
    monkeypatch.setattr(llm, "chat", lambda s, u, timeout=None: json.dumps(payload))


def test_v4_prompt_has_the_rule_and_the_citations_field():
    p = A.system_prompt(cfg(4))
    assert p is A.SYSTEM_PROMPT_V4
    assert "If you cannot give the specific figure or fact asked for, set status to refused; " \
           "you may still list the inputs you found." in p
    assert '"citations"' in p
    assert "If you cannot give the specific figure" not in A.SYSTEM_PROMPT_V3 and A.system_prompt(config) is A.SYSTEM_PROMPT


def test_v4_turns_a_soft_refusal_into_a_refusal_and_logs_it(monkeypatch, capsys):
    _reply(monkeypatch, {"status": "answered", "citations": ["C1"],
                         "answer": "Net revenue inputs found [C1]. The PepsiCo net revenue figure for 2022 cannot be computed "
                                   "from the provided filings."})
    r = A.answer("What was PepsiCo net revenue in 2022?", "consumer", cfg(4))
    assert r["status"] == "refused" and r["citations"] == [] and "cannot be computed" in r["answer"]
    assert "soft refusal" in capsys.readouterr().err and A.last_run["soft_refusal"] is True


def test_default_and_v3_keep_the_soft_refusal_as_answered(monkeypatch):
    for v in (1, 3):
        _reply(monkeypatch, {"status": "answered", "citations": ["C1"],
                             "answer": "The PepsiCo net revenue figure for 2022 cannot be computed from the provided filings [C1]."})
        assert A.answer("What was PepsiCo net revenue in 2022?", "consumer", cfg(v))["status"] == "answered"


def test_v4_leaves_a_correct_answer_and_a_partial_multi_company_answer_alone(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda q, role, k, c, companies=None: [hit(1)])
    _reply(monkeypatch, {"status": "answered", "citations": ["C1"], "answer": "Revenue was 2,415 million [C1]."})
    assert A.answer("What was PepsiCo net revenue in 2022?", "consumer", cfg(4))["status"] == "answered"
    _reply(monkeypatch, {"status": "answered", "citations": ["C1"],
                         "answer": "PepsiCo net revenue was 2,415 million [C1]. Best Buy revenue is not in the provided filings."})
    assert A.answer("Compare PepsiCo and Best Buy revenue in 2022", "consumer", cfg(4))["status"] == "answered"
