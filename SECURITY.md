# Security Policy & Forensic Safety

## 1. Local-First Architecture
ForenX is engineered to operate strictly in a local-first environment:
- No telemetry or external analytics.
- No transmission of evidence files or browser history to third-party cloud servers.
- Application servers bind to `localhost` / `127.0.0.1` by default.

## 2. Evidence Safety & Non-Destructive Acquisition
- **Controlled Copying:** Original evidence databases are preserved in an isolated vault (`forenx_workspace/evidence_vault/`).
- **Read-Only Analysis:** Parsers operate exclusively on working copies (`working_copies/`) using read-only SQLite connections (`?mode=ro` and `PRAGMA query_only = ON`).
- **In-Transit Integrity:** SHA-256 hashes are computed before and after evidence copying. If a concurrent write occurs, the acquisition is rejected as inconsistent.

## 3. Privacy & Sensitive Data Exclusion
ForenX enforces strict exclusion policies:
- Passwords and encrypted credentials (`Login Data`) are NEVER accessed or extracted.
- Session tokens, cookies (`Cookies`), and autofill secrets are NEVER parsed or stored.
- SQLite queries extract only URLs, visit timestamps, page titles, download metadata, and bookmark titles.

## 4. Reporting Security Vulnerabilities
If you discover a security issue or path traversal vulnerability in ForenX, please report it responsibly by contacting the maintainers or opening a confidential security advisory.
