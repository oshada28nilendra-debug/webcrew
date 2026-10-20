# WebCrew first release design

User-approved scope: a bounded planner/browser executor/outcome verifier with site restrictions, checkpoints and resumable evidence. This unattended delivery uses the authorized local-package fallback; no repository has been designated.

## Narrow release

Complete read-only checklist investigations across a user-reviewed, explicit list of exact page URLs. Example: follow a community workshop directory, find the accessibility and cancellation policies, collect exact rendered passages, independently reopen the pages, and export a verified checklist with source links. A task includes an objective and factual criteria with literal `contains` phrases. These phrases are acceptance checks, not semantic truth guarantees.

The planner selects finite observed link IDs or passage IDs. The executor uses Playwright Chromium in a fresh context with JavaScript, service workers, cookies and downloads unavailable to the agent. Only exact allowlisted main-document GET requests are permitted. Subresources, redirects to unlisted URLs and all other methods are blocked. The independent verifier uses another fresh context and must find the exact collected passage again; a separate model call can veto semantic relevance. It cannot override deterministic missing-evidence checks. No model-written code or selector is executed.

Persist task-bound state in SQLite, with a process lock, atomic state/event transactions, bounded cumulative action/model-call budgets, explicit pause/resume and terminal failures. Record pending steps before external reads. Resumption may repeat a read after an interrupted operation, never an external write. User-controlled checkpoint files are not signed evidence or safe to accept from strangers.

Consequential writes are unavailable in this release. A requested submission/purchase/fill/click produces `needs_approval`, an action-bound approval request and no browser effect. An approval artifact is not execution authorization: actual write execution is deliberately deferred. GET requests can have side effects on badly designed sites, so only reviewed public information pages should be allowlisted. This is not a network sandbox or protection from malicious browser exploits.

## Alternatives and trade-offs

A deterministic breadth-first baseline is simpler and sufficient for literal checklists; include it and compare on the same authored fixture. A general browser agent is broader but difficult to verify in this delivery. Choose a finite-action model planner plus fresh verifier for inspectability, without claiming a swarm, novelty, broad success rate or superiority over the baseline. Separate responsibilities alone do not prove multi-agent benefit.

## Acceptance

- Real Chromium visits linked pages and exports the correct source passages.
- Missing facts, changed sources, fabricated passage IDs and verifier veto cannot yield verified success.
- Pause/restart preserves collected evidence and cumulative budgets; changed task/checkpoint corruption fails closed.
- Off-list navigation, third-party resources and write actions never reach a fixture server.
- Genuine compatible HTTP model adapter, explicit local versus remote consent, bounded calls and redacted failures.
- Run deterministic unit/failure tests, actual browser integration, baseline comparison and (when runtime available) real local-model smoke. Report each independently.

## Boundaries

No login, dynamic JavaScript apps, arbitrary controls, file upload/download, CAPTCHA bypass, purchases, authenticated tasks, autonomous source discovery or cross-page numerical inference. Evidence establishes rendered text at observation time, not source truth. Exact-page allowlists require preparation and can become stale. No production-security or general task-accuracy claim.
