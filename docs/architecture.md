# ForenX Architecture & System Design

```
+-------------------------------------------------------------+
|                  ForenX UI Presentation Layer               |
|    - Streamlit App (app.py) / React SPA Workbench (App.tsx) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   Application Services Layer                |
|    - Case Management (cases.py)                             |
|    - Evidence Vault & Acquisition (acquisition.py)          |
|    - Integrity Verification (integrity.py)                  |
|    - Analysis Orchestration (analysis_service.py)           |
|    - Known-Answer Validation Engine (validation.py)         |
|    - Report Generation & Anti-XSS (reporting.py)            |
|    - Cryptographic Audit Logger (audit.py)                  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                Browser Artifact Parsers Layer               |
|    - Chromium History Parser (visits, urls, downloads)      |
|    - Firefox Places Parser (moz_places, visits, bookmarks)  |
|    - Read-Only SQLite Safety Wrapper (base.py)              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                  Normalized Event Model Layer               |
|    - WebKit 1601 UTC Microsecond Normalizer                 |
|    - Firefox PRTime 1970 UTC Microsecond Normalizer         |
|    - Physical Source Reference & Traceability               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                    Storage & Persistence                    |
|    - ForenX SQLite Application Database (WAL mode)          |
|    - Isolated Evidence Vault (Original preserved files)     |
|    - Controlled Working Copies                              |
+-------------------------------------------------------------+
```
