# WebCrew Implementation Plan

Goal: deliver the approved navigation/evidence/checkpoint workflow as a forkable Python CLI.
Architecture: validated finite task schema → planner → browser executor → SQLite state/event journal → fresh browser verifier → optional independent model review → escaped local reports.
Stack: Python 3.11+, stdlib core/HTTP/SQLite, Playwright 1.61.0 Chromium. Spec: DESIGN.md.
Execution: native implementation in this unattended run; user instruction to continue without follow-up overrides skill approval pauses. Fresh final review after implementation.

Global constraints: exact URL allowlist; 12 pages, 24 steps, 32 model calls maximum; no write tools; no paid calls; no publication until repository designation.
Review focus: malformed JSON/Unicode; resume under changed task/budgets; page redirects and subresource exfiltration; stale source verification; provider failures and checkpoint tampering.

1. Schema/evidence policy (`core.py`, `files.py`, `tests/test_core.py`). Write failing tests for valid task, URL ambiguity, exact passage selection and missing criteria; implement then run all tests.
2. State/provider boundaries (`state.py`, `provider.py`, `httpio.py`, `tests/test_state_provider.py`). Test task binding, locks, atomic events and cumulative budgets, malformed/unauthorized responses; implement and run suite.
3. Browser/workflow (`browser.py`, `runner.py`, `tests/test_browser.py`). Test actual linked navigation, independent changed-source rejection, pause/resume, off-list request blocking and write deferral. Implement finite actions, baseline, verifier; run suite with Chromium.
4. CLI/reports/demo/CI/docs. Execute installed CLI, baseline and genuine local-model fixture if possible; inspect actual exports and record separate verification. Obtain independent review, fix important findings with regressions, package and persist source.
