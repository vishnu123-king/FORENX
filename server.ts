import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import fs from "fs";
import { execFile } from "child_process";
import multer from "multer";

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "100mb" }));
app.use(express.urlencoded({ extended: true, limit: "100mb" }));

// Configure upload directory for incoming evidence
const uploadDir = path.join(process.cwd(), "forenx_workspace", "incoming_evidence");
fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    cb(null, uploadDir);
  },
  filename: (_req, file, cb) => {
    // Preserve original filename
    cb(null, file.originalname);
  }
});
const upload = multer({ storage, limits: { fileSize: 500 * 1024 * 1024 } });

// Helper to execute Python ForenX IPC bridge
function runForenxBridge(cmd: string, args: Record<string, any> = {}): Promise<any> {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({ cmd, args });
    const pyScript = path.join(process.cwd(), "src", "forenx_api.py");
    const env = {
      ...process.env,
      PYTHONPATH: `${path.join(process.cwd(), "src")}:${path.join(process.cwd(), "tests")}:${process.cwd()}`
    };

    execFile("python3", [pyScript, payload], { env, maxBuffer: 50 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        console.error("Python bridge execution error:", error, stderr);
        return reject(new Error(stderr || error.message));
      }
      try {
        const parsed = JSON.parse(stdout.trim());
        if (parsed.status === "error") {
          return reject(new Error(parsed.message));
        }
        resolve(parsed.data || parsed);
      } catch (err: any) {
        console.error("Failed to parse Python JSON output:", stdout);
        reject(new Error(`Invalid JSON from Python bridge: ${stdout.slice(0, 300)}`));
      }
    });
  });
}

// ----------------- API ROUTES -----------------

