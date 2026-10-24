import React, { useState, useEffect } from "react";
import { Case, DiscoveredProfile } from "../../types/forenx";
import {
  HardDrive,
  Search,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  Play,
  FileCode2,
  Lock,
  ArrowRight
} from "lucide-react";

interface LocalForensicsPageProps {
  activeCase: Case | null;
  onAcquisitionComplete: () => void;
  onNavigateToTimeline: () => void;
}

export const LocalForensicsPage: React.FC<LocalForensicsPageProps> = ({
  activeCase,
  onAcquisitionComplete,
  onNavigateToTimeline
}) => {
  const [profiles, setProfiles] = useState<DiscoveredProfile[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [acquiring, setAcquiring] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [acquisitionResult, setAcquisitionResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDiscover = async () => {
    setLoading(true);
    setError(null);
    setAcquisitionResult(null);
    try {
      const res = await fetch("/api/discovery/local");
      const json = await res.json();
      if (json.success) {
        setProfiles(json.data || []);
        // Select all by default
        setSelectedIds(new Set((json.data || []).map((p: any) => p.profile_id)));
      } else {
        throw new Error(json.error || "Failed to discover local browser profiles.");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleDiscover();
  }, []);

  const toggleSelect = (profileId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(profileId)) {
        next.delete(profileId);
      } else {
        next.add(profileId);
      }
      return next;
    });
  };

  const handleAcquire = async () => {
    if (!activeCase) {
      setError("Please select an active case first.");
      return;
    }
    if (!authorized) {
      setError("Investigator authorization is required prior to acquiring evidence.");
      return;
    }

    const approvedProfiles = profiles.filter(p => selectedIds.has(p.profile_id));
    if (approvedProfiles.length === 0) {
      setError("Select at least one discovered browser profile to acquire.");
      return;
    }

    setAcquiring(true);
    setError(null);

    try {
      const res = await fetch("/api/acquisition/local", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: activeCase.id,
          profiles: approvedProfiles.map(p => ({
            browser_name: p.browser_name,
            browser_family: p.browser_family,
            profile_label: p.profile_label,
            artifacts: p.available_artifacts
          })),
          investigator: activeCase.investigator_label || "Lead Examiner",
          notes: `Authorized local acquisition for case ${activeCase.id}`
        })
      });

      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Local acquisition failed.");
      }

      setAcquisitionResult(json.data);
      onAcquisitionComplete();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAcquiring(false);
    }
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <HardDrive size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">Select an investigation case from the sidebar before initiating local evidence collection.</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <HardDrive size={15} />
            <span>Mode A — Local System Forensics</span>
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            Local Browser Discovery &amp; Controlled Acquisition
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5">
            Discovers Chrome, Edge, Brave, and Firefox profiles on this machine. Acquires allowlisted artifacts into a verifiable <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">.forenx.zip</code> package with online SQLite backups and WAL sidecars.
          </p>
        </div>

        <button
          onClick={handleDiscover}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] disabled:opacity-50 shrink-0"
        >
          <Search size={14} className={loading ? "animate-spin" : ""} />
          <span>{loading ? "Discovering..." : "Scan Local Profiles"}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 font-medium flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Acquisition Result Box */}
      {acquisitionResult && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 space-y-3 animate-in fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-emerald-700" />
              <h3 className="font-bold text-sm text-emerald-900">
                Acquisition &amp; Evidence Ingestion Completed Successfully!
              </h3>
            </div>
            <button
              onClick={onNavigateToTimeline}
              className="flex items-center gap-1 text-xs font-bold text-[#6D3FC0] bg-white px-3 py-1 rounded-md border border-emerald-200 hover:bg-[#FAF7FE]"
            >
              <span>View Timeline</span>
              <ArrowRight size={13} />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-white p-2.5 rounded border border-emerald-100">
              <span className="text-[#746B80] block text-[10px] uppercase">Package Generated</span>
              <span className="font-mono font-bold text-[#43206F] truncate block">{acquisitionResult.package_filename}</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-emerald-100">
              <span className="text-[#746B80] block text-[10px] uppercase">Artifacts Acquired</span>
              <span className="font-bold text-emerald-800 text-sm">{acquisitionResult.artifacts_collected}</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-emerald-100">
              <span className="text-[#746B80] block text-[10px] uppercase">Events Extracted</span>
              <span className="font-bold text-[#43206F] text-sm">{acquisitionResult.events_extracted}</span>
            </div>
            <div className="bg-white p-2.5 rounded border border-emerald-100">
              <span className="text-[#746B80] block text-[10px] uppercase">Integrity Status</span>
              <span className="font-bold text-emerald-800 uppercase text-[11px]">{acquisitionResult.verification_status}</span>
            </div>
          </div>

          <div className="text-[11px] font-mono text-[#746B80] break-all bg-white p-2 rounded border border-emerald-100">
            Outer Package SHA-256: <strong>{acquisitionResult.package_sha256}</strong>
          </div>
        </div>
      )}

      {/* Discovered Profiles Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#43206F]">
            Discovered Local Profiles ({profiles.length})
          </h3>
          <span className="text-xs text-[#746B80]">
            {selectedIds.size} of {profiles.length} selected for acquisition
          </span>
        </div>

        {profiles.length === 0 ? (
          <div className="bg-white rounded-xl border border-[#E8E0EF] p-12 text-center text-xs text-[#746B80]">
            No supported browser profiles found in standard user paths on this system. Click "Scan Local Profiles" or use Mode B for remote endpoints.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profiles.map(p => {
              const isSelected = selectedIds.has(p.profile_id);
              return (
                <div
                  key={p.profile_id}
                  onClick={() => toggleSelect(p.profile_id)}
                  className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${
                    isSelected
                      ? "border-[#6D3FC0] ring-1 ring-[#6D3FC0]/30 shadow-xs"
                      : "border-[#E8E0EF] opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
                      />
                      <span className="font-bold text-sm text-[#43206F]">{p.profile_label}</span>
                    </div>
                    <span className="text-[10px] font-semibold text-[#6D3FC0] bg-[#F2ECFA] px-2 py-0.5 rounded-full">
                      {p.browser_family}
                    </span>
                  </div>

                  <div className="text-[11px] font-mono text-[#746B80] truncate mb-3">
                    {p.profile_path}
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-[#E8E0EF]">
                    <span className="text-[10px] font-bold text-[#746B80] uppercase tracking-wider block">
                      Allowlisted Artifacts Found:
                    </span>
                    {p.available_artifacts.map((art, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs bg-[#FAF7FE] p-1.5 rounded">
                        <span className="font-semibold text-[#282235]">{art.artifact_type}</span>
                        <div className="flex items-center gap-2 text-[11px] text-[#746B80]">
                          <span>{(art.byte_size / 1024).toFixed(1)} KB</span>
                          {art.has_wal && (
                            <span className="text-[9px] bg-purple-100 text-purple-800 font-bold px-1 rounded">
                              +WAL
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Scope Authorization & Acquisition Trigger */}
      {profiles.length > 0 && (
        <div className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs space-y-4">
          <div className="flex items-start gap-3">
            <Lock size={18} className="text-[#6D3FC0] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="font-bold text-xs text-[#43206F] uppercase tracking-wider">
                Forensic Collection Authorization
              </h4>
              <p className="text-xs text-[#746B80] leading-relaxed">
                Collection is restricted to allowlisted browser artifacts (<code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">History</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">Bookmarks</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">places.sqlite</code>). Passwords, cookies, autofill, and session tokens are strictly excluded.
              </p>
            </div>
          </div>

          <label className="flex items-center gap-2 text-xs font-semibold text-[#282235] cursor-pointer p-3 bg-[#FAF7FE] rounded-lg border border-[#E8E0EF]">
            <input
              type="checkbox"
              checked={authorized}
              onChange={e => setAuthorized(e.target.checked)}
              className="rounded text-[#6D3FC0] focus:ring-[#6D3FC0]"
            />
            <span>I confirm authorization to acquire browser artifacts from the selected local profiles for case {activeCase.name} ({activeCase.id}).</span>
          </label>

          <div className="flex justify-end">
            <button
              onClick={handleAcquire}
              disabled={acquiring || !authorized || selectedIds.size === 0}
              className="flex items-center gap-2 px-6 py-2.5 text-xs font-bold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm disabled:opacity-50"
            >
              <Play size={15} className={acquiring ? "animate-spin" : ""} />
              <span>{acquiring ? "Acquiring & Analyzing..." : "Acquire & Analyze Selected Artifacts"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
