import React, { useState, useEffect } from "react";
import { Case, ValidationRun } from "../../types/forenx";
import {
  TestTube2,
  Play,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  RefreshCw,
  Award
} from "lucide-react";

interface ValidationLabPageProps {
  activeCase: Case | null;
}

export const ValidationLabPage: React.FC<ValidationLabPageProps> = ({ activeCase }) => {
  const [runs, setRuns] = useState<ValidationRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "mismatches" | "missing" | "unexpected">("overview");

  const fetchValidations = async () => {
    if (!activeCase) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/validations`);
      const json = await res.json();
      if (json.success) {
        setRuns(json.data || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchValidations();
  }, [activeCase?.id]);

  const handleRunValidation = async () => {
    if (!activeCase) return;
    setEvaluating(true);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/validate`, { method: "POST" });
      const json = await res.json();
      if (json.success) {
        await fetchValidations();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setEvaluating(false);
    }
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <TestTube2 size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">Select an active case to evaluate extraction precision and recall against ground-truth datasets.</p>
      </div>
    );
  }

  const latest = runs[0] || null;

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Research Statement Header */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <Award size={15} />
            <span>Academic Research Engine</span>
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            Known-Answer Validation Lab
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5 max-w-2xl">
            Empirical benchmark comparing extracted artifacts against controlled ground-truth manifests.
            Computes mathematical Precision and Recall with safe zero-denominator handling.
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={evaluating}
          className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm disabled:opacity-50 shrink-0"
        >
          <Play size={15} className={evaluating ? "animate-spin" : ""} />
          <span>{evaluating ? "Evaluating..." : "Run Validation Suite"}</span>
        </button>
      </div>

      {/* Primary Metrics Cards */}
      {latest ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs">
              <span className="text-xs font-semibold text-[#746B80] block mb-1">Precision</span>
              <div className="text-2xl font-black text-[#282235]">
                {latest.precision !== null ? `${(latest.precision * 100).toFixed(1)}%` : "N/A"}
              </div>
              <span className="text-[10px] text-[#746B80]">Matched / Extracted</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs">
              <span className="text-xs font-semibold text-[#746B80] block mb-1">Recall</span>
              <div className="text-2xl font-black text-[#282235]">
                {latest.recall !== null ? `${(latest.recall * 100).toFixed(1)}%` : "N/A"}
              </div>
              <span className="text-[10px] text-[#746B80]">Matched / Expected</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs">
              <span className="text-xs font-semibold text-[#746B80] block mb-1">Expected Events</span>
              <div className="text-2xl font-black text-[#6D3FC0]">{latest.expected_count}</div>
              <span className="text-[10px] text-[#746B80]">Ground Truth</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs">
              <span className="text-xs font-semibold text-[#746B80] block mb-1">Matched Events</span>
              <div className="text-2xl font-black text-emerald-700">{latest.matched_count}</div>
              <span className="text-[10px] text-[#746B80]">Verified Accurate</span>
            </div>

            <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs">
              <span className="text-xs font-semibold text-[#746B80] block mb-1">Discrepancies</span>
              <div className={`text-2xl font-black ${latest.missing_count > 0 || (latest.details?.field_mismatches?.length || 0) > 0 ? "text-[#B83D5B]" : "text-emerald-700"}`}>
                {latest.missing_count + (latest.details?.field_mismatches?.length || 0)}
              </div>
              <span className="text-[10px] text-[#746B80]">Missing / Mismatches</span>
            </div>
          </div>

          {/* Details Tabs & Tables */}
          <div className="bg-white rounded-xl border border-[#E8E0EF] p-6 shadow-xs space-y-4">
            <div className="flex border-b border-[#E8E0EF] gap-4 text-xs font-semibold">
              <button
                onClick={() => setActiveTab("overview")}
                className={`pb-2.5 transition-colors ${activeTab === "overview" ? "border-b-2 border-[#6D3FC0] text-[#6D3FC0]" : "text-[#746B80] hover:text-[#282235]"}`}
              >
                Evaluation Summary
              </button>
              <button
                onClick={() => setActiveTab("mismatches")}
                className={`pb-2.5 transition-colors flex items-center gap-1.5 ${activeTab === "mismatches" ? "border-b-2 border-[#6D3FC0] text-[#6D3FC0]" : "text-[#746B80] hover:text-[#282235]"}`}
              >
                <span>Field Mismatches</span>
                <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px]">
                  {latest.details?.field_mismatches?.length || 0}
                </span>
              </button>
              <button
                onClick={() => setActiveTab("missing")}
                className={`pb-2.5 transition-colors flex items-center gap-1.5 ${activeTab === "missing" ? "border-b-2 border-[#6D3FC0] text-[#6D3FC0]" : "text-[#746B80] hover:text-[#282235]"}`}
              >
                <span>Missing Records</span>
                <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px]">
                  {latest.missing_count}
                </span>
              </button>
              <button
                onClick={() => setActiveTab("unexpected")}
                className={`pb-2.5 transition-colors flex items-center gap-1.5 ${activeTab === "unexpected" ? "border-b-2 border-[#6D3FC0] text-[#6D3FC0]" : "text-[#746B80] hover:text-[#282235]"}`}
              >
                <span>Unexpected Records</span>
                <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px]">
                  {latest.unexpected_count}
                </span>
              </button>
            </div>

            {/* Tab content */}
            {activeTab === "overview" && (
              <div className="space-y-3 text-xs">
                <div className="p-4 bg-[#FAF7FE] rounded-lg border border-[#E8E0EF] text-[#282235]">
                  <strong className="text-[#43206F] block mb-1">Result Summary:</strong>
                  {latest.result_summary}
                </div>
                <div className="p-4 bg-emerald-50/50 rounded-lg border border-emerald-100 text-[#282235]">
                  <strong className="text-emerald-900 block mb-1">Methodology &amp; Matching Rules:</strong>
                  Events are evaluated across composite key <code className="font-mono bg-white px-1 py-0.5 rounded text-[11px]">browser_family + event_type + url</code>. Timestamps are verified within a 2.0-second tolerance window to account for database microsecond rounding.
                </div>
              </div>
            )}

            {activeTab === "mismatches" && (
              <div>
                {!latest.details?.field_mismatches || latest.details.field_mismatches.length === 0 ? (
                  <div className="p-8 text-center text-xs text-emerald-700 font-medium">
                    ✓ Zero field mismatches detected between extracted data and ground truth!
                  </div>
                ) : (
                  <div className="divide-y divide-[#E8E0EF]">
                    {latest.details.field_mismatches.map((m, idx) => (
                      <div key={idx} className="py-3 text-xs space-y-1">
                        <div className="font-bold text-[#43206F]">{m.url}</div>
                        <div className="text-[#746B80]">
                          Field <code className="font-mono bg-purple-50 px-1 py-0.5 rounded">{m.field}</code>: Expected <span className="text-emerald-700 font-semibold">{m.expected}</span> vs Actual <span className="text-amber-700 font-semibold">{m.actual}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "missing" && (
              <div>
                {!latest.details?.missing_records || latest.details.missing_records.length === 0 ? (
                  <div className="p-8 text-center text-xs text-emerald-700 font-medium">
                    ✓ All expected ground truth records were successfully recovered!
                  </div>
                ) : (
                  <div className="divide-y divide-[#E8E0EF]">
                    {latest.details.missing_records.map((r, idx) => (
                      <div key={idx} className="py-3 text-xs">
                        <div className="font-bold text-[#B83D5B]">{r.url}</div>
                        <div className="text-[#746B80]">{r.browser_family} — {r.event_type} (Test ID: {r.test_id})</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "unexpected" && (
              <div>
                {!latest.details?.unexpected_records || latest.details.unexpected_records.length === 0 ? (
                  <div className="p-8 text-center text-xs text-emerald-700 font-medium">
                    ✓ Zero unexpected records extracted outside of test ground truth scope.
                  </div>
                ) : (
                  <div className="divide-y divide-[#E8E0EF]">
                    {latest.details.unexpected_records.map((u, idx) => (
                      <div key={idx} className="py-3 text-xs">
                        <div className="font-bold text-[#43206F]">{u.url}</div>
                        <div className="text-[#746B80]">{u.browser_family} — {u.event_type}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-[#E8E0EF] p-12 text-center shadow-xs">
          <TestTube2 size={40} className="mx-auto text-[#6D3FC0]/40 mb-3" />
          <h2 className="text-base font-bold text-[#43206F] mb-1">No Validation Runs Recorded</h2>
          <p className="text-xs text-[#746B80] max-w-md mx-auto mb-4">
            Execute the validation suite to evaluate extracted evidence against the synthetic ground-truth benchmark.
          </p>
          <button
            onClick={handleRunValidation}
            disabled={evaluating}
            className="px-5 py-2.5 text-xs font-bold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
          >
            Run Validation Suite Now
          </button>
        </div>
      )}
    </div>
  );
};
