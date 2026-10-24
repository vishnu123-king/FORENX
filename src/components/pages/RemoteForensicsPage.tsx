import React, { useState, useEffect } from "react";
import { Case, Endpoint, AcquisitionJob } from "../../types/forenx";
import {
  Radio,
  Laptop,
  Briefcase,
  ShieldCheck,
  Plus,
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Terminal,
  ArrowRight,
  UploadCloud
} from "lucide-react";

interface RemoteForensicsPageProps {
  activeCase: Case | null;
  onNavigate: (page: any) => void;
  onOpenUploadPackage?: () => void;
}

export const RemoteForensicsPage: React.FC<RemoteForensicsPageProps> = ({
  activeCase,
  onNavigate,
  onOpenUploadPackage
}) => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [jobs, setJobs] = useState<AcquisitionJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [epRes, jobRes] = await Promise.all([
        fetch("/api/endpoints"),
        fetch(activeCase ? `/api/jobs?case_id=${activeCase.id}` : "/api/jobs")
      ]);
      const epJson = await epRes.json();
      const jobJson = await jobRes.json();

      if (epJson.success) setEndpoints(epJson.data || []);
      if (jobJson.success) setJobs(jobJson.data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load remote forensics data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeCase]);

  const activeEndpoints = endpoints.filter(e => e.enrollment_status === "active");
  const pendingJobs = jobs.filter(j => j.status === "created" || j.status === "pending" || j.status === "approved");
  const completedJobs = jobs.filter(j => j.status === "completed");

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <Radio size={14} className="text-[#D96A9B]" />
            <span>Mode B — Remote System Forensics</span>
          </div>
          <h1 className="text-xl font-bold text-[#43206F] mt-0.5">
            Remote Endpoint Orchestration &amp; Scoped Collection
          </h1>
          <p className="text-xs text-[#746B80] mt-1 max-w-2xl">
            Examine remote client machines via authorized, scoped collection jobs. Supports both connected agent telemetry and portable offline Field Collector evidence packages.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] transition-colors"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigate("Endpoints")}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-xs"
          >
            <Laptop size={14} />
            <span>Manage Endpoints</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg bg-[#F2ECFA] flex items-center justify-center text-[#6D3FC0] shrink-0">
            <Laptop size={22} />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider">Active Endpoints</div>
            <div className="text-2xl font-bold text-[#43206F]">{activeEndpoints.length}</div>
            <div className="text-[10px] text-[#746B80] mt-0.5">{endpoints.length} total enrolled</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg bg-[#FCEAF2] flex items-center justify-center text-[#D96A9B] shrink-0">
            <Briefcase size={22} />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider">Pending Jobs</div>
            <div className="text-2xl font-bold text-[#43206F]">{pendingJobs.length}</div>
            <div className="text-[10px] text-[#746B80] mt-0.5">Awaiting agent acquisition</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
            <CheckCircle2 size={22} />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider">Completed Jobs</div>
            <div className="text-2xl font-bold text-[#43206F]">{completedJobs.length}</div>
            <div className="text-[10px] text-[#746B80] mt-0.5">Packaged and verified</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs flex items-center gap-4">
          <div className="w-11 h-11 rounded-lg bg-purple-50 flex items-center justify-center text-[#6D3FC0] shrink-0">
            <ShieldCheck size={22} />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider">Security Policy</div>
            <div className="text-xs font-bold text-emerald-700 mt-1">Strict Allowlist</div>
            <div className="text-[10px] text-[#746B80] mt-0.5">Zero Shell / No Secrets</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Architecture & Scoped Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Workflow Guide & Security Guarantees */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-[#43206F] flex items-center gap-2">
              <Radio size={16} className="text-[#6D3FC0]" />
              <span>Remote Collection Workflow</span>
            </h2>

            <div className="space-y-3 text-xs">
              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#F2ECFA] text-[#6D3FC0] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  1
                </span>
                <div>
                  <div className="font-semibold text-[#282235]">Enroll Authorized Endpoint</div>
                  <div className="text-[#746B80] text-[11px] mt-0.5">
                    Generate a one-time token bound to device OS and organization identity.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#F2ECFA] text-[#6D3FC0] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  2
                </span>
                <div>
                  <div className="font-semibold text-[#282235]">Define Scoped Job</div>
                  <div className="text-[#746B80] text-[11px] mt-0.5">
                    Select allowlisted browser artifacts (Chrome History, Firefox Places). No shell commands or arbitrary execution allowed.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#F2ECFA] text-[#6D3FC0] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  3
                </span>
                <div>
                  <div className="font-semibold text-[#282235]">Acquire &amp; Package</div>
                  <div className="text-[#746B80] text-[11px] mt-0.5">
                    Agent performs read-only logical SQLite backup, calculates dual SHA-256 hashes, and builds standard <code className="font-mono text-[10px]">FX-ACQ-*.forenx.zip</code>.
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#F2ECFA] text-[#6D3FC0] font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                  4
                </span>
                <div>
                  <div className="font-semibold text-[#282235]">Workbench Verification</div>
                  <div className="text-[#746B80] text-[11px] mt-0.5">
                    Workbench verifies outer zip hash, individual artifact hashes, inspects manifest, and parses normalized events into the timeline.
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-[#E8E0EF] space-y-2">
              <button
                onClick={() => onNavigate("Collection Jobs")}
                className="w-full flex items-center justify-center gap-1.5 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors"
              >
                <span>Dispatch Collection Job</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Offline Field Collector Panel */}
          <div className="bg-[#FAF7FE] p-5 rounded-xl border border-[#E8E0EF] shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#43206F]">
              <Terminal size={16} className="text-[#6D3FC0]" />
              <span>Offline Field Collector</span>
            </div>
            <p className="text-[11px] text-[#746B80] leading-relaxed">
              For air-gapped or offline client laptops, run the standalone <code className="font-mono font-bold text-[#6D3FC0]">forenx-collector</code> CLI directly. It generates the identical standard <code className="font-mono text-[10px]">.forenx.zip</code> package for manual import.
            </p>
            <div className="bg-white p-2.5 rounded-lg border border-[#E8E0EF] font-mono text-[10px] text-[#282235] select-all overflow-x-auto">
              python -m forenx.agent.field_collector --case {activeCase?.id.slice(0, 8) || "CASE-001"} --output /media/usb/FX-ACQ.forenx.zip
            </div>
            <button
              onClick={() => onNavigate("Evidence Vault")}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] transition-colors"
            >
              <UploadCloud size={14} className="text-[#6D3FC0]" />
              <span>Import Offline Package</span>
            </button>
          </div>
        </div>

        {/* Right Column: Recent Remote Activity & Endpoint Status */}
        <div className="lg:col-span-2 space-y-6">
          {/* Enrolled Endpoints Card */}
          <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-[#43206F]">Enrolled Forensic Endpoints</h2>
                <p className="text-xs text-[#746B80]">Client workstations authorized for scoped collection</p>
              </div>
              <button
                onClick={() => onNavigate("Endpoints")}
                className="text-xs font-semibold text-[#6D3FC0] hover:text-[#43206F] flex items-center gap-1"
              >
                <span>View All ({endpoints.length})</span>
                <ArrowRight size={13} />
              </button>
            </div>

            {endpoints.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#746B80] border border-dashed border-[#E8E0EF] rounded-lg">
                <Laptop size={32} className="mx-auto text-[#6D3FC0]/30 mb-2" />
                <div className="font-semibold text-[#43206F]">No endpoints enrolled yet</div>
                <div className="text-[11px] mt-0.5">Generate an enrollment token to authorize client devices.</div>
                <button
                  onClick={() => onNavigate("Endpoints")}
                  className="mt-3 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
                >
                  Enroll First Device
                </button>
              </div>
            ) : (
              <div className="divide-y divide-[#E8E0EF]">
                {endpoints.slice(0, 4).map(ep => (
                  <div key={ep.id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#F2ECFA] flex items-center justify-center text-[#6D3FC0] shrink-0 font-mono text-[10px] font-bold">
                        {ep.operating_system.slice(0, 3).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-bold text-[#282235] flex items-center gap-2">
                          <span>{ep.device_label}</span>
                          <span className="font-mono text-[10px] text-[#746B80] bg-[#FAF7FE] px-1.5 py-0.2 rounded border border-[#E8E0EF]">
                            {ep.ip_address}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#746B80] mt-0.5">
                          ID: <span className="font-mono">{ep.id.slice(0, 10)}...</span> • Agent v{ep.agent_version} • Last seen: {new Date(ep.last_seen).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                          ep.enrollment_status === "active"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {ep.enrollment_status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Collection Jobs Card */}
          <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-[#43206F]">Scoped Collection Jobs</h2>
                <p className="text-xs text-[#746B80]">Execution state of remote artifact collection tasks</p>
              </div>
              <button
                onClick={() => onNavigate("Collection Jobs")}
                className="text-xs font-semibold text-[#6D3FC0] hover:text-[#43206F] flex items-center gap-1"
              >
                <span>View All ({jobs.length})</span>
                <ArrowRight size={13} />
              </button>
            </div>

            {jobs.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#746B80] border border-dashed border-[#E8E0EF] rounded-lg">
                <Briefcase size={32} className="mx-auto text-[#6D3FC0]/30 mb-2" />
                <div className="font-semibold text-[#43206F]">No collection jobs dispatched yet</div>
                <div className="text-[11px] mt-0.5">Jobs allow investigators to define explicit, allowlisted collection scopes.</div>
                <button
                  onClick={() => onNavigate("Collection Jobs")}
                  className="mt-3 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
                >
                  Create Collection Job
                </button>
              </div>
            ) : (
              <div className="divide-y divide-[#E8E0EF]">
                {jobs.slice(0, 5).map(job => (
                  <div key={job.id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <div className="font-bold text-[#282235] flex items-center gap-2">
                        <span className="font-mono text-[#43206F]">{job.id.slice(0, 14)}...</span>
                        <span
                          className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                            job.status === "completed"
                              ? "bg-emerald-100 text-emerald-800"
                              : job.status === "pending" || job.status === "created"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {job.status}
                        </span>
                      </div>
                      <div className="text-[11px] text-[#746B80] mt-0.5">
                        Endpoint: <span className="font-mono">{job.endpoint_id.slice(0, 10)}...</span> • Requester: {job.requesting_investigator_id} • Created: {new Date(job.created_at).toLocaleTimeString()}
                      </div>
                      {job.outcome_summary && (
                        <div className="text-[11px] text-[#6D3FC0] mt-0.5 font-medium">
                          {job.outcome_summary}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => onNavigate("Collection Jobs")}
                      className="px-2.5 py-1 text-[11px] font-semibold rounded-md border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE]"
                    >
                      Inspect
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
