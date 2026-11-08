"""Tests for the ask pipeline. No index, model or network: retrieval and the LLM are mocked."""
import json

from pathlib import Path

import pytest
import requests

from drg import answer as A
from drg import ask, config, llm
from drg.retrieve import Hit

ROOT = Path(__file__).resolve().parent.parent


def hit(n, company="PepsiCo", text="Net revenue was 2,415 million."):
    return Hit(doc_id=f"DOC_{n}", page=n, chunk_id=f"chunk{n}", score=0.5, text=text,
               company=company, page_header="Statement (In millions)", period="2022")


@pytest.fixture(autouse=True)
def real_manifest(monkeypatch):
    monkeypatch.setattr(config, "MANIFEST_PATH", ROOT / "manifest.csv")
    A._periods_cache.clear()


@pytest.fixture
def no_retrieval(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("retrieve() must not be called")
    monkeypatch.setattr(A, "retrieve", boom)
    monkeypatch.setattr(llm, "chat", boom)


def fake_llm(monkeypatch, payload):
    calls = []

    def chat(system, user, timeout=None):
        calls.append((system, user))
        return payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr(llm, "chat", chat)
    return calls


# ------------------------------------------------------------------ off-desk
@pytest.mark.parametrize("q", [
    "Pfizer revenue 2022",
    "Compare PepsiCo and Pfizer revenue in FY2022",   # one company off-desk is enough
])
def test_off_desk_refusal_makes_no_retrieval_call(no_retrieval, q):
    r = A.answer(q, "consumer")
    assert r == {"status": "refused", "answer": A.OFF_DESK, "citations": []}


def test_lead_is_not_off_desk(monkeypatch):
    seen = []
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: seen.append((a, k)) or [hit(1)])
    fake_llm(monkeypatch, {"status": "answered", "answer": "Revenue was 2,415 million [C1]."})
    assert A.answer("Pfizer revenue 2022", "lead")["status"] == "answered"
    assert seen


# ---------------------------------------------------------------- post-check
def test_postcheck_drops_invalid_markers():
    hits = [hit(1), hit(2)]
    text, cites = A.postcheck("Rev [C1]. Profit [C5]. Both [C2, C9]. Zero [C0].", hits)
    assert text == "Rev [C1]. Profit . Both [C2]. Zero ."
    assert [c["chunk_id"] for c in cites] == ["chunk1", "chunk2"]
    assert cites[0] == {"doc_id": "DOC_1", "page": 1, "chunk_id": "chunk1"}


def test_postcheck_dedupes_citations_in_order_of_use():
    _, cites = A.postcheck("a [C2] b [C1] c [C2]", [hit(1), hit(2)])
    assert [c["chunk_id"] for c in cites] == ["chunk2", "chunk1"]


@pytest.mark.parametrize("llm_answer", [
    "Revenue was 2,415 million.",            # no markers at all
    "Revenue was 2,415 million [C9].",       # only an invalid marker
])
def test_answered_without_valid_citation_becomes_refused(monkeypatch, llm_answer):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])
    fake_llm(monkeypatch, {"status": "answered", "answer": llm_answer})
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r == {"status": "refused", "answer": A.NO_CITATION, "citations": []}


def test_answered_with_valid_citation(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1), hit(2)])
    fake_llm(monkeypatch, {"status": "answered",
                           "answer": "Net revenue was 2,415 million (FY2022) [C2] [C7]."})
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r["status"] == "answered"
    assert r["citations"] == [{"doc_id": "DOC_2", "page": 2, "chunk_id": "chunk2"}]
    assert "[C7]" not in r["answer"] and "[C2]" in r["answer"]


def test_number_check_warns_but_does_not_fail(capsys):
    h = hit(1, text="Net revenue was 2,415 million.")
    warned = A.check_numbers("Revenue was 2,415 [C1]. Profit was 9,999 [C1].", [h])
    assert warned == ["9999"]
    assert "WARN number 9,999" in capsys.readouterr().err
    # calculation results, years and small integers are not flagged
    assert A.check_numbers("In 2022 there were 3 segments. Result: 4,830 = 2,415 * 2 [C1]", [h]) == []


