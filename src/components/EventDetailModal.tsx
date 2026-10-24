import React from "react";
import { X, ExternalLink, Calendar, Database, ShieldAlert, Cpu } from "lucide-react";
import { ForensicEvent } from "../types/forenx";

interface EventDetailModalProps {
  event: ForensicEvent | null;
  onClose: () => void;
}

export const EventDetailModal: React.FC<EventDetailModalProps> = ({ event, onClose }) => {
  if (!event) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-xl border border-[#E8E0EF] w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#E8E0EF] flex items-center justify-between bg-[#FAF7FE]">
          <div className="flex items-center gap-2 text-[#43206F] font-bold">
            <span className="text-xs px-2 py-0.5 rounded bg-[#6D3FC0] text-white font-semibold">
              {event.browser_family}
            </span>
            <span className="text-sm">Event Record: {event.id}</span>
          </div>
          <button onClick={onClose} className="text-[#746B80] hover:text-[#282235]">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Main Title and URL */}
          <div className="bg-[#FAF7FE] p-4 rounded-lg border border-[#E8E0EF]">
            <div className="text-xs font-semibold text-[#746B80] uppercase tracking-wider mb-1">
              {event.event_type.replace("_", " ").toUpperCase()}
            </div>
            <h2 className="text-base font-bold text-[#43206F] mb-1.5 break-words">
              {event.title || "No Title Recorded"}
            </h2>
            <div className="flex items-center gap-1.5 text-xs text-[#6D3FC0] break-all font-mono">
              <ExternalLink size={13} className="shrink-0" />
              <a href={event.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                {event.url}
              </a>
            </div>
          </div>

          {/* Timestamps Section */}
          <div className="border border-[#E8E0EF] rounded-lg p-4">
            <div className="flex items-center gap-2 text-xs font-bold text-[#43206F] uppercase tracking-wider mb-2">
              <Calendar size={14} className="text-[#6D3FC0]" />
              <span>Timestamp Reconstruction</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-white p-2.5 rounded border border-[#E8E0EF]">
                <div className="text-[#746B80] mb-0.5">Normalized UTC Timestamp:</div>
                <div className="font-mono font-bold text-[#282235]">
                  {event.normalized_utc || "OUT OF RANGE / UNPARSEABLE"}
                </div>
              </div>
              <div className="bg-white p-2.5 rounded border border-[#E8E0EF]">
                <div className="text-[#746B80] mb-0.5">Raw Native Timestamp:</div>
                <div className="font-mono text-[#282235]">
                  {event.raw_timestamp.toLocaleString()} ({event.timestamp_format})
                </div>
              </div>
            </div>
            <div className="mt-2 text-[11px] text-[#746B80]">
              Conversion Status:{" "}
              <span className={`font-semibold ${event.conversion_status === "success" ? "text-emerald-700" : "text-amber-700"}`}>
                {event.conversion_status.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Source Provenance & Forensic Traceability */}
          <div className="border border-[#E8E0EF] rounded-lg p-4">
            <div className="flex items-center gap-2 text-xs font-bold text-[#43206F] uppercase tracking-wider mb-2">
              <Database size={14} className="text-[#6D3FC0]" />
              <span>Source Provenance &amp; Forensic Traceability</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
              <div className="bg-white p-2 rounded border border-[#E8E0EF]">
                <div className="text-[10px] text-[#746B80] uppercase">Source DB</div>
                <div className="font-bold text-[#43206F]">{event.source_database}</div>
              </div>
              <div className="bg-white p-2 rounded border border-[#E8E0EF]">
                <div className="text-[10px] text-[#746B80] uppercase">Table Reference</div>
                <div className="text-[#43206F]">{event.source_table}</div>
              </div>
              <div className="bg-white p-2 rounded border border-[#E8E0EF]">
                <div className="text-[10px] text-[#746B80] uppercase">Source Record ID</div>
                <div className="text-[#43206F]">#{event.source_record_id}</div>
              </div>
            </div>
          </div>

          {/* Extra Metadata & Transition Qualifier */}
          {event.extra_metadata && Object.keys(event.extra_metadata).length > 0 && (
            <div className="border border-[#E8E0EF] rounded-lg p-4">
              <div className="flex items-center gap-2 text-xs font-bold text-[#43206F] uppercase tracking-wider mb-2">
                <Cpu size={14} className="text-[#6D3FC0]" />
                <span>Transition &amp; Technical Attributes</span>
              </div>
              <pre className="text-xs font-mono bg-[#FAF7FE] p-3 rounded border border-[#E8E0EF] overflow-x-auto text-[#282235]">
                {JSON.stringify(event.extra_metadata, null, 2)}
              </pre>
            </div>
          )}

          {/* Warnings */}
          {event.warning && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start gap-2">
              <ShieldAlert size={16} className="shrink-0 mt-0.5 text-amber-600" />
              <div>
                <div className="font-bold">Parser Warning:</div>
                <div>{event.warning}</div>
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-3 border-t border-[#E8E0EF] bg-[#FAF7FE] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] shadow-sm"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
