"""ask --role <role> "<question>": exactly one JSON object on stdout; logs on stderr."""
import argparse
import json
import sys

from . import acl


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=True) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ask")
    ap.add_argument("--role", required=True)
    ap.add_argument("question")
    a = ap.parse_args(argv)
    try:
        from .answer import answer

        emit(answer(a.question, a.role))
        return 0
    except acl.UnknownRole as e:
        print(f"ask: {e}", file=sys.stderr)
        emit({"status": "refused", "answer": f"Unknown role {a.role!r}", "citations": []})
        return 2
    except Exception as e:  # never exit without a JSON object
        print(f"ask: unexpected error: {e!r}", file=sys.stderr)
        emit({"status": "refused", "answer": "Internal error", "citations": []})
        return 1


if __name__ == "__main__":
    sys.exit(main())
