import React from "react";
import { Case } from "../types/forenx";
import { Sparkles, Plus, Folder } from "lucide-react";

interface HeaderProps {
  pageTitle: string;
  activeCase: Case | null;
  onOpenNewCase: () => void;
  onSeedDemo: () => void;
  isSeeding: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  pageTitle,
  activeCase,
  onOpenNewCase,
  onSeedDemo,
  isSeeding
}) => {
  return (
    <header className="h-16 border-b border-[#E8E0EF] bg-white px-8 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold text-[#43206F] tracking-tight">{pageTitle}</h1>
        {activeCase ? (
          <div className="flex items-center gap-2 text-xs text-[#746B80] bg-[#FAF7FE] px-2.5 py-1 rounded-md border border-[#E8E0EF]">
            <Folder size={12} className="text-[#6D3FC0]" />
            <span className="font-semibold text-[#43206F]">{activeCase.name}</span>
            <span className="text-[11px] font-mono text-[#746B80]">({activeCase.id.slice(0, 8)})</span>
          </div>
        ) : (
          <span className="text-xs text-[#746B80] italic bg-slate-50 px-2 py-0.5 rounded">No active case selected</span>
        )}
      </div>

      <div className="flex items-center gap-2.5">
        <button
          onClick={onSeedDemo}
          disabled={isSeeding}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-[#D96A9B]/40 bg-[#FCEAF2] text-[#B83D5B] hover:bg-[#FCEAF2]/80 transition-colors disabled:opacity-50"
        >
          <Sparkles size={14} className={isSeeding ? "animate-spin" : ""} />
          <span>{isSeeding ? "Seeding..." : "Load Synthetic Demo"}</span>
        </button>

        <button
          onClick={onOpenNewCase}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm"
        >
          <Plus size={14} />
          <span>New Case</span>
        </button>
      </div>
    </header>
  );
};
