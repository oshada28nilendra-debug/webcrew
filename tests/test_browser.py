import tempfile
import unittest
from pathlib import Path

from webcrew.browser import Browser
from webcrew.core import Error, Task
from webcrew.runner import run
from webcrew.state import Store
from tests.fixture import Site


class ScriptedPlanner:
    """Deterministic test double, never a live model result."""

    calls = 0
    usage = {"prompt_tokens": 0, "completion_tokens": 0}
    last = None

    def ask(self, role, context):
        if role == "verifier":
            return {"accepted": True, "reason": "fixture"}
        from webcrew.runner import baseline_action

        return baseline_action(context)


class BrowserTests(unittest.TestCase):
    def test_meta_refresh_cannot_misattribute_evidence(self):
        with Site() as site:
            data = site.task()
            data["allowed_urls"].append(site.base + "/refresh")
            task = Task.parse(data, demo=True)
            with Browser(task) as browser:
                with self.assertRaises(Error):
                    browser.read(site.base + "/refresh")
            self.assertNotIn(("GET", "/refund"), site.requests)

    def test_real_chromium_read_and_link_filter(self):
        with Site() as site:
            task = Task.parse(site.task(), demo=True)
            with Browser(task) as browser:
                snap = browser.read(task.start_url)
                self.assertEqual(len(snap["links"]), 2)
                self.assertEqual(snap["links"][0]["url"], site.base + "/access")
                with self.assertRaises(Error):
                    browser.read(site.base + "/write")
            self.assertNotIn(("GET", "/write"), site.requests)
            self.assertNotIn(("GET", "/track"), site.requests)
            self.assertFalse(any(method == "POST" for method, _ in site.requests))

    def test_baseline_end_to_end_and_resume(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            p = Path(d) / "run.db"
            first = run(task, p, pause_after=2)
            self.assertEqual(first["status"], "paused")
            result = run(task, p)
            self.assertEqual(result["status"], "verified")
            self.assertEqual({e["criterion"] for e in result["evidence"]}, {"access", "refund"})
            self.assertGreater(result["steps"], first["steps"])
            self.assertEqual(run(task, p)["steps"], result["steps"])
            self.assertGreaterEqual(site.requests.count(("GET", "/access")), 2)

    def test_simulated_planner_independent_verifier_veto(self):
        class Veto(ScriptedPlanner):
            def ask(self, role, context):
                if role == "verifier":
                    return {"accepted": False, "reason": "does not satisfy goal"}
                return super().ask(role, context)

        with Site() as site, tempfile.TemporaryDirectory() as d:
            result = run(Task.parse(site.task(), demo=True), Path(d) / "run.db", model=Veto())
            self.assertEqual(result["status"], "incomplete")

    def test_changed_source_fails_fresh_verification(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            p = Path(d) / "run.db"
            run(task, p, pause_after=4)
            site.changed = True
            result = run(task, p)
            self.assertEqual(result["status"], "incomplete")
            self.assertFalse(result["verification"]["passed"])

    def test_write_request_pauses_without_effect(self):
        class Writer(ScriptedPlanner):
            def ask(self, *_):
                return {"action": "submit", "description": "Buy a ticket"}

        with Site() as site, tempfile.TemporaryDirectory() as d:
            result = run(Task.parse(site.task(), demo=True), Path(d) / "run.db", model=Writer())
            self.assertEqual(result["status"], "needs_approval")
            self.assertIn("digest", result["approval_request"])
            self.assertEqual(site.requests, [("GET", "/")])

    def test_unknown_action_is_recorded_failure(self):
        class Invalid(ScriptedPlanner):
            def ask(self, *_):
                return {"action": "visit", "link": "l999"}

        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            p = Path(d) / "run.db"
            result = run(task, p, model=Invalid())
            self.assertEqual(result["status"], "failed")
            with Store(p, task) as store:
                self.assertEqual(store.load()["status"], "failed")

    def test_budget_exhaustion_persists(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            data = site.task()
            data["max_steps"] = 1
            task = Task.parse(data, demo=True)
            result = run(task, Path(d) / "run.db")
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["steps"], 1)

    def test_redirect_to_unlisted_page_blocked(self):
        with Site() as site:
            data = site.task()
            data["allowed_urls"].append(site.base + "/redirect")
            task = Task.parse(data, demo=True)
            with Browser(task) as browser:
                with self.assertRaises(Error):
                    browser.read(site.base + "/redirect")
            self.assertNotIn(("GET", "/write"), site.requests)
