# Validation — 20 October 2026

**Target user:** small community organizations and operators repeatedly collecting public service/workshop policy details across a known set of pages.
**Pain point:** an agent can navigate correctly yet declare an unsupported outcome. Independently observed outcomes and resumable state are useful when a task pauses or a source changes.

## Primary evidence inspected

- Browser Use, https://github.com/browser-use/browser-use : MIT Python browser-agent library, local and cloud options, general task execution. Already addresses broad navigation; no claim that browser agents are new.
- Stagehand, https://github.com/browserbase/stagehand : browser `act`, `observe` and schema-based `extract`, with conventional programmatic control. A better fit for many production integrations. WebCrew does not claim these primitives are missing.
- Skyvern, https://github.com/Skyvern-AI/skyvern : Playwright-compatible AI SDK, no-code workflows and multi-agent browser automation. Broad workflow orchestration is already available. Its local SQLite setup is documented; do not claim it requires cloud or Postgres.
- Yin et al., *Constructing Challenging Browser-Use Tasks by Controlled Environment Interventions*, submitted 20 September 2026, https://arxiv.org/abs/2609.35814 : abstract reports controlled environment changes and success-declaration failures. This supports the relevance of outcome verification, not market demand, and does not establish WebCrew's efficacy. No paper code/data reused.
- Playwright network controls, https://playwright.dev/python/docs/network and API https://playwright.dev/python/docs/api/class-browsercontext : route interception and service-worker limitations informed the browser boundary. Playwright 1.61.0 is a direct dependency, Apache-2.0. Chromium/Chrome distribution is external, not bundled.

**Current alternatives:** manual browser/checklist, deterministic Playwright script, the three broad agents/SDKs above.
**Gap (engineering hypothesis):** a small exact-page-only, inspectable package whose planner decisions, source passages, checkpoint and independent re-observations travel together is easier to audit and fork for narrow workflows. This is a packaging and scope choice; competitor documentation does not prove competitors lack similar controls.
**Differentiator:** finite IDs and no write tools, a task-bound SQLite journal and fresh source verification before completion. A separate semantic-review call can veto literal matches. Do not call this a swarm or proven multi-agent improvement.
**Feasibility:** finite read-only task across 1–12 reviewed HTML pages; literal checklist and local browser fixture allow deterministic outcome checks. Authenticated/dynamic tasks deferred.
**Risks:** allowlist preparation, source changes, bad acceptance phrases, negation, model misinterpretation and bounded-context omissions. GET requests may have side effects. Hosted APIs can cost money and receive page data; default demonstration is keyless local.
**Decision:** proceed with this narrowed scope; do not compete on general browser autonomy. Run a deterministic literal/BFS baseline on the same fixture. No user interviews, adoption evidence, accuracy benchmark or novelty claim.

## Licensing

New source/fixtures: MIT. The user-owned RubricTrace MIT project supplies the generic `files.py`, `httpio.py` and checksum download helper; its MIT notice is retained. The competitors are research references, not vendored dependencies. Installed metadata: Playwright 1.61.0 Apache-2.0, pyee 13.0.1 MIT, greenlet 3.5.6 MIT AND PSF-2.0. The optional official Qwen3-4B-GGUF weights are Apache-2.0; llama.cpp runtime MIT. Model/runtime and browser binaries are deliberately excluded from the source archive.
