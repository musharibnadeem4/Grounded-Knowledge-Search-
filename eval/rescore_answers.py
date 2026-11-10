#!/usr/bin/env python
"""Re-score the stored answers of an --answers run with the CURRENT scorer / question file (no LLM calls).

  python eval/rescore_answers.py <run-name> [--questions eval/questions_v2.jsonl]

Reads eval/results/<run>.json and writes NEW files eval/results/<run>_rescored.json / .md (the original is never
touched, nothing is appended to summary.csv). Use it when the scorer or a question's numeric spec was corrected
after a run, so older runs stay comparable.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import answer_metrics  # noqa: E402
import run_eval  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_name")
    ap.add_argument("--questions", default=str(ROOT / "eval" / "questions_v2.jsonl"))
    ap.add_argument("--suffix", default="_rescored",
                    help="output name = <run><suffix> (use a new suffix when <run>_rescored already exists)")
    a = ap.parse_args()
    src = RESULTS / f"{a.run_name}.json"
    dst = RESULTS / f"{a.run_name}{a.suffix}.json"
    if dst.exists():
        sys.exit(f"{dst} already exists; results are never overwritten")
    res = json.loads(src.read_text(encoding="utf-8"))
    qs = {q["id"]: q for q in run_eval.load_questions(a.questions)}
    from collections import defaultdict
    for row in res["rows"]:
        old = row.get("answer_metrics")
        if not old:
            continue
        q = qs[row["id"]]
        row["has_numeric"] = bool(q.get("numeric"))
        new = answer_metrics.score_answer(q, row["answer"], old["seconds"], old["llm_called"],
                                          old["ungrounded_warnings"], old.get("waited_s", 0.0))
        new["context_chunks"] = old.get("context_chunks", 0)
        row["answer_metrics"] = new
    by_type, by_tag = defaultdict(list), defaultdict(list)
    for r in res["rows"]:
        by_type[r["type"]].append(r)
        for t in r["tags"]:
            by_tag[t].append(r)
    by_split = defaultdict(list)
    for r in res["rows"]:
        by_split[r.get("split", "tune")].append(r)
    res["answers"] = {**res["answers"],   # keeps llm, sleep_s, max_llm_calls, live_calls, llm_cache
                      "overall": answer_metrics.summarize(res["rows"]),
                      "by_split": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_split.items())},
                      "by_type": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_type.items())},
                      "by_tag": {t: answer_metrics.summarize(rs) for t, rs in sorted(by_tag.items())}}
    res["run_name"] = a.run_name + a.suffix
    res["rescored_from"] = a.run_name
    dst.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    (RESULTS / f"{a.run_name}{a.suffix}.md").write_text(run_eval.render_md(res, res["config"]["args"]["k"]),
                                                       encoding="utf-8")
    ov = res["answers"]["overall"]
    print(f"wrote {dst}: " + " ".join(f"{o}={ov[o + '_rate']:.3f}({ov['n_' + o]})" for o in answer_metrics.OUTCOMES)
          + f" of n={ov['n_numeric']} numeric-gold questions")


if __name__ == "__main__":
    main()
