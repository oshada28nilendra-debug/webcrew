# Security boundaries

This is a bounded local research tool, not a hosted multi-tenant service or hardened browser sandbox. Use trusted task/state directories and an unprivileged environment. The local read-only transport checks exact approved URLs, public DNS and a pinned address; browser page requests are intercepted and fulfilled with bounded HTML plus a restrictive CSP. Browser internals/background traffic and OS process access are not a complete network-isolation guarantee. Use network/container restrictions when needed.

Page text is untrusted. Finite IDs, exact passage gates, fresh checks and model-review separation reduce some errors but do not prove injection immunity. Poor acceptance phrases, negation and source misinformation can still mislead. Inspect reports before making decisions.

Never allowlist action URLs or secrets in URLs. GET is not inherently side-effect-free. No login profiles, cookies, writes or credentials are exposed as agent tools. Approval requests are informational: write execution is absent. API keys are environment-only and provider error bodies are withheld. Optional remote model transmission requires explicit CLI consent.

SQLite is local trusted state, not a signed attestation. Its checksum is not an anti-forgery mechanism. Do not import databases from others. Output directories are new-only but parent directories must be trusted against concurrent filesystem attacks. Reports store exact source content; don't publish private investigations.

If you find a vulnerability, avoid posting secrets or exploit material against real sites. Reproduce on a local fictional fixture and contact the maintainer privately through an appropriate repository channel after publication.
