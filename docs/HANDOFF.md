# Release handoff

WebCrew's bounded read-only release is implemented, published and verified for delayed slot `2026-10-19-afternoon`.

- Repository: https://github.com/oshada28nilendra-debug/webcrew
- Branch: `feat/webcrew-first-release`
- Review: https://github.com/oshada28nilendra-debug/webcrew/pull/1 (open; never automatically merged)
- Tested implementation: `2816d38f346f6b3a8a6f79ca4ae90a47517f809d`
- Actual CI, public-browser and real-model evidence: [VERIFICATION.md](VERIFICATION.md) and [publication record](../delivery/github-verification.json).

All 46 tests passed on Python 3.11, 3.12 and 3.13. Actual public HTTPS execution and six local-model inference calls passed their separate workflows. The earlier local DNS restriction was resolved through hosted CI. No paid model API or key was used.

The workflow supports approved public HTML information tasks, persisted pause/resume and fresh evidence verification. It does not execute consequential writes, authenticate to websites or control dynamic applications. The simpler deterministic baseline also passed the authored fixture; no model advantage is established.

User review and merge remain separate. Read the feature branch until merged. Earlier source ZIPs and `VERIFICATION-HISTORY.md` retain historical results; prefer this branch for current code. SQLite fixture checkpoints remain in the historical archive; full JSON observations/events are retained here. Browser/model binaries are excluded.

The third 19 October slot remains pending explicit project selection. ExperimentCrew was a proposal only. CaptionGuard and StockSage were rejected. All 27 slot identities remain in PROJECT_LEDGER.json.
