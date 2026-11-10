#!/usr/bin/env python
"""Retrieval eval. Calls drg.retrieve.retrieve() directly (not the CLI).

  python eval/run_eval.py --run-name baseline [--k 5 10 20] [--index-dir ./index]

Writes eval/results/<run-name>.json and .md and appends a row to
eval/results/summary.csv. Run from the project root.

Notes on definitions:
  * Results are chunks; several top-k results can come from one page. k counts
    chunks, and ranks (for MRR) are chunk ranks.
  * gold = set of (doc_id, page) over all gold entries of a question.
  * Retrieval is run once per question at max(k, 10); @k slices that list.
  * Latency is the wall time of retrieve() (embed + Chroma) at that depth,
    after one untimed warm-up query, so model load is excluded.
"""
import argparse
import csv
import datetime as dt
import ast
import json
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drg import acl, config  # noqa: E402
from drg import answer as ask_pipeline  # noqa: E402
from drg import llm  # noqa: E402
from drg.ingest import read_index_meta  # noqa: E402
from drg.query import parse_query  # noqa: E402
from drg.retrieve import last_timings, retrieve  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_metrics  # noqa: E402
import cost_estimate  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


# ----------------------------------------------------------------------- helpers
def git_info():
    def run(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)

    sha = run("rev-parse", "HEAD")
    if sha.returncode:
        return {"sha": None, "dirty": None}
    dirty = bool(run("status", "--porcelain", "--untracked-files=no").stdout.strip())
    return {"sha": sha.stdout.strip(), "dirty": dirty}