# ----------------------------------------------------------- refuse / errors
@pytest.mark.parametrize("payload", [
    {"status": "refused", "answer": "REFUSE"},
    {"status": "answered", "answer": "REFUSE"},
])
def test_llm_refuse(monkeypatch, payload):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])
    fake_llm(monkeypatch, payload)
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r == {"status": "refused", "answer": A.NO_ANSWER, "citations": []}


def test_llm_error_returns_refused_llm_unavailable(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])

    def chat(*a, **k):
        raise llm.LLMError("timeout")
    monkeypatch.setattr(llm, "chat", chat)
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r == {"status": "refused", "answer": "LLM unavailable", "citations": []}


def test_invalid_llm_json_is_refused(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])
    fake_llm(monkeypatch, "this is not json")
    assert A.answer("What was PepsiCo net revenue in FY2022?", "consumer")["status"] == "refused"


def test_no_hits_is_refused_without_calling_llm(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [])
    monkeypatch.setattr(llm, "chat", lambda *a, **k: pytest.fail("LLM must not be called"))
    assert A.answer("What was PepsiCo net revenue in FY2022?", "consumer")["status"] == "refused"


# --------------------------------------------------------------- retrieval plan
def test_single_company_one_retrieve_call(monkeypatch):
    calls = []
    monkeypatch.setattr(A, "retrieve", lambda q, role, k, cfg, **kw: calls.append((k, kw)) or [hit(1)])
    fake_llm(monkeypatch, {"status": "answered", "answer": "x 2,415 [C1]"})
    A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert calls == [(config.ASK_K, {})]


def test_multi_company_retrieves_per_company_and_interleaves(monkeypatch):
    calls = []

    def fake(q, role, k, cfg, companies=None):
        calls.append((k, tuple(companies)))
        c = companies[0]
        return [hit(i, company=c).__class__(doc_id=f"{c}_{i}", page=i, chunk_id=f"{c}{i}",
                                            score=0.1, text="t", company=c) for i in range(1, k + 1)]
    monkeypatch.setattr(A, "retrieve", fake)
    calls_llm = fake_llm(monkeypatch, {"status": "answered", "answer": "x [C1]"})
    A.answer("Compare Best Buy and PepsiCo revenue in FY2022", "consumer")
    assert calls == [(6, ("Best Buy",)), (6, ("PepsiCo",))]  # ASK_K_PER_COMPANY each
    ctx = calls_llm[0][1]
    # interleaved: Best Buy, PepsiCo, Best Buy, PepsiCo ...
    assert ctx.index("[C1] Best Buy_1") < ctx.index("[C2] PepsiCo_1") < ctx.index("[C3] Best Buy_2")


def test_per_company_depth_is_ask_k_per_company_regardless_of_company_count(monkeypatch):
    ks = []
    monkeypatch.setattr(A, "retrieve", lambda q, role, k, cfg, companies=None: ks.append(k) or [])
    A.gather("x", "lead", {"AMD", "Adobe"}, config)
    A.gather("x", "lead", {"AMD", "Adobe", "Corning", "Verizon"}, config)
    assert ks == [config.ASK_K_PER_COMPANY] * 6 and config.ASK_K_PER_COMPANY == 6


def test_context_block_format():
    ctx = A.build_context([hit(1)])
    first = ctx.splitlines()[0]
    assert first == "[C1] DOC_1 | PepsiCo | 2022 | page 1 | Statement (In millions)"


