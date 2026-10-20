"""Local trusted checkpoint journal. SQLite transaction commits state and event together."""

import fcntl
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .core import Error, digest
from .files import loads


class Store:
    def __init__(self, path, task):
        self.path, self.task = Path(path), task
        self.lock = self.conn = None

    def __enter__(self):
        try:
            if self.path.is_symlink() or self.path.with_suffix(".lock").is_symlink():
                raise Error("Checkpoint and lock must not be symlinks")
            if self.path.exists() and (
                not self.path.is_file() or self.path.stat().st_size > 10_000_000
            ):
                raise Error("Invalid or oversized checkpoint")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(
                self.path.with_suffix(".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
            )
            self.lock = os.fdopen(fd, "w")
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.conn = sqlite3.connect(self.path, timeout=1)
            os.chmod(self.path, 0o600)
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), task TEXT, payload TEXT, checksum TEXT)"
            )
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, payload TEXT)"
            )
            row = self.conn.execute("SELECT task,payload,checksum FROM state WHERE id=1").fetchone()
            if row:
                if row[0] != self.task.fingerprint:
                    raise Error(
                        "Checkpoint belongs to another task or policy; use a new checkpoint"
                    )
                state = loads(row[1])
                if digest(state) != row[2]:
                    raise Error("Checkpoint integrity mismatch")
                self._validate(state)
            else:
                state = {
                    "schema": 1,
                    "status": "running",
                    "steps": 0,
                    "calls": 0,
                    "visited": [],
                    "current": None,
                    "evidence": [],
                    "verification": None,
                    "pending": None,
                    "model_usage": {"prompt_tokens": 0, "completion_tokens": 0},
                }
                self._put(state)
                self.conn.commit()
            return self
        except (OSError, sqlite3.Error, Error, ValueError, TypeError):
            self.__exit__(None, None, None)
            raise Error(
                "Cannot open checkpoint: locked, corrupt, unsafe or task policy changed"
            ) from None

    def _validate(self, s):
        if (
            not isinstance(s, dict)
            or s.get("schema") != 1
            or type(s.get("steps")) is not int
            or type(s.get("calls")) is not int
        ):
            raise Error("Invalid checkpoint schema")
        if not 0 <= s["steps"] <= self.task.max_steps or not 0 <= s["calls"] <= self.task.max_calls:
            raise Error("Invalid checkpoint budgets")
        if s.get("status") not in {
            "running",
            "paused",
            "verifying",
            "verified",
            "incomplete",
            "failed",
            "needs_approval",
        }:
            raise Error("Invalid checkpoint status")
        if (
            not isinstance(s.get("visited"), list)
            or any(u not in self.task.allowed_urls for u in s["visited"])
            or not isinstance(s.get("evidence"), list)
            or len(s["evidence"]) > 64
        ):
            raise Error("Invalid checkpoint contents")
        ids = {c["id"] for c in self.task.criteria}
        for e in s["evidence"]:
            if (
                not isinstance(e, dict)
                or set(e) != {"criterion", "text", "url", "source_sha256", "text_sha256", "passage"}
                or any(not isinstance(v, str) for v in e.values())
            ):
                raise Error("Invalid checkpoint evidence")
            if (
                e["criterion"] not in ids
                or e["url"] not in self.task.allowed_urls
                or digest(e["text"]) != e["text_sha256"]
            ):
                raise Error("Invalid checkpoint evidence binding")
        for link in s.get("frontier", []):
            if (
                not isinstance(link, dict)
                or link.get("url") not in self.task.allowed_urls
                or not isinstance(link.get("id"), str)
            ):
                raise Error("Invalid checkpoint navigation frontier")
        current = s.get("current")
        if current is not None and (
            not isinstance(current, dict) or current.get("url") not in self.task.allowed_urls
        ):
            raise Error("Invalid checkpoint current page")

    def _put(self, state):
        self._validate(state)
        self.conn.execute(
            "INSERT OR REPLACE INTO state VALUES (1,?,?,?)",
            (self.task.fingerprint, json.dumps(state, ensure_ascii=True), digest(state)),
        )

    def save(self, state, event):
        event = dict(event, timestamp=datetime.now(timezone.utc).isoformat())
        with self.conn:
            self._put(state)
            self.conn.execute(
                "INSERT INTO events(payload) VALUES (?)", (json.dumps(event, ensure_ascii=True),)
            )

    def load(self):
        return loads(self.conn.execute("SELECT payload FROM state WHERE id=1").fetchone()[0])

    def events(self):
        return [
            loads(row[0]) for row in self.conn.execute("SELECT payload FROM events ORDER BY id")
        ]

    def __exit__(self, *_):
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.lock:
            self.lock.close()
            self.lock = None