def load_questions(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_doc_types(manifest_path):
    with open(manifest_path, newline="", encoding="utf-8-sig") as f:
        return {r["doc_id"].strip(): r["doc_type"].strip() for r in csv.DictReader(f)}


def pct(values, p):
    s = sorted(values)
    if not s:
        return None
    i = (len(s) - 1) * p / 100
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


# ----------------------------------------------------------------------- scoring
# What `ask` actually reads: the per-company/interleaved retrieval (ASK_K or ASK_K_PER_COMPANY) and then the
# token-budgeted context. askk_page_hit = a gold page is among those chunks before the budget;
# ctx_page_hit / ctx_gold_recall = after the budget (what the LLM sees).
CTX_METRICS = ["askk_page_hit", "ctx_page_hit", "ctx_gold_recall"]


def score_ctx(q, ask_hits, ctx_hits):
    gold_pages = {(g["doc_id"], p) for g in q["gold"] for p in g["pages"]}
    ask_set = {(h.doc_id, h.page) for h in ask_hits}
    ctx_set = {(h.doc_id, h.page) for h in ctx_hits}
    return {"askk_page_hit": float(bool(ask_set & gold_pages)),
            "ctx_page_hit": float(bool(ctx_set & gold_pages)),
            "ctx_gold_recall": len(ctx_set & gold_pages) / len(gold_pages) if gold_pages else 0.0}


def score_question(q, hits, ks):
    """Per-question retrieval metrics (answerable only)."""
    gold_pages = {(g["doc_id"], p) for g in q["gold"] for p in g["pages"]}
    gold_docs = {g["doc_id"] for g in q["gold"]}
    m = {}
    for k in ks:
        top = hits[:k]
        found = {(h.doc_id, h.page) for h in top} & gold_pages
        m[f"doc_hit@{k}"] = float(any(h.doc_id in gold_docs for h in top))
        m[f"page_hit@{k}"] = float(bool(found))
        m[f"gold_page_recall@{k}"] = len(found) / len(gold_pages) if gold_pages else 0.0
    rr = 0.0
    for rank, h in enumerate(hits[:10], 1):
        if (h.doc_id, h.page) in gold_pages:
            rr = 1.0 / rank
            break
    m["mrr@10"] = rr
    return m


def aggregate(rows, ks):
    """rows: per-question dicts with a 'metrics' entry (answerable only)."""
    names = [f"{b}@{k}" for k in ks for b in ("doc_hit", "page_hit", "gold_page_recall")]
    names.append("mrr@10")
    out = {"n": len(rows)}
    for n in names + CTX_METRICS:
        vals = [r["metrics"][n] for r in rows if n in r["metrics"]]
        out[n] = mean(vals) if vals else None
    return out


def fmt(x):
    return "-" if x is None else f"{x:.3f}"


def parse_overrides(items, cfg):
    """['KEY=VALUE', ...] -> {KEY: value}. KEY must be an existing drg.config setting."""
    out = {}
    for item in items:
        key, sep, raw = item.partition("=")
        key = key.strip()
        if not sep or not hasattr(cfg, key) or not key.isupper():
            sys.exit(f"--set {item!r}: expected KEY=VALUE with KEY an existing drg.config "
                     f"setting (e.g. YEAR_COMPANY_FILTER=True)")
        try:
            out[key] = ast.literal_eval(raw.strip())
        except (ValueError, SyntaxError):
            out[key] = raw.strip()
    return out


# ------------------------------------------------------------------------ answers
def evaluate_answers(path, questions):
    """Stub: answer-quality metrics (correctness, faithfulness, ...) are not implemented."""
    raise NotImplementedError("answer-quality metrics are not implemented yet")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--k", type=int, nargs="+", default=[5, 10, 20])
    ap.add_argument("--index-dir", default=str(ROOT / "index"))
    ap.add_argument("--questions", default=str(Path(__file__).resolve().parent / "questions_v2.jsonl"),
                    help="question file (default: eval/questions_v2.jsonl = 20 dev + 34 generated; "
                         "eval/questions.jsonl is the original 20 dev questions)")
    ap.add_argument("--set", dest="overrides", action="append", default=[], metavar="KEY=VALUE",
                    help="override a drg.config flag for this run, e.g. --set YEAR_COMPANY_FILTER=True "
                         "(repeatable; value parsed as a Python literal, else a string)")
    ap.add_argument("--answers", action="store_true",
                    help="also run the ask pipeline in-process (live LLM calls) and score the answers")
    ap.add_argument("--sleep", type=float, default=8.0,
                    help="with --answers: seconds to wait after each question that called the LLM "
                         "(rate limits; 429s are additionally retried by drg.llm)")
    ap.add_argument("--max-llm-calls", type=int, default=None, metavar="N",
                    help="with --answers: stop cleanly after N live provider calls (cache hits are free) and write "
                         "the results so far marked PARTIAL. Also stops at once if the provider's daily cap is hit")
    ap.add_argument("--no-llm-cache", action="store_true",
                    help="with --answers: do not read/write the prompt-keyed LLM response cache (cache/llm). "
                         "The cache avoids paying twice for identical prompts (Groq free tier: 200k tokens/day)")
    ap.add_argument("--split", choices=["tune", "holdout", "all"], default="all",
                    help="which questions to run (default all); questions without a `split` field count as tune. "
                         "The report always lists tune and holdout separately. When tuning, use --split tune: "
                         "holdout is for the final evaluation only")
    a = ap.parse_args()

    if (RESULTS / f"{a.run_name}.json").exists():
        sys.exit(f"eval/results/{a.run_name}.json already exists; results are never overwritten - "
                 f"pick a new --run-name")
    ks = sorted(set(a.k))
    kmax = max(max(ks), 10)
    cfg = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.INDEX_DIR = Path(a.index_dir)
    cfg.MANIFEST_PATH = ROOT / "manifest.csv"
    overrides = parse_overrides(a.overrides, cfg)
    for key, val in overrides.items():
        setattr(cfg, key, val)
    if overrides:
        print(f"config overrides: {overrides}", file=sys.stderr)
    index_meta = read_index_meta(cfg.INDEX_DIR)  # how the index was built (None = predates it)
    print(f"index metadata: {index_meta}", file=sys.stderr)

    questions = load_questions(a.questions)
    if a.split != "all":
        questions = [q for q in questions if q.get("split", "tune") == a.split]
    elif any(q.get("split") == "holdout" for q in questions):
        print("NOTE --split all includes the HOLDOUT questions (reported separately; do not tune on them)",
              file=sys.stderr)
    if a.split == "holdout":
        print("NOTE running HOLDOUT questions (final evaluation only)", file=sys.stderr)
    if not questions:
        sys.exit(f"no questions for --split {a.split}")
    doc_types = load_doc_types(cfg.MANIFEST_PATH)
    print(f"{len(questions)} questions, k={ks}, index={cfg.INDEX_DIR}", file=sys.stderr)

    if a.answers and not a.no_llm_cache:
        llm.enable_cache(ROOT / "cache" / "llm")
    retrieve("warm-up query", "lead", 1, cfg)  # load model, untimed
    if a.answers:  # live LLM: say what it will cost before spending anything
        cost_estimate.report(cost_estimate.estimate(questions, cfg), len(questions), a.max_llm_calls)

    rows, latencies, rerank_lat, leaks_total = [], [], [], 0
    partial = None
    calls0 = llm.api_calls
    for qi, q in enumerate(questions):
        if a.answers and a.max_llm_calls is not None and llm.api_calls - calls0 >= a.max_llm_calls:
            partial = {"reason": f"--max-llm-calls {a.max_llm_calls} reached", "questions_run": len(rows),
                       "questions_total": len(questions), "next_question": q["id"]}
            print(f"PARTIAL: {partial['reason']} after {len(rows)} of {len(questions)} questions", file=sys.stderr)
            break
        q.setdefault("gold", [])
        allowed = set(acl.allowed_companies(q["role"]))
        t0 = time.perf_counter()
        hits = retrieve(q["question"], q["role"], kmax, cfg)
        ms = (time.perf_counter() - t0) * 1000
        latencies.append(ms)
        rerank_s = last_timings().get("rerank_s")  # None when RERANKER is off
        if rerank_s is not None:
            rerank_lat.append(rerank_s * 1000)
        leaks = sum(h.company not in allowed for h in hits)
        leaks_total += leaks
        row = {
            "id": q["id"], "role": q["role"], "type": q["type"], "tags": q["tags"],
            "split": q.get("split", "tune"),
            "gold": q["gold"],
            "doc_types": sorted({doc_types.get(g["doc_id"], "unknown") for g in q["gold"]}),
            "latency_ms": round(ms, 1),
            "rerank_ms": None if rerank_s is None else round(rerank_s * 1000, 1),
            "acl_leaks": leaks,
            "top10": [{"doc_id": h.doc_id, "page": h.page, "score": round(h.score, 5)}
                      for h in hits[:10]],
        }
        row["metrics"] = score_question(q, hits, ks) if q["type"] == "answerable" else None
        if row["metrics"] is not None:
            # same retrieval + context budget as `ask` (untimed; not part of the latency numbers)
            companies, _ = parse_query(q["question"])
            ask_hits = ask_pipeline.gather(q["question"], q["role"], companies, cfg)
            ctx_hits = ask_pipeline.fit_budget(ask_hits, cfg.CONTEXT_TOKEN_BUDGET, multi=len(companies) >= 2)
            row["metrics"].update(score_ctx(q, ask_hits, ctx_hits))
            row["ctx"] = [{"doc_id": h.doc_id, "page": h.page} for h in ctx_hits]
        rows.append(row)
        if a.answers:
            t1, w0, h0 = time.perf_counter(), llm.total_wait, llm.cache_stats()["hits"]
            res = ask_pipeline.answer(q["question"], q["role"], cfg)
            secs = time.perf_counter() - t1
            waited = llm.total_wait - w0
            cached = llm.cache_stats()["hits"] > h0
            st = ask_pipeline.last_run
            if st.get("quota_exhausted"):  # the provider's daily cap: this and every later call would fail
                rows.pop()  # do not score a refusal that the model never made
                partial = {"reason": "provider daily quota exhausted", "questions_run": len(rows),
                           "questions_total": len(questions), "next_question": q["id"]}
                print(f"PARTIAL: provider daily quota exhausted at {q['id']}; stopping with {len(rows)} of "
                      f"{len(questions)} questions", file=sys.stderr)
                break
            row["answer"] = res
            row["answer_metrics"] = answer_metrics.score_answer(
                q, res, secs, st.get("llm_called", False), st.get("ungrounded_warnings", 0), waited)
            row["answer_metrics"]["context_chunks"] = st.get("context_chunks", 0)
            row["answer_metrics"]["llm_cached"] = cached
            row["question"], row["gold_answer"] = q["question"], q.get("answer", "")
            row["has_numeric"] = bool(q.get("numeric"))
            print(f"[{qi + 1}/{len(questions)}] {q['id']} {q['type']}: {res['status']} "
                  f"(expected {row['answer_metrics']['expected']}) {secs:.1f}s", file=sys.stderr)
            if st.get("llm_called") and not cached and a.sleep > 0 and qi < len(questions) - 1:
                time.sleep(a.sleep)  # pace real API calls (a cache hit makes none)

    answerable = [r for r in rows if r["metrics"]]
    overall = aggregate(answerable, ks)
    by_tag, by_doc_type, by_type = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in answerable:
        for t in r["tags"]:
            by_tag[t].append(r)
        for t in r["doc_types"]:
            by_doc_type[t].append(r)
    for r in rows:
        by_type[r["type"]].append(r)
    by_split = defaultdict(list)
    for r in answerable:
        by_split[r["split"]].append(r)
    breakdowns = {
        "by_split": {t: aggregate(rs, ks) for t, rs in sorted(by_split.items())},
        "by_tag": {t: aggregate(rs, ks) for t, rs in sorted(by_tag.items())},
        "by_doc_type": {t: aggregate(rs, ks) for t, rs in sorted(by_doc_type.items())},
    }
    answers = None
    if a.answers:
        print(f"LLM cache: {llm.cache_stats()}", file=sys.stderr)
        by_kind_a, by_tag_a = defaultdict(list), defaultdict(list)
        for r in rows:
            by_kind_a[r["type"]].append(r)
            for t in r["tags"]:
                by_tag_a[t].append(r)
        by_split_a = defaultdict(list)
        for r in rows:
            by_split_a[r["split"]].append(r)
        answers = {"overall": answer_metrics.summarize(rows),
                   "by_split": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_split_a.items())},
                   "by_type": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_kind_a.items())},
                   "by_tag": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_tag_a.items())},
                   "llm": dict(zip(("provider", "model"), llm._env())),
                   "sleep_s": a.sleep, "max_llm_calls": a.max_llm_calls,
                   "live_calls": llm.api_calls - calls0, "llm_cache": llm.cache_stats() if not a.no_llm_cache else None}
    latency = {"p50_ms": pct(latencies, 50), "p95_ms": pct(latencies, 95),
               "mean_ms": mean(latencies), "n": len(latencies)}
    # reranker time alone (already included in the totals above); None when RERANKER is off
    rerank_latency = ({"p50_ms": pct(rerank_lat, 50), "p95_ms": pct(rerank_lat, 95),
                       "mean_ms": mean(rerank_lat), "n": len(rerank_lat)}
                      if rerank_lat else None)

    git = git_info()
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    full_config = {
        "args": {"run_name": a.run_name, "k": ks, "index_dir": str(cfg.INDEX_DIR),
                 "questions": a.questions, "split": a.split, "answers": a.answers},
        "drg.config": {k: str(getattr(cfg, k)) for k in dir(cfg) if k.isupper()},
        "overrides": {k: repr(v) for k, v in overrides.items()},
        "retrieved_depth": kmax,
        "question_types": {t: len(rs) for t, rs in sorted(by_type.items())},
    }
    result = {"run_name": a.run_name, "timestamp": now, "git": git, "config": full_config,
              "metrics": {"overall": overall, "acl_leaks": leaks_total, "latency": latency,
                          "rerank_latency": rerank_latency},
              "index_meta": index_meta if index_meta is not None
              else {"note": "no index_meta.json (index predates it)", "context_header": False},
              "breakdowns": breakdowns, "answers": answers, "split": a.split,
              "partial": partial, "status": "PARTIAL" if partial else "COMPLETE", "rows": rows}

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{a.run_name}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    (RESULTS / f"{a.run_name}.md").write_text(
        render_md(result, ks), encoding="utf-8")
    append_summary(result, ks)
    print(f"wrote {RESULTS / (a.run_name + '.json')}, .md, and updated summary.csv",
          file=sys.stderr)
    if leaks_total:
        print(f"ACL LEAKS: {leaks_total}", file=sys.stderr)
        return 1
    return 0


