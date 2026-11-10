#!/usr/bin/env python
"""Cold CLI latency: run `search` or `ask` N times, each in a fresh process, and report wall time.

  python scripts/cold_latency.py ask    --n 5 [--set KEY=VALUE ...] [--gap 40]
  python scripts/cold_latency.py search --n 5 [--set KEY=VALUE ...]

--set patches drg.config inside the child process before the CLI's main() runs (same code path as the console
script; used to time a candidate config before it becomes the default). `ask` calls the live LLM, so runs are
spaced --gap seconds apart (Groq 8k tokens/minute); the gap is NOT part of the measured time. For ask the
report also splits the time: everything before the LLM call ("pre-LLM") and the LLM call itself (taken from the
`ask latency:` stderr line). Nothing else should be running while you measure.
"""
import argparse
import ast
import json
import platform
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
QUESTION = {"ask": "Compare R&D spending at AMD and Pfizer in 2022.",
            "search": "What was Adobe's operating profit for fiscal 2022?"}
ROLE = {"ask": "lead", "search": "tech_telecom"}


FAKE = ("from drg import llm\n"
        "llm.chat = lambda system, user, timeout=None: "
        "'{\"status\": \"answered\", \"answer\": \"stub [C1]\"}'\n")


def child_code(cmd, sets, fake_llm=False):
    patch = "\n".join(f"config.{k} = {v!r}" for k, v in sets.items())
    if fake_llm:
        patch += "\n" + FAKE
    argv = (["--role", ROLE[cmd], QUESTION[cmd]] if cmd == "ask"
            else ["--role", ROLE[cmd], "--k", "5", QUESTION[cmd]])
    return (f"import sys\nsys.path.insert(0, {str(ROOT)!r})\nfrom drg import config\n{patch}\n"
            f"from drg.{cmd} import main\nsys.exit(main({argv!r}))\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ask", "search"])
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--fake-llm", action="store_true",
                    help="ask: replace the network LLM call by an instant stub (no tokens spent); the time "
                         "measured is then everything except the LLM request")
    ap.add_argument("--gap", type=float, default=40.0, help="seconds between ask runs (rate limit)")
    a = ap.parse_args()
    sets = {}
    for item in a.sets:
        k, _, v = item.partition("=")
        try:
            sets[k] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            sets[k] = v
    code = child_code(a.cmd, sets, a.fake_llm)
    rows = []
    for i in range(a.n):
        if i and a.cmd == "ask" and not a.fake_llm:
            time.sleep(a.gap)
        t0 = time.perf_counter()
        r = subprocess.run([str(PY), "-c", code], cwd=ROOT, capture_output=True, text=True)
        wall = time.perf_counter() - t0
        m = re.search(r"ask latency: parse=([\d.]+)s retrieve=([\d.]+)s llm=([\d.]+)s total=([\d.]+)s", r.stderr)
        llm = float(m.group(3)) if m else 0.0
        waited = sum(float(x) for x in re.findall(r"waiting ([\d.]+)s", r.stderr))
        out = r.stdout.strip().splitlines()
        ok = r.returncode == 0 and len(out) == 1 and bool(json.loads(out[0]))
        rows.append({"wall_s": round(wall, 2), "llm_s": round(llm, 2), "pre_llm_s": round(wall - llm, 2),
                     "rate_limit_wait_s": waited, "ok": ok})
        print(f"run {i + 1}/{a.n}: wall {wall:.2f}s (llm {llm:.2f}s, pre-LLM {wall - llm:.2f}s) ok={ok}",
              file=sys.stderr)

    def stat(key):
        xs = sorted(r[key] for r in rows)
        return {"median": round(statistics.median(xs), 2), "min": xs[0], "max": xs[-1]}

    rep = {"cmd": a.cmd, "n": a.n, "config_patch": sets, "wall_s": stat("wall_s"), "pre_llm_s": stat("pre_llm_s"),
           "runs": rows, "hardware": f"{platform.processor()}; {platform.platform()}"}
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
