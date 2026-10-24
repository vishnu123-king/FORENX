import React, { useState, useEffect } from "react";
import { Endpoint, EnrollmentToken } from "../../types/forenx";
import {
  Laptop,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Copy,
  Check,
  AlertTriangle,
  X,
  Terminal,
  Calendar,
  Lock,
  Wifi,
  WifiOff
} from "lucide-react";

export const EndpointsPage: React.FC = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [error, setError] = useState<string | null>(null);

  // Modal State for Generating Enrollment Token
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);
  const [tokenDeviceLabel, setTokenDeviceLabel] = useState("");
  const [tokenOS, setTokenOS] = useState("Windows");
  const [tokenInvestigator, setTokenInvestigator] = useState("Lead Investigator");
  const [generatedToken, setGeneratedToken] = useState<EnrollmentToken | null>(null);
  const [tokenGenerating, setTokenGenerating] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  // Revocation state
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const loadEndpoints = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/endpoints");
      const json = await res.json();
      if (json.success) {
        setEndpoints(json.data || []);
      } else {
        throw new Error(json.error || "Failed to load endpoints.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEndpoints();
  }, []);

  const handleCreateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenDeviceLabel.trim()) return;

    setTokenGenerating(true);
    setError(null);
    try {
      const res = await fetch("/api/endpoints/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_label: tokenDeviceLabel,
          operating_system: tokenOS,
          created_by: tokenInvestigator
        })
      });
      const json = await res.json();
      if (json.success) {
        setGeneratedToken(json.data);
      } else {
        throw new Error(json.error || "Failed to create enrollment token.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setTokenGenerating(false);
    }
  };

  const handleSimulateEnrollment = async (tokenStr: string) => {
    setLoading(true);
    try {
      const res = await fetch("/api/endpoints/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: tokenStr,
          certificate_identity: `SHA256-CERT-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
          ip_address: `192.168.1.${Math.floor(Math.random() * 200 + 10)}`
        })
      });
      const json = await res.json();
      if (json.success) {
        setIsTokenModalOpen(false);
        setGeneratedToken(null);
        setTokenDeviceLabel("");
        await loadEndpoints();
      } else {
        throw new Error(json.error || "Enrollment simulation failed.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (endpointId: string) => {
    if (!confirm("Are you sure you want to revoke this endpoint? Revoked endpoints cannot execute acquisition jobs.")) {
      return;
    }
    setRevokingId(endpointId);
    try {
      const res = await fetch(`/api/endpoints/${endpointId}/revoke`, { method: "POST" });
      const json = await res.json();
      if (json.success) {
        await loadEndpoints();
      } else {
        throw new Error(json.error || "Failed to revoke endpoint.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setRevokingId(null);
    }
  };

  const handleCopyToken = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2500);
  };

  const filteredEndpoints = endpoints.filter(ep => {
    const matchesSearch =
      ep.device_label.toLowerCase().includes(search.toLowerCase()) ||
      ep.ip_address.toLowerCase().includes(search.toLowerCase()) ||
      ep.id.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || ep.enrollment_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <Laptop size={14} className="text-[#D96A9B]" />
            <span>Endpoint Security &amp; Identity</span>
          </div>
          <h1 className="text-xl font-bold text-[#43206F] mt-0.5">Enrolled Forensic Endpoints</h1>
          <p className="text-xs text-[#746B80] mt-1 max-w-2xl">
            Authorize and manage client devices participating in remote browser forensics. Enforce mutual certificate identity, one-time enrollment, and instantaneous revocation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadEndpoints}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] transition-colors"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => {
              setGeneratedToken(null);
              setIsTokenModalOpen(true);
            }}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-xs"
          >
            <Plus size={15} />
            <span>Generate Enrollment Token</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl text-xs flex items-center gap-2">
          <AlertTriangle size={16} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#746B80]" />
          <input
            type="text"
            placeholder="Search by device label, IP, or ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#6D3FC0] text-[#282235]"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs font-semibold text-[#746B80]">Status:</span>
          <div className="flex rounded-lg border border-[#E8E0EF] p-0.5 bg-[#FAF7FE] text-xs">
            {["all", "active", "revoked", "offline"].map(st => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-md capitalize font-medium transition-colors ${
                  statusFilter === st
                    ? "bg-[#6D3FC0] text-white font-semibold shadow-xs"
                    : "text-[#746B80] hover:text-[#43206F]"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Endpoints Table */}
      <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs overflow-hidden">
        {filteredEndpoints.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#746B80] space-y-3">
            <Laptop size={40} className="mx-auto text-[#6D3FC0]/30" />
            <div className="font-bold text-sm text-[#43206F]">No Endpoints Found</div>
            <p className="max-w-md mx-auto">
              {search || statusFilter !== "all"
                ? "No enrolled endpoints match your filter criteria."
                : "No client devices have been enrolled yet. Generate a one-time enrollment token to connect your first machine."}
            </p>
            {!search && statusFilter === "all" && (
              <button
                onClick={() => {
                  setGeneratedToken(null);
                  setIsTokenModalOpen(true);
                }}
                className="mt-2 px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
              >
                Generate First Enrollment Token
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF7FE] border-b border-[#E8E0EF] text-[#746B80] font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-5 py-3">Device &amp; OS</th>
                  <th className="px-5 py-3">Endpoint ID</th>
                  <th className="px-5 py-3">Network &amp; Agent</th>
                  <th className="px-5 py-3">Identity / Fingerprint</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0EF]">
                {filteredEndpoints.map(ep => {
                  const isActive = ep.enrollment_status === "active";
                  const isRevoked = ep.enrollment_status === "revoked";
                  return (
                    <tr key={ep.id} className="hover:bg-[#FCFAFD] transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-9 h-9 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                              isActive
                                ? "bg-[#F2ECFA] text-[#6D3FC0]"
                                : "bg-gray-100 text-gray-500"
                            }`}
                          >
                            <Laptop size={18} />
                          </div>
                          <div>
                            <div className="font-bold text-sm text-[#43206F] flex items-center gap-1.5">
                              <span>{ep.device_label}</span>
                              <span className="text-[10px] font-semibold px-2 py-0.2 rounded bg-purple-50 text-[#6D3FC0] border border-[#E8E0EF]">
                                {ep.operating_system}
                              </span>
                            </div>
                            <div className="text-[11px] text-[#746B80] mt-0.5">
                              Enrolled: {new Date(ep.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-5 py-4 font-mono text-[11px] text-[#282235]">
                        <span title={ep.id}>{ep.id.slice(0, 14)}...</span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-mono text-[11px] text-[#282235] flex items-center gap-1.5">
                          {isActive ? (
                            <Wifi size={13} className="text-emerald-600" />
                          ) : (
                            <WifiOff size={13} className="text-gray-400" />
                          )}
                          <span>{ep.ip_address}</span>
                        </div>
                        <div className="text-[10px] text-[#746B80] mt-0.5">
                          Agent v{ep.agent_version} • Last seen {new Date(ep.last_seen).toLocaleTimeString()}
                        </div>
                      </td>

                      <td className="px-5 py-4 font-mono text-[11px] text-[#746B80]">
                        <div className="flex items-center gap-1 text-[10px] text-[#43206F]">
                          <Lock size={12} className="text-[#6D3FC0]" />
                          <span title={ep.certificate_identity}>
                            {ep.certificate_identity.slice(0, 16)}...
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase flex items-center gap-1 w-fit ${
                            isActive
                              ? "bg-emerald-100 text-emerald-800"
                              : isRevoked
                              ? "bg-rose-100 text-rose-800"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {isActive && <ShieldCheck size={12} />}
                          {isRevoked && <ShieldAlert size={12} />}
                          <span>{ep.enrollment_status}</span>
                        </span>
                        {ep.revocation_timestamp && (
                          <div className="text-[10px] text-rose-600 mt-1">
                            Revoked: {new Date(ep.revocation_timestamp).toLocaleDateString()}
                          </div>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        {isActive && (
                          <button
                            onClick={() => handleRevoke(ep.id)}
                            disabled={revokingId === ep.id}
                            className="px-3 py-1 text-xs font-semibold rounded-lg border border-rose-200 text-rose-700 hover:bg-rose-50 transition-colors disabled:opacity-50"
                          >
                            {revokingId === ep.id ? "Revoking..." : "Revoke"}
                          </button>
                        )}
                        {isRevoked && (
                          <span className="text-[11px] font-medium text-[#746B80] italic">
                            Revoked
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Generate Enrollment Token */}
      {isTokenModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#E8E0EF] space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-[#E8E0EF] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#F2ECFA] flex items-center justify-center text-[#6D3FC0]">
                  <Laptop size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#43206F]">Generate Enrollment Token</h3>
                  <p className="text-[11px] text-[#746B80]">Issue single-use token for remote client authorization</p>
                </div>
              </div>
              <button
                onClick={() => setIsTokenModalOpen(false)}
                className="text-[#746B80] hover:text-[#43206F] p-1 rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            {!generatedToken ? (
              <form onSubmit={handleCreateToken} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-[#282235] mb-1">
                    Client Device Label <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., HR-FINANCE-LAPTOP-04"
                    value={tokenDeviceLabel}
                    onChange={e => setTokenDeviceLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-semibold text-[#282235] mb-1">Operating System</label>
                    <select
                      value={tokenOS}
                      onChange={e => setTokenOS(e.target.value)}
                      className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                    >
                      <option value="Windows">Windows (10/11)</option>
                      <option value="Linux">Linux (Ubuntu/Debian)</option>
                      <option value="macOS">macOS</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#282235] mb-1">Requesting Investigator</label>
                    <input
                      type="text"
                      value={tokenInvestigator}
                      onChange={e => setTokenInvestigator(e.target.value)}
                      className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                    />
                  </div>
                </div>

                <div className="bg-[#FAF7FE] p-3 rounded-lg border border-[#E8E0EF] text-[11px] text-[#746B80] space-y-1">
                  <div className="font-semibold text-[#43206F]">Security Properties:</div>
                  <ul className="list-disc list-inside space-y-0.5 text-[10px]">
                    <li>Tokens expire in 60 minutes and can be used exactly once.</li>
                    <li>Credentials are bound to device OS and issued certificate identity.</li>
                    <li>Never transmits or allows arbitrary shell commands or scripts.</li>
                  </ul>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsTokenModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] text-[#746B80] hover:bg-[#FAF7FE]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={tokenGenerating || !tokenDeviceLabel.trim()}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50"
                  >
                    {tokenGenerating ? "Generating..." : "Generate Token"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4 text-xs">
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 p-3.5 rounded-xl flex items-start gap-2.5">
                  <ShieldCheck size={18} className="text-emerald-700 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-bold text-xs">One-Time Enrollment Token Generated</div>
                    <div className="text-[11px] text-emerald-800 mt-0.5">
                      Valid for 60 minutes. Use on target client to establish mutual certificate identity.
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider mb-1">
                    Raw Enrollment Token
                  </div>
                  <div className="flex items-center gap-2 bg-[#FAF7FE] p-2.5 rounded-lg border border-[#E8E0EF] font-mono text-[11px] text-[#282235]">
                    <span className="flex-1 select-all break-all">{generatedToken.token}</span>
                    <button
                      onClick={() => handleCopyToken(generatedToken.token)}
                      className="p-1.5 text-[#6D3FC0] hover:bg-[#F2ECFA] rounded-md shrink-0"
                      title="Copy Token"
                    >
                      {copiedToken ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                    </button>
                  </div>
                </div>

                <div>
                  <div className="text-[11px] font-semibold text-[#746B80] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <Terminal size={12} className="text-[#6D3FC0]" />
                    <span>Client Enrollment Command</span>
                  </div>
                  <div className="bg-slate-900 text-slate-100 p-3 rounded-lg font-mono text-[10px] space-y-1 overflow-x-auto select-all">
                    <div>python -m forenx.agent.field_collector enroll \</div>
                    <div className="pl-4">--server http://forenx-workbench.local:3000 \</div>
                    <div className="pl-4">--token {generatedToken.token}</div>
                  </div>
                </div>

                <div className="border-t border-[#E8E0EF] pt-4 flex items-center justify-between">
                  <button
                    onClick={() => handleSimulateEnrollment(generatedToken.token)}
                    className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-xs"
                    title="Simulate client endpoint enrolling right now"
                  >
                    Simulate Client Enrollment
                  </button>

                  <button
                    onClick={() => {
                      setIsTokenModalOpen(false);
                      setGeneratedToken(null);
                      setTokenDeviceLabel("");
                      loadEndpoints();
                    }}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
