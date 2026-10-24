import React, { useState } from "react";
import { Case } from "../../types/forenx";
import { Search, FolderKanban, Archive, CheckCircle, Plus, Calendar, User, FileText } from "lucide-react";

interface CasesPageProps {
  cases: Case[];
  activeCaseId: string | null;
  onSelectCase: (caseId: string) => void;
  onOpenNewCase: () => void;
  onCaseArchived: (caseId: string) => void;
}

export const CasesPage: React.FC<CasesPageProps> = ({
  cases,
  activeCaseId,
  onSelectCase,
  onOpenNewCase,
  onCaseArchived
}) => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [archivingId, setArchivingId] = useState<string | null>(null);

  const filtered = cases.filter(c => {
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    if (search.trim()) {
      const term = search.toLowerCase();
      const inName = c.name.toLowerCase().includes(term);
      const inDesc = (c.description || "").toLowerCase().includes(term);
      const inInv = (c.investigator_label || "").toLowerCase().includes(term);
      if (!inName && !inDesc && !inInv) return false;
    }
    return true;
  });

  const handleArchive = async (e: React.MouseEvent, caseId: string) => {
    e.stopPropagation();
    if (!window.confirm("Archive this case? All evidence and events remain preserved in the repository.")) {
      return;
    }
    setArchivingId(caseId);
    try {
      const res = await fetch(`/api/cases/${caseId}/archive`, { method: "POST" });
      const json = await res.json();
      if (json.success) {
        onCaseArchived(caseId);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setArchivingId(null);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-2.5 text-[#746B80]" size={16} />
            <input
              type="text"
              placeholder="Search cases by name, description, or investigator..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-[#E8E0EF] rounded-lg bg-white text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30"
            />
          </div>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-[#E8E0EF] rounded-lg px-3 py-2 bg-white text-[#282235] focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <button
          onClick={onOpenNewCase}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm shrink-0"
        >
          <Plus size={15} />
          <span>New Investigation Case</span>
        </button>
      </div>

      {/* Cases List */}
      {filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-[#E8E0EF] p-12 text-center text-[#746B80] text-sm">
          No cases matching criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map(c => {
            const isSelected = c.id === activeCaseId;
            return (
              <div
                key={c.id}
                onClick={() => onSelectCase(c.id)}
                className={`bg-white rounded-xl border p-5 cursor-pointer transition-all ${
                  isSelected
                    ? "border-[#6D3FC0] ring-2 ring-[#6D3FC0]/20 shadow-md"
                    : "border-[#E8E0EF] hover:border-[#6D3FC0]/40 shadow-xs"
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-bold text-base text-[#43206F]">{c.name}</h2>
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                          c.status === "active"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-[#746B80] mt-0.5">{c.id}</div>
                  </div>

                  {isSelected && (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-[#6D3FC0] bg-[#F2ECFA] px-2 py-0.5 rounded-full">
                      <CheckCircle size={12} />
                      Active
                    </span>
                  )}
                </div>

                <p className="text-xs text-[#746B80] line-clamp-2 mb-4">
                  {c.description || "No description provided."}
                </p>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-[#746B80] pt-3 border-t border-[#E8E0EF]">
                  <div className="flex items-center gap-1.5">
                    <User size={13} className="text-[#6D3FC0]" />
                    <span className="truncate">{c.investigator_label || "Unassigned"}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar size={13} className="text-[#6D3FC0]" />
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {c.notes && (
                  <div className="mt-3 p-2 bg-[#FAF7FE] rounded text-[11px] text-[#746B80] italic flex items-start gap-1.5">
                    <FileText size={13} className="shrink-0 mt-0.5 text-[#D96A9B]" />
                    <span className="line-clamp-1">{c.notes}</span>
                  </div>
                )}

                <div className="mt-4 pt-3 border-t border-[#E8E0EF] flex items-center justify-between">
                  <span className="text-[11px] text-[#6D3FC0] font-semibold">
                    {isSelected ? "Currently Selected" : "Click to select"}
                  </span>
                  {c.status === "active" && (
                    <button
                      onClick={e => handleArchive(e, c.id)}
                      disabled={archivingId === c.id}
                      className="text-[11px] font-medium text-slate-500 hover:text-[#B83D5B] flex items-center gap-1 px-2 py-1 rounded hover:bg-rose-50"
                    >
                      <Archive size={12} />
                      <span>{archivingId === c.id ? "Archiving..." : "Archive"}</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
