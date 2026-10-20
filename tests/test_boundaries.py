import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webcrew.browser import resolve
from webcrew.core import Error, Task
from webcrew.runner import _context, run
from webcrew.state import Store
from tests.fixture import Site
from tests.test_browser import ScriptedPlanner
from tests.test_core import task_data


class BoundaryTests(unittest.TestCase):
    def test_dns_private_result_rejected(self):
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.1", 443))]):
            with self.assertRaises(Error):
                resolve(Task.parse(task_data()))

    def test_finite_choices_do_not_offer_premature_completion(self):
        task = Task.parse(task_data())
        state = {
            "evidence": [],
            "current": {"passages": [{"id": "p0", "text": "Directory"}]},
            "frontier": [{"id": "l0", "url": "https://example.org/policy"}],
            "visited": [task.start_url],
            "steps": 0,
        }
        choices = _context(task, state)["action_options"]
        self.assertEqual(choices, [{"id": "a0", "action": {"action": "visit", "link": "l0"}}])

    def test_model_choice_dispatch_and_unknown_choice(self):
        class ChoicePlanner(ScriptedPlanner):
            def ask(self, role, context):
                if role == "verifier":
                    return {"accepted": True, "reason": "fixture reviewer"}
                baseline = super().ask(role, context)
                for option in context["action_options"]:
                    if option["action"] == baseline:
                        return {"choice": option["id"]}
                raise AssertionError("baseline choice must be available")

        class InvalidChoice(ScriptedPlanner):
            def ask(self, *_):
                return {"choice": "a999"}

        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            self.assertEqual(
                run(task, Path(d) / "good.db", model=ChoicePlanner())["status"], "verified"
            )
            bad = run(task, Path(d) / "bad.db", model=InvalidChoice())
            self.assertEqual(bad["status"], "failed")
            self.assertEqual(bad["calls"], 1)

    def test_call_budget_survives_resume(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            data = site.task()
            data["max_calls"] = 2
            task = Task.parse(data, demo=True)
            p = Path(d) / "run.db"
            first = run(task, p, model=ScriptedPlanner(), pause_after=1)
            self.assertEqual(first["calls"], 1)
            last = run(task, p, model=ScriptedPlanner())
            self.assertEqual(last["calls"], 2)
            self.assertEqual(last["status"], "failed")
            self.assertIn("budget", last["reason"])

    def test_resume_rejects_changed_mode(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            p = Path(d) / "run.db"
            run(task, p, pause_after=1)
            with self.assertRaises(Error):
                run(task, p, model=ScriptedPlanner())

    def test_no_evidence_cannot_claim_success(self):
        class Premature(ScriptedPlanner):
            def ask(self, *_):
                return {"action": "finish"}

        with Site() as site, tempfile.TemporaryDirectory() as d:
            result = run(Task.parse(site.task(), demo=True), Path(d) / "x.db", model=Premature())
            self.assertEqual(result["status"], "incomplete")
            self.assertFalse(result["verification"]["passed"])

    def test_interrupted_read_intent_resumes_with_budget_reserved(self):
        with Site() as site, tempfile.TemporaryDirectory() as d:
            task = Task.parse(site.task(), demo=True)
            p = Path(d) / "x.db"
            with Store(p, task) as store:
                state = store.load()
                state["steps"] = 1
                state["pending"] = {"action": "visit", "link": "l0"}
                store.save(state, {"type": "action_started"})
            result = run(task, p)
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["steps"], 6)
