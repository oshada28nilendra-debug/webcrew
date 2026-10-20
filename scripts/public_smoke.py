"""Actual opt-in public HTTPS browser check; a failed result is never a fixture pass."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from webcrew.browser import resolve, _NavigationPolicy
from webcrew.core import Error, Task
from webcrew.httpio import DeadlineHTTP, read_exchange
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
    # Public-only diagnostic, using exactly the same DNS-pinned bounded transport.
    # No private URLs, credentials, response headers or bodies are logged.
    diagnostic = {"url": task.start_url}
    try:
        addresses = resolve(task)
        url = urlsplit(task.start_url)
        conn = DeadlineHTTP(url.hostname, 443, 15, tls=True, ip=addresses[url.hostname])
        status, headers, body = read_exchange(
            conn,
            "GET",
            url.path or "/",
            {"User-Agent": "WebCrew/0.1 read-only audit", "Accept": "text/html"},
            timeout=15,
            max_bytes=1_000_000,
        )
        diagnostic.update(
            status=status,
            mime=headers.get("content-type"),
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
        )
        parser = _NavigationPolicy()
        parser.feed(body.decode("utf-8"))
        parser.close()
        diagnostic["html_navigation_policy"] = "passed"
    except (Error, UnicodeError) as exc:
        diagnostic["error"] = str(exc)
    (args.out / "transport-diagnostic.json").write_text(json.dumps(diagnostic, indent=2) + "\n")
    print(json.dumps(diagnostic), flush=True)
    state = run(task, args.out / "run.db")
    with Store(args.out / "run.db", task) as store:
        export(state, store.events(), args.out / "report")
    print(state["status"], state.get("reason", ""))
    return 0 if state["status"] == "verified" else 3


if __name__ == "__main__":
    raise SystemExit(main())
