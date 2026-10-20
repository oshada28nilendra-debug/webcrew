"""Self-contained authored-site demo. Fixture server and browser share one process namespace."""

import argparse
import json
from pathlib import Path

from tests.fixture import Site
from webcrew.core import Task
from webcrew.provider import Model
from webcrew.report import export
from webcrew.runner import run
from webcrew.state import Store


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--endpoint")
    p.add_argument("--model")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    with Site() as site:
        task = Task.parse(site.task(), demo=True)
        (args.out / "task.json").write_text(json.dumps(task.raw, indent=2) + "\n")
        model = Model(args.endpoint, args.model) if args.endpoint else None
        checkpoint = args.out / "run.db"
        state = run(task, checkpoint, model=model, pause_after=2)
        if state["status"] != "paused":
            raise RuntimeError("Expected explicit pause; inspect checkpoint")
        state = run(task, checkpoint, model=model)
        with Store(checkpoint, task) as store:
            export(state, store.events(), args.out / "report")
        result = {
            "status": state["status"],
            "mode": state["mode"],
            "steps": state["steps"],
            "calls": state["calls"],
            "usage": state["model_usage"],
            "requests": site.requests,
            "pause_resume": True,
            "fixture": "Authored fictional workshop; not a real website task benchmark",
            "browser_version": state["current"]["browser_version"],
        }
        (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        if state["status"] != "verified" or any(
            path in {"/write", "/track"} or method != "GET" for method, path in site.requests
        ):
            raise RuntimeError("Demo did not meet outcome/network gates")


if __name__ == "__main__":
    main()
