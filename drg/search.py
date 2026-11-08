"""search --role <role> --k <n> "<question>": JSON list on stdout, best first."""
import argparse
import json
import sys

from . import acl, config
from .retrieve import retrieve


def main(argv=None):
    ap = argparse.ArgumentParser(prog="search")
    ap.add_argument("--role", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("question")
    a = ap.parse_args(argv)
    if a.k < 1:
        print("search: --k must be >= 1", file=sys.stderr)
        return 2
    try:
        hits = retrieve(a.question, a.role, a.k, config)
    except acl.UnknownRole as e:
        print(f"search: {e}", file=sys.stderr)
        return 2
    out = [{"doc_id": h.doc_id, "page": h.page, "chunk_id": h.chunk_id,
            "score": h.score, "text": h.text} for h in hits]
    sys.stdout.write(json.dumps(out, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
