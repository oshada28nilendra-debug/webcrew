import json
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from webcrew.core import Error, Task
from webcrew.files import loads, read_json
from webcrew.provider import Model
from webcrew.state import Store
from tests.test_core import task_data


class StateTests(unittest.TestCase):
    def test_invalid_state_payload_rejected_before_commit(self):
        with tempfile.TemporaryDirectory() as d:
            with Store(Path(d) / "x.db", Task.parse(task_data())) as store:
                s = store.load()
                s["evidence"] = [None]
                with self.assertRaises(Error):
                    store.save(s, {"type": "invalid"})

    def test_resume_atomic_task_bound(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "run.db"
            task = Task.parse(task_data())
            with Store(path, task) as store:
                s = store.load()
                s["steps"] = 1
                store.save(s, {"type": "test"})
            with Store(path, task) as store:
                self.assertEqual(store.load()["steps"], 1)
                self.assertEqual(len(store.events()), 1)
            changed = task_data()
            changed["max_steps"] = 13
            with self.assertRaises(Error):
                with Store(path, Task.parse(changed)):
                    pass

    def test_lock_excludes_concurrent_runner(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "run.db"
            task = Task.parse(task_data())
            with Store(path, task):
                with self.assertRaises(Error):
                    with Store(path, task):
                        pass

    def test_corrupt_checkpoint_safe_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "run.db"
            p.write_bytes(b"not sqlite")
            with self.assertRaises(Error):
                with Store(p, Task.parse(task_data())):
                    pass

    def test_symlink_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.symlink_to(Path(d) / "y")
            with self.assertRaises(Error):
                with Store(p, Task.parse(task_data())):
                    pass


class JSONTests(unittest.TestCase):
    def test_invalid_json_values(self):
        for raw in ['{"a":1,"a":2}', "1e999", "NaN", '"\\ud800"', "[" * 70 + "0" + "]" * 70]:
            with self.subTest(raw=raw[:40]), self.assertRaises(Error):
                loads(raw)

    def test_read_size_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            p.write_bytes(b" " * 2_000_001)
            with self.assertRaises(Error):
                read_json(p)
            p.unlink()
            p.symlink_to(Path(d) / "y")
            with self.assertRaises(Error):
                read_json(p)


class ProviderTests(unittest.TestCase):
    def test_missing_hostname_rejected_at_construction(self):
        with self.assertRaises(Error):
            Model("https:///chat/completions", "m", remote_consent=True)

    def test_malformed_usage_is_safe_adapter_error(self):
        from unittest.mock import patch

        for usage in [None, [], 5, "bad"]:
            payload = json.dumps(
                {"choices": [{"message": {"content": '{"choice":"a0"}'}}], "usage": usage}
            ).encode()
            with (
                self.subTest(usage=usage),
                patch("webcrew.provider.request_bytes", return_value=(200, {}, payload)),
            ):
                with self.assertRaises(Error):
                    Model("http://127.0.0.1:8080/v1/chat/completions", "m").ask("planner", {})

    def test_remote_needs_consent_and_tls(self):
        for endpoint in [
            "https://example.org/v1/chat/completions",
            "http://example.org/v1/chat/completions",
        ]:
            with self.assertRaises(Error):
                Model(endpoint, "m")

    def test_real_http_adapter_and_redacted_failure(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                raw = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if raw["model"] == "fail":
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b"SECRET: must not escape")
                else:
                    payload = json.dumps(
                        {
                            "choices": [{"message": {"content": '{"action":"finish"}'}}],
                            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
                        }
                    ).encode()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(payload)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
            model = Model(endpoint, "test")
            result = model.ask("planner", {})
            self.assertEqual(result["action"], "finish")
            self.assertEqual(model.usage["prompt_tokens"], 10)
            with self.assertRaises(Error) as ctx:
                Model(endpoint, "fail").ask("planner", {})
            self.assertNotIn("SECRET", str(ctx.exception))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
