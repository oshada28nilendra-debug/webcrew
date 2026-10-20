# Verification — 20 October 2026

## Follow-up check — 20 October, afternoon

Reopened the actual saved archive and matched its recorded 105159-byte SHA256 before continuation. Retried `scripts/public_smoke.py` after restoring the Python browser dependency removed by workspace maintenance. It again exited 3 with `Approved page DNS resolution failed`; no public page or browser was exercised. Actual new report: `delivery/public-retry-20261020-1300/report/report.json`. This retry does not rerun or supersede the earlier 40-test/local-model results. Application source is unchanged.

GitHub API now confirms RubricTrace PR #1 was user-merged on 19 October, with current main `ab5c5be944de7b41037b06802b2599f3372693a1`. Corrected the top-level batch ledger; retained historical test/PR records. Actual inspection metadata: `delivery/rubrictrace-merge-check.json`. No RubricTrace repository writes were made. WebCrew still has no designated repository, and the next project still requires selection. These outstanding items do not change the existing sequence.

Status: **implementation delivered; real browser and local-model fixture verified; public-site integration and GitHub publication remain blocked/pending.** This is the delayed `2026-10-19-afternoon` release. Do not call it fully finished or production ready.

## Executed locally

- Python 3.12.14: **40 tests passed, zero skips**, including real Chromium headless-shell 149.0.7827.55 navigation, fresh-context verification, changed-source refusal, pause/resume, cumulative budgets, forbidden navigation/redirect/meta-refresh blocking and proposed-write deferral. `delivery/tests.txt` is the actual output. Simulated planner/provider boundary tests are explicitly named; they are not live-model evidence.
- Ruff 0.15.7 lint and format check, compileall and wheel build passed. Isolated wheel installation and actual installed CLI ran from `/tmp`, completed the fictional site task and exported two evidence records: `delivery/installed-cli.json`. The CLI child imported the installed wheel, not the source tree.
- Independent review found two important issues and two related input defects. All four were reproduced RED→GREEN and the full suite rerun. Details in `REVIEW.md`.
- Gitleaks 8.30.1, checksum-verified scanner, found no source-package credential leaks. Actual redacted report: `delivery/gitleaks.json`. This is a source scan, not an account-access audit or complete-security guarantee.

Full Chrome could not launch here because its process-singleton Unix socket was denied. Official matching headless-shell worked without changing system permissions. Playwright's CDN initially returned a truncated error response; the official Chrome for Testing Google storage download succeeded. Browser binaries are not bundled.

## Genuine model + browser workflow

`delivery/live-model-final/` retains the final run after review fixes:

- Checksum-pinned llama.cpp **b11718**, official Qwen3-4B GGUF **Q4_K_M**, CPU. URLs/expected SHA256 are in `provenance.json` and the downloader.
- **Six actual inference calls**: five planner choices and a separate outcome review; **4,933 prompt / 62 completion tokens**, no paid API or credential.
- Finite action choices selected real allowed navigation/evidence operations. The workflow paused after two steps, resumed SQLite state, completed five actions and issued six permitted fixture GETs including independent source revisits. No tracker, purchase endpoint or POST reached the server.
- Exact findings: “Step-free access is available at the east entrance.” and “Full refund is available until 48 hours before the workshop.” Both passages and text hashes were inspected and independently recomputed from the final report.
- Separate semantic review accepted both criteria. This is one authored positive fixture, not a user study, injection benchmark, broad accuracy result or independent model-family ensemble.

Earlier attempts remain: attempt 1 selected an irrelevant passage and failed closed; attempt 2 prematurely finished and returned incomplete. Finite eligible action options narrowed the planner interface; attempt 3 and the final reviewed rerun succeeded. `delivery/live-model-history.json` records all four outcomes.

## Simpler baseline

No-model literal/BFS workflow independently succeeded on the identical fixture: five actions, six GETs, zero inference calls. The model did not improve this fixture's result or action count. `delivery/baseline-comparison.json` contains the actual comparison. This demonstrates bounded coordination/auditability, not a proven need for multiple agents.

## Blocked or not executed

- Actual `https://www.python.org/` attempt **failed closed at system DNS resolution** before fetching content. Failed checkpoint/report retained in `delivery/public-browser/`. Public HTTPS browser integration is **not verified here**. Local fictional HTTP/browser execution is verified separately.
- No WebCrew repository designated: **no remote commit, push, PR, hosted CI or deployment**. Included ordinary/manual real-model workflows have not run remotely. Python 3.11/3.13 checks are configured but unexecuted here.
- No paid remote model, login/authenticated profile, arbitrary dynamic controls, external write execution, accessibility audit, real-user benchmark or production-security review.

Next: designate a repository, run included checks and `manual-public-browser-integration` there under working DNS/egress, and inspect actual evidence before upgrading completion status. `PYTHONPATH=. python scripts/public_smoke.py --out public-output` executes the same public check locally. Resume this source; do not rebuild it.
