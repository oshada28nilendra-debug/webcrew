import argparse
import json
import sys
from pathlib import Path

from .core import Error, Task
from .files import read_json
from .provider import Model
from .report import export
from .runner import run
from .state import Store


def main():
    parser = argparse.ArgumentParser(
        description="Bounded browser checklist investigations; no external write tools"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("task", type=Path)
    p.add_argument("--checkpoint", required=True, type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--pause-after", type=int)
    p.add_argument(
        "--demo", action="store_true", help="Permit literal 127.0.0.1 HTTP fixture pages"
    )
    p.add_argument(
        "--endpoint",
        help="Full compatible /v1/chat/completions endpoint; omitted uses deterministic baseline",
    )
    p.add_argument("--model")
    p.add_argument(
        "--allow-remote-model",
        action="store_true",
        help="Consent to sending task/page text to remote HTTPS provider; provider billing may apply",
    )
    args = parser.parse_args()
    try:
        if bool(args.endpoint) != bool(args.model):
            raise Error("Provide both --endpoint and --model")
        task = Task.parse(read_json(args.task), demo=args.demo)
        model = (
            Model(args.endpoint, args.model, remote_consent=args.allow_remote_model)
            if args.endpoint
            else None
        )
        state = run(task, args.checkpoint, model=model, pause_after=args.pause_after)
        if args.output:
            with Store(args.checkpoint, task) as store:
                export(state, store.events(), args.output)
        print(
            json.dumps(
                {
                    "status": state["status"],
                    "steps": state["steps"],
                    "calls": state["calls"],
                    "evidence_count": len(state["evidence"]),
                    "reason": state.get("reason"),
                    "checkpoint": str(args.checkpoint),
                },
                ensure_ascii=True,
            )
        )
        return 0 if state["status"] == "verified" else 3
    except (Error, OSError) as exc:
        print("WebCrew: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
