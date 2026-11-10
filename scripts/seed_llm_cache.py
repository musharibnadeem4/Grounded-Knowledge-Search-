#!/usr/bin/env python
"""Seed the LLM response cache (cache/llm) from the raw responses an earlier --answers run logged on stderr.

  python scripts/seed_llm_cache.py logs/p4_baseline_tune_answers.log [--set KEY=VALUE ...] [--split tune]

Why: Groq's free tier allows 200k tokens/day, about one full answer run. Responses that were already paid for are
recovered from the log ("LLM raw response (first 2000 chars): ..."), the prompt of every question is rebuilt by
running the same retrieval + context assembly with the run's config (--set must repeat the run's overrides), and
(prompt -> raw response) is stored in the cache. Makes NO API call. Responses longer than 2000 characters were
truncated in the log and are skipped. The cache key includes provider and model, so entries only match the model
that produced them.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drg import answer as A  # noqa: E402
from drg import config, llm  # noqa: E402

MARK = re.compile(r"^\[(\d+)/(\d+)\] (\S+) ", re.M)
RAW = re.compile(r"LLM raw response \(first 2000 chars\): (.*?)\nask latency:", re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--split", default="tune")
    ap.add_argument("--questions", default=str(ROOT / "eval" / "questions_v2.jsonl"))
    ap.add_argument("--cache-dir", default=str(ROOT / "cache" / "llm"))
    a = ap.parse_args()

    cfg = SimpleNamespace(**{k: getattr(config, k) for k in dir(config) if k.isupper()})
    cfg.INDEX_DIR, cfg.MANIFEST_PATH = ROOT / "index", ROOT / "manifest.csv"
    for item in a.sets:
        k, _, v = item.partition("=")
        setattr(cfg, k, ast.literal_eval(v))
    qs = [json.loads(l) for l in open(a.questions, encoding="utf-8") if l.strip()]
    qs = [q for q in qs if a.split == "all" or q.get("split", "tune") == a.split]

    data = Path(a.log).read_bytes()
    try:  # logs redirected from a Windows console are in the ANSI code page (cp1252), not UTF-8
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252", errors="replace")
    marks = list(MARK.finditer(text))
    llm.enable_cache(a.cache_dir)
    seeded = skipped = 0
    start = 0
    for m in marks:
        i, qid = int(m.group(1)), m.group(3)
        seg = text[start:m.start()]
        start = m.start()
        q = qs[i - 1]
        assert q["id"] == qid, f"log question {qid} != questions file {q['id']} at position {i}"
        raws = RAW.findall(seg)
        if not raws:
            continue  # refused before the LLM (off-desk / out of range) or the call failed
        cap = raws[-1]
        raw = None
        for cand in (cap.split("\n", 1)[0], cap.split("\nWARN", 1)[0], cap):
            try:
                json.loads(cand)
                raw = cand
                break
            except ValueError:
                continue
        if raw is None:
            skipped += 1
            print(f"skip {qid}: logged response is truncated / not JSON", file=sys.stderr)
            continue

        def fake(system, user, timeout=None, _raw=raw):
            llm.cache_put(system, user, _raw)
            return _raw
        real, llm.chat = llm.chat, fake
        try:
            A.answer(q["question"], q["role"], cfg)
        finally:
            llm.chat = real
        seeded += 1
    print(f"seeded {seeded} responses ({skipped} skipped) into {a.cache_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
