import React from "react";
import {
  LayoutDashboard,
  FolderKanban,
  HardDrive,
  Radio,
  Laptop,
  Briefcase,
  ShieldCheck,
  Compass,
  Clock,
  TestTube2,
  FileText,
  ScrollText,
  Settings,
  Info,
  ChevronRight
} from "lucide-react";
import { Case } from "../types/forenx";

export type NavPage =
  | "Overview"
  | "Cases"
  | "Local System Forensics"
  | "Remote System Forensics"
  | "Endpoints"
  | "Collection Jobs"
  | "Evidence Vault"
  | "Artifact Explorer"
  | "Unified Timeline"
  | "Validation Lab"
  | "Reports"
  | "Audit Log"
  | "Settings"
  | "About";

interface SidebarProps {
  currentPage: NavPage;
  onSelectPage: (page: NavPage) => void;
  cases: Case[];
  activeCaseId: string | null;
  onSelectCase: (caseId: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onSelectPage,
  cases,
  activeCaseId,
  onSelectCase
}) => {
  const navItems: Array<{ id: NavPage; label: string; icon: React.ReactNode; group?: string }> = [
    { id: "Overview", label: "Overview", icon: <LayoutDashboard size={17} /> },
    { id: "Cases", label: "Cases", icon: <FolderKanban size={17} /> },

    // Acquisition Operations Group
    { id: "Local System Forensics", label: "Local Forensics", icon: <HardDrive size={17} />, group: "Acquisition Modes" },
    { id: "Remote System Forensics", label: "Remote Forensics", icon: <Radio size={17} /> },
    { id: "Endpoints", label: "Endpoints", icon: <Laptop size={17} /> },
    { id: "Collection Jobs", label: "Collection Jobs", icon: <Briefcase size={17} /> },

    // Evidence & Analysis Group
    { id: "Evidence Vault", label: "Evidence Vault", icon: <ShieldCheck size={17} />, group: "Analysis & Proof" },
    { id: "Artifact Explorer", label: "Artifact Explorer", icon: <Compass size={17} /> },
    { id: "Unified Timeline", label: "Timeline", icon: <Clock size={17} /> },
    { id: "Validation Lab", label: "Validation Lab", icon: <TestTube2 size={17} /> },
    { id: "Reports", label: "Reports", icon: <FileText size={17} /> },
    { id: "Audit Log", label: "Audit Log", icon: <ScrollText size={17} /> },

    // Configuration Group
    { id: "Settings", label: "Settings", icon: <Settings size={17} />, group: "System" },
    { id: "About", label: "About", icon: <Info size={17} /> }
  ];

  const activeCase = cases.find(c => c.id === activeCaseId);

  return (
    <aside className="w-64 bg-[#F8F4FD] border-r border-[#E8E0EF] flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#E8E0EF]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#6D3FC0] flex items-center justify-center text-white shadow-sm font-black text-xs">
            FX
          </div>
          <div>
            <div className="text-xl font-bold tracking-tight text-[#43206F] flex items-center leading-none">
              <span>FOREN</span>
              <span className="text-[#D96A9B]">X</span>
            </div>
            <div className="text-[10px] tracking-wide text-[#746B80] font-medium uppercase mt-0.5">
              Dual-Mode Forensics
            </div>
          </div>
        </div>
      </div>

      {/* Case Context Selector */}
      <div className="px-3.5 py-2.5 bg-[#F2ECFA]/60 border-b border-[#E8E0EF]">
        <div className="text-[10px] font-semibold text-[#746B80] uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Active Case</span>
          {activeCase && (
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-bold uppercase">
              {activeCase.status}
            </span>
          )}
        </div>
        {cases.length === 0 ? (
          <div className="text-xs text-[#746B80] italic py-0.5">No active cases</div>
        ) : (
          <select
            className="w-full text-xs font-semibold bg-white text-[#282235] border border-[#E8E0EF] rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#6D3FC0] truncate"
            value={activeCaseId || ""}
            onChange={e => onSelectCase(e.target.value)}
          >
            {cases.map(c => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.id.slice(0, 8)})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-0.5 text-xs">
        {navItems.map((item, idx) => {
          const isActive = currentPage === item.id;
          return (
            <React.Fragment key={item.id}>
              {item.group && (
                <div className={`text-[10px] font-bold text-[#746B80] uppercase tracking-wider px-2 pb-1 ${idx > 0 ? "pt-3" : "pt-1"}`}>
                  {item.group}
                </div>
              )}
              <button
                onClick={() => onSelectPage(item.id)}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg font-medium transition-colors ${
                  isActive
                    ? "bg-[#6D3FC0] text-white shadow-xs font-semibold"
                    : "text-[#282235] hover:bg-[#F2ECFA] hover:text-[#43206F]"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={isActive ? "text-white" : "text-[#6D3FC0]"}>{item.icon}</span>
                  <span className="truncate">{item.label}</span>
                </div>
                {isActive && <ChevronRight size={13} className="opacity-80 shrink-0" />}
              </button>
            </React.Fragment>
          );
        })}
      </nav>

      {/* System Integrity Footer */}
      <div className="p-3 border-t border-[#E8E0EF] bg-white/50 text-[10px] text-[#746B80]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-semibold text-[#282235]">Engine Online</span>
          </div>
          <span className="font-mono text-[9px] bg-purple-50 text-[#6D3FC0] px-1 rounded border border-[#E8E0EF]">
            Dual-Mode v1.0
          </span>
        </div>
      </div>
    </aside>
  );
};
