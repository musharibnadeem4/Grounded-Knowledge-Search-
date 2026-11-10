"""run_eval: retrieval-only by default, cost estimate, --max-llm-calls PARTIAL, provider-quota stop."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import run_eval as RE  # noqa: E402
from drg import llm  # noqa: E402


def _qs(tmp_path, n=4):
    p = tmp_path / "q.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(json.dumps({"id": f"q{i}", "role": "lead", "question": "Adobe operating profit fiscal 2022",
                                "type": "answerable", "tags": [], "answer": "x",
                                "gold": [{"doc_id": "ADOBE_2022_10K", "pages": [54]}]}) + "\n")
    return p


@pytest.fixture
def stubbed(monkeypatch, tmp_path):
    monkeypatch.setattr(RE, "RESULTS", tmp_path / "res")
    monkeypatch.setattr(RE, "retrieve", lambda *a, **k: [])
    monkeypatch.setattr(RE.ask_pipeline, "gather", lambda *a, **k: [])
    monkeypatch.setattr(RE.cost_estimate, "estimate",
                        lambda qs, cfg: dict(calls=len(qs), cached=0, uncached_calls=len(qs), tokens=1000,
                                             uncached_tokens=1000, mean_tokens_per_call=250))
    monkeypatch.setattr(RE.llm, "enable_cache", lambda p: None)
    return tmp_path


def _run(monkeypatch, tmp_path, *extra):
    monkeypatch.setattr(sys, "argv", ["run_eval", "--run-name", "t", "--index-dir", str(tmp_path / "idx"),
                                      "--questions", str(_qs(tmp_path)), "--split", "all", *extra])
    RE.main()
    return json.loads((tmp_path / "res" / "t.json").read_text(encoding="utf-8"))


def test_default_is_retrieval_only(stubbed, monkeypatch):
    monkeypatch.setattr(RE.ask_pipeline, "answer", lambda *a, **k: pytest.fail("LLM pipeline must not run"))
    res = _run(monkeypatch, stubbed)
    assert res["answers"] is None and res["status"] == "COMPLETE" and res["partial"] is None


def test_max_llm_calls_stops_cleanly_and_marks_partial(stubbed, monkeypatch, capsys):
    def fake_answer(q, role, cfg):
        llm.api_calls += 1
        RE.ask_pipeline.last_run.clear()
        RE.ask_pipeline.last_run.update(llm_called=True, ungrounded_warnings=0, context_chunks=0)
        return {"status": "refused", "answer": "x", "citations": []}
    monkeypatch.setattr(RE.ask_pipeline, "answer", fake_answer)
    res = _run(monkeypatch, stubbed, "--answers", "--sleep", "0", "--max-llm-calls", "2")
    assert res["status"] == "PARTIAL" and len(res["rows"]) == 2
    assert res["partial"]["questions_run"] == 2 and res["partial"]["questions_total"] == 4
    assert "PARTIAL RUN" in (stubbed / "res" / "t.md").read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "estimated LLM cost" in err and "--max-llm-calls 2" in err


def test_provider_quota_stops_the_run_and_drops_the_unanswered_question(stubbed, monkeypatch):
    calls = []

    def fake_answer(q, role, cfg):
        calls.append(q)
        RE.ask_pipeline.last_run.clear()
        if len(calls) == 3:
            RE.ask_pipeline.last_run.update(quota_exhausted=True)
            return {"status": "refused", "answer": RE.ask_pipeline.QUOTA_EXHAUSTED, "citations": []}
        RE.ask_pipeline.last_run.update(llm_called=False, ungrounded_warnings=0, context_chunks=0)
        return {"status": "refused", "answer": "x", "citations": []}
    monkeypatch.setattr(RE.ask_pipeline, "answer", fake_answer)
    res = _run(monkeypatch, stubbed, "--answers", "--sleep", "0")
    assert res["status"] == "PARTIAL" and "quota" in res["partial"]["reason"]
    assert len(res["rows"]) == 2 and len(calls) == 3      # the quota-refused question is not scored


def test_cost_estimate_report_text(capsys):
    from cost_estimate import report
    report(dict(calls=37, cached=10, uncached_calls=27, tokens=120000, uncached_tokens=90000,
                mean_tokens_per_call=3243), 41, 20)
    err = capsys.readouterr().err
    assert "41 questions -> 37 reach the LLM" in err and "10 already in the response cache" in err
    assert "90,000 tokens" in err and "45%" in err and "--max-llm-calls 20" in err