def render_md(res, ks):
    g, ov = res["git"], res["metrics"]["overall"]
    sha = "none (no commits)" if not g["sha"] else g["sha"] + (" (dirty)" if g["dirty"] else "")
    lat = res["metrics"]["latency"]
    rl = res["metrics"].get("rerank_latency")
    cols = ([f"{b}@{k}" for k in ks for b in ("doc_hit", "page_hit", "gold_page_recall")]
            + ["mrr@10"] + CTX_METRICS)

    def table(groups):
        lines = ["| group | n | " + " | ".join(cols) + " |",
                 "|---|---:|" + "---:|" * len(cols)]
        for name, m in groups:
            lines.append(f"| {name} | {m['n']} | " + " | ".join(fmt(m[c]) for c in cols) + " |")
        return "\n".join(lines)

    out = [f"# Eval run: {res['run_name']}\n"]
    if res.get("partial"):
        pt = res["partial"]
        out.append(f"> **PARTIAL RUN** - {pt['reason']}: {pt['questions_run']} of {pt['questions_total']} questions "
                   f"were run (stopped before `{pt['next_question']}`). Metrics cover only those questions.\n")
    out += [
           f"- Timestamp: {res['timestamp']}",
           f"- Config overrides (--set): {res['config']['overrides'] or 'none'}",
           f"- Index metadata: {res.get('index_meta')}",
           f"- Git SHA: {sha}",
           f"- Question types: {res['config']['question_types']}",
           f"- **ACL leaks: {res['metrics']['acl_leaks']}** (must be 0)",
           f"- Search latency: p50 {lat['p50_ms']:.0f} ms, p95 {lat['p95_ms']:.0f} ms "
           f"(n={lat['n']}, retrieval depth {res['config']['retrieved_depth']}, model load excluded)",
           (f"- Rerank latency (included in the above): p50 {rl['p50_ms']:.0f} ms, "
            f"p95 {rl['p95_ms']:.0f} ms" if rl else "- Rerank latency: n/a (RERANKER off)") + "\n",
           "## Overall (answerable questions)\n", table([("all", ov)]), "",
           "## By split (tune = used for decisions, holdout = first looked at in the final evaluation)\n",
           table(list(res["breakdowns"].get("by_split", {}).items())), "",
           "## By tag\n", table(list(res["breakdowns"]["by_tag"].items())) if
           res["breakdowns"]["by_tag"] else "_no tagged questions_", "",
           "## By doc_type (of gold doc)\n",
           table(list(res["breakdowns"]["by_doc_type"].items())), "",
           ] + answers_md(res) + ["## Full config\n", "```json", json.dumps(res["config"], indent=1), "```", ""]
    return "\n".join(out)


