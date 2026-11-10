"""ask pipeline: parse -> (off-desk check) -> retrieve -> prompt -> LLM -> post-check.

All retrieval goes through drg.retrieve.retrieve(), so access control always applies.
"""
import json
import re
import sys
import time
import unicodedata
from decimal import Decimal, InvalidOperation

from . import acl, config, llm, unavailable
from .query import company_subquery, load_periods, parse_query
from .retrieve import retrieve

OFF_DESK = "This question concerns a company outside your desk's coverage."
NO_ANSWER = "The provided documents do not contain the answer for the exact company and period asked."
NO_CITATION = "No supported answer could be cited from the available documents."
LLM_DOWN = "LLM unavailable"
QUOTA_EXHAUSTED = "LLM quota exhausted (provider daily limit); retrieval succeeded"
CITATION_REMINDER = ("\n\nREMINDER: put a citation marker such as [C3] after every factual claim, using only the "
                     "block numbers shown above. An answer without markers is rejected.")

SYSTEM_PROMPT = """You answer questions about company filings using ONLY the numbered context blocks provided.

Rules:
1. Answer ONLY from the context. Never use outside knowledge.
2. Put a citation marker such as [C3] after every factual claim. Use only markers that exist in the context.
3. For any calculated figure, state the formula and each input value with its own citation, then the result.
4. State units explicitly. Each block header ends with the page_header, which carries the units (for example "(In thousands)", "(In millions)", "(In billions)") and the statement name. Convert using those units and say which units you report in.
5. State the fiscal period the figures refer to.
6. If only part of the question can be answered from the context, answer that part with citations and state explicitly which part is not in the provided filings (status "answered"). Reply with status "refused" and answer "REFUSE" only when the context contains nothing relevant to the exact company and period asked.
7. Output ONLY a JSON object: {"status": "answered" or "refused", "answer": "..."}"""

# PROMPT_VERSION = 2 (experiment X7): the same rules plus explicit guidance on units / scale, calculation inputs
# and fiscal-period mismatches.
SYSTEM_PROMPT_V2 = SYSTEM_PROMPT.replace(
    "7. Output ONLY a JSON object",
    """7. Copy figures exactly as printed, in the filing's own units (thousands / millions / billions), and say which
unit you report in. If the question asks for another unit, convert and show the conversion. Never mix units.
8. For percentages, ratios and differences: write the formula, each input with its [C] marker, and the result
rounded to one decimal place (one decimal for percentages, whole numbers for amounts in millions).
9. Check the fiscal period of every figure: block headers and column headings tell you which year or quarter a
column is. If the context only contains figures for a different period than the one asked, do not use them;
say what period is available and set status "refused" unless part of the question can be answered.
Retailers' fiscal years end in January/February: state which fiscal year the figures cover.
10. Output ONLY a JSON object""")

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


# PROMPT_VERSION = 3: citations are a structured field. Same rules as version 1, except that the context blocks used
# are listed in a "citations" array (inline [C#] markers stay welcome but optional).
SYSTEM_PROMPT_V3 = SYSTEM_PROMPT.replace(
    "2. Put a citation marker such as [C3] after every factual claim. Use only markers that exist in the context.",
    "2. List every context block your answer relies on in the \"citations\" array, e.g. [\"C3\", \"C7\"]. Inline markers "
    "such as [C3] after claims are welcome but optional. Use only block ids that exist in the context.",
).replace(
    "7. Output ONLY a JSON object: {\"status\": \"answered\" or \"refused\", \"answer\": \"...\"}",
    "7. Output ONLY a JSON object: {\"status\": \"answered\" or \"refused\", \"answer\": \"...\", "
    "\"citations\": [\"C3\", \"C7\"]} (an empty citations array when refusing).",
)
CITATION_REMINDER_V3 = ("\n\nREMINDER: your answer must list the context blocks it relies on in the \"citations\" "
                        "array (for example [\"C3\", \"C7\"]) using only the block numbers shown above. "
                        "An answer without any valid citation is rejected.")


# PROMPT_VERSION = 4: version 3 (structured citations) plus one rule: a question whose specific figure cannot be given is
# refused, not "answered" with a caveat. A post-check (soft_refusal) enforces it when the model does not.
SYSTEM_PROMPT_V4 = SYSTEM_PROMPT_V3.replace(
    "exact company and period asked.\n7.",
    "exact company and period asked.\n"
    "If you cannot give the specific figure or fact asked for, set status to refused; you may still list the inputs you found.\n7.")


def prompt_version(cfg):
    return getattr(cfg, "PROMPT_VERSION", 1)


def system_prompt(cfg):
    return {2: SYSTEM_PROMPT_V2, 3: SYSTEM_PROMPT_V3, 4: SYSTEM_PROMPT_V4}.get(prompt_version(cfg), SYSTEM_PROMPT)


