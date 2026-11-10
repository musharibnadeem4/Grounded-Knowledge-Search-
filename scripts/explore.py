#!/usr/bin/env python
"""Corpus exploration report (markdown).

Usage:
    python scripts/explore.py <corpus_dir> [--manifest manifest.csv]
        [--questions dev_questions.jsonl] [--out docs/notes/explore_report.md]
        [--min-chars 50]

Sections:
  1. Per-PDF stats: page count, chars/page (min/median/mean/max), pages with
     near-zero text (possible scans).
  2. Manifest doc_id -> file matching (case-sensitive and case-insensitive).
  3. For each dev question, first 300 chars of each gold page, read with
     pdfplumber via pdf.pages[page - 1] (i.e. gold pages assumed 1-based).
"""
import argparse
import csv
import json
import re
import statistics
from decimal import Decimal, InvalidOperation
import sys
from pathlib import Path

import pdfplumber


def page_text(page):
    try:
        return page.extract_text() or ""
    except Exception as e:  # keep going on a bad page
        return f"<<extract error: {e}>>"


NUM_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?|\d*\.\d+")


def canon_numbers(text):
    """Numbers in text as canonical strings: commas dropped, trailing zeros
    stripped, so '1,577' == '1577.00'. $ and % are ignored naturally."""
    found = []
    for m in NUM_RE.findall(text or ""):
        try:
            found.append(format(Decimal(m.replace(",", "")).normalize(), "f"))
        except InvalidOperation:
            pass
    return found


def answer_numbers(answer):
    """Unique (canonical, weak) pairs. weak = written without a decimal point
    and either a year-like value (1990-2030) or under 10."""
    out = {}
    for m in NUM_RE.findall(str(answer or "")):
        try:
            d = Decimal(m.replace(",", ""))
        except InvalidOperation:
            continue
        canon = format(d.normalize(), "f")
        weak = "." not in m and (Decimal(1990) <= d <= Decimal(2030) or d < 10)
        out[canon] = out.get(canon, True) and weak
    return list(out.items())


def page_numbers(text):
    return set(canon_numbers(text))


def scan_pdf(path, min_chars):
    chars = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                chars.append(len(page_text(page).strip()))
    except Exception as e:
        return {"error": str(e)}
    low = [i + 1 for i, c in enumerate(chars) if c < min_chars]
    return {"n": len(chars), "chars": chars, "low": low}


def fmt_pages(pages, limit=15):
    s = ", ".join(map(str, pages[:limit]))
    return s + (f", ... (+{len(pages) - limit})" if len(pages) > limit else "")