ANS_COLS = ["n", "n_answerable", "status_accuracy", "refusal_recall", "refusal_precision",
            "answer_rate_on_answerable", "refusal_rate_on_answerable", "numeric_accuracy", "n_numeric",
            "correct_rate", "partial_rate", "soft_refusal_rate", "refused_rate", "confident_error_rate", "citation_hit",
            "citation_precision", "ungrounded_warnings", "latency_p50_s", "latency_p95_s",
            "latency_net_p50_s", "latency_net_p95_s"]


def answers_md(res):
    an = res.get("answers")
    if not an:
        return []

    def tbl(groups):
        lines = ["| group | " + " | ".join(ANS_COLS) + " |", "|---|" + "---:|" * len(ANS_COLS)]
        for name, m in groups:
            lines.append(f"| {name} | " + " | ".join(
                (fmt(m[c]) if isinstance(m[c], float) or m[c] is None else str(m[c])) for c in ANS_COLS) + " |")
        return "\n".join(lines)

    out = [f"## Answer quality (live LLM {an.get('llm')}; sleep {an['sleep_s']} s; split {res.get('split')})\n",
           tbl([("all", an["overall"])] + list(an.get("by_split", {}).items())), "", "### By question type\n", tbl(list(an["by_type"].items())), "",
           "### By tag\n", tbl(list(an["by_tag"].items())), "",
           "### Per question\n", "| id | type | expected | got | numeric_ok | cite_hit | warnings | s |",
           "|---|---|---|---|---|---|---|---:|"]
    for r in res["rows"]:
        m = r.get("answer_metrics")
        if m:
            out.append(f"| {r['id']} | {r['type']} | {m['expected']} | {m['got']} | {m['numeric_ok']} | "
                       f"{m['cite_hit']} | {m['ungrounded_warnings']} | {m['seconds']} |")
    out += ["", "### Manual review (answered, no numeric check)\n"]
    manual = [r for r in res["rows"] if r.get("answer_metrics") and r["type"] == "answerable"
              and not r.get("has_numeric") and r["answer"]["status"] == "answered"]
    if not manual:
        out.append("_none_")
    for r in manual:
        out += [f"**{r['id']}** ({r['role']})", f"- Q: {r['question']}",
                f"- Gold: {r['gold_answer']}", f"- System: {r['answer']['answer']}",
                f"- Cited: {[(c['doc_id'], c['page']) for c in r['answer']['citations']]}", ""]
    return out + [""]


