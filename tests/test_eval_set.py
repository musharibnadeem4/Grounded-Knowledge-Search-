"""eval/questions_v2.jsonl: shape, mix, split and evidence (the evidence check is also run by the builder)."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT))
import build_questions_v2 as B  # noqa: E402
from drg import acl  # noqa: E402

QS = [json.loads(l) for l in open(ROOT / "eval" / "questions_v2.jsonl", encoding="utf-8") if l.strip()]


def test_mix_and_split():
    assert len(QS) >= 45
    gen = [q for q in QS if q["source"] == "generated"]
    assert Counter(q["kind"] for q in gen) == {"single": 14, "lead_compare": 5, "year_ambiguous": 3,
                                                "off_desk": 6, "unanswerable": 6}
    assert all(q["verified"] is False for q in gen)
    assert [q for q in QS if q["source"] == "dev"] and all(q["split"] == "tune" for q in QS if q["source"] == "dev")
    held = [q for q in gen if q["split"] == "holdout"]
    assert 0.35 <= len(held) / len(gen) <= 0.45
    assert all("holdout" in q["tags"] for q in held)
    assert len({q["id"] for q in QS}) == len(QS)


def test_off_desk_questions_name_a_company_outside_the_role():
    from drg.query import parse_query
    for q in QS:
        if q["type"] == "off_desk":
            companies, _ = parse_query(q["question"])
            assert companies and not companies <= set(acl.allowed_companies(q["role"])), q["id"]
        if q["type"] in ("answerable", "unanswerable") and q["source"] == "generated":
            companies, _ = parse_query(q["question"])
            assert companies <= set(acl.allowed_companies(q["role"])), q["id"]


def test_evidence_is_on_gold_pages():
    for q in QS:
        if q["source"] == "generated":
            B.check(q)  # exits if evidence is missing from the parse cache
