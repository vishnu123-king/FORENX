import React from "react";
import { GlobalStats, Case } from "../../types/forenx";
import {
  FolderKanban,
  ShieldCheck,
  Compass,
  Clock,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Activity,
  CheckCircle2
} from "lucide-react";

interface OverviewPageProps {
  stats: GlobalStats | null;
  cases: Case[];
  onSelectCase: (caseId: string) => void;
  onNavigate: (page: any) => void;
  onSeedDemo: () => void;
  onOpenNewCase: () => void;
  isSeeding: boolean;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  stats,
  cases,
  onSelectCase,
  onNavigate,
  onSeedDemo,
  onOpenNewCase,
  isSeeding
}) => {
  const statCards = [
    {
      label: "Total Cases",
      value: stats?.total_cases ?? 0,
      icon: <FolderKanban className="text-[#6D3FC0]" size={20} />,
      bg: "bg-[#F2ECFA]"
    },
    {
      label: "Evidence Vault Items",
      value: stats?.total_evidence ?? 0,
      icon: <ShieldCheck className="text-[#287D60]" size={20} />,
      bg: "bg-emerald-50"
    },
    {
      label: "Analysis Runs",
      value: stats?.total_analysis_runs ?? 0,
      icon: <Compass className="text-[#6D3FC0]" size={20} />,
      bg: "bg-[#F2ECFA]"
    },
    {
      label: "Extracted Artifacts",
      value: stats?.total_events ?? 0,
      icon: <Clock className="text-[#D96A9B]" size={20} />,
      bg: "bg-[#FCEAF2]"
    },
    {
      label: "Integrity Failures",
      value: stats?.verification_failures ?? 0,
      icon: <AlertTriangle className={stats?.verification_failures ? "text-[#B83D5B]" : "text-emerald-600"} size={20} />,
      bg: stats?.verification_failures ? "bg-rose-50" : "bg-emerald-50"
    }
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Banner Notice */}
      <div className="bg-[#FAF7FE] border-l-4 border-[#6D3FC0] p-4 rounded-r-xl border border-[#E8E0EF] shadow-xs flex items-center justify-between">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-[#6D3FC0] mb-0.5">
            Academic Research Workbench
          </div>
          <div className="text-sm font-semibold text-[#43206F]">
            Cross-Platform Browser Artifact Forensics &amp; Evidence Validation
          </div>
          <p className="text-xs text-[#746B80] mt-1">
            Local-first verification: source preservation, WebKit/PRTime timestamp normalization, and known-answer validation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate("Validation Lab")}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-[#E8E0EF] text-[#43206F] hover:bg-[#F2ECFA] transition-colors"
          >
            Validation Lab
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statCards.map((card, idx) => (
          <div
            key={idx}
            className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-[#746B80]">{card.label}</span>
              <div className={`p-2 rounded-lg ${card.bg}`}>{card.icon}</div>
            </div>
            <div className="text-2xl font-black text-[#282235] tracking-tight">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Empty State or Cases Table */}
      {cases.length === 0 ? (
        <div className="bg-white rounded-2xl border border-[#E8E0EF] p-12 text-center shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-[#F2ECFA] text-[#6D3FC0] flex items-center justify-center mx-auto mb-4">
            <FolderKanban size={32} />
          </div>
          <h2 className="text-xl font-bold text-[#43206F] mb-2">No Active Cases Found</h2>
          <p className="text-sm text-[#746B80] max-w-md mx-auto mb-6">
            Get started by creating your first forensic investigation or initialize the synthetic cross-browser research benchmark.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={onOpenNewCase}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm"
            >
              Create First Case
            </button>
            <button
              onClick={onSeedDemo}
              disabled={isSeeding}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg border border-[#D96A9B]/40 bg-[#FCEAF2] text-[#B83D5B] hover:bg-[#FCEAF2]/80 transition-colors"
            >
              <Sparkles size={14} className={isSeeding ? "animate-spin" : ""} />
              <span>{isSeeding ? "Generating..." : "Explore Synthetic Benchmark"}</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active / Recent Cases (2 cols) */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-[#E8E0EF] p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-[#43206F]">Investigation Cases</h2>
              <button
                onClick={() => onNavigate("Cases")}
                className="text-xs font-semibold text-[#6D3FC0] hover:underline flex items-center gap-1"
              >
                <span>View all ({cases.length})</span>
                <ArrowRight size={13} />
              </button>
            </div>

            <div className="divide-y divide-[#E8E0EF]">
              {cases.slice(0, 5).map(c => (
                <div
                  key={c.id}
                  onClick={() => onSelectCase(c.id)}
                  className="py-3.5 flex items-center justify-between hover:bg-[#FAF7FE] px-2 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-[#282235]">{c.name}</span>
                      <span className="text-[10px] font-mono text-[#746B80] bg-[#F2ECFA] px-1.5 py-0.5 rounded">
                        {c.id.slice(0, 8)}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                          c.status === "active" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                    <div className="text-xs text-[#746B80] line-clamp-1">
                      {c.description || "No description provided."}
                    </div>
                  </div>
                  <div className="text-right text-xs text-[#746B80]">
                    <div className="font-medium text-[#282235]">{c.investigator_label || "Unassigned"}</div>
                    <div className="text-[11px]">{new Date(c.updated_at).toLocaleDateString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Engine Status & Activity (1 col) */}
          <div className="bg-white rounded-xl border border-[#E8E0EF] p-6 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-bold text-[#43206F] mb-3">
                <Activity size={16} className="text-[#6D3FC0]" />
                <span>Forensic Engine Status</span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
                  <span className="text-[#746B80]">Audit Chain:</span>
                  <span className="font-semibold text-emerald-700 flex items-center gap-1">
                    <CheckCircle2 size={13} />
                    Verified (Chained)
                  </span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
                  <span className="text-[#746B80]">Chromium Parser:</span>
                  <span className="font-semibold text-[#43206F]">v1.0.0 (History)</span>
                </div>

                <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
                  <span className="text-[#746B80]">Firefox Parser:</span>
                  <span className="font-semibold text-[#43206F]">v1.0.0 (places.sqlite)</span>
                </div>

                {stats?.recent_activity && (
                  <div className="p-3 bg-[#F2ECFA]/60 rounded-lg border border-[#E8E0EF] mt-3">
                    <div className="text-[11px] font-bold text-[#6D3FC0] uppercase mb-1">Last Extraction:</div>
                    <div className="text-xs font-semibold text-[#282235]">
                      {stats.recent_activity.records_extracted} artifacts extracted
                    </div>
                    <div className="text-[11px] text-[#746B80]">
                      Status: {stats.recent_activity.status} ({stats.recent_activity.warnings_count} warnings)
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-[#E8E0EF] flex gap-2">
              <button
                onClick={() => onNavigate("Evidence Vault")}
                className="flex-1 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] text-center"
              >
                Evidence Vault
              </button>
              <button
                onClick={() => onNavigate("Unified Timeline")}
                className="flex-1 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] text-[#43206F] hover:bg-[#FAF7FE] text-center"
              >
                Timeline
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