def append_summary(res, ks):
    ov, lat = res["metrics"]["overall"], res["metrics"]["latency"]
    row = {"run_name": res["run_name"], "timestamp": res["timestamp"],
           "git_sha": res["git"]["sha"] or "", "git_dirty": res["git"]["dirty"],
           "overrides": ";".join(f"{k}={v}" for k, v in res["config"]["overrides"].items()),
           "index_context_header": res.get("index_meta", {}).get("context_header", ""),
           "n_answerable": ov["n"]}
    for k in ks:
        for b in ("doc_hit", "page_hit", "gold_page_recall"):
            row[f"{b}@{k}"] = round(ov[f"{b}@{k}"], 4) if ov[f"{b}@{k}"] is not None else ""
    row["mrr@10"] = round(ov["mrr@10"], 4) if ov["mrr@10"] is not None else ""
    for c in CTX_METRICS:
        row[c] = round(ov[c], 4) if ov.get(c) is not None else ""
    row["split"] = res.get("split", "")
    row["status"] = res.get("status", "COMPLETE")
    an = (res.get("answers") or {}).get("overall")
    if an:
        for c in ("status_accuracy", "refusal_recall", "refusal_precision", "numeric_accuracy",
                  "correct_rate", "partial_rate", "soft_refusal_rate", "refused_rate", "confident_error_rate",
                  "answered_wrong_rate", "refusal_rate_on_answerable",
                  "citation_hit", "citation_precision", "ungrounded_warnings", "latency_p50_s", "latency_p95_s",
                  "latency_net_p50_s", "latency_net_p95_s"):
            row[f"ans_{c}"] = round(an[c], 4) if isinstance(an[c], float) else (an[c] if an[c] is not None else "")
    row.update({"acl_leaks": res["metrics"]["acl_leaks"],
                "latency_p50_ms": round(lat["p50_ms"], 1),
                "latency_p95_ms": round(lat["p95_ms"], 1)})
    rl = res["metrics"].get("rerank_latency")
    row["rerank_p50_ms"] = round(rl["p50_ms"], 1) if rl else ""
    row["rerank_p95_ms"] = round(rl["p95_ms"], 1) if rl else ""

    path = RESULTS / "summary.csv"
    existing = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    header = list(existing[0].keys()) if existing else []
    for key in row:  # union of columns if --k differs between runs
        if key not in header:
            header.append(key)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, restval="")
        w.writeheader()
        w.writerows(existing + [row])


if __name__ == "__main__":
    sys.exit(main())
