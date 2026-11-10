"""Detect answers that say the asked figure is unavailable (used by the PROMPT_VERSION=4 post-check in drg/answer.py and by the
eval scorer eval/answer_metrics.py, so that both use one definition).

The detector is a heuristic over wording, not a proof; it was written after reading the confident-error cases of the first
answer runs and is applied uniformly.
"""
import re

UNAVAIL = re.compile(
    r"(?:cannot|can't|can not|could not|unable to|not possible to)\s+(?:be\s+)?"
    r"(?:compute[d]?|calculate[d]?|determine[d]?|derive[d]?|provide[d]?|answer(?:ed)?|find|found|give|completed)"
    r"|\bnot\s+(?:present|provided|disclosed|available|included|reported|given|contained|found|stated|listed)\b"
    r"|\b(?:do|does|did)\s+not\s+(?:contain|include|provide|disclose|report|specify|state|give|list|have)\b"
    r"|\bno\s+(?:information|data|figure|disclosure)\b"
    r"|\binsufficient\b|\bunavailable\b"
    r"|\bnot\s+in\s+the\s+(?:provided|supplied|given)\b",
    re.I)

_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[a-z][a-z&]{2,}")
_STOP = frozenset("the and for with what was were how much many did does has have that this from into than its their over "
                  "year years fiscal quarter based using given answer round decimal places please state each its all any "
                  "per between among which who when where why also".split())
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
_MARK = re.compile(r"\[[^\]]*C\d+[^\]]*\]|\(C\d+\)|【[^】]*】")


def has_unavailability(text):
    return bool(UNAVAIL.search(text or ""))


def _sentences(text):
    return [s.strip() for s in _SENT.split(_MARK.sub("", text or "")) if s.strip()]


def _has_figure(sentence):
    """A number that is not a year (1990-2030) and not a small integer."""
    for m in _NUM.finditer(sentence):
        raw = m.group(0)
        v = float(raw.replace(",", ""))
        if re.fullmatch(r"\d{4}", raw) and 1990 <= v <= 2030:
            continue
        if "." not in raw and "," not in raw and v < 10:
            continue
        return True
    return False


def _content(text):
    return {w for w in _WORD.findall((text or "").lower()) if w not in _STOP}


def soft_refusal(question, answer, n_companies):
    """True if an answer with status 'answered' is in substance a refusal: it explicitly says the asked figure or fact is
    unavailable and gives no figure for it.
      * several companies named: a partial answer stays 'answered' as long as some sentence without an unavailability
        phrase carries a figure; it is a soft refusal only if no such sentence exists.
      * one company: the unavailability sentence must refer to the question (share a content word with it); inputs
        listed elsewhere in the answer do not count as the asked figure.
    """
    sents = _sentences(answer)
    flagged = [s for s in sents if has_unavailability(s)]
    if not flagged:
        return False
    if n_companies >= 2:
        return not any(_has_figure(s) for s in sents if not has_unavailability(s))
    q = _content(question)
    return any(q & _content(s) for s in flagged)
