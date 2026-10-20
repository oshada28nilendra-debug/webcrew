# Verification — 20 October 2026

**Bounded release implemented, published and verified; PR #1 is open.**

Repository: https://github.com/oshada28nilendra-debug/webcrew
Branch: `feat/webcrew-first-release`
PR: https://github.com/oshada28nilendra-debug/webcrew/pull/1
Tested implementation: `2816d38f346f6b3a8a6f79ca4ae90a47517f809d`.

## Actual hosted checks

- [Ordinary CI](https://github.com/oshada28nilendra-debug/webcrew/actions/runs/39435871875): **46 tests passed, zero skips per Python 3.11/3.12/3.13**, including actual Chromium. Lint/format/compile, isolated wheel build, baseline demo and Gitleaks passed. All three decoded job logs inspected.
- [Public browser](https://github.com/oshada28nilendra-debug/webcrew/actions/runs/39435871737): real guarded HTTPS fetch of IANA's example-domain documentation, 6,774 HTML bytes, Chromium149.0.7827.55, exact documentation-purpose passage collected and observed again in a fresh context. Downloaded artifact12272790099 SHA256 `04900922ed26f77dae1ab66fff8919220e4bb65f7eb38dbd585a21e9042cc0f9` matched; actual report and passage/hash were inspected locally. Retained `delivery/github-public-browser/`.
- [Real local-model CI](https://github.com/oshada28nilendra-debug/webcrew/actions/runs/39435871874): checksum-pinned llama.cppb11718 + official Qwen3-4B Q4_K_M CPU; **six actual calls, 4,933 prompt /62 completion tokens**, five actions, pause after two/resume, fresh-source review. Downloaded artifact12271625691 SHA256 `21dabd2220441e7d5a231bc1cb2e09a498fb25e4194da24d82401378c671a754` matched. Actual access/refund passages and hashes were recomputed locally against fresh observations. Retained `delivery/github-live-model/`. No paid API/key.

Local full suite also passed46/46 with real headless-shell149.0.7827.55. Fresh lint/format, isolated wheel build and an installed-wheel CLI run from /tmp against gzip HTML passed. Prior40-test and model evidence is historical, retained in `VERIFICATION-HISTORY.md` and delivery/. The generic compatible HTTP adapter is real; simulated-provider tests remain distinct from these actual model calls.

## Failures retained and fixed

Initial hosted Python3.12/3.13 checks passed40tests but failed wheel creation without a global setuptools backend; build isolation fixed it. Initial public fetch returned gzip and was incorrectly decoded as raw UTF8. A real-browser regression failed before bounded gzip decoding was added; five decoder tests cover expansion, malformed/truncated/concatenated data, UTF8 and unsupported encoding. Independent focused review found no important issue.

After gzip decoding, the Python homepage correctly failed the existing80-passage observation limit. The public smoke was narrowed to a shorter official IANA documentation page; limits were not relaxed. Earlier failed run IDs and reasons remain in `delivery/github-verification.json`. Earlier local weak/failed model attempts remain in `delivery/live-model-history.json`.

## Scope and limitations

This verifies one authored workshop checklist with a real model and one real public documentation page. The no-model BFS/literal baseline also completes the workshop fixture in the same5actions and6GETs with zero inference; no model advantage or broad task accuracy demonstrated. The separate model verifier shares a model family with the planner. No production-security, injection-immunity, accessibility or user-study claim.

Read-only HTML tasks only. Authenticated/dynamic apps and external write execution are out of scope; proposed writes stop without execution. Local DNS remains restricted, but the former public-integration blocker is resolved in hosted CI. Old no-repository/blocked notes are historical. PR review/merge remains the user's decision.
