# WebCrew

**A small AI browser task team that shows its evidence before declaring success.**

WebCrew follows approved page links to complete a factual checklist, saves progress locally, and independently revisits the sources. Use it for public workshop policies, service eligibility details, or recurring information checks across a known set of pages.

This first release supports **read-only HTML investigations**. It does not log in, submit forms, make purchases or control arbitrary applications. It is a focused, forkable implementation, not a claim to outperform general browser agents.

## How it works

1. You describe the task, exact permitted page URLs and factual acceptance phrases.
2. A model planner chooses an observed link or an eligible exact passage ID.
3. The browser worker observes real Chromium DOM text through a bounded, address-pinned HTML transport.
4. SQLite commits observations, decisions, budgets and progress together.
5. An outcome verifier opens a fresh browser context and checks that every cited passage still exists. In model mode, a separate model call can veto semantic relevance.
6. You receive an escaped HTML report, structured JSON and a resumable checkpoint.

The executor is a deterministic worker, not a third LLM. The verifier has separate context but can share the same underlying model; its errors may be correlated. We make no swarm or multi-agent superiority claim.

## Quickstart

Python 3.11+ on Linux; the checkpoint lock currently uses POSIX `fcntl` (Windows users: WSL2). No API key is needed for the baseline demo.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m playwright install --with-deps chromium --only-shell
PYTHONPATH=. python scripts/demo.py --out demo-output
```

The demo starts a fictional three-page workshop site, pauses after two steps, resumes from SQLite, gathers accessibility/refund passages, revisits both pages and exports `demo-output/report/report.html` and `report.json`. Expected status: `verified`, two evidence records, zero model calls. The site contains a deliberately forbidden purchase link, image and script; none should reach its server.

`--out` directories must not exist. Keep different runs in different directories. The temporary fixture URLs in retained reports are historical evidence; use the demo to start a new live fixture.

## Your own checklist

Create `task.json` using this schema (replace these illustrative URLs and phrases with reviewed public information pages):

```json
{
  "objective": "Find the workshop access and cancellation policies",
  "start_url": "https://example.org/workshops",
  "allowed_urls": [
    "https://example.org/workshops",
    "https://example.org/access",
    "https://example.org/cancellation"
  ],
  "criteria": [
    {"id": "access", "description": "Venue accessibility", "contains": "Step-free access"},
    {"id": "refund", "description": "Cancellation refund window", "contains": "Full refund"}
  ],
  "max_steps": 16,
  "max_calls": 20
}
```

```bash
webcrew run task.json --checkpoint work/checkpoint.db --pause-after 2
webcrew run task.json --checkpoint work/checkpoint.db --output work/report
```

Without `--endpoint` this runs the simpler literal-match/breadth-first baseline. It is useful on its own and is sufficient for the authored demonstration. A phrase match is an acceptance test, not proof that a source is truthful or that a statement is affirmative. Choose specific phrases; inspect the report.

## Real local AI

Run an OpenAI-compatible local model server and add:

```bash
webcrew run task.json --checkpoint work/ai.db \
  --endpoint http://127.0.0.1:8080/v1/chat/completions \
  --model your-local-model --output work/ai-report
```

For the exact optional release smoke (Linux x64, Python 3.12+ for checksum-verified runtime extraction; roughly 3 GB downloads plus model RAM):

```bash
python scripts/download_model.py --out model-runtime
PYTHONPATH=. python scripts/live_smoke.py --runtime model-runtime --out live-output
```

This downloads pinned llama.cpp b11718 and the official Qwen3-4B Q4_K_M weights, verifies SHA256 before execution, starts a CPU server, and runs the actual browser/planner/verifier workflow. No paid API or key. The source package does not contain the browser, runtime or weights. Earlier failed attempts remain in `delivery/`.

## Optional remote provider

Supply a full HTTPS `/v1/chat/completions` URL, model name and `--allow-remote-model`. Set `WEBCREW_API_KEY` in your environment when required. This explicitly sends the objective, page text and evidence to that provider; provider billing and data policies apply. No remote paid provider was used for this delivery. Never put credentials in task URLs, JSON or source files. Environment variables are not loaded automatically from `.env`.

| Setting | Purpose |
|---|---|
| `WEBCREW_API_KEY` | Optional environment-only Bearer credential |
| `WEBCREW_CHROMIUM` | Optional trusted installed Chromium/headless-shell executable path |
| `--demo` | Permit literal `127.0.0.1` HTTP fixture pages; never use for untrusted tasks |
| `--pause-after N` | Pause after N actions in this invocation; cumulative budgets remain unchanged |

Exit codes: `0` verified; `3` paused/incomplete/failed/needs approval; `2` invalid input/setup/report failure. Terminal checkpoint results are historical and returned without rerunning; start a new checkpoint for a new verification. Resume uses the same task, demo policy and planner mode. Changed policy requires a new checkpoint.

## Boundaries and safeguards

- At most 12 exact URLs, eight criteria, 24 actions and 32 model calls. Inputs at most 2 MB, HTML responses at most 1 MB, rendered observations at most 24 KB. Model output at most 512 tokens per call, 128 KB per HTTP response. No automatic retries.
- Reviewed URLs require HTTPS, no credentials, query strings, fragments or encoded paths. Public DNS results are checked and one address is pinned per browser session. System DNS resolution itself is outside the HTTP deadline.
- Only approved main-document GETs are fetched; redirects, subresources, service workers, scripts, downloads and arbitrary browser controls are unavailable. A fixed trusted DOM-reading script is used by Playwright; model-written scripts/selectors are never executed.
- Any proposed write stops at `needs_approval` with an action/task digest. **Write execution is not implemented.** An approval file cannot enable it. GETs can cause side effects on badly designed sites: approve information pages only.
- Checkpoints/reports contain page text and task details. Keep them private. SQLite checksums detect accidental payload changes, not malicious forgery. Do not accept checkpoint databases from strangers.
- Local state/output directories must be trusted and not concurrently modified by other users. Browser isolation here is not an operating-system sandbox. Run as an unprivileged account/container for untrusted content. Browser parsing has its own security risks.
- Missing text, stale passages, model refusal, invalid IDs or exhausted budgets cannot become verified success. Models can still misunderstand relevance or be influenced by malicious page text; no general prompt-injection immunity claim.

## Development and evidence

```bash
python -m unittest discover -v
python -m ruff check .
python -m ruff format --check .
python -m compileall -q webcrew
python -m build --wheel --no-isolation
```

Browser tests are mandatory and fail if Chromium is unavailable; none silently substitutes a fake browser. Simulated model tests are named separately. See [verification](docs/VERIFICATION.md), [validation and alternatives](docs/VALIDATION.md), [design](docs/DESIGN.md), [handoff](docs/HANDOFF.md) and [security](SECURITY.md). Included GitHub workflows have not run remotely without a designated repository.

## Contributing

Open an issue with a minimal fictional task/fixture and expected outcome. Keep policy, model integration, browser worker and verification separate. New actions require deny-path and outcome tests. Never contribute real credentials, private page content, student/customer data or authenticated profiles. See `CONTRIBUTING.md` and the MIT license.
