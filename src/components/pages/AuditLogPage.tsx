import React, { useState, useEffect } from "react";
import { AuditEntry } from "../../types/forenx";
import { ScrollText, ShieldCheck, AlertTriangle, Lock, RefreshCw } from "lucide-react";

export const AuditLogPage: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [isChainIntact, setIsChainIntact] = useState(true);
  const [chainErrors, setChainErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/audit?limit=150");
      const json = await res.json();
      if (json.success) {
        setEntries(json.data.entries || []);
        setIsChainIntact(json.data.chain_intact);
        setChainErrors(json.data.chain_errors || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
  }, []);

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Cryptographic Status */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <Lock size={14} />
            <span>Cryptographic Chain of Custody</span>
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            Tamper-Evident Forensic Audit Log
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5">
            Every forensic action (case initialization, evidence acquisition, hash calculation, parsing, and report generation) is recorded into a SHA-256 hash-chained log.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`px-3.5 py-2 rounded-lg text-xs font-bold flex items-center gap-2 border ${
              isChainIntact
                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                : "bg-rose-50 text-rose-800 border-rose-200"
            }`}
          >
            {isChainIntact ? <ShieldCheck size={16} /> : <AlertTriangle size={16} />}
            <span>{isChainIntact ? "CHAIN INTACT (VERIFIED)" : "TAMPER DETECTED"}</span>
          </div>

          <button
            onClick={fetchAudit}
            className="p-2 text-[#746B80] hover:text-[#43206F] rounded-lg border border-[#E8E0EF]"
            title="Refresh audit log"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {chainErrors.length > 0 && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-900 space-y-1">
          <div className="font-bold flex items-center gap-1.5 text-rose-800">
            <AlertTriangle size={15} />
            <span>Cryptographic Verification Failures Detected:</span>
          </div>
          {chainErrors.map((err, idx) => (
            <div key={idx} className="font-mono text-[11px]">• {err}</div>
          ))}
        </div>
      )}

      {/* Audit Entries Table */}
      <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-[#FAF7FE] text-[#746B80] border-b border-[#E8E0EF]">
                <th className="p-3 font-semibold">Timestamp (UTC)</th>
                <th className="p-3 font-semibold">Operation</th>
                <th className="p-3 font-semibold">Case Context</th>
                <th className="p-3 font-semibold">Outcome</th>
                <th className="p-3 font-semibold">Operation Details</th>
                <th className="p-3 font-semibold">Block Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E8E0EF]">
              {entries.map(entry => (
                <tr key={entry.id} className="hover:bg-[#FAF7FE]">
                  <td className="p-3 font-mono text-[11px] text-[#282235] whitespace-nowrap">
                    {entry.timestamp_utc.replace("T", " ").slice(0, 19)}Z
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    <span className="font-semibold text-[#43206F] bg-[#F2ECFA] px-2 py-0.5 rounded text-[11px]">
                      {entry.operation}
                    </span>
                  </td>
                  <td className="p-3 font-mono text-[11px] text-[#746B80] whitespace-nowrap">
                    {entry.case_id ? entry.case_id.slice(0, 12) : "—"}
                  </td>
                  <td className="p-3 whitespace-nowrap">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        entry.outcome === "success"
                          ? "bg-emerald-100 text-emerald-800"
                          : entry.outcome === "warning"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {entry.outcome}
                    </span>
                  </td>
                  <td className="p-3 text-[#282235] max-w-sm truncate" title={entry.details}>
                    {entry.details}
                  </td>
                  <td className="p-3 font-mono text-[10px] text-[#746B80] whitespace-nowrap" title={`Prev: ${entry.previous_entry_hash}\nCurr: ${entry.entry_hash}`}>
                    {entry.entry_hash.slice(0, 12)}...
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
