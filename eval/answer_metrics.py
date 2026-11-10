"""Scoring helpers for run_eval --answers (pure functions, unit-tested in tests/test_answer_metrics.py)."""
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from drg.unavailable import has_unavailability  # noqa: E402

_NUM = re.compile(
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:\s*(?P<unit>%|percent\b|billion\b|bn\b|million\b|mm\b|thousand\b))?", re.I)
_SCALE_USD_M = {"billion": 1000.0, "bn": 1000.0, "million": 1.0, "mm": 1.0, "thousand": 0.001}
_SCALE_COUNT = {"billion": 1e9, "bn": 1e9, "million": 1e6, "mm": 1e6, "thousand": 1e3}


def _norm(text):
    text = text.replace(" ", " ").replace(" ", " ")
    return unicodedata.normalize("NFKC", text)


def extract_numbers(text):
    """-> [(value, unit_word_or_None, decimals)] for every number in the text ('1,577.00' -> 1577.0, 2)."""
    out = []
    for m in _NUM.finditer(_norm(text)):
        unit = (m.group("unit") or "").lower() or None
        raw = m.group("num")
        out.append((float(raw.replace(",", "")), unit, len(raw.split(".")[1]) if "." in raw else 0))
    return out


def _candidates(value, unit, kind):
    """-> [(value_in_kind_unit, scale)]: values a token could stand for (usd_m: USD millions); `scale` converts
    a unit of the token's last printed digit into the same unit (for rounding tolerance)."""
    c = [(value, 1.0)]
    if kind == "usd_m":
        if unit in _SCALE_USD_M:
            c.append((value * _SCALE_USD_M[unit], _SCALE_USD_M[unit]))
        c.append((value / 1000.0, 0.001))          # a statement reported in thousands
    elif kind == "count" and unit in _SCALE_COUNT:
        c.append((value * _SCALE_COUNT[unit], _SCALE_COUNT[unit]))
    return c


def _close(a, scale, decimals, b, kind):
    """a matches b if within 1 %, or (rounding-aware) within half a unit of the last digit the answer printed:
    '10%' matches 10.29, '$1.3 billion' matches 1,320 million, '4.5%' matches 4.53."""
    tol = max(0.01 * abs(b), 0.5 * (10 ** -decimals) * scale)
    return abs(a - b) <= tol


def numeric_match(answer_text, spec):
    """spec: {"kind": usd_m|pct|count, "values": [...], "mode": any|all}. True if the answer states the
    expected figure(s) within 1 % (percentages: or within 0.06 points). Scale words are honoured
    ('$5.0 billion' == 5000 USD millions; '$5,005 million' == 5005)."""
    kind = spec["kind"]
    nums = extract_numbers(answer_text)
    hit = []
    for exp in spec["values"]:
        alts = exp if isinstance(exp, (list, tuple)) else [exp]  # [a, b]: either value is accepted
        hit.append(any(_close(c, sc, d, e, kind) for e in alts
                       for v, u, d in nums for c, sc in _candidates(v, u, kind)))
    return all(hit) if spec.get("mode", "any") == "all" else any(hit)


def numeric_hits(answer_text, spec):
    """Per expected value: does the answer state it (same matching as numeric_match)?"""
    kind = spec["kind"]
    nums = extract_numbers(answer_text)
    out = []
    for exp in spec["values"]:
        alts = exp if isinstance(exp, (list, tuple)) else [exp]
        out.append(any(_close(c, sc, d, e, kind) for e in alts
                       for v, u, d in nums for c, sc in _candidates(v, u, kind)))
    return out


OUTCOMES = ("correct", "partial", "soft_refusal", "refused", "confident_error")


def classify_numeric(answer_text, spec, got, numeric_ok):
    """Outcome of one answerable question with numeric gold (definitions in eval/README.md):
      refused          status refused
      correct          answered, the expected figure(s) stated
      partial          multi-part question (several expected figures), at least one stated correctly, and the answer
                       explicitly marks the rest unavailable
      soft_refusal     status answered, but the answer explicitly says the asked figure is unavailable / cannot be
                       computed and no expected figure is stated
      confident_error  anything else that was answered: a wrong final figure stated without saying it is unavailable
    Only the expected figures are checked: other numbers in the answer (inputs, years) are not judged."""
    if got == "refused":
        return "refused"
    if numeric_ok:
        return "correct"
    if has_unavailability(answer_text):
        hits = numeric_hits(answer_text, spec)
        if len(spec["values"]) > 1 and any(hits):
            return "partial"
        return "soft_refusal"
    return "confident_error"


def expected_status(q):
    return "answered" if q["type"] == "answerable" else "refused"


