import unittest

from webcrew.core import Error, Task, collect, verify_evidence


def task_data(base="https://example.org"):
    return {
        "objective": "Find workshop policies",
        "start_url": base + "/",
        "allowed_urls": [base + "/", base + "/policy"],
        "criteria": [
            {"id": "access", "description": "Accessible venue", "contains": "Step-free access"}
        ],
        "max_steps": 12,
        "max_calls": 16,
    }


class CoreTests(unittest.TestCase):
    def test_invalid_dns_labels_rejected(self):
        with self.assertRaises(Error):
            Task.parse(task_data("https://" + "a" * 64 + ".org"))

    def test_malformed_url_container_and_string_do_not_crash(self):
        for urls in [[{}], [1], [None], ["https://example.org/\ud800"]]:
            d = task_data()
            d["allowed_urls"] = urls
            with self.subTest(urls=repr(urls)), self.assertRaises(Error):
                Task.parse(d)

    def test_valid_task(self):
        self.assertEqual(Task.parse(task_data()).start_url, "https://example.org/")

    def test_unlisted_start_rejected(self):
        d = task_data()
        d["start_url"] += "admin"
        with self.assertRaises(Error):
            Task.parse(d)

    def test_ambiguous_urls_rejected(self):
        for url in [
            "http://example.org/",
            "https://user:pw@example.org/",
            "https://example.org/?token=x",
            "https://example.org/%2e%2e/admin",
            "https://example.org/a#b",
        ]:
            d = task_data()
            d["allowed_urls"] = [url]
            d["start_url"] = url
            with self.subTest(url=url), self.assertRaises(Error):
                Task.parse(d)

    def test_private_network_rejected_except_explicit_demo(self):
        with self.assertRaises(Error):
            Task.parse(task_data("http://127.0.0.1:8000"))
        self.assertTrue(Task.parse(task_data("http://127.0.0.1:8000"), demo=True))

    def test_budget_bounds(self):
        for v in [0, 25, True, "3"]:
            d = task_data()
            d["max_steps"] = v
            with self.subTest(v=v), self.assertRaises(Error):
                Task.parse(d)

    def test_duplicate_criteria_rejected(self):
        d = task_data()
        d["criteria"] *= 2
        with self.assertRaises(Error):
            Task.parse(d)

    def test_exact_passage_resolved_by_id(self):
        snap = {
            "url": "https://example.org/policy",
            "passages": [{"id": "p0", "text": "Step-free access is available."}],
            "sha256": "a" * 64,
        }
        result = collect(Task.parse(task_data()), snap, [{"criterion": "access", "passage": "p0"}])
        self.assertEqual(result[0]["text"], "Step-free access is available.")
        self.assertEqual(result[0]["source_sha256"], "a" * 64)

    def test_invented_or_irrelevant_selection_rejected(self):
        snap = {
            "url": "https://example.org/policy",
            "passages": [{"id": "p0", "text": "No parking."}],
            "sha256": "a" * 64,
        }
        for choice in [
            {"criterion": "access", "passage": "p9"},
            {"criterion": "access", "passage": "p0"},
        ]:
            with self.assertRaises(Error):
                collect(Task.parse(task_data()), snap, [choice])

    def test_missing_and_changed_evidence_do_not_verify(self):
        task = Task.parse(task_data())
        self.assertFalse(verify_evidence(task, [], {})["passed"])
        evidence = [{"criterion": "access", "text": "Step-free access", "url": task.start_url}]
        self.assertFalse(
            verify_evidence(
                task, evidence, {task.start_url: {"passages": [{"text": "Stairs only"}]}}
            )["passed"]
        )
        self.assertTrue(
            verify_evidence(
                task, evidence, {task.start_url: {"passages": [{"text": "Step-free access"}]}}
            )["passed"]
        )
