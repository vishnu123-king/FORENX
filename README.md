# ForenX: Cross-Platform Digital Forensics & Evidence Validation Workbench

[![Tests](https://img.shields.io/badge/pytest-42%20passed-287D60.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.10-6D3FC0.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-D96A9B.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-43206F.svg)](README.md)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)](package.json)

ForenX is an enterprise-grade academic digital forensics and remote incident response workbench. It supports both **Mode A (Local System Analysis)** and **Mode B (Remote Orchestration & Agent Operations)** to acquire authorized browser artifacts, calculate and verify cryptographic SHA-256 evidence integrity, normalize microsecond-accurate native timestamps, reconstruct cross-browser chronological timelines, execute empirical known-answer validation, and produce court-admissible audit trails.

---

## 🔬 Academic Research & Operational Objective

> *"How effectively can a source-traceable evidence-integrity and known-answer validation layer improve the reproducibility, verifiability, and remote orchestration of cross-browser artifact analysis?"*

ForenX addresses the opacity and manual bottleneck of conventional forensic extraction tools through a dual-mode architecture:

1. **Physical Grounding & Source Traceability:** Every extracted artifact binds directly to its source database path, table name, and physical row ID.
2. **Explicit Microsecond Timestamp Normalization:** Standardizes WebKit 1601 UTC microseconds (Chromium family) and PRTime 1970 UTC microseconds (Mozilla Firefox) into ISO-8601 UTC strings with explicit conversion flags.
3. **Dual-Level Cryptographic Integrity:** Computes streaming SHA-256 hashes for individual database copies and standardized `FX-ACQ-*.forenx.zip` evidence packages.
4. **Mode B Remote Client Connection & Orchestration:** Leverages single-use cryptographic tokens to enroll remote client endpoints, issue scoped collection jobs, and securely stream evidence.
5. **Known-Answer Empirical Validation Lab:** Evaluates extracted events against ground-truth benchmark manifests to compute empirical Precision and Recall metrics with zero-denominator safety.
6. **Tamper-Evident Chained Audit Trail:** Logs all examiner actions into a cryptographically chained SHA-256 sequence.

---

## 🌐 Dual Operational Modes

### 💻 Mode A: Local System Forensics
- **Direct System Ingestion:** Automatically discovers local Chrome, Edge, Brave, and Firefox profiles on the workstation.
- **WAL Sidecar Snapshotting:** Safe online snapshotting of active SQLite databases (`History-wal`, `places.sqlite-wal`) using non-locking read transactions.
- **Evidence Vault Ingestion:** Drag-and-drop raw SQLite databases or portable `.forenx.zip` packages.

### 📡 Mode B: Remote Endpoint Orchestration
- **Cryptographic Token Enrollment:** Generate single-use enrollment tokens with time-to-live (TTL) bounds and endpoint caps.
- **Scoped Remote Job Queue:** Target remote endpoints for specific browser families (Chromium, Firefox) and artifact categories (visits, URLs, downloads, bookmarks).
- **Portable Agent Execution:** Remote endpoints run lightweight Python collection agents (`forenx.agent.field_collector`) to build verifiable evidence archives locally or upload over TLS.

---

## 🚀 Key Features

- **Evidence Vault & Dual Verification:**
  - Ingest raw browser databases or standardized `FX-ACQ-*.forenx.zip` evidence archives.
  - Automatic pre/post acquisition SHA-256 hash validation and sidecar preservation.
- **Remote Endpoint & Job Manager:**
  - Real-time status tracking for enrolled remote workstations (Online, Offline, In Job).
  - Configurable collection parameters (artifact allowlists, max file sizes, job priority).
- **Cross-Browser Extraction:**
  - **Chromium Family (Chrome, Edge, Brave, Vivaldi):** Visits (`visits`), URLs (`urls`), Transition Qualifiers (`LINK`, `TYPED`, `AUTO_BOOKMARK`), and Downloads (`downloads`).
  - **Mozilla Firefox:** Places (`moz_places`), History Visits (`moz_historyvisits`), and Bookmarks (`moz_bookmarks`).
- **Unified Timeline Explorer:**
  - Chronological multi-browser event reconstruction with fuzzy URL search, title filtering, and browser breakdown charts.
  - Deep inspection modal displaying raw integer timestamps alongside normalized UTC ISO-8601 datetimes.
- **Validation Lab:**
  - Automated known-answer verification against synthetic ground-truth datasets.
  - Precision, Recall, F1-Score calculations, missing record detection, and unexpected artifact flag analysis.
- **Multi-Format Export & Reporting:**
  - Self-contained, responsive HTML executive reports with embedded charts and anti-XSS escaping.
  - Structured JSON findings and CSV timeline exports for SIEM/EDR integration.

---

## 🛠️ Quickstart Installation

### Requirements
- **Node.js**: 18.0 or higher
- **Python**: 3.10 or 3.11+
- **Git**: For source version control

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone https://github.com/forenx/forenx-workbench.git
cd forenx-workbench

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
# Install frontend & server dependencies
npm install

# Install Python forensic engine dependencies
pip install -r requirements.txt
```

### Step 3: Run Development Server
```bash
# Launch full-stack React frontend + Express API server (Port 3000)
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## 📡 Remote Client Connection Guide (Mode B)

To collect browser artifacts from a remote client host and stream evidence to the central ForenX server:

### 1. Generate Single-Use Enrollment Token on Workbench
1. Open the ForenX Web Interface (`http://localhost:3000`).
2. Navigate to **Endpoints** or **Remote Forensics** in the navigation bar.
3. Click **Generate Token**.
4. Set the token parameters:
   - **Token Name / Label:** `INCIDENT-2026-CLIENT-09`
   - **Expiration:** 24 Hours
   - **Max Uses:** 1 (Single-use recommended for strict custody)
5. Copy the generated enrollment token (e.g. `FX-TOK-9A2E7F4C81`).

### 2. Run Portable Field Collector on Remote Machine
On the remote Windows or Linux target host:

```bash
# Option A: Execute using Python module
python3 -m forenx.agent.field_collector \
  --out ./forenx_output \
  --case CASE-2026-09 \
  --examiner "Remote Incident Agent" \
  --notes "Remote evidence acquisition"

# Option B: Standard offline field collection
python3 -m forenx.agent.field_collector -o ./evidence_packages
```

### 3. Verify & Import Remote Evidence Package
1. Transfer the generated `FX-ACQ-*.forenx.zip` archive or upload it directly via the **Remote Forensics** UI.
2. In the ForenX Workbench, navigate to **Evidence Vault**.
3. Select **Import Package** and select the ZIP file.
4. ForenX will automatically verify the internal `manifest.json` SHA-256 hashes against the physical payload and log a tamper-evident audit entry.

---

## 🏭 Production Deployment Guide

### Option 1: Standalone Node.js & Python Production Server
```bash
# 1. Build optimized frontend bundle
npm run build

# 2. Start Express production server
npm start
```

By default, Express serves the static production build from `/dist` and exposes API endpoints on port 3000. Environment configuration can be defined in a `.env` file:
```env
PORT=3000
NODE_ENV=production
DATABASE_PATH=./data/forenx.sqlite
JWT_SECRET=your-secure-jwt-secret-key
```

### Option 2: Docker Compose Production Stack
Deploy ForenX with an Nginx reverse proxy using Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'

services:
  forenx-app:
    build: .
    container_name: forenx_workbench
    restart: always
    environment:
      - PORT=3000
      - NODE_ENV=production
    volumes:
      - forenx-data:/app/data
      - forenx-evidence:/app/evidence
    ports:
      - "3000:3000"

  nginx:
    image: nginx:alpine
    container_name: forenx_proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - forenx-app

volumes:
  forenx-data:
  forenx-evidence:
```

Launch the container stack:
```bash
docker-compose up -d --build
```

### Option 3: Nginx Reverse Proxy Configuration
Sample Nginx proxy configuration (`nginx.conf`) with SSL termination:

```nginx
server {
    listen 80;
    server_name forenx.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name forenx.yourdomain.com;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 500M;  # Allow large evidence archive uploads

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📦 Standalone Executable Packaging (PyInstaller)

To compile the `field_collector` agent into a zero-dependency, self-contained executable for remote field deployments:

### Linux Compilation
```bash
pip install pyinstaller

pyinstaller --onefile \
  --name forenx_collector_linux \
  --add-data "src/forenx:forenx" \
  src/forenx/agent/field_collector.py
```
The compiled binary will be generated at `dist/forenx_collector_linux`.

### Windows Compilation (PowerShell / CMD)
```cmd
pip install pyinstaller

pyinstaller --onefile ^
  --name forenx_collector_win.exe ^
  --add-data "src/forenx;forenx" ^
  src/forenx/agent/field_collector.py
```
The compiled binary will be generated at `dist\forenx_collector_win.exe`.

---

## 🧪 Automated Testing & Verification

ForenX contains a comprehensive test suite covering database isolation, artifact extraction, microsecond timestamp converters, remote job queues, evidence package verification, and chained audit logs.

```bash
# Set Python path
export PYTHONPATH=src:tests:.

# Run full pytest test suite (42 unit & integration tests)
pytest -v

# Run Python linting
ruff check src tests

# Run TypeScript type check
npm run typecheck
```

---

## 📂 Repository Structure

```
ForenX/
├── server.ts                   # Full-stack Express server with Vite middleware & REST endpoints
├── package.json                # Node dependencies & script runners
├── pyproject.toml              # Python metadata, tool settings & pytest config
├── requirements.txt            # Core Python forensic engine dependencies
├── docker-compose.yml          # Container orchestration template
├── src/
│   ├── forenx/                 # Python Forensic Engine Core
│   │   ├── config.py           # Configuration parameters & default paths
│   │   ├── database.py         # SQLite schema initialization & connection helpers
│   │   ├── models.py           # Dataclasses & Pydantic domain models
│   │   ├── exceptions.py       # Custom forensic exception hierarchy
│   │   ├── cases.py            # Case management & metadata persistence
│   │   ├── acquisition.py      # Non-destructive evidence handling & WAL sidecars
│   │   ├── integrity.py        # Streaming SHA-256 hash calculator & verifier
│   │   ├── timestamps.py       # WebKit (1601) & PRTime (1970) microsecond converters
│   │   ├── events.py           # Unified timeline reconstruction & filters
│   │   ├── validation.py       # Empirical ground-truth Precision/Recall engine
│   │   ├── reporting.py        # Self-contained HTML, JSON, and CSV report exporter
│   │   ├── audit.py            # Chained cryptographic SHA-256 audit logger
│   │   ├── cli.py              # CLI entry point & benchmark seeder
│   │   ├── agent/              # Remote & field acquisition agents
│   │   │   └── field_collector.py # Standalone offline collector script
│   │   ├── discovery/          # Browser discovery modules
│   │   │   └── browser_discovery.py # Cross-platform browser profile finder
│   │   ├── evidence/           # Evidence packaging & vault management
│   │   │   └── package.py      # FX-ACQ zip package generator & verifier
│   │   ├── remote/             # Mode B remote orchestration handlers
│   │   │   ├── endpoints.py    # Remote endpoint & token manager
│   │   │   └── jobs.py         # Scoped collection job queue manager
│   │   ├── parsers/            # Read-only browser artifact parsers
│   │   │   ├── base.py         # Base parser with read-only SQLite pragma
│   │   │   ├── chromium.py     # Chrome, Edge, Brave history & download parser
│   │   │   └── firefox.py      # Firefox places.sqlite parser
│   │   └── services/           # Higher-level forensic orchestrator
│   ├── App.tsx                 # Main React router & layout frame
│   ├── main.tsx                # React DOM entry point
│   └── components/             # React workbench UI views
│       ├── Navigation.tsx      # Top bar navigation & active status indicators
│       └── pages/              # 14 Navigation view pages
│           ├── OverviewPage.tsx      # System dashboard & quick metrics
│           ├── CasesPage.tsx         # Active forensic case manager
│           ├── LocalForensicsPage.tsx# Mode A local browser scanner
│           ├── RemoteForensicsPage.tsx# Mode B remote orchestration workbench
│           ├── EndpointsPage.tsx     # Enrolled client host & token manager
│           ├── CollectionJobsPage.tsx# Scoped collection job queue
│           ├── EvidenceVaultPage.tsx # Evidence package importer & SHA-256 validator
│           ├── ArtifactExplorerPage.tsx # Raw database artifact table inspector
│           ├── TimelinePage.tsx      # Unified chronological browser event timeline
│           ├── ValidationLabPage.tsx # Ground-truth benchmark Precision/Recall evaluator
│           ├── ReportsPage.tsx       # Executive HTML, JSON, CSV report generator
│           ├── AuditLogPage.tsx      # Cryptographic SHA-256 chained operation audit log
│           ├── SettingsPage.tsx      # Forensic parameters & storage preferences
│           └── AboutPage.tsx         # Academic framework overview & methodology
├── tests/                      # Automated Test Suite (42 Tests)
│   ├── conftest.py             # Shared pytest fixtures & isolated DB context
│   ├── unit/                   # Unit tests (packages, discovery, remote, timestamps, etc.)
│   └── integration/            # Full-workflow acquisition & validation tests
└── docs/                       # Technical & forensic methodology documentation
```

---

## ⚖️ Forensic Scope & Disclaimer

1. **Academic & Authorized Research Focus:** ForenX is designed for legitimate incident response, academic research, and educational demonstration.
2. **Integrity vs Authenticity:** A cryptographic SHA-256 hash verifies that evidence byte contents match the acquired baseline; it does not prove the original source host was untampered prior to acquisition.
3. **Privacy & Exclusion Safeguards:** ForenX strictly avoids extracting stored passwords, sensitive credentials, autofill field values, or session authentication cookies.

---

## 📄 License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

