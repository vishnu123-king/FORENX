import React, { useState } from "react";
import { X, FolderPlus } from "lucide-react";

interface NewCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCaseCreated: (newCase: any) => void;
}

export const NewCaseModal: React.FC<NewCaseModalProps> = ({ isOpen, onClose, onCaseCreated }) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [investigator, setInvestigator] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Case name is required.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/cases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, investigator, notes })
      });
      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Failed to create case");
      }
      onCaseCreated(json.data);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-xl border border-[#E8E0EF] w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#E8E0EF] flex items-center justify-between bg-[#FAF7FE]">
          <div className="flex items-center gap-2 text-[#43206F] font-bold">
            <FolderPlus size={18} className="text-[#6D3FC0]" />
            <span>Create Forensic Investigation Case</span>
          </div>
          <button onClick={onClose} className="text-[#746B80] hover:text-[#282235]">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 font-medium">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Case Name <span className="text-[#B83D5B]">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Incident 2026-B91 — Suspect Browser Audit"
              className="w-full text-sm border border-[#E8E0EF] rounded-lg px-3 py-2 text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30 focus:border-[#6D3FC0]"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Investigation Description
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Brief summary of allegations, scope, and objectives..."
              rows={2}
              className="w-full text-sm border border-[#E8E0EF] rounded-lg px-3 py-2 text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30 focus:border-[#6D3FC0]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Lead Investigator Identifier
            </label>
            <input
              type="text"
              value={investigator}
              onChange={e => setInvestigator(e.target.value)}
              placeholder="e.g. Lead Examiner Dr. S. Ramanujan"
              className="w-full text-sm border border-[#E8E0EF] rounded-lg px-3 py-2 text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30 focus:border-[#6D3FC0]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Initial Handling &amp; Provenance Notes
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Source workstation identifier, chain of custody reference, legal authorization..."
              rows={2}
              className="w-full text-sm border border-[#E8E0EF] rounded-lg px-3 py-2 text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30 focus:border-[#6D3FC0]"
            />
          </div>

          <div className="pt-3 border-t border-[#E8E0EF] flex justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-lg text-[#746B80] hover:bg-[#F2ECFA]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50 shadow-sm"
            >
              {loading ? "Creating..." : "Initialize Case"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
