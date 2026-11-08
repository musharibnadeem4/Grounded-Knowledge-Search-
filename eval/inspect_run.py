#!/usr/bin/env python
"""Inspect page_hit@5 failures of an eval run.

  python eval/inspect_run.py <run-name>

Reads eval/results/<run-name>.json (made by run_eval.py), and for each answerable
question whose top-5 contains no gold (doc_id, page), writes
eval/results/<run-name>_failures.md. Retrieval is re-run with retrieve() at k=50
using the index/config recorded in the run. Run from the project root.

page_header is read from cache/pages/<doc_id>.jsonl with the same cleaning
ingest uses (no direct access to the index).

Labels, relative to the gold doc(s):
  SAME_DOC                 result is from a gold doc (right filing, wrong page)
  SAME_COMPANY_OTHER_DOC   same company as a gold doc, different filing
  OTHER_COMPANY            different company
"""
import argparse
import ast
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drg import config  # noqa: E402
from drg.ingest import clean_page  # noqa: E402
from drg.retrieve import retrieve  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
LABELS = ["SAME_DOC", "SAME_COMPANY_OTHER_DOC", "OTHER_COMPANY"]
_headers = {}


def page_header(doc_id, page):
    if doc_id not in _headers:
        pages = {}
        p = ROOT / "cache" / "pages" / f"{doc_id}.jsonl"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                f.readline()  # meta line
                for line in f:
                    r = json.loads(line)
                    pages[r["page"]] = r["text"]
        _headers[doc_id] = pages
    text = _headers[doc_id].get(page)
    return clean_page(text)[1] if text is not None else "(not in cache)"


def one_line(s, n=None):
    s = " / ".join(x.strip() for x in s.splitlines() if x.strip())
    s = s.replace("`", "'")
    return s[:n] if n else s


def label(hit, gold_docs, gold_companies):
    if hit.doc_id in gold_docs:
        return "SAME_DOC"
    if hit.company in gold_companies:
        return "SAME_COMPANY_OTHER_DOC"
    return "OTHER_COMPANY"


# Retrieval settings that were added to drg.config after some runs were made, with the
# value they effectively had before they existed. Extend this when adding a new flag.
LEGACY_DEFAULTS = {"YEAR_COMPANY_FILTER": False, "RERANKER": None,
                   "MIN_CHUNK_CHARS": 0, "QUERY_CLEAN": False,
                   "DROP_BOILERPLATE": False, "PREFER_10K_OVER_ANNUALREPORT": False}
_PATH_KEYS = {"INDEX_DIR", "MANIFEST_PATH", "CACHE_DIR"}  # taken from the run args / repo root


