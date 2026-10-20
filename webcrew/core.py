"""Task and finite evidence policy; no browser/model side effects."""

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


class Error(Exception):
    """Safe user-facing failure; never include provider bodies or secrets."""


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def text(value, name, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise Error(f"Invalid {name}")
    try:
        value.encode("utf-8")
    except UnicodeError:
        raise Error(f"Invalid {name}") from None
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise Error(f"Invalid {name}")
    return value


def valid_url(value, demo=False):
    text(value, "URL", 2000)
    try:
        u = urlsplit(value)
        port = u.port
        demo_host = demo and u.hostname == "127.0.0.1"
        if u.scheme != "https" and not (demo_host and u.scheme == "http"):
            raise Error("URLs require HTTPS (loopback HTTP needs --demo)")
        if not u.hostname or u.username or u.password or u.query or u.fragment:
            raise Error("URLs cannot contain credentials, queries or fragments")
        if "%" in value or "\\" in value or any(c.isspace() for c in value):
            raise Error("Encoded or ambiguous URLs are unsupported")
        if u.path != "/" and (
            not u.path.startswith("/")
            or "//" in u.path
            or any(p in {".", ".."} for p in u.path.split("/"))
        ):
            raise Error("Use canonical absolute page URLs")
        if (
            u.hostname != u.hostname.lower()
            or value != u.geturl()
            or (port is not None and not demo_host and port != 443)
        ):
            raise Error("Use canonical URLs and standard HTTPS ports")
        try:
            address = ipaddress.ip_address(u.hostname)
        except ValueError:
            if len(u.hostname) > 253 or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in u.hostname.split(".")
            ):
                raise Error("Invalid DNS hostname")
            if (
                u.hostname == "localhost"
                or "." not in u.hostname
                or u.hostname.endswith((".local", ".internal"))
            ):
                raise Error("Private hosts are unsupported")
        else:
            if not address.is_global and not demo_host:
                raise Error("Private addresses are unsupported")
    except ValueError:
        raise Error("Invalid URL") from None
    return value


@dataclass(frozen=True)
class Task:
    raw: dict
    objective: str
    start_url: str
    allowed_urls: tuple
    criteria: tuple
    max_steps: int
    max_calls: int
    demo: bool

    @classmethod
    def parse(cls, d, demo=False):
        if not isinstance(d, dict) or set(d) - {
            "objective",
            "start_url",
            "allowed_urls",
            "criteria",
            "max_steps",
            "max_calls",
        }:
            raise Error("Invalid task fields")
        objective = text(d.get("objective"), "objective", 1500)
        urls = d.get("allowed_urls")
        if (
            not isinstance(urls, list)
            or not 1 <= len(urls) <= 12
            or any(not isinstance(v, str) for v in urls)
            or len(set(urls)) != len(urls)
        ):
            raise Error("Provide 1–12 distinct allowed URLs")
        urls = tuple(valid_url(v, demo) for v in urls)
        start = d.get("start_url")
        if start not in urls:
            raise Error("Start URL must be allowlisted")
        criteria = d.get("criteria")
        if not isinstance(criteria, list) or not 1 <= len(criteria) <= 8:
            raise Error("Provide 1–8 criteria")
        ids = set()
        for c in criteria:
            if not isinstance(c, dict) or set(c) != {"id", "description", "contains"}:
                raise Error("Each criterion needs id, description and contains")
            ident = text(c["id"], "criterion ID", 32)
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", ident) or ident in ids:
                raise Error("Invalid or duplicate criterion ID")
            ids.add(ident)
            text(c["description"], "criterion description", 300)
            text(c["contains"], "acceptance phrase", 200)
        budgets = []
        for name, default, maximum in [("max_steps", 24, 24), ("max_calls", 32, 32)]:
            v = d.get(name, default)
            if type(v) is not int or not 1 <= v <= maximum:
                raise Error(f"Invalid {name}")
            budgets.append(v)
        raw = {
            "objective": objective,
            "start_url": start,
            "allowed_urls": list(urls),
            "criteria": criteria,
            "max_steps": budgets[0],
            "max_calls": budgets[1],
        }
        return cls(raw, objective, start, urls, tuple(criteria), *budgets, demo)

    @property
    def fingerprint(self):
        return digest({"task": self.raw, "demo": self.demo, "schema": 1})


def collect(task, snapshot, selections):
    if not isinstance(selections, list) or not 1 <= len(selections) <= 8:
        raise Error("Collect needs 1–8 selections")
    passages = {p["id"]: p["text"] for p in snapshot["passages"]}
    criteria = {c["id"]: c for c in task.criteria}
    result = []
    for choice in selections:
        if not isinstance(choice, dict) or set(choice) != {"criterion", "passage"}:
            raise Error("Invalid evidence selection")
        criterion, passage = choice["criterion"], choice["passage"]
        if (
            not isinstance(criterion, str)
            or not isinstance(passage, str)
            or criterion not in criteria
            or passage not in passages
        ):
            raise Error("Unknown criterion or passage ID")
        quote = passages[passage]
        if criteria[criterion]["contains"].casefold() not in quote.casefold():
            raise Error("Selected passage fails the literal acceptance check")
        result.append(
            {
                "criterion": criterion,
                "text": quote,
                "url": snapshot["url"],
                "source_sha256": snapshot["sha256"],
                "text_sha256": digest(quote),
                "passage": passage,
            }
        )
    return result


def verify_evidence(task, evidence, fresh):
    checks = []
    for c in task.criteria:
        candidates = [
            e
            for e in evidence
            if e["criterion"] == c["id"]
            and e["url"] in task.allowed_urls
            and c["contains"].casefold() in e["text"].casefold()
        ]
        valid = [
            e
            for e in candidates
            if any(p["text"] == e["text"] for p in fresh.get(e["url"], {}).get("passages", []))
        ]
        checks.append(
            {
                "criterion": c["id"],
                "passed": bool(valid),
                "evidence": valid,
                "reason": "Exact passage observed again"
                if valid
                else "Missing, changed or unmatched evidence",
            }
        )
    return {"passed": all(c["passed"] for c in checks), "checks": checks}
