import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webcrew.cli import main
from webcrew.report import export


class CLITests(unittest.TestCase):
    def test_bad_task_exit_two_no_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.json"
            p.write_text('{"objective": 9}')
            with patch(
                "sys.argv", ["webcrew", "run", str(p), "--checkpoint", str(Path(d) / "run.db")]
            ):
                self.assertEqual(main(), 2)

    def test_inert_html_and_safe_json(self):
        with tempfile.TemporaryDirectory() as d:
            state = {
                "status": "incomplete",
                "steps": 0,
                "calls": 0,
                "evidence": [
                    {
                        "criterion": "x",
                        "url": "https://example.org/",
                        "text": "<script>alert(1)</script>",
                        "text_sha256": "a",
                    }
                ],
                "reason": "<img onerror=bad>",
            }
            out = Path(d) / "report"
            export(state, [], out)
            html = (out / "report.html").read_text()
            self.assertNotIn("<script>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertEqual(
                json.loads((out / "report.json").read_text())["state"]["status"], "incomplete"
            )
            with self.assertRaises(Exception):
                export(state, [], out)
