#!/usr/bin/env python
"""Compare two eval runs question by question. Reads stored results only (no retrieval).

  python eval/compare_runs.py <runA> <runB>

For each answerable question: rank of the first gold-page chunk in A and in B, and a
verdict ("B better" / "B worse" / same). Ranks are limited to the results stored in
each run's json (run_eval.py stores the top 10), so a miss is shown as ">N" with N the
stored depth. A miss ranks worse than any hit; two misses are "same".
Markdown goes to stdout.
"""
import argparse
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"


def load(name):
    p = RESULTS / f"{name}.json"
    if not p.exists():
        sys.exit(f"no such run: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def first_gold_rank(row):
    gold = {(g["doc_id"], p) for g in row["gold"] for p in g["pages"]}
    for rank, h in enumerate(row["top10"], 1):
        if (h["doc_id"], h["page"]) in gold:
            return rank
    return None


def compare_flag(a):
    """Per-question hit/miss comparison for askk / ctx / answer. Net = B better - B worse."""
    ra, rb = load(a.run_a), load(a.run_b)

    def val(row):
        if a.metric == "answer":
            m = row.get("answer_metrics")
            return None if not m or m.get("answer_ok") is None else float(bool(m["answer_ok"]))
        m = row.get("metrics")
        key = {"askk": "askk_page_hit", "ctx": "ctx_page_hit"}[a.metric]
        return None if not m or key not in m else m[key]

    rows_a, rows_b = {r["id"]: r for r in ra["rows"]}, {r["id"]: r for r in rb["rows"]}
    groups = {"B better": [], "B worse": [], "same": []}
    lines = [f"# {a.run_a} (A) vs {a.run_b} (B), metric: {a.metric}\n",
             "| id | role | A | B | verdict |", "|---|---|---:|---:|---|"]
    skipped = []
    for i in rows_a:
        if i not in rows_b:
            continue
        x, y = val(rows_a[i]), val(rows_b[i])
        if x is None or y is None:
            skipped.append(i)
            continue
        verdict = "B better" if y > x else "B worse" if y < x else "same"
        groups[verdict].append(i)
        lines.append(f"| {i} | {rows_a[i]['role']} | {x:g} | {y:g} | {verdict} |")
    n = sum(len(v) for v in groups.values())
    lines += ["", "## Counts\n", f"- {n} questions compared ({len(skipped)} without this metric skipped)"]
    for v in ("B better", "B worse", "same"):
        lines.append(f"- **{v}: {len(groups[v])}**" + (f" - {', '.join(groups[v])}" if groups[v] else ""))
    lines.append(f"- **net (B better - B worse): {len(groups['B better']) - len(groups['B worse'])}**")
    sys.stdout.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--metric", choices=["rank", "askk", "ctx", "answer"], default="rank",
                    help="rank (default): rank of the first gold-page chunk in the stored top 10; "
                         "askk / ctx: gold page among the chunks ask retrieves / the budgeted LLM context; "
                         "answer: answer_ok (numeric match, or correct refusal) from an --answers run")
    a = ap.parse_args()
    if a.metric != "rank":
        return compare_flag(a)

    ra, rb = load(a.run_a), load(a.run_b)
    rows_a = {r["id"]: r for r in ra["rows"] if r["type"] == "answerable"}
    rows_b = {r["id"]: r for r in rb["rows"] if r["type"] == "answerable"}
    ids = [i for i in rows_a if i in rows_b]
    for name, only in ((a.run_a, set(rows_a) - set(rows_b)), (a.run_b, set(rows_b) - set(rows_a))):
        if only:
            print(f"WARN {len(only)} answerable question(s) only in {name}, skipped: "
                  f"{', '.join(sorted(only))}", file=sys.stderr)
    for i in ids:
        if rows_a[i]["gold"] != rows_b[i]["gold"]:
            print(f"WARN {i}: gold differs between the runs; using each run's own gold",
                  file=sys.stderr)

    depth = max(len(r["top10"]) for r in list(rows_a.values()) + list(rows_b.values()))
    miss = f">{depth}"
    fmt = lambda r: miss if r is None else str(r)

    groups = {"B better": [], "B worse": [], "same": []}
    lines = [f"# {a.run_a} (A) vs {a.run_b} (B)\n",
             f"Rank of the first gold-page chunk within the stored top {depth} "
             f"(`{miss}` = not in it).\n",
             f"| id | role | A rank | B rank | verdict |", "|---|---|---:|---:|---|"]
    for i in ids:
        x, y = first_gold_rank(rows_a[i]), first_gold_rank(rows_b[i])
        xa, yb = (depth + 1 if x is None else x), (depth + 1 if y is None else y)
        verdict = "B better" if yb < xa else "B worse" if yb > xa else "same"
        groups[verdict].append(i)
        lines.append(f"| {i} | {rows_a[i]['role']} | {fmt(x)} | {fmt(y)} | {verdict} |")

    lines += ["", "## Counts\n", f"- {len(ids)} answerable questions compared"]
    for v in ("B better", "B worse", "same"):
        lines.append(f"- **{v}: {len(groups[v])}**" + (f" — {', '.join(groups[v])}" if groups[v] else ""))
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