# ------------------------------------------------------------------- llm.py
def test_llm_errors_become_llmerror(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    def timeout(*a, **k):
        raise requests.Timeout("slow")
    monkeypatch.setattr(requests, "post", timeout)
    with pytest.raises(llm.LLMError):
        llm.chat("s", "u")


def test_groq_without_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(llm, "load_dotenv", lambda *a, **k: None)
    with pytest.raises(llm.LLMError):
        llm.chat("s", "u")


# --------------------------------------------------------------------- CLI
def test_cli_prints_exactly_one_json_object(no_retrieval, capsys):
    assert ask.main(["--role", "consumer", "Pfizer revenue 2022"]) == 0
    out = capsys.readouterr().out
    assert len(out.strip().splitlines()) == 1
    assert json.loads(out) == {"status": "refused", "answer": A.OFF_DESK, "citations": []}


def test_cli_unknown_role_still_prints_json(capsys):
    assert ask.main(["--role", "intern", "anything"]) == 2
    obj = json.loads(capsys.readouterr().out)
    assert obj["status"] == "refused" and obj["citations"] == []


# ------------------------------------------------- citation marker forms + logging
@pytest.mark.parametrize("form,expected_text,expected_chunks", [
    ("[C1]", "[C1]", ["chunk1"]),
    ("[C1, C3]", "[C1, C3]", ["chunk1", "chunk3"]),
    ("[C1][C3]", "[C1][C3]", ["chunk1", "chunk3"]),
    ("[C1-C3]", "[C1, C2, C3]", ["chunk1", "chunk2", "chunk3"]),
    ("(C1)", "[C1]", ["chunk1"]),
    ("\u3010C1\u3011", "[C1]", ["chunk1"]),
    # extras that follow from the same parser
    ("[C1; C3]", "[C1, C3]", ["chunk1", "chunk3"]),
    ("[c2\u2013c3]", "[C2, C3]", ["chunk2", "chunk3"]),   # en dash, lower case
    ("[C2-C9]", "[C2, C3]", ["chunk2", "chunk3"]),        # out-of-range members dropped
    ("[C7-C9]", "", []),                                  # nothing valid -> marker removed
])
def test_citation_marker_forms(form, expected_text, expected_chunks):
    hits = [hit(1), hit(2), hit(3)]
    text, cites = A.postcheck(f"Revenue was 2,415 million {form}.", hits)
    assert text == f"Revenue was 2,415 million {expected_text}."
    assert [c["chunk_id"] for c in cites] == expected_chunks


def test_non_citations_are_left_alone():
    text, cites = A.postcheck("See Note C (C. 2022) and [Cx] and (C) and section C1.", [hit(1)])
    assert text == "See Note C (C. 2022) and [Cx] and (C) and section C1."
    assert cites == []


def test_number_check_ignores_all_marker_forms(capsys):
    h = hit(1, text="Net revenue was 2,415 million.")
    A.check_numbers("Revenue was 2,415 (C1) and 2,415 \u3010C1\u3011 and 2,415 [C1-C1].", [h])
    assert "WARN" not in capsys.readouterr().err


def test_answer_with_alternative_marker_forms_is_answered(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1), hit(2), hit(3)])
    fake_llm(monkeypatch, {"status": "answered", "answer": "Net revenue was 2,415 million \u3010C2\u3011 (C3)."})
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r["status"] == "answered"
    assert [c["chunk_id"] for c in r["citations"]] == ["chunk2", "chunk3"]


def test_logs_retrieved_chunks_and_raw_llm_response(monkeypatch, capsys):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1), hit(2)])
    raw = json.dumps({"status": "answered", "answer": "Revenue 2,415 [C1]. " + "x" * 3000})
    fake_llm(monkeypatch, raw)
    A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    err = capsys.readouterr().err
    assert "C1 DOC_1 p.1" in err and "C2 DOC_2 p.2" in err
    line = next(l for l in err.splitlines() if l.startswith("LLM raw response"))
    assert line.endswith(raw[:2000]) and raw[:2001] not in line  # first 2,000 chars only


# ------------------------------------------------------------ text normalisation
@pytest.mark.parametrize("raw,expected", [
    ("1\u202f234", "1 234"),                 # narrow no-break space
    ("a\u00a0b", "a b"),                     # no-break space
    ("Form 10\u2011K", "Form 10-K"),         # non-breaking hyphen (NFKC alone would give U+2010)
    ("2015\u20132017", "2015-2017"),         # en dash
    ("\uff21\uff22\uff23 \u2460", "ABC 1"),  # NFKC: full-width letters, circled digit
    ("\ufb01nal \u00bd", "final 1\u20442"),  # NFKC: ligature, vulgar fraction
    ("plain text", "plain text"),
])
def test_normalize_text(raw, expected):
    out = A.normalize_text(raw)
    assert out == expected
    assert "\u202f" not in out and "\u00a0" not in out and "\u2011" not in out and "\u2013" not in out