def apply_recorded_config(cfg, run):
    """Make cfg equal the drg.config snapshot stored in the run (values were saved with
    str()). Keys missing from an old snapshot get their pre-existence value: LEGACY_DEFAULTS,
    else False for any flag that is a bool now, else the current value."""
    snap = run["config"].get("drg.config", {})
    for key in [k for k in vars(cfg) if k.isupper() and k not in _PATH_KEYS]:
        cur = getattr(cfg, key)
        if key in snap:
            raw = snap[key]
            if isinstance(cur, str):
                val = raw
            else:
                try:
                    val = ast.literal_eval(raw)
                except (ValueError, SyntaxError):
                    val = raw
        elif key in LEGACY_DEFAULTS:
            val = LEGACY_DEFAULTS[key]
        elif isinstance(cur, bool):
            val = False
        else:
            continue
        if val != cur:
            print(f"replaying {key}={val!r} (current default {cur!r})", file=sys.stderr)
            setattr(cfg, key, val)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_name")
    a = ap.parse_args()

    run = json.loads((RESULTS / f"{a.run_name}.json").read_text(encoding="utf-8"))
    cfg = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.INDEX_DIR = Path(run["config"]["args"]["index_dir"])
    cfg.MANIFEST_PATH = ROOT / "manifest.csv"
    apply_recorded_config(cfg, run)  # full recorded snapshot, so old runs replay as they ran
    # apply the config overrides recorded in the run (run_eval --set); stored as repr strings
    for key, raw in run["config"].get("overrides", {}).items():
        if not hasattr(cfg, key):
            sys.exit(f"run {a.run_name!r} recorded override {key}={raw}, "
                     f"but drg.config has no such setting")
        try:
            val = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            val = raw
        setattr(cfg, key, val)
        print(f"applying recorded override {key}={val!r}", file=sys.stderr)
    with open(cfg.MANIFEST_PATH, newline="", encoding="utf-8-sig") as f:
        company_of = {r["doc_id"].strip(): r["company"].strip() for r in csv.DictReader(f)}
    with open(run["config"]["args"]["questions"], encoding="utf-8") as f:
        questions = {q["id"]: q for q in map(json.loads, (l for l in f if l.strip()))}

    # Re-run retrieval (k=50) for every question and require the fresh top-10 to equal
    # the stored top-10; otherwise the index/config no longer matches the run.
    fresh, bad = {}, []
    for row in run["rows"]:
        q = questions[row["id"]]
        hits = retrieve(q["question"], q["role"], 50, cfg)
        fresh[row["id"]] = hits
        top = [(h.doc_id, h.page, h.score) for h in hits[:10]]
        old = [(h["doc_id"], h["page"], h["score"]) for h in row["top10"]]
        if len(top) != len(old) or any(
                (x[0], x[1]) != (y[0], y[1]) or abs(x[2] - y[2]) > 1e-4
                for x, y in zip(top, old)):
            bad.append(row["id"])
    if bad:
        sys.exit(f"ERROR: fresh top-10 differs from the stored top-10 of run {a.run_name!r} "
                 f"for {len(bad)} question(s), first: {bad[0]} (all: {', '.join(bad)}). "
                 f"The index or config no longer matches the run; nothing written.")

    failures = []
    for row in run["rows"]:
        if row["type"] != "answerable":
            continue
        gold = {(g["doc_id"], p) for g in row["gold"] for p in g["pages"]}
        if not any((h["doc_id"], h["page"]) in gold for h in row["top10"][:5]):
            failures.append(row)
    n_ans = sum(r["type"] == "answerable" for r in run["rows"])
    print(f"{len(failures)} of {n_ans} answerable questions fail page_hit@5", file=sys.stderr)

    out = [f"# Failures (page_hit@5 = false): {a.run_name}\n",
           f"{len(failures)} of {n_ans} answerable questions. Index: `{cfg.INDEX_DIR}`. "
           "Top-5 below comes from a fresh retrieve() at k=50 (same index/config as the run).\n"]
    rank_counts = Counter()
    label_counts = Counter()
    for row in failures:
        q = questions[row["id"]]
        gold = {(g["doc_id"], p) for g in row["gold"] for p in g["pages"]}
        gold_docs = {d for d, _ in gold}
        gold_companies = {company_of[d] for d in gold_docs}
        hits = fresh[row["id"]]

        out.append(f"## {row['id']} ({q['role']})\n")
        out.append(f"**Q:** {q['question']}\n")
        out.append("**Gold:** " + ", ".join(f"({d}, p.{p})" for d, p in sorted(gold)) + "\n")
        out.append("**Top 5:**\n")
        for rank, h in enumerate(hits[:5], 1):
            lab = label(h, gold_docs, gold_companies)
            label_counts[lab] += 1
            out.append(f"{rank}. `{lab}` {h.doc_id} p.{h.page} score={h.score:.3f}  ")
            out.append(f"   header: {one_line(page_header(h.doc_id, h.page))}  ")
            out.append(f"   text: {one_line(h.text, 120)}")
        rank = next((i for i, h in enumerate(hits, 1) if (h.doc_id, h.page) in gold), None)
        if rank is None:
            rank_counts["not in top 50"] += 1
            out.append("\n**First gold-page chunk:** not in top 50\n")
        else:
            rank_counts["rank 6-50" if rank > 5 else "rank 1-5"] += 1
            out.append(f"\n**First gold-page chunk:** rank {rank}\n")

    out.append("## Counts\n")
    out.append(f"- Failures: {len(failures)}")
    out.append(f"- Gold page at rank 6-50: {rank_counts['rank 6-50']}")
    out.append(f"- Gold page not in top 50: {rank_counts['not in top 50']}")
    if rank_counts["rank 1-5"]:
        out.append(f"- Gold page at rank 1-5 (unexpected; run vs re-run differ): {rank_counts['rank 1-5']}")
    total = sum(label_counts.values())
    out.append(f"- Top-5 results across all failures ({total}):")
    for lab in LABELS:
        out.append(f"  - {lab}: {label_counts[lab]}")
    path = RESULTS / f"{a.run_name}_failures.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
