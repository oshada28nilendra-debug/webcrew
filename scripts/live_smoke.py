"""Run the real local model and browser fixture together; never an offline/mock result."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runtime = args.runtime.resolve()
    binary = next(runtime.rglob("llama-server"))
    env = dict(os.environ, LD_LIBRARY_PATH=str(binary.parent), PYTHONPATH=str(Path.cwd()))
    env.pop("WEBCREW_API_KEY", None)
    command = [
        str(binary),
        "-m",
        str(runtime / "model.gguf"),
        "--host",
        "127.0.0.1",
        "--port",
        "18082",
        "-c",
        "8192",
        "-np",
        "1",
        "-t",
        "4",
        "-ngl",
        "0",
        "--no-webui",
    ]
    with (args.out / "runtime.log").open("w") as log:
        server = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError("Local model server exited; see runtime.log")
                try:
                    with urllib.request.urlopen("http://127.0.0.1:18082/health", timeout=1) as r:
                        if r.status == 200:
                            break
                except OSError:
                    time.sleep(0.5)
            else:
                raise RuntimeError("Local model did not become ready")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/demo.py",
                    "--out",
                    str(args.out / "workflow"),
                    "--endpoint",
                    "http://127.0.0.1:18082/v1/chat/completions",
                    "--model",
                    "Qwen3-4B",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=900,
            )
            (args.out / "demo.stdout.txt").write_text(result.stdout)
            (args.out / "demo.stderr.txt").write_text(result.stderr)
            provenance = json.loads((runtime / "provenance.json").read_text())
            (args.out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
            print(result.stdout, flush=True)
            if result.returncode:
                raise RuntimeError("Real-model workflow gate failed; retained actual outputs")
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    main()
