"""Actual opt-in public HTTPS browser check; a failed result is never a fixture pass."""

import argparse
from pathlib import Path

from webcrew.core import Task
from webcrew.report import export
from webcrew.runner import run
from webcrew.state import Store


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    task = Task.parse(
        {
            "objective": "Find a public description of Python as a programming language",
            "start_url": "https://www.python.org/",
            "allowed_urls": ["https://www.python.org/"],
            "criteria": [
                {
                    "id": "language",
                    "description": "Python language description",
                    "contains": "programming language",
                }
            ],
        }
    )
    state = run(task, args.out / "run.db")
    with Store(args.out / "run.db", task) as store:
        export(state, store.events(), args.out / "report")
    print(state["status"], state.get("reason", ""))
    return 0 if state["status"] == "verified" else 3


if __name__ == "__main__":
    raise SystemExit(main())
