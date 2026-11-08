"""ask pipeline: parse -> (off-desk check) -> retrieve -> prompt -> LLM -> post-check.

All retrieval goes through drg.retrieve.retrieve(), so access control always applies.
"""
import json
import re
import sys
import time
import unicodedata
from decimal import Decimal, InvalidOperation

from . import acl, config, llm
from .query import company_subquery, load_periods, parse_query
from .retrieve import retrieve

OFF_DESK = "This question concerns a company outside your desk's coverage."
NO_ANSWER = "The provided documents do not contain the answer for the exact company and period asked."
NO_CITATION = "No supported answer could be cited from the available documents."
LLM_DOWN = "LLM unavailable"

SYSTEM_PROMPT = """You answer questions about company filings using ONLY the numbered context blocks provided.

Rules:
1. Answer ONLY from the context. Never use outside knowledge.
2. Put a citation marker such as [C3] after every factual claim. Use only markers that exist in the context.
3. For any calculated figure, state the formula and each input value with its own citation, then the result.
4. State units explicitly. Each block header ends with the page_header, which carries the units (for example "(In thousands)", "(In millions)", "(In billions)") and the statement name. Convert using those units and say which units you report in.
5. State the fiscal period the figures refer to.
6. If only part of the question can be answered from the context, answer that part with citations and state explicitly which part is not in the provided filings (status "answered"). Reply with status "refused" and answer "REFUSE" only when the context contains nothing relevant to the exact company and period asked.
7. Output ONLY a JSON object: {"status": "answered" or "refused", "answer": "..."}"""

# Citation markers: [C1]  [C1, C3]  [C1][C3] (two markers)  [C1-C3] (range)  (C1)  【C1】
_ITEM = r"C\d+(?:\s*[-–—]\s*C?\d+)?"
_LIST = rf"{_ITEM}(?:\s*[,;]\s*{_ITEM})*"
_MARKER = re.compile(rf"\[\s*(?P<a>{_LIST})\s*\]|\(\s*(?P<b>{_LIST})\s*\)"
                     rf"|【\s*(?P<c>{_LIST})\s*】", re.I)
_RANGE = re.compile(r"C(\d+)\s*[-–—]\s*C?(\d+)", re.I)
_NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?|\d*\.\d+")
_CALC_WORDS = ("=", "calculat", "comput", "formula", "equals", "result")
# SEC form names such as "10-K", "Form 10-Q", "8-K/A" contain numbers that are not figures
_FORM = re.compile(r"\b(?:form\s+)?(?:10-?K|10-?Q|8-?K)(?:405|SB|/A)?\b", re.I)


def log(msg):
    print(msg, file=sys.stderr, flush=True)


# ------------------------------------------------------------------- retrieval
def interleave(lists):
    """Round-robin merge, dropping duplicate chunks."""
    out, seen = [], set()
    for i in range(max((len(x) for x in lists), default=0)):
        for lst in lists:
            if i < len(lst) and lst[i].chunk_id not in seen:
                seen.add(lst[i].chunk_id)
                out.append(lst[i])
    return out


_periods_cache = {}


def out_of_range(companies, year, cfg):
    """Companies for which `year` is beyond the corpus: year > latest manifest period + 1
    (+1 allows forecast questions about next year). Returns the sorted list of such
    companies if it holds for EVERY named company, else []."""
    if year is None or not companies:
        return []
    path = str(cfg.MANIFEST_PATH)
    if path not in _periods_cache:
        _periods_cache[path] = load_periods(path)
    periods = _periods_cache[path]
    late = {}
    for c in companies:
        years = [int(p) for p in periods.get(c, ()) if p.isdigit()]
        if not years or year <= max(years) + 1:
            return []
        late[c] = max(years)
    return sorted(late)


def gather(question, role, companies, cfg):
    """One retrieve() call, or one per company for multi-company questions."""
    if len(companies) >= 2:
        k = cfg.ASK_K_PER_COMPANY
        per = []
        for c in sorted(companies):
            # each company gets its own query: the other companies and the connecting
            # words are removed so they cannot pull the search toward the wrong filings
            sub_q = company_subquery(question, c)
            log(f"sub-query [{c}]: {sub_q!r}")
            per.append(retrieve(sub_q, role, k, cfg, companies=[c]))
        return interleave(per)
    return retrieve(question, role, cfg.ASK_K, cfg)


def build_context(hits):
    blocks = []
    for i, h in enumerate(hits, 1):
        header = " / ".join(x.strip() for x in h.page_header.splitlines() if x.strip())
        blocks.append(f"[C{i}] {h.doc_id} | {h.company} | {h.period} | page {h.page} | {header}\n"
                      f"{h.text.strip()}")
    return "\n\n".join(blocks)


def normalize_text(s):
    """NFKC, plus narrow/no-break spaces -> ' ' and non-breaking hyphen / en dash -> '-'
    (done before NFKC, which would turn U+2011 into U+2010)."""
    s = s.replace("\u202f", " ").replace("\u00a0", " ")
    s = s.replace("\u2011", "-").replace("\u2013", "-")
    return unicodedata.normalize("NFKC", s)


