import React, { useState, useEffect } from "react";
import { Case, Endpoint, AcquisitionJob } from "../../types/forenx";
import {
  Briefcase,
  Plus,
  RefreshCw,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Play,
  FileCode,
  ShieldCheck,
  X,
  Lock,
  ChevronRight,
  ExternalLink,
  Laptop
} from "lucide-react";

interface CollectionJobsPageProps {
  activeCase: Case | null;
  onNavigateToTimeline?: () => void;
  onNavigateToVault?: () => void;
}

export const CollectionJobsPage: React.FC<CollectionJobsPageProps> = ({
  activeCase,
  onNavigateToTimeline,
  onNavigateToVault
}) => {
  const [jobs, setJobs] = useState<AcquisitionJob[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [executingJobId, setExecutingJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<AcquisitionJob | null>(null);

  // New Scoped Job Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedEndpointId, setSelectedEndpointId] = useState<string>("");
  const [investigatorLabel, setInvestigatorLabel] = useState("Lead Investigator");
  const [incidentRef, setIncidentRef] = useState("INC-2026-0042");
  const [allowChromeHistory, setAllowChromeHistory] = useState(true);
  const [allowChromeBookmarks, setAllowChromeBookmarks] = useState(true);
  const [allowFirefoxPlaces, setAllowFirefoxPlaces] = useState(true);
  const [preserveWal, setPreserveWal] = useState(true);
  const [creatingJob, setCreatingJob] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = activeCase ? `/api/jobs?case_id=${activeCase.id}` : "/api/jobs";
      const [jobRes, epRes] = await Promise.all([
        fetch(url),
        fetch("/api/endpoints")
      ]);
      const jobJson = await jobRes.json();
      const epJson = await epRes.json();

      if (jobJson.success) setJobs(jobJson.data || []);
      if (epJson.success) {
        setEndpoints(epJson.data || []);
        const active = (epJson.data || []).filter((e: Endpoint) => e.enrollment_status === "active");
        if (active.length > 0 && !selectedEndpointId) {
          setSelectedEndpointId(active[0].id);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeCase]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCase) {
      setError("Please select an active case first.");
      return;
    }
    if (!selectedEndpointId) {
      setError("Select an enrolled target endpoint.");
      return;
    }

    const approvedBrowsers: string[] = [];
    const approvedArtifacts: string[] = [];
    if (allowChromeHistory) {
      approvedBrowsers.push("Google Chrome", "Microsoft Edge", "Brave", "Chromium");
      approvedArtifacts.push("History");
    }
    if (allowChromeBookmarks) {
      if (!approvedBrowsers.includes("Google Chrome")) approvedBrowsers.push("Google Chrome");
      approvedArtifacts.push("Bookmarks");
    }
    if (allowFirefoxPlaces) {
      approvedBrowsers.push("Mozilla Firefox");
      approvedArtifacts.push("places.sqlite");
    }

    setCreatingJob(true);
    setError(null);
    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: activeCase.id,
          endpoint_id: selectedEndpointId,
          investigator: investigatorLabel,
          scope: {
            approved_browsers: Array.from(new Set(approvedBrowsers)),
            approved_artifact_types: approvedArtifacts,
            allow_wal_sidecars: preserveWal,
            max_package_size_mb: 250
          },
          metadata: {
            warrant_or_incident_id: incidentRef,
            investigator_signature_label: investigatorLabel,
            scope_summary: `Scoped extraction of ${approvedArtifacts.join(", ")} on authorized endpoint.`
          }
        })
      });

      const json = await res.json();
      if (json.success) {
        setIsModalOpen(false);
        await loadData();
      } else {
        throw new Error(json.error || "Failed to create acquisition job.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreatingJob(false);
    }
  };

  const handleExecuteJob = async (jobId: string) => {
    setExecutingJobId(jobId);
    setError(null);
    try {
      const res = await fetch(`/api/jobs/${jobId}/execute`, { method: "POST" });
      const json = await res.json();
      if (json.success) {
        await loadData();
      } else {
        throw new Error(json.error || "Failed to execute acquisition job.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setExecutingJobId(null);
    }
  };

  const getEndpointLabel = (epId: string) => {
    const ep = endpoints.find(e => e.id === epId);
    return ep ? `${ep.device_label} (${ep.operating_system})` : epId.slice(0, 12);
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <Briefcase size={14} className="text-[#D96A9B]" />
            <span>Scoped Remote Acquisitions</span>
          </div>
          <h1 className="text-xl font-bold text-[#43206F] mt-0.5">Collection Jobs Queue</h1>
          <p className="text-xs text-[#746B80] mt-1 max-w-2xl">
            Strict, schema-validated jobs dispatched to remote endpoints. All jobs are cryptographically nonced, strictly scoped to allowlisted browser artifacts, and protected against command injection.
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
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-xs"
          >
            <Plus size={15} />
            <span>Create Scoped Job</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Security Scope Banner */}
      <div className="bg-[#FAF7FE] border border-[#E8E0EF] p-4 rounded-xl flex items-start gap-3 text-xs">
        <ShieldCheck size={18} className="text-[#6D3FC0] shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <div className="font-bold text-[#43206F]">Schema-Enforced Forensic Scope Guarantee</div>
          <p className="text-[#746B80] leading-relaxed">
            Per <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[10px]">schemas/acquisition-job.schema.json</code>, jobs strictly permit read-only acquisition of Chromium History, Bookmarks, and Firefox places.sqlite. Execution of arbitrary shell scripts, credential databases, passwords, and cookies is strictly blocked at the protocol level.
          </p>
        </div>
      </div>

      {/* Jobs List */}
      <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs overflow-hidden">
        {jobs.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#746B80] space-y-3">
            <Briefcase size={40} className="mx-auto text-[#6D3FC0]/30" />
            <div className="font-bold text-sm text-[#43206F]">No Collection Jobs Yet</div>
            <p className="max-w-md mx-auto">
              Create a scoped collection job to authorize and collect browser evidence from an enrolled remote endpoint.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-2 px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
            >
              Dispatch First Job
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF7FE] border-b border-[#E8E0EF] text-[#746B80] font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">Job ID &amp; Target Endpoint</th>
                  <th className="px-5 py-3">Case ID</th>
                  <th className="px-5 py-3">Requester &amp; Ref</th>
                  <th className="px-5 py-3">Scope Allowlist</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0EF]">
                {jobs.map(job => {
                  const isCompleted = job.status === "completed";
                  const isPending = job.status === "created" || job.status === "pending" || job.status === "approved";
                  const isExecuting = executingJobId === job.id;

                  return (
                    <tr key={job.id} className="hover:bg-[#FCFAFD] transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-bold text-sm text-[#43206F] font-mono">
                          {job.id}
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-[#746B80] mt-0.5">
                          <Laptop size={12} className="text-[#6D3FC0]" />
                          <span className="font-medium text-[#282235]">
                            {getEndpointLabel(job.endpoint_id)}
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 font-mono text-[11px] text-[#282235]">
                        <span title={job.case_id}>{job.case_id.slice(0, 10)}...</span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-semibold text-[#282235]">{job.requesting_investigator_id}</div>
                        <div className="text-[10px] text-[#746B80] font-mono mt-0.5">
                          {job.authorization_metadata?.warrant_or_incident_id || "Direct Authorization"}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {(job.authorized_scope?.approved_artifact_types || []).map((art, idx) => (
                            <span
                              key={idx}
                              className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F2ECFA] text-[#6D3FC0]"
                            >
                              {art}
                            </span>
                          ))}
                        </div>
                        <div className="text-[10px] text-[#746B80] mt-1">
                          Nonce: <span className="font-mono">{job.replay_nonce?.slice(0, 8)}...</span>
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase flex items-center gap-1 w-fit ${
                            isCompleted
                              ? "bg-emerald-100 text-emerald-800"
                              : isPending
                              ? "bg-amber-100 text-amber-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {isCompleted ? <CheckCircle2 size={12} /> : <Clock size={12} />}
                          <span>{job.status}</span>
                        </span>
                        {job.package_id && (
                          <div className="text-[10px] text-[#6D3FC0] font-mono mt-1 font-semibold">
                            Pkg: {job.package_id.slice(0, 12)}...
                          </div>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isPending && (
                            <button
                              onClick={() => handleExecuteJob(job.id)}
                              disabled={isExecuting}
                              className="flex items-center gap-1 px-3 py-1 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50 shadow-xs"
                            >
                              <Play size={12} className={isExecuting ? "animate-spin" : ""} />
                              <span>{isExecuting ? "Executing..." : "Execute Job"}</span>
                            </button>
                          )}

                          <button
                            onClick={() => setSelectedJob(job)}
                            className="px-2.5 py-1 text-xs font-medium rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE]"
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Create Scoped Job */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#E8E0EF] space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-[#E8E0EF] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#F2ECFA] flex items-center justify-center text-[#6D3FC0]">
                  <Briefcase size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#43206F]">Dispatch Scoped Acquisition Job</h3>
                  <p className="text-[11px] text-[#746B80]">Define authorized artifacts for remote collection</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-[#746B80] hover:text-[#43206F] p-1 rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateJob} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#282235] mb-1">
                  Target Endpoint <span className="text-rose-500">*</span>
                </label>
                {endpoints.filter(e => e.enrollment_status === "active").length === 0 ? (
                  <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg text-xs">
                    No active endpoints available. Please enroll an endpoint first.
                  </div>
                ) : (
                  <select
                    value={selectedEndpointId}
                    onChange={e => setSelectedEndpointId(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                  >
                    {endpoints
                      .filter(e => e.enrollment_status === "active")
                      .map(ep => (
                        <option key={ep.id} value={ep.id}>
                          {ep.device_label} ({ep.operating_system} - {ep.ip_address})
                        </option>
                      ))}
                  </select>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#282235] mb-1">Warrant / Incident Ref</label>
                  <input
                    type="text"
                    value={incidentRef}
                    onChange={e => setIncidentRef(e.target.value)}
                    placeholder="e.g. INC-2026-0042"
                    className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#282235] mb-1">Investigator Signature</label>
                  <input
                    type="text"
                    value={investigatorLabel}
                    onChange={e => setInvestigatorLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#282235] mb-1.5">
                  Authorized Artifact Allowlist
                </label>
                <div className="space-y-2 bg-[#FAF7FE] p-3 rounded-lg border border-[#E8E0EF]">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowChromeHistory}
                      onChange={e => setAllowChromeHistory(e.target.checked)}
                      className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
                    />
                    <span className="font-semibold text-[#282235]">Chromium Family: History database</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowChromeBookmarks}
                      onChange={e => setAllowChromeBookmarks(e.target.checked)}
                      className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
                    />
                    <span className="font-semibold text-[#282235]">Chromium Family: Bookmarks JSON</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowFirefoxPlaces}
                      onChange={e => setAllowFirefoxPlaces(e.target.checked)}
                      className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
                    />
                    <span className="font-semibold text-[#282235]">Firefox: places.sqlite database</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer pt-1 border-t border-[#E8E0EF]">
                    <input
                      type="checkbox"
                      checked={preserveWal}
                      onChange={e => setPreserveWal(e.target.checked)}
                      className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
                    />
                    <span className="text-[#746B80]">Preserve SQLite Write-Ahead Logging sidecars (-wal, -shm)</span>
                  </label>
                </div>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 p-2.5 rounded-lg text-[10px] text-emerald-900 flex items-start gap-2">
                <ShieldCheck size={14} className="text-emerald-700 shrink-0 mt-0.5" />
                <span>
                  Anti-Exfiltration Policy: Passwords, cookies, session tokens, and remote scripts are strictly prohibited.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#E8E0EF]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] text-[#746B80] hover:bg-[#FAF7FE]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingJob || !selectedEndpointId}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50"
                >
                  {creatingJob ? "Creating..." : "Dispatch Job"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Job Details Inspector */}
      {selectedJob && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-[#E8E0EF] space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-[#E8E0EF] pb-3">
              <div>
                <h3 className="text-sm font-bold text-[#43206F]">Acquisition Job Details</h3>
                <p className="text-[11px] font-mono text-[#746B80]">{selectedJob.id}</p>
              </div>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-[#746B80] hover:text-[#43206F] p-1 rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-3 bg-[#FAF7FE] p-3 rounded-xl border border-[#E8E0EF]">
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Status</div>
                  <div className="font-bold text-[#43206F] capitalize">{selectedJob.status}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Replay Nonce</div>
                  <div className="font-mono text-[11px] text-[#282235]">{selectedJob.replay_nonce}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Created</div>
                  <div className="text-[#282235]">{new Date(selectedJob.created_at).toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Outcome</div>
                  <div className="text-[#282235]">{selectedJob.outcome_summary || "Pending execution"}</div>
                </div>
              </div>

              <div>
                <div className="text-[11px] font-bold text-[#43206F] mb-1">Job Authorization Payload (JSON)</div>
                <pre className="bg-slate-900 text-slate-100 p-3 rounded-xl text-[10px] font-mono overflow-x-auto">
                  {JSON.stringify(selectedJob, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#E8E0EF]">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
