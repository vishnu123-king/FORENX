import React, { useState } from "react";
import { X, UploadCloud, FileCode2, AlertCircle } from "lucide-react";

interface UploadEvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  onUploaded: (evidence: any) => void;
}

export const UploadEvidenceModal: React.FC<UploadEvidenceModalProps> = ({
  isOpen,
  onClose,
  caseId,
  onUploaded
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to acquire into the case vault.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("notes", notes);

    try {
      const res = await fetch(`/api/cases/${caseId}/evidence/upload`, {
        method: "POST",
        body: formData
      });
      const json = await res.json();
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Failed to import evidence");
      }
      onUploaded(json.data);
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
            <UploadCloud size={18} className="text-[#6D3FC0]" />
            <span>Acquire Browser Evidence</span>
          </div>
          <button onClick={onClose} className="text-[#746B80] hover:text-[#282235]">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 font-medium flex items-center gap-2">
              <AlertCircle size={15} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Select Evidence Database File <span className="text-[#B83D5B]">*</span>
            </label>
            <div className="border-2 border-dashed border-[#E8E0EF] rounded-xl p-6 text-center hover:bg-[#FAF7FE] transition-colors cursor-pointer relative">
              <input
                type="file"
                onChange={e => setFile(e.target.files?.[0] || null)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center">
                <FileCode2 size={32} className="text-[#6D3FC0] mb-2" />
                {file ? (
                  <div>
                    <div className="text-sm font-semibold text-[#43206F]">{file.name}</div>
                    <div className="text-xs text-[#746B80]">{(file.size / 1024).toFixed(1)} KB</div>
                  </div>
                ) : (
                  <div>
                    <span className="text-xs font-medium text-[#43206F]">
                      Drop Chromium <code className="font-mono bg-purple-50 px-1 py-0.5 rounded">History</code> or Firefox <code className="font-mono bg-purple-50 px-1 py-0.5 rounded">places.sqlite</code>
                    </span>
                    <p className="text-[11px] text-[#746B80] mt-1">or click to browse local files (up to 500 MB)</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#43206F] uppercase tracking-wider mb-1">
              Acquisition &amp; Source Provenance Notes
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Acquired from user profile while browser was stopped. Associated sidecar files noted."
              rows={3}
              className="w-full text-sm border border-[#E8E0EF] rounded-lg px-3 py-2 text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30 focus:border-[#6D3FC0]"
            />
          </div>

          <div className="p-3 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-[11px] text-[#746B80] space-y-1">
            <div className="font-semibold text-[#43206F]">Controlled Vault Procedure:</div>
            <div>• Evidence is hashed (SHA-256) before and after copying to ensure byte integrity.</div>
            <div>• The original file is preserved untouched; analysis runs strictly on working copies.</div>
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
              disabled={loading || !file}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50 shadow-sm"
            >
              {loading ? "Acquiring..." : "Acquire into Vault"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
