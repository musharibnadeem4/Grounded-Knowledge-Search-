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
from drg.retrieve import retrieve  # noqa: E402

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
    for n in names:
        out[n] = mean([r["metrics"][n] for r in rows])
    return out


def fmt(x):
    return "-" if x is None else f"{x:.3f}"


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
    ap.add_argument("--questions", default=str(Path(__file__).resolve().parent / "questions.jsonl"))
    ap.add_argument("--answers", default=None,
                    help="(stub) path to generated answers; answer-quality metrics not implemented")
    a = ap.parse_args()

    ks = sorted(set(a.k))
    kmax = max(max(ks), 10)
    cfg = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.INDEX_DIR = Path(a.index_dir)
    cfg.MANIFEST_PATH = ROOT / "manifest.csv"

    questions = load_questions(a.questions)
    doc_types = load_doc_types(cfg.MANIFEST_PATH)
    print(f"{len(questions)} questions, k={ks}, index={cfg.INDEX_DIR}", file=sys.stderr)

    if a.answers:
        print("WARN --answers given, but answer-quality metrics are not implemented; ignoring",
              file=sys.stderr)

    retrieve("warm-up query", "lead", 1, cfg)  # load model, untimed

    rows, latencies, leaks_total = [], [], 0
    for q in questions:
        allowed = set(acl.allowed_companies(q["role"]))
        t0 = time.perf_counter()
        hits = retrieve(q["question"], q["role"], kmax, cfg)
        ms = (time.perf_counter() - t0) * 1000
        latencies.append(ms)
        leaks = sum(h.company not in allowed for h in hits)
        leaks_total += leaks
        row = {
            "id": q["id"], "role": q["role"], "type": q["type"], "tags": q["tags"],
            "gold": q["gold"],
            "doc_types": sorted({doc_types.get(g["doc_id"], "unknown") for g in q["gold"]}),
            "latency_ms": round(ms, 1), "acl_leaks": leaks,
            "top10": [{"doc_id": h.doc_id, "page": h.page, "score": round(h.score, 5)}
                      for h in hits[:10]],
        }
        row["metrics"] = score_question(q, hits, ks) if q["type"] == "answerable" else None
        rows.append(row)

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
    breakdowns = {
        "by_tag": {t: aggregate(rs, ks) for t, rs in sorted(by_tag.items())},
        "by_doc_type": {t: aggregate(rs, ks) for t, rs in sorted(by_doc_type.items())},
    }
    latency = {"p50_ms": pct(latencies, 50), "p95_ms": pct(latencies, 95),
               "mean_ms": mean(latencies), "n": len(latencies)}

    git = git_info()
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    full_config = {
        "args": {"run_name": a.run_name, "k": ks, "index_dir": str(cfg.INDEX_DIR),
                 "questions": a.questions},
        "drg.config": {k: str(getattr(cfg, k)) for k in dir(cfg) if k.isupper()},
        "retrieved_depth": kmax,
        "question_types": {t: len(rs) for t, rs in sorted(by_type.items())},
    }
    result = {"run_name": a.run_name, "timestamp": now, "git": git, "config": full_config,
              "metrics": {"overall": overall, "acl_leaks": leaks_total, "latency": latency},
              "breakdowns": breakdowns, "rows": rows}

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
    cols = [f"{b}@{k}" for k in ks for b in ("doc_hit", "page_hit", "gold_page_recall")] + ["mrr@10"]

    def table(groups):
        lines = ["| group | n | " + " | ".join(cols) + " |",
                 "|---|---:|" + "---:|" * len(cols)]
        for name, m in groups:
            lines.append(f"| {name} | {m['n']} | " + " | ".join(fmt(m[c]) for c in cols) + " |")
        return "\n".join(lines)

    out = [f"# Eval run: {res['run_name']}\n",
           f"- Timestamp: {res['timestamp']}",
           f"- Git SHA: {sha}",
           f"- Question types: {res['config']['question_types']}",
           f"- **ACL leaks: {res['metrics']['acl_leaks']}** (must be 0)",
           f"- Search latency: p50 {lat['p50_ms']:.0f} ms, p95 {lat['p95_ms']:.0f} ms "
           f"(n={lat['n']}, retrieval depth {res['config']['retrieved_depth']}, model load excluded)\n",
           "## Overall (answerable questions)\n", table([("all", ov)]), "",
           "## By tag\n", table(list(res["breakdowns"]["by_tag"].items())) if
           res["breakdowns"]["by_tag"] else "_no tagged questions_", "",
           "## By doc_type (of gold doc)\n",
           table(list(res["breakdowns"]["by_doc_type"].items())), "",
           "## Full config\n", "```json", json.dumps(res["config"], indent=1), "```", ""]
    return "\n".join(out)


def append_summary(res, ks):
    ov, lat = res["metrics"]["overall"], res["metrics"]["latency"]
    row = {"run_name": res["run_name"], "timestamp": res["timestamp"],
           "git_sha": res["git"]["sha"] or "", "git_dirty": res["git"]["dirty"],
           "n_answerable": ov["n"]}
    for k in ks:
        for b in ("doc_hit", "page_hit", "gold_page_recall"):
            row[f"{b}@{k}"] = round(ov[f"{b}@{k}"], 4) if ov[f"{b}@{k}"] is not None else ""
    row["mrr@10"] = round(ov["mrr@10"], 4) if ov["mrr@10"] is not None else ""
    row.update({"acl_leaks": res["metrics"]["acl_leaks"],
                "latency_p50_ms": round(lat["p50_ms"], 1),
                "latency_p95_ms": round(lat["p95_ms"], 1)})

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