def md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus_dir")
    ap.add_argument("--manifest", default="manifest.csv")
    ap.add_argument("--questions", default="dev_questions.jsonl")
    ap.add_argument("--out", default="docs/notes/explore_report.md")
    ap.add_argument("--min-chars", type=int, default=50,
                    help="pages with fewer stripped chars are 'near-zero'")
    args = ap.parse_args()

    corpus = Path(args.corpus_dir)
    pdfs = sorted(corpus.glob("*.pdf"), key=lambda p: p.name)
    out = []
    w = out.append

    w(f"# Corpus exploration: `{corpus}`\n")
    w(f"- PDFs found: **{len(pdfs)}**")
    w(f"- Near-zero text threshold: < {args.min_chars} chars/page\n")

    # ---- 1. per-PDF stats
    w("## 1. Per-PDF stats\n")
    w("| file | pages | min | median | mean | max | near-zero pages | near-zero pages (1-based) |")
    w("|---|---:|---:|---:|---:|---:|---:|---|")
    stats = {}
    for i, p in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {p.name}", file=sys.stderr)
        s = scan_pdf(p, args.min_chars)
        stats[p.stem] = s
        if "error" in s:
            w(f"| {p.name} | ERROR: {md_cell(s['error'])} | | | | | | |")
            continue
        c = s["chars"]
        if not c:
            w(f"| {p.name} | 0 | | | | | 0 | |")
            continue
        w(f"| {p.name} | {s['n']} | {min(c)} | {int(statistics.median(c))} | "
          f"{int(statistics.mean(c))} | {max(c)} | {len(s['low'])} | {fmt_pages(s['low'])} |")

    ok = {k: v for k, v in stats.items() if "error" not in v}
    w("")
    w(f"- Total pages: {sum(v['n'] for v in ok.values())}")
    flagged = sorted(((len(v['low']) / v['n'], k, len(v['low']), v['n'])
                      for k, v in ok.items() if v['n'] and v['low']), reverse=True)
    if flagged:
        w("- PDFs with near-zero pages, worst first (fraction): "
          + "; ".join(f"{k} {nl}/{n}" for _, k, nl, n in flagged[:15]))
    else:
        w("- No PDFs have near-zero text pages.")
    errs = [k for k, v in stats.items() if "error" in v]
    if errs:
        w(f"- Unreadable PDFs: {', '.join(errs)}")
    w("")

    # ---- 2. manifest matching
    w("## 2. Manifest doc_id vs files\n")
    mpath = Path(args.manifest)
    with open(mpath, newline="", encoding="utf-8-sig") as f:
        ids = [r["doc_id"].strip() for r in csv.DictReader(f)]
    stems = {p.stem for p in pdfs}
    lower = {}
    for st in stems:
        lower.setdefault(st.lower(), []).append(st)
    exact_miss = [d for d in ids if d not in stems]
    ci_miss = [d for d in ids if d.lower() not in lower]
    case_only = [d for d in exact_miss if d.lower() in lower]
    dupes = sorted({d for d in ids if ids.count(d) > 1})
    unlisted = sorted(stems - set(ids))
    ci_collisions = {k: v for k, v in lower.items() if len(v) > 1}

    w(f"- Manifest rows: **{len(ids)}** ({len(set(ids))} unique)")
    w(f"- Matched case-sensitive: **{len(ids) - len(exact_miss)}/{len(ids)}**")
    w(f"- Matched case-insensitive: **{len(ids) - len(ci_miss)}/{len(ids)}**")
    w(f"- Missing case-sensitive: {len(exact_miss)}")
    for d in exact_miss:
        note = f" -> case-insensitive match: {lower[d.lower()]}" if d.lower() in lower else " -> NO file"
        w(f"  - `{d}`{note}")
    w(f"- Match only when ignoring case: {len(case_only)}")
    w(f"- Missing even case-insensitively: {len(ci_miss)}")
    if dupes:
        w(f"- Duplicate doc_ids in manifest: {', '.join(dupes)}")
    if ci_collisions:
        w(f"- Files colliding when lowercased: {ci_collisions}")
    w(f"- PDFs not in manifest (case-sensitive): {len(unlisted)}")
    for u in unlisted:
        w(f"  - `{u}`")
    w("")

    # ---- 3. gold pages
    w("## 3. Gold pages (assumed 1-based; text = `pdf.pages[page - 1]`)\n")
    qs = []
    qpath = Path(args.questions)
    with open(qpath, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                qs.append(json.loads(line))
    w(f"{len(qs)} questions from `{qpath}`.\n")
    tally = {"found on gold page": 0, "found only on neighbour": 0,
             "not found": 0, "skipped": 0}
    summary_idx = len(out)
    w("")  # placeholder, filled in after the loop

    for q in qs:
        did = q.get("doc_id")
        pages = q.get("pages") or []
        w(f"### {q.get('id')} — {did}\n")
        w(f"**Q:** {q.get('question')}\n")
        w(f"**Gold pages:** {pages}\n")
        path = corpus / f"{did}.pdf"
        if not path.exists():
            alt = lower.get(str(did).lower())
            if alt:
                path = corpus / f"{alt[0]}.pdf"
                w(f"_File matched case-insensitively: `{path.name}`_\n")
            else:
                w("**MISSING FILE**\n")
                continue
        try:
            with pdfplumber.open(path) as pdf:
                n = len(pdf.pages)
                w(f"_{path.name}: {n} pages_\n")
                for pg in pages:
                    if not 1 <= pg <= n:
                        w(f"- **page {pg}: OUT OF RANGE for 1-based (1..{n})**\n")
                        continue
                    t = page_text(pdf.pages[pg - 1]).strip()
                    w(f"**Page {pg}** ({len(t)} chars):\n")
                    w("```")
                    w(t[:300])
                    w("```\n")

                # numeric check of the answer against gold +/- 1 pages
                nums = answer_numbers(q.get("answer"))
                if nums:
                    gold = {pg for pg in pages if 1 <= pg <= n}
                    neigh = {x for pg in gold for x in (pg - 1, pg + 1)
                             if 1 <= x <= n} - gold
                    num_sets = {x: page_numbers(page_text(pdf.pages[x - 1]))
                                for x in sorted(gold | neigh)}
                    w(f"**Answer numbers** (gold pages {sorted(gold)}, "
                      f"neighbours {sorted(neigh)}):\n")
                    for num, weak in nums:
                        on_gold = [x for x in sorted(gold) if num in num_sets[x]]
                        on_neigh = [x for x in sorted(neigh) if num in num_sets[x]]
                        if weak:
                            tally["skipped"] += 1
                            w(f"- `{num}`: skipped (weak)")
                            continue
                        if on_gold:
                            verdict = "found on gold page"
                        elif on_neigh:
                            verdict = "found only on neighbour"
                        else:
                            verdict = "not found"
                        tally[verdict] += 1
                        w(f"- `{num}`: {verdict} — pages {on_gold + on_neigh or '[]'}")
                    w("")
        except Exception as e:
            w(f"**ERROR opening {path.name}: {e}**\n")

    out[summary_idx] = (
        "**Answer-number summary:** "
        f"{tally['found on gold page']} found on gold page / "
        f"{tally['found only on neighbour']} neighbour-only / "
        f"{tally['not found']} not found / "
        f"{tally['skipped']} skipped (weak)\n")

    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