def score_answer(q, result, seconds, llm_called, warnings, waited=0.0):
    """Per-question answer metrics. `result` = {"status", "answer", "citations"}."""
    exp = expected_status(q)
    m = {"status_ok": result["status"] == exp, "expected": exp, "got": result["status"],
         "seconds": round(seconds, 2), "waited_s": round(waited, 2),
         "seconds_net": round(max(seconds - waited, 0.0), 2), "llm_called": llm_called, "ungrounded_warnings": warnings,
         "numeric_ok": None, "cite_hit": None, "cite_precision": None}
    if q["type"] == "answerable" and result["status"] == "answered":
        if q.get("numeric"):
            m["numeric_ok"] = numeric_match(result["answer"], q["numeric"])
        ok = {(g["doc_id"], p) for g in q.get("gold", []) + q.get("alt_gold", []) for p in g["pages"]}
        cites = [(c["doc_id"], c["page"]) for c in result["citations"]]
        m["cite_hit"] = any(c in ok for c in cites)
        m["cite_precision"] = (sum(c in ok for c in cites) / len(cites)) if cites else 0.0
    elif q["type"] == "answerable" and q.get("numeric"):
        m["numeric_ok"] = False  # refused an answerable numeric question
    if q["type"] == "answerable" and q.get("numeric"):
        m["outcome"] = classify_numeric(result["answer"], q["numeric"], result["status"], m["numeric_ok"])
    m["answer_ok"] = (m["status_ok"] if q["type"] != "answerable"
                      else (m["numeric_ok"] if q.get("numeric") else None))
    return m


def _outcome(r):
    """Stored outcome; for rows scored before outcomes existed, the old two-way reading."""
    m = r["answer_metrics"]
    if m.get("outcome"):
        return m["outcome"]
    if m["numeric_ok"] is None:
        return None
    return "refused" if m["got"] == "refused" else ("correct" if m["numeric_ok"] else "confident_error")


def _confident_error(r):
    return _outcome(r) == "confident_error"


def answered_wrong_rate(rows):
    """Old definition of the 'confident error rate' (rescored3): answered and numeric wrong, including soft refusals and
    partial answers. Kept for comparison."""
    num = [r for r in rows if r["type"] == "answerable" and r["answer_metrics"]["numeric_ok"] is not None]
    return (sum(r["answer_metrics"]["got"] == "answered" and r["answer_metrics"]["numeric_ok"] is False
                for r in num) / len(num)) if num else None


def outcome_rate(rows, outcome):
    num = [r for r in rows if r["type"] == "answerable" and _outcome(r) is not None]
    return (sum(_outcome(r) == outcome for r in num) / len(num)) if num else None


def confident_error_rate(rows):
    """Among answerable questions with numeric gold: share with a wrong final figure stated (outcome confident_error).
    Soft refusals, partial answers and refusals are reported separately."""
    return outcome_rate(rows, "confident_error")


def summarize(rows):
    """rows: dicts with q-type info and an `answer_metrics` entry -> aggregate dict."""
    def rate(xs):
        xs = [x for x in xs if x is not None]
        return (sum(bool(x) for x in xs) / len(xs)) if xs else None

    ans = [r for r in rows if r["type"] == "answerable"]
    neg = [r for r in rows if r["type"] != "answerable"]
    refused = [r for r in rows if r["answer_metrics"]["got"] == "refused"]
    good_refusals = [r for r in refused if r["type"] != "answerable"]
    lat = sorted(r["answer_metrics"]["seconds"] for r in rows)
    net = sorted(r["answer_metrics"].get("seconds_net", r["answer_metrics"]["seconds"]) for r in rows)

    def pct(p, xs=None):
        xs = lat if xs is None else xs
        if not xs:
            return None
        i = (len(xs) - 1) * p / 100
        lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
        return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)

    cites = [r["answer_metrics"]["cite_precision"] for r in ans]
    return {
        "n": len(rows), "n_answerable": len(ans), "n_negative": len(neg),
        "status_accuracy": rate([r["answer_metrics"]["status_ok"] for r in rows]),
        "refusal_recall": rate([r["answer_metrics"]["got"] == "refused" for r in neg]),
        "refusal_precision": (len(good_refusals) / len(refused)) if refused else None,
        "answer_rate_on_answerable": rate([r["answer_metrics"]["got"] == "answered" for r in ans]),
        "numeric_accuracy": rate([r["answer_metrics"]["numeric_ok"] for r in ans
                                  if r["answer_metrics"]["numeric_ok"] is not None]),
        "n_numeric": sum(r["answer_metrics"]["numeric_ok"] is not None for r in ans),
        # confident error rate: of the answerable questions with numeric gold, the share where the system
        # answered (status=answered) with a wrong number. A refusal is not a confident error.
        "confident_error_rate": confident_error_rate(ans),
        "n_confident_errors": sum(_confident_error(r) for r in ans),
        "answered_wrong_rate": answered_wrong_rate(ans),
        **{f"{o}_rate": outcome_rate(ans, o) for o in OUTCOMES},
        **{f"n_{o}": sum(_outcome(r) == o for r in ans) for o in OUTCOMES},
        # refusal rate on the same population (answerable questions with numeric gold) and on all answerable ones
        "refusal_rate_numeric": (lambda xs: (sum(r["answer_metrics"]["got"] == "refused" for r in xs) / len(xs)) if xs else None)(
            [r for r in ans if r["answer_metrics"]["numeric_ok"] is not None]),
        "refusal_rate_on_answerable": (1 - rate([r["answer_metrics"]["got"] == "answered" for r in ans])) if ans else None,
        "citation_hit": rate([r["answer_metrics"]["cite_hit"] for r in ans]),
        "citation_precision": (sum(c for c in cites if c is not None) / len([c for c in cites if c is not None])
                               if any(c is not None for c in cites) else None),
        "ungrounded_warnings": sum(r["answer_metrics"]["ungrounded_warnings"] for r in rows),
        "latency_p50_s": pct(50), "latency_p95_s": pct(95),
        "latency_net_p50_s": pct(50, net), "latency_net_p95_s": pct(95, net),  # excluding 429 retry-after waits
    }