def test_final_answer_is_normalised_and_fullwidth_markers_still_parse(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: [hit(1)])
    fake_llm(monkeypatch, {"status": "answered",
                           "answer": "Net revenue was 2,415\u00a0million\u2013FY2022 (10\u2011K) \uff3bC1\uff3d."})
    r = A.answer("What was PepsiCo net revenue in FY2022?", "consumer")
    assert r["status"] == "answered"
    assert r["answer"] == "Net revenue was 2,415 million-FY2022 (10-K) [C1]."
    assert [c["chunk_id"] for c in r["citations"]] == ["chunk1"]


# ----------------------------------------------- ungrounded-number check: ignores
def test_number_check_ignores_form_names_years_and_small_integers(capsys):
    h = hit(1, text="Net revenue was 2,415 million.")
    text = ("Per Form 10-K, the 10-Q, the 8-K, the 10-K/A and the Form 10-K405 filings, "
            "the 9 segments reported in 1990, 2022 and 2030 had revenue of 2,415 [C1].")
    assert A.check_numbers(text, [h]) == []
    assert "WARN" not in capsys.readouterr().err


@pytest.mark.parametrize("text,warned", [
    ("Profit was 9,999 [C1].", ["9999"]),
    ("There were 10 segments [C1].", ["10"]),              # integers >= 10 are checked
    ("Revenue was 2,015 million [C1].", ["2015"]),         # comma = a figure, not a year
    ("Margin was 7.5% [C1].", ["7.5"]),                    # decimals are checked even if < 10
    ("The 2031 outlook was 5 [C1].", ["2031"]),            # outside 1990-2030
    ("Form 10-K shows 9,999 [C1].", ["9999"]),             # form name ignored, figure still checked
])
def test_number_check_still_flags_real_figures(text, warned):
    h = hit(1, text="Net revenue was 2,415 million.")
    assert A.check_numbers(text, [h]) == warned


# ------------------------------------------------------------------ partial answers
def test_system_prompt_allows_partial_answers_and_limits_refuse():
    p = A.SYSTEM_PROMPT
    assert "only part of the question can be answered" in p
    assert "which part is not in the provided filings" in p
    assert 'status "answered"' in p
    assert "only when the context contains nothing relevant to the exact company and period" in p


# ------------------------------------------------------- out-of-range refusal
def test_latest_periods_in_manifest_are_what_the_tests_assume():
    from drg.query import load_periods
    per = load_periods(ROOT / "manifest.csv")
    assert max(per["Boeing"]) == "2022" and max(per["PepsiCo"]) == "2023"


@pytest.mark.parametrize("q,role,msg", [
    ("What did Boeing report for FY2024?", "health_industrials",
     "No filings in the corpus cover FY2024 for Boeing."),
    ("What is Boeing's backlog forecast for FY2030?", "lead",
     "No filings in the corpus cover FY2030 for Boeing."),
    # every named company is out of range -> all are listed
    ("Compare Boeing and Pfizer in FY2030", "health_industrials",
     "No filings in the corpus cover FY2030 for Boeing, Pfizer."),
])
def test_out_of_range_year_refused_before_retrieval(no_retrieval, capsys, q, role, msg):
    r = A.answer(q, role)
    assert r == {"status": "refused", "answer": msg, "citations": []}
    assert "beyond the corpus" in capsys.readouterr().err  # logged


@pytest.mark.parametrize("q,role", [
    ("What production rate changes is Boeing forecasting for FY2023?", "health_industrials"),  # latest 2022 + 1
    ("What was Boeing's revenue in FY2022?", "health_industrials"),
    ("What is Boeing's revenue?", "health_industrials"),                                      # no year
    ("Which was higher in FY2025, Boeing or Pfizer?", "health_industrials"),                  # Pfizer latest 2023: 2025 > 2024 too
])
def test_in_range_or_yearless_questions_are_not_refused_by_range(monkeypatch, q, role):
    called = []
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: called.append(1) or [])
    r = A.answer(q, role)
    if "FY2025" in q:
        assert r["answer"].startswith("No filings in the corpus cover FY2025")
    else:
        assert called  # got as far as retrieval


