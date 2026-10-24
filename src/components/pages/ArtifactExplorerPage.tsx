import React, { useState, useEffect } from "react";
import { Case, Evidence, AnalysisRun } from "../../types/forenx";
import { Compass, Play, AlertTriangle, CheckCircle, FileText, Cpu, Clock, RefreshCw } from "lucide-react";

interface ArtifactExplorerPageProps {
  activeCase: Case | null;
  evidenceItems: Evidence[];
  onAnalysisCompleted: () => void;
  onNavigateToTimeline: () => void;
}

export const ArtifactExplorerPage: React.FC<ArtifactExplorerPageProps> = ({
  activeCase,
  evidenceItems,
  onAnalysisCompleted,
  onNavigateToTimeline
}) => {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    if (!activeCase) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/analysis-runs`);
      const json = await res.json();
      if (json.success) {
        setRuns(json.data);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [activeCase?.id]);

  const handleRunAnalysis = async () => {
    if (!activeCase) return;
    setAnalyzing(true);
    setError(null);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Analysis failed");
      }
      await fetchRuns();
      onAnalysisCompleted();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <Compass size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">Select an active case to run artifact parsers and inspect browser databases.</p>
      </div>
    );
  }

  const latestRun = runs[0] || null;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner & Trigger */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider">
            Browser Artifact Extraction Engine
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            Artifact Explorer &amp; Schema Inspector
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5">
            Executes read-only schema queries on controlled working copies of Chromium (<code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">urls</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">visits</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">downloads</code>) and Firefox (<code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">moz_places</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">moz_historyvisits</code>, <code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">moz_bookmarks</code>).
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchRuns}
            className="p-2 text-[#746B80] hover:text-[#43206F] rounded-lg border border-[#E8E0EF]"
            title="Refresh runs"
          >
            <RefreshCw size={15} />
          </button>

          <button
            onClick={handleRunAnalysis}
            disabled={analyzing || evidenceItems.length === 0}
            className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm disabled:opacity-50"
          >
            <Play size={15} className={analyzing ? "animate-spin" : ""} />
            <span>{analyzing ? "Extracting Artifacts..." : "Run Forensic Extraction"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 font-medium flex items-center gap-2">
          <AlertTriangle size={16} className="text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Latest Run Highlights */}
      {latestRun && (
        <div className="bg-[#FAF7FE] border border-[#E8E0EF] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#43206F]">
                Latest Extraction Summary ({latestRun.id})
              </h3>
            </div>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded uppercase ${
                latestRun.status === "completed"
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {latestRun.status}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="bg-white p-3 rounded-lg border border-[#E8E0EF]">
              <span className="text-[#746B80] block mb-1">Records Seen</span>
              <span className="text-xl font-bold text-[#282235]">{latestRun.records_seen}</span>
            </div>
            <div className="bg-white p-3 rounded-lg border border-[#E8E0EF]">
              <span className="text-[#746B80] block mb-1">Extracted &amp; Normalized</span>
              <span className="text-xl font-bold text-emerald-700">{latestRun.records_extracted}</span>
            </div>
            <div className="bg-white p-3 rounded-lg border border-[#E8E0EF]">
              <span className="text-[#746B80] block mb-1">Records Skipped</span>
              <span className="text-xl font-bold text-[#746B80]">{latestRun.records_skipped}</span>
            </div>
            <div className="bg-white p-3 rounded-lg border border-[#E8E0EF]">
              <span className="text-[#746B80] block mb-1">Parser Warnings</span>
              <span className={`text-xl font-bold ${latestRun.warnings_count > 0 ? "text-amber-700" : "text-emerald-700"}`}>
                {latestRun.warnings_count}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-[#746B80] pt-2 border-t border-[#E8E0EF]">
            <span>Active Parsers: <strong className="text-[#43206F]">{latestRun.parser_versions}</strong></span>
            <button
              onClick={onNavigateToTimeline}
              className="text-xs font-semibold text-[#6D3FC0] hover:underline"
            >
              Inspect Events in Unified Timeline →
            </button>
          </div>
        </div>
      )}

      {/* Analysis Runs History Table */}
      <div className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs">
        <h3 className="text-sm font-bold text-[#43206F] mb-4">Historical Extraction Runs</h3>
        {runs.length === 0 ? (
          <div className="text-center py-8 text-xs text-[#746B80]">
            No extractions run for this case yet. Click "Run Forensic Extraction" above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E8E0EF] text-[#746B80] bg-[#FAF7FE]">
                  <th className="p-2.5 font-semibold">Run ID</th>
                  <th className="p-2.5 font-semibold">Timestamp (Started)</th>
                  <th className="p-2.5 font-semibold">Extracted</th>
                  <th className="p-2.5 font-semibold">Skipped</th>
                  <th className="p-2.5 font-semibold">Warnings</th>
                  <th className="p-2.5 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0EF]">
                {runs.map(r => (
                  <tr key={r.id} className="hover:bg-[#FAF7FE]">
                    <td className="p-2.5 font-mono font-medium text-[#43206F]">{r.id}</td>
                    <td className="p-2.5 text-[#746B80]">{new Date(r.started_at).toLocaleString()}</td>
                    <td className="p-2.5 font-bold text-emerald-700">{r.records_extracted}</td>
                    <td className="p-2.5 text-[#746B80]">{r.records_skipped}</td>
                    <td className="p-2.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${r.warnings_count > 0 ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>
                        {r.warnings_count}
                      </span>
                    </td>
                    <td className="p-2.5">
                      <span className="font-semibold text-[#282235] uppercase text-[10px]">{r.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