// Global statistics
app.get("/api/stats", async (_req, res) => {
  try {
    const data = await runForenxBridge("stats");
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List cases
app.get("/api/cases", async (req, res) => {
  try {
    const data = await runForenxBridge("list_cases", {
      status: req.query.status as string,
      search: req.query.search as string
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Create case
app.post("/api/cases", async (req, res) => {
  try {
    const { name, description, investigator, notes } = req.body;
    if (!name || !name.trim()) {
      return res.status(400).json({ success: false, error: "Case name is required." });
    }
    const data = await runForenxBridge("create_case", { name, description, investigator, notes });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Get case detail
app.get("/api/cases/:id", async (req, res) => {
  try {
    const data = await runForenxBridge("get_case", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(404).json({ success: false, error: err.message });
  }
});

// Archive case
app.post("/api/cases/:id/archive", async (req, res) => {
  try {
    const data = await runForenxBridge("archive_case", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List evidence for case
app.get("/api/cases/:id/evidence", async (req, res) => {
  try {
    const data = await runForenxBridge("list_evidence", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Upload evidence file to case vault
app.post("/api/cases/:id/evidence/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: "No file was uploaded." });
    }
    const notes = req.body.notes || "";
    const data = await runForenxBridge("import_file", {
      case_id: req.params.id,
      file_path: req.file.path,
      notes
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});
// Discover local browser profiles
app.get("/api/discovery/local", async (_req, res) => {
  try {
    const data = await runForenxBridge("discover_local");
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Acquire authorized local profiles into evidence package
app.post("/api/acquisition/local", async (req, res) => {
  try {
    const { case_id, profiles, investigator, notes } = req.body;
    if (!case_id) {
      return res.status(400).json({ success: false, error: "Case ID is required." });
    }
    const data = await runForenxBridge("acquire_local", { case_id, profiles, investigator, notes });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List evidence packages for case
app.get("/api/cases/:id/packages", async (req, res) => {
  try {
    const data = await runForenxBridge("list_packages", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Import portable .forenx.zip package
app.post("/api/cases/:id/packages/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: "No package archive uploaded." });
    }
    const expected_sha256 = req.body.expected_sha256 || null;
    const data = await runForenxBridge("import_package", {
      case_id: req.params.id,
      package_path: req.file.path,
      expected_sha256
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List endpoints
app.get("/api/endpoints", async (_req, res) => {
  try {
    const data = await runForenxBridge("list_endpoints");
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Create enrollment token
app.post("/api/endpoints/token", async (req, res) => {
  try {
    const { device_label, operating_system, created_by } = req.body;
    const data = await runForenxBridge("create_enrollment_token", { device_label, operating_system, created_by });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Enroll endpoint using token
app.post("/api/endpoints/enroll", async (req, res) => {
  try {
    const { token, certificate_identity, ip_address } = req.body;
    const data = await runForenxBridge("enroll_endpoint", { token, certificate_identity, ip_address });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Revoke endpoint
app.post("/api/endpoints/:id/revoke", async (req, res) => {
  try {
    const data = await runForenxBridge("revoke_endpoint", { endpoint_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List acquisition jobs
app.get("/api/jobs", async (req, res) => {
  try {
    const data = await runForenxBridge("list_jobs", {
      case_id: req.query.case_id as string,
      endpoint_id: req.query.endpoint_id as string
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Create scoped acquisition job
app.post("/api/jobs", async (req, res) => {
  try {
    const { case_id, endpoint_id, investigator, scope, metadata } = req.body;
    const data = await runForenxBridge("create_job", {
      case_id,
      endpoint_id,
      investigator,
      scope,
      metadata
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Execute acquisition job
app.post("/api/jobs/:id/execute", async (req, res) => {
  try {
    const data = await runForenxBridge("execute_job", { job_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});
// Verify evidence SHA-256 integrity
app.post("/api/evidence/:id/verify", async (req, res) => {
  try {
    const data = await runForenxBridge("verify_evidence", { evidence_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Run analysis on case
app.post("/api/cases/:id/analyze", async (req, res) => {
  try {
    const data = await runForenxBridge("run_analysis", {
      case_id: req.params.id,
      evidence_id: req.body.evidence_id
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List analysis runs
app.get("/api/cases/:id/analysis-runs", async (req, res) => {
  try {
    const data = await runForenxBridge("list_analysis_runs", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Query unified timeline events
app.get("/api/cases/:id/timeline", async (req, res) => {
  try {
    const data = await runForenxBridge("list_events", {
      case_id: req.params.id,
      browser: req.query.browser as string,
      event_type: req.query.event_type as string,
      search: req.query.search as string,
      limit: parseInt(req.query.limit as string || "200", 10),
      offset: parseInt(req.query.offset as string || "0", 10)
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Run known-answer validation
app.post("/api/cases/:id/validate", async (req, res) => {
  try {
    const data = await runForenxBridge("run_validation", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// List validations
app.get("/api/cases/:id/validations", async (req, res) => {
  try {
    const data = await runForenxBridge("list_validations", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Get case reports (HTML, JSON, CSV)
app.get("/api/cases/:id/report", async (req, res) => {
  try {
    const data = await runForenxBridge("get_report_data", { case_id: req.params.id });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Get audit log
app.get("/api/audit", async (req, res) => {
  try {
    const data = await runForenxBridge("get_audit", {
      case_id: req.query.case_id as string,
      limit: parseInt(req.query.limit as string || "100", 10)
    });
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Seed synthetic demo
app.post("/api/demo/seed", async (_req, res) => {
  try {
    const data = await runForenxBridge("seed_demo");
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Settings & environment info
app.get("/api/settings", async (_req, res) => {
  try {
    const data = await runForenxBridge("settings");
    res.json({ success: true, data });
  } catch (err: any) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ----------------- VITE MIDDLEWARE SETUP -----------------
async function startServer() {
  if (process.env.NODE_ENV === "production") {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  } else {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: process.env.DISABLE_HMR === 'true' ? false : false,
        watch: process.env.DISABLE_HMR === 'true' ? null : {},
      },
      appType: "spa"
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`ForenX Forensic Workbench server running on port ${PORT}`);
  });
}

startServer().catch(err => {
  console.error("Failed to start ForenX server:", err);
  process.exit(1);
});