_CITE_ID = re.compile(r"C?\s*(\d+)(?:\s*[-\u2013\u2014]\s*C?\s*(\d+))?", re.I)


def cite_field_ids(value):
    """Block numbers named in an LLM "citations" field: ["C3","C7"], "C3, C7", [3, 7], ["C1-C3"] -> [3, 7] ..."""
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple)) else re.split(r"[,;]", str(value))
    out = []
    for it in items:
        m = _CITE_ID.fullmatch(str(it).strip().strip("[]()"))
        if not m:
            continue
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        out += list(range(lo, hi + 1)) if lo <= hi and hi - lo <= 100 else [lo, hi]
    return list(dict.fromkeys(out))


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


def cap_per_page(hits, cap, k):
    """Keep at most `cap` chunks of any (doc, page) - first ones in rank order - and the first `k` overall."""
    seen, out = {}, []
    for h in hits:
        key = (h.doc_id, h.page)
        if seen.get(key, 0) < cap:
            seen[key] = seen.get(key, 0) + 1
            out.append(h)
    return out[:k]


def _retrieve_k(q, role, k, cfg, companies=None):
    """retrieve() for the ask context; with ASK_MAX_CHUNKS_PER_PAGE it fetches 3x and caps chunks per page."""
    cap = getattr(cfg, "ASK_MAX_CHUNKS_PER_PAGE", 0)
    if not cap:
        return retrieve(q, role, k, cfg, companies=companies) if companies else retrieve(q, role, k, cfg)
    hits = retrieve(q, role, k * 3, cfg, companies=companies) if companies else retrieve(q, role, k * 3, cfg)
    return cap_per_page(hits, cap, k)


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
            per.append(_retrieve_k(sub_q, role, k, cfg, companies=[c]))
        return interleave(per)
    return _retrieve_k(question, role, cfg.ASK_K, cfg)


def format_block(i, h):
    header = " / ".join(x.strip() for x in h.page_header.splitlines() if x.strip())
    return (f"[C{i}] {h.doc_id} | {h.company} | {h.period} | page {h.page} | {header}\n"
            f"{h.text.strip()}")


def build_context(hits):
    return "\n\n".join(format_block(i, h) for i, h in enumerate(hits, 1))


_tok = None


def _tokenizer_json():
    """tokenizer.json of the embedding model: the ONNX export dir, else the Hugging Face cache snapshot."""
    from pathlib import Path

    from . import hf

    cands = [Path(config.ONNX_DIR) / "tokenizer.json"]
    snaps = hf._hub_cache() / ("models--" + config.EMBED_MODEL.replace("/", "--")) / "snapshots"
    if snaps.is_dir():
        cands += sorted(snaps.glob("*/tokenizer.json"))
    return next((c for c in cands if c.exists()), None)


def count_tokens(s):
    """Token count with the bge tokenizer (an approximation of the LLM's own count). Uses the light `tokenizers`
    library on tokenizer.json (no transformers / torch import); falls back to the transformers tokenizer."""
    global _tok
    if _tok is None:
        path = _tokenizer_json()
        if path is not None:
            from tokenizers import Tokenizer

            t = Tokenizer.from_file(str(path))
            t.no_truncation()
            t.no_padding()
            _tok = ("fast", t)
        else:
            from .ingest import load_tokenizer
            _tok = ("hf", load_tokenizer())
    kind, t = _tok
    if kind == "fast":
        return len(t.encode(s, add_special_tokens=False).ids)
    return len(t.encode(s, add_special_tokens=False))


def fit_budget(hits, budget, multi=False):
    """Keep chunks in the given (rank / interleaved) order while they fit in `budget` tokens.
    multi=True: every company gets an equal share (budget // n_companies); once a chunk does
    not fit in its company's share, that company's remaining chunks are dropped.
    The first chunk of each company is always kept. Logs kept / dropped.
    Returns the kept chunks (original order)."""
    companies = list(dict.fromkeys(h.company for h in hits)) if multi else [None]
    share = budget // len(companies)
    used = dict.fromkeys(companies, 0)
    closed, kept, dropped = set(), [], []
    for h in hits:
        c = h.company if multi else None
        if c in closed:
            dropped.append(h)
            continue
        n = count_tokens(format_block(len(kept) + 1, h))
        if used[c] > 0 and used[c] + n > share:
            closed.add(c)
            dropped.append(h)
            continue
        used[c] += n
        kept.append(h)
    per = (" (" + ", ".join(f"{c}: {used[c]}/{share}" for c in companies) + ")") if multi else ""
    log(f"context budget {budget} tokens: kept {len(kept)} chunks "
        f"({sum(used.values())} tokens){per}, dropped {len(dropped)}"
        + (": " + ", ".join(f"{h.doc_id} p.{h.page}" for h in dropped) if dropped else ""))
    return kept