# ------------------------------------------------------------------ post-check
def postcheck(text, hits):
    """Keep only [Cx] markers that exist in the context.
    Returns (cleaned_text, citations) with citations in order of first valid use."""
    n = len(hits)
    cites, seen = [], set()

    def indices(inner):
        out = []
        for tok in re.split(r"\s*[,;]\s*", inner):
            r = _RANGE.fullmatch(tok)
            if r:
                lo, hi = int(r.group(1)), int(r.group(2))
                out += list(range(lo, hi + 1)) if lo <= hi and hi - lo <= 100 else [lo, hi]
            else:
                out.append(int(tok[1:]))
        return list(dict.fromkeys(out))

    def fix(m):
        keep = []
        for idx in indices(m.group("a") or m.group("b") or m.group("c")):
            if 1 <= idx <= n:
                keep.append(f"C{idx}")
                if idx not in seen:
                    seen.add(idx)
                    h = hits[idx - 1]
                    cites.append({"doc_id": h.doc_id, "page": h.page, "chunk_id": h.chunk_id})
            else:
                log(f"WARN dropped invalid citation marker C{idx} (context has {n} chunks)")
        return f"[{', '.join(keep)}]" if keep else ""

    cleaned = re.sub(r"[ \t]{2,}", " ", _MARKER.sub(fix, text)).strip()
    return cleaned, cites


def _canon(s):
    try:
        return format(Decimal(s.replace(",", "")).normalize(), "f")
    except InvalidOperation:
        return None


def check_numbers(answer, cited_hits):
    """Warn (never fail) about numbers in the answer that appear in no cited chunk and are
    not presented as a calculation result. Form names (10-K, 10-Q, 8-K, Form 10-K), years
    1990-2030 (plain 4 digits) and integers < 10 are ignored."""
    in_chunks = set()
    for h in cited_hits:
        in_chunks |= {c for c in (_canon(m) for m in _NUM.findall(h.text)) if c}
    plain = _FORM.sub(" ", _MARKER.sub("", answer))
    warned = []
    for sent in re.split(r"(?<=[.!?])\s+|\n+", plain):
        calc = any(w in sent.lower() for w in _CALC_WORDS)
        for m in _NUM.findall(sent):
            c = _canon(m)
            if c is None:
                continue
            if re.fullmatch(r"\d{4}", m) and 1990 <= Decimal(c) <= 2030:
                continue  # a year (a figure like 2,015 has a comma and is still checked)
            if "." not in m and Decimal(c) < 10:
                continue
            if c not in in_chunks and not calc and c not in warned:
                warned.append(c)
                log(f"WARN number {m} in the answer is not in any cited chunk "
                    f"and not marked as a calculation: {sent.strip()[:120]!r}")
    return warned


def parse_llm_json(raw):
    try:
        obj = json.loads(raw)
    except ValueError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise
        obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        raise ValueError("LLM output is not a JSON object")
    return obj


# --------------------------------------------------------------------- pipeline
def refused(msg):
    return {"status": "refused", "answer": msg, "citations": []}


def answer(question, role, cfg=None):
    """-> {"status", "answer", "citations"}. Never raises for LLM problems."""
    cfg = cfg or config
    t0 = time.perf_counter()
    allowed = set(acl.allowed_companies(role))  # raises acl.UnknownRole
    companies, year = parse_query(question)
    t_parse = time.perf_counter()
    log(f"ask parse: companies={sorted(companies)} year={year}")

    def done(result, t_ret=None, t_llm=None):
        end = time.perf_counter()
        r = t_ret if t_ret is not None else t_parse
        log(f"ask latency: parse={t_parse - t0:.3f}s retrieve={r - t_parse:.3f}s "
            f"llm={(t_llm - r) if t_llm else 0:.3f}s total={end - t0:.3f}s")
        return result

    if companies - allowed:
        log(f"refusing: off-desk companies {sorted(companies - allowed)} for role {role}")
        return done(refused(OFF_DESK))  # nothing retrieved

    beyond = out_of_range(companies, year, cfg)
    if beyond:
        log(f"refusing: FY{year} is beyond the corpus for {beyond} (latest period + 1)")
        return done(refused(f"No filings in the corpus cover FY{year} for {', '.join(beyond)}."))

    hits = gather(question, role, companies, cfg)
    t_ret = time.perf_counter()
    log(f"retrieved {len(hits)} chunks:")
    for i, h in enumerate(hits, 1):
        log(f"C{i} {h.doc_id} p.{h.page}")
    if not hits:
        return done(refused(NO_ANSWER), t_ret)

    user = f"Context:\n\n{build_context(hits)}\n\nQuestion: {question}"
    try:
        raw = llm.chat(SYSTEM_PROMPT, user)
    except llm.LLMError as e:
        log(f"LLM error: {e}")
        return done(refused(LLM_DOWN), t_ret, time.perf_counter())
    t_llm = time.perf_counter()
    log(f"LLM raw response (first 2000 chars): {raw[:2000]}")

    try:
        obj = parse_llm_json(raw)
    except ValueError as e:
        log(f"LLM returned invalid JSON ({e}): {raw[:200]!r}")
        return done(refused(LLM_DOWN), t_ret, t_llm)
    status = str(obj.get("status", "")).strip().lower()
    text = str(obj.get("answer", "")).strip()
    if status == "refused" or text.upper() == "REFUSE" or not text:
        msg = (NO_ANSWER if text.upper() in ("", "REFUSE")
               else normalize_text(_MARKER.sub("", text)).strip())
        return done(refused(msg), t_ret, t_llm)

    text, citations = postcheck(normalize_text(text), hits)
    if not citations:
        log("answer had no valid citation; refusing")
        return done(refused(NO_CITATION), t_ret, t_llm)
    by_id = {h.chunk_id: h for h in hits}
    check_numbers(text, [by_id[c["chunk_id"]] for c in citations])
    return done({"status": "answered", "answer": text, "citations": citations}, t_ret, t_llm)
