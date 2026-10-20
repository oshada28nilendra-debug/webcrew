# Final independent review

A separate read-only reviewer inspected the full implementation, requirements and tests, and ran the then-current 36-test suite with real Chromium. No critical finding was reported.

Important fixes, each reproduced before fixing:

- HTML meta refresh could navigate to another approved page and attribute its passages to the original URL. Added `test_meta_refresh_cannot_misattribute_evidence` (failed before fix). The transport now rejects meta refresh before fulfilling any HTML, authorizes one expected main document per read, and confirms the observed URL and body hash are present before returning a snapshot. The regression passes with real Chromium; the refresh destination is not requested.
- Provider `usage: null/list/int/string` could raise uncaught AttributeError. Added `test_malformed_usage_is_safe_adapter_error` (all four variants failed before fix). Provider usage must now be an object; malformed responses become the normal redacted Error.
- Overlong DNS labels and missing model endpoint hostnames could escape clean input handling. Added `test_invalid_dns_labels_rejected` and `test_missing_hostname_rejected_at_construction` (both failed before fix), tightened construction checks and DNS Unicode failure conversion; both pass.

No deferred minor review finding or behavior ruling remains. Full final suite and live-model rerun are recorded separately in VERIFICATION.md. The review is a focused engineering review, not a penetration test or complete-security guarantee.

## Publication integration follow-up

Hosted public HTTPS execution exposed gzip-encoded HTML from python.org. Added a real-browser reproducer that failed before the fix, plus bounded-decoder tests for oversized expansion, truncation, multiple members, invalid UTF-8 and unsupported encodings. The fix uses a capped single-member zlib decoder and keeps the 1 MB compressed/expanded limits. A separate read-only reviewer inspected the change and ran all six new encoding/browser cases; no important findings. The local complete suite passed 46 tests, zero skips. Hosted packaging also now uses isolated builds, because Python 3.12/3.13 environments lacked a global setuptools backend.

The Python homepage subsequently fetched and decoded correctly, then failed closed at the existing 80-passage observation limit. The public integration fixture was narrowed to IANA's shorter official example-domain documentation page; the product budget was retained. Earlier failed hosted outcomes remain part of the verification history.