def test_mixed_range_multi_company_question_still_retrieves(monkeypatch):
    # PepsiCo's latest period is 2023, Boeing's 2022: FY2024 is within PepsiCo's +1 only
    called = []
    monkeypatch.setattr(A, "retrieve", lambda *a, **k: called.append(1) or [])
    A.answer("Compare PepsiCo and Boeing in FY2024", "lead")
    assert called  # not out of range for every company, so retrieval proceeds


# ------------------------------------------------- per-company sub-queries
@pytest.mark.parametrize("question,company,expected", [
    ("Compare R&D spending at AMD and Pfizer in 2022", "AMD", "R&D spending at AMD in 2022"),
    ("Compare R&D spending at AMD and Pfizer in 2022", "Pfizer", "R&D spending at Pfizer in 2022"),
    ("AMD vs Adobe revenue FY2022", "AMD", "AMD revenue FY2022"),
    ("AMD vs Adobe revenue FY2022", "Adobe", "Adobe revenue FY2022"),
    ("Which had higher revenue in FY2022, Boeing or Pfizer?", "Boeing",
     "Which had higher revenue in FY2022, Boeing?"),
    ("Which had higher revenue in FY2022, Boeing or Pfizer?", "Pfizer",
     "Which had higher revenue in FY2022, Pfizer?"),
    ("Compare AMD's and Adobe's R&D in FY2022", "AMD", "AMD's R&D in FY2022"),
    ("Compare AMD, Adobe and Corning gross margin in 2021", "Adobe", "Adobe gross margin in 2021"),
    ("Compare AMD, Adobe and Corning gross margin in 2021", "Corning", "Corning gross margin in 2021"),
    ("How did JnJ compared to Pfizer perform in 2022?", "Pfizer", "How did Pfizer perform in 2022?"),
    ("How did JnJ compared to Pfizer perform in 2022?", "Johnson & Johnson", "How did JnJ perform in 2022?"),
    ("Pfizer versus Boeing: which spent more on R&D in 2020?", "Boeing",
     "Boeing: which spent more on R&D in 2020?"),
])
def test_company_subquery(question, company, expected):
    from drg.query import company_subquery, parse_query
    sub = company_subquery(question, company)
    assert sub == expected
    assert parse_query(sub)[0] == {company}  # exactly one company left, and the year survives
    assert parse_query(sub)[1] == parse_query(question)[1]


def test_company_subquery_falls_back_to_original_question():
    from drg.query import company_subquery
    assert company_subquery("x", "AMD") == "x"   # company not in the text: unchanged


def test_ask_retrieves_with_one_subquery_per_company_and_logs_them(monkeypatch, capsys):
    seen = []

    def fake(q, role, k, cfg, companies=None):
        seen.append((q, k, tuple(companies)))
        return [hit(len(seen), company=companies[0])]
    monkeypatch.setattr(A, "retrieve", fake)
    fake_llm(monkeypatch, {"status": "answered", "answer": "x [C1]"})
    question = "Compare R&D spending at AMD and Adobe in 2022"
    A.answer(question, "tech_telecom")
    assert seen == [("R&D spending at AMD in 2022", 6, ("AMD",)),
                    ("R&D spending at Adobe in 2022", 6, ("Adobe",))]
    err = capsys.readouterr().err
    assert "sub-query [AMD]: 'R&D spending at AMD in 2022'" in err
    assert "sub-query [Adobe]: 'R&D spending at Adobe in 2022'" in err


def test_llm_still_sees_the_original_question(monkeypatch):
    monkeypatch.setattr(A, "retrieve", lambda q, role, k, cfg, companies=None: [hit(1, company=companies[0])])
    calls = fake_llm(monkeypatch, {"status": "answered", "answer": "x [C1]"})
    question = "Compare R&D spending at AMD and Adobe in 2022"
    A.answer(question, "tech_telecom")
    assert calls[0][1].endswith(f"Question: {question}")
