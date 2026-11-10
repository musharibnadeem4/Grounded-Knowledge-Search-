"""Token-cost estimate printed before a live-LLM (--answers) run, so a run cannot silently eat the daily quota."""
import contextlib
import io
import sys

from drg import acl
from drg import answer as A
from drg import llm
from drg.query import parse_query

# provider tokens ~= bge tokens * 1.15 (different tokenizers); a reasoning model also emits hidden reasoning tokens
PROVIDER_FACTOR = 1.15
COMPLETION_ALLOWANCE = 400  # tokens per call (observed totals were ~3.4k per call for ~2.9k-token contexts)
DAILY_CAP_GROQ_FREE = 200_000


def estimate(questions, cfg):
    """-> dict(calls, cached, uncached_calls, prompt_tokens, uncached_tokens, mean_prompt). Retrieval is run for
    every question that would reach the LLM (off-desk and out-of-range questions are refused before it)."""
    system = A.system_prompt(cfg)
    sys_tokens = A.count_tokens(system)
    calls = cached = prompt = uncached = 0
    for q in questions:
        companies, year = parse_query(q["question"])
        if companies - set(acl.allowed_companies(q["role"])) or A.out_of_range(companies, year, cfg):
            continue
        with contextlib.redirect_stderr(io.StringIO()):  # gather / fit_budget log a lot
            hits = A.gather(q["question"], q["role"], companies, cfg)
            kept = A.fit_budget(hits, cfg.CONTEXT_TOKEN_BUDGET, multi=len(companies) >= 2) if hits else []
        if not kept:
            continue
        user = "Context:\n\n" + A.build_context(kept) + "\n\nQuestion: " + q["question"]
        tokens = int((sys_tokens + A.count_tokens(user)) * PROVIDER_FACTOR) + COMPLETION_ALLOWANCE
        calls += 1
        prompt += tokens
        hit = llm._cache["dir"] is not None and llm._cache_file(system, user).exists()
        if hit:
            cached += 1
        else:
            uncached += tokens
    return {"calls": calls, "cached": cached, "uncached_calls": calls - cached, "tokens": prompt,
            "uncached_tokens": uncached, "mean_tokens_per_call": (prompt // calls) if calls else 0}


def report(est, n_questions, max_calls=None, file=None):
    file = file or sys.stderr
    print(f"estimated LLM cost: {n_questions} questions -> {est['calls']} reach the LLM "
          f"(~{est['mean_tokens_per_call']} tokens each incl. ~{COMPLETION_ALLOWANCE} completion), "
          f"{est['cached']} already in the response cache -> {est['uncached_calls']} live calls "
          f"~= {est['uncached_tokens']:,} tokens "
          f"({est['uncached_tokens'] / DAILY_CAP_GROQ_FREE:.0%} of Groq's free 200,000-token daily cap)",
          file=file, flush=True)
    if max_calls is not None:
        print(f"--max-llm-calls {max_calls}: the run stops cleanly after that many live calls and is marked PARTIAL",
              file=file, flush=True)