def normalize_text(s):
    """NFKC, plus narrow/no-break spaces -> ' ' and non-breaking hyphen / en dash -> '-'
    (done before NFKC, which would turn U+2011 into U+2010)."""
    s = s.replace("\u202f", " ").replace("\u00a0", " ")
    s = s.replace("\u2011", "-").replace("\u2013", "-")
    return unicodedata.normalize("NFKC", s)


# ------------------------------------------------------------------ post-check
def postcheck(text, hits, field_ids=()):
    """Keep only [Cx] markers that exist in the context, plus the ids of a structured citations field (union;
    ids outside the context are dropped). Returns (cleaned_text, citations): inline markers in order of first
    valid use, then field-only ids in field order."""
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
    for idx in field_ids:
        if 1 <= idx <= n:
            if idx not in seen:
                seen.add(idx)
                h = hits[idx - 1]
                cites.append({"doc_id": h.doc_id, "page": h.page, "chunk_id": h.chunk_id})
        else:
            log(f"WARN dropped invalid citation id C{idx} from the citations field (context has {n} chunks)")
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


last_run = {}  # stats of the most recent answer() call (for eval); never part of the CLI output


def answer(question, role, cfg=None):
    """-> {"status", "answer", "citations"}. Never raises for LLM problems."""
    cfg = cfg or config
    last_run.clear()
    last_run.update(llm_called=False, ungrounded_warnings=0, context_chunks=0)
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

    all_hits = hits
    budget = cfg.CONTEXT_TOKEN_BUDGET
    for attempt in (0, 1):
        hits = fit_budget(all_hits, budget, multi=len(companies) >= 2)
        user = f"Context:\n\n{build_context(hits)}\n\nQuestion: {question}"
        last_run["context_chunks"] = len(hits)
        try:
            last_run["llm_called"] = True
            raw = llm.chat(system_prompt(cfg), user)
            break
        except llm.LLMQuotaError as e:
            # daily cap: waiting is pointless, so say why. Retrieval worked; show which pages it found.
            log(f"LLM quota exhausted: {e}")
            log("retrieved pages that could not be sent to the LLM: "
                + ", ".join(f"{h.doc_id} p.{h.page}" for h in hits))
            last_run["quota_exhausted"] = True
            return done(refused(QUOTA_EXHAUSTED), t_ret, time.perf_counter())
        except llm.LLMError as e:
            if e.status == 413 and attempt == 0:
                budget //= 2
                log(f"LLM returned 413 (request too large); retrying once with the context "
                    f"budget halved to {budget} tokens")
                continue
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

    if prompt_version(cfg) == 4 and unavailable.soft_refusal(question, text, len(companies)):
        # status "answered", but the answer says the asked figure is unavailable and gives none: a refusal in substance
        log("soft refusal: status was 'answered' but the answer states the asked figure is unavailable; "
            "setting status to refused")
        last_run["soft_refusal"] = True
        return done(refused(normalize_text(_MARKER.sub("", text)).strip()), t_ret, t_llm)

    v3 = prompt_version(cfg) in (3, 4)
    text, citations = postcheck(normalize_text(text), hits, cite_field_ids(obj.get("citations")) if v3 else ())
    if not citations and (getattr(cfg, "RETRY_UNCITED", False) or v3):
        # the model answered but forgot the [C#] markers: ask once more, with a reminder
        log("answer had no valid citation; retrying once with a citation reminder")
        last_run["retried_uncited"] = True
        try:
            raw2 = llm.chat(system_prompt(cfg), user + (CITATION_REMINDER_V3 if v3 else CITATION_REMINDER))
            obj2 = parse_llm_json(raw2)
            text2 = str(obj2.get("answer", "")).strip()
            if str(obj2.get("status", "")).strip().lower() == "answered" and text2:
                text, citations = postcheck(normalize_text(text2), hits,
                                            cite_field_ids(obj2.get("citations")) if v3 else ())
        except llm.LLMQuotaError as e:
            log(f"LLM quota exhausted during the citation retry: {e}")
            last_run["quota_exhausted"] = True
            return done(refused(QUOTA_EXHAUSTED), t_ret, time.perf_counter())
        except (llm.LLMError, ValueError) as e:
            log(f"citation retry failed: {e}")
        t_llm = time.perf_counter()
    if not citations:
        log("answer had no valid citation; refusing")
        return done(refused(NO_CITATION), t_ret, t_llm)
    by_id = {h.chunk_id: h for h in hits}
    last_run["ungrounded_warnings"] = len(
        check_numbers(text, [by_id[c["chunk_id"]] for c in citations]))
    return done({"status": "answered", "answer": text, "citations": citations}, t_ret, t_llm)
