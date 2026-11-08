#!/usr/bin/env python
"""Convert dev_questions.jsonl into eval/questions.jsonl.

Target schema (one JSON object per line):
  {"id", "role", "question", "answer",
   "type": "answerable|unanswerable|off_desk",
   "gold": [{"doc_id", "pages": [...]}],     # list: lead / year-ambiguous questions can have several
   "tags": [...]}

Usage: python eval/convert_dev.py [--src dev_questions.jsonl] [--out eval/questions.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path


def convert(q):
    pages = sorted(set(q["pages"]))
    tags = ["multi_page"] if len(pages) > 1 else []
    return {
        "id": q["id"],
        "role": q["role"],
        "question": q["question"],
        "answer": q["answer"],
        "type": "answerable",
        "gold": [{"doc_id": q["doc_id"], "pages": pages}],
        "tags": tags,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="dev_questions.jsonl")
    ap.add_argument("--out", default=str(Path("eval") / "questions.jsonl"))
    a = ap.parse_args()
    with open(a.src, encoding="utf-8") as f:
        rows = [convert(json.loads(l)) for l in f if l.strip()]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_multi = sum("multi_page" in r["tags"] for r in rows)
    print(f"wrote {len(rows)} questions ({n_multi} multi_page) to {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
