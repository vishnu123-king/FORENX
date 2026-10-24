import React, { useState, useEffect } from "react";
import { Case, Evidence, EvidencePackage } from "../../types/forenx";
import {
  ShieldCheck,
  UploadCloud,
  Copy,
  Check,
  RefreshCw,
  FileCode,
  AlertTriangle,
  Info,
  Database,
  Archive,
  ExternalLink,
  Lock,
  ChevronRight,
  X
} from "lucide-react";

interface EvidenceVaultPageProps {
  activeCase: Case | null;
  evidenceItems: Evidence[];
  onOpenUpload: () => void;
  onRefreshEvidence: () => void;
}

export const EvidenceVaultPage: React.FC<EvidenceVaultPageProps> = ({
  activeCase,
  evidenceItems,
  onOpenUpload,
  onRefreshEvidence
}) => {
  const [activeTab, setActiveTab] = useState<"artifacts" | "packages">("artifacts");
  const [packages, setPackages] = useState<EvidencePackage[]>([]);
  const [loadingPackages, setLoadingPackages] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [verifyMessage, setVerifyMessage] = useState<Record<string, string>>({});

  // Package upload modal
  const [isPackageUploadOpen, setIsPackageUploadOpen] = useState(false);
  const [packageFile, setPackageFile] = useState<File | null>(null);
  const [expectedHash, setExpectedHash] = useState("");
  const [uploadingPackage, setUploadingPackage] = useState(false);
  const [packageUploadError, setPackageUploadError] = useState<string | null>(null);

  // Package inspect modal
  const [inspectingPackage, setInspectingPackage] = useState<EvidencePackage | null>(null);

  const loadPackages = async () => {
    if (!activeCase) return;
    setLoadingPackages(true);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/packages`);
      const json = await res.json();
      if (json.success) {
        setPackages(json.data || []);
      }
    } catch (err) {
      console.error("Error loading packages:", err);
    } finally {
      setLoadingPackages(false);
    }
  };

  useEffect(() => {
    loadPackages();
  }, [activeCase]);

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleVerify = async (evidenceId: string) => {
    setVerifyingId(evidenceId);
    try {
      const res = await fetch(`/api/evidence/${evidenceId}/verify`, { method: "POST" });
      const json = await res.json();
      if (json.success) {
        setVerifyMessage(prev => ({
          ...prev,
          [evidenceId]: json.data.is_match
            ? "SHA-256 verified intact with recorded hash."
            : `Hash mismatch! Computed: ${json.data.calculated_sha256?.slice(0, 16)}...`
        }));
        onRefreshEvidence();
      }
    } catch (err: any) {
      setVerifyMessage(prev => ({ ...prev, [evidenceId]: `Error: ${err.message}` }));
    } finally {
      setVerifyingId(null);
    }
  };

  const handlePackageUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCase || !packageFile) return;

    setUploadingPackage(true);
    setPackageUploadError(null);
    try {
      const formData = new FormData();
      formData.append("file", packageFile);
      if (expectedHash.trim()) {
        formData.append("expected_sha256", expectedHash.trim());
      }

      const res = await fetch(`/api/cases/${activeCase.id}/packages/upload`, {
        method: "POST",
        body: formData
      });
      const json = await res.json();
      if (json.success) {
        setIsPackageUploadOpen(false);
        setPackageFile(null);
        setExpectedHash("");
        await loadPackages();
        onRefreshEvidence();
      } else {
        throw new Error(json.error || "Failed to import evidence package.");
      }
    } catch (err: any) {
      setPackageUploadError(err.message);
    } finally {
      setUploadingPackage(false);
    }
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <ShieldCheck size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">
          Please select an investigation case from the sidebar or cases tab to access the Evidence Vault.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Vault Header Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
            <ShieldCheck size={14} className="text-[#D96A9B]" />
            <span>Evidence Vault &amp; Cryptographic Store</span>
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            {activeCase.name} <span className="text-xs font-mono font-normal text-[#746B80]">({activeCase.id})</span>
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5">
            Preserved byte copies, standardized <code className="font-mono text-[11px]">FX-ACQ-*.forenx.zip</code> archives, and SHA-256 chain of custody receipts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPackageUploadOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg border border-[#6D3FC0] text-[#6D3FC0] bg-[#FAF7FE] hover:bg-[#F2ECFA] transition-colors shadow-xs"
          >
            <Archive size={14} />
            <span>Import Package (.forenx.zip)</span>
          </button>
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-xs"
          >
            <UploadCloud size={14} />
            <span>Import Raw DB</span>
          </button>
        </div>
      </div>

      {/* Forensic Policy Notice */}
      <div className="bg-[#FAF7FE] border border-[#E8E0EF] rounded-xl p-4 text-xs text-[#282235] flex items-start gap-3">
        <Info size={18} className="text-[#6D3FC0] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-[#43206F]">Dual-Level Forensic Integrity Assurance:</div>
          <p className="text-[#746B80] leading-relaxed">
            Outer archive files (<code className="font-mono bg-purple-50 px-1 py-0.5 rounded text-[11px]">FX-ACQ-*.forenx.zip</code>) possess an external package SHA-256 stored strictly outside the zip. Internal artifact databases possess independent SHA-256 hashes recorded inside the signed manifest. Path traversal, symlink escapes, and zip bombs are strictly validated and rejected upon ingestion.
          </p>
        </div>
      </div>

      {/* Vault Tabs */}
      <div className="flex border-b border-[#E8E0EF] gap-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab("artifacts")}
          className={`pb-3 flex items-center gap-2 transition-colors relative ${
            activeTab === "artifacts"
              ? "text-[#6D3FC0] font-bold border-b-2 border-[#6D3FC0]"
              : "text-[#746B80] hover:text-[#43206F]"
          }`}
        >
          <Database size={15} />
          <span>Extracted Artifact Files ({evidenceItems.length})</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("packages");
            loadPackages();
          }}
          className={`pb-3 flex items-center gap-2 transition-colors relative ${
            activeTab === "packages"
              ? "text-[#6D3FC0] font-bold border-b-2 border-[#6D3FC0]"
              : "text-[#746B80] hover:text-[#43206F]"
          }`}
        >
          <Archive size={15} />
          <span>Evidence Packages ({packages.length})</span>
        </button>
      </div>

      {/* Tab 1: Extracted Evidence Artifacts */}
      {activeTab === "artifacts" && (
        <>
          {evidenceItems.length === 0 ? (
            <div className="bg-white rounded-xl border border-[#E8E0EF] p-12 text-center shadow-xs">
              <Database size={40} className="mx-auto text-[#6D3FC0]/40 mb-3" />
              <h2 className="text-base font-bold text-[#43206F] mb-1">No Evidence Imported Yet</h2>
              <p className="text-xs text-[#746B80] max-w-sm mx-auto mb-4">
                Import an authorized browser history database or run Local / Remote Forensics to acquire artifacts.
              </p>
              <button
                onClick={onOpenUpload}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
              >
                Import First Artifact
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {evidenceItems.map(item => {
                const isVerified = item.verification_status === "verified";
                const msg = verifyMessage[item.id];
                return (
                  <div
                    key={item.id}
                    className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs space-y-4"
                  >
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-[#F2ECFA] flex items-center justify-center text-[#6D3FC0] shrink-0">
                          <FileCode size={20} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-[#43206F]">{item.filename}</span>
                            <span className="text-[10px] font-mono text-[#746B80] bg-[#FAF7FE] border border-[#E8E0EF] px-1.5 py-0.5 rounded">
                              {item.id}
                            </span>
                            <span className="text-[10px] font-semibold text-[#6D3FC0] bg-[#F2ECFA] px-2 py-0.5 rounded-full">
                              {item.evidence_type}
                            </span>
                          </div>
                          <div className="text-xs text-[#746B80] mt-0.5">
                            Size: <strong>{(item.byte_size / 1024).toFixed(1)} KB</strong> ({item.byte_size.toLocaleString()} bytes) | Imported: {new Date(item.imported_at).toLocaleString()}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1 ${
                            isVerified
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {isVerified ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
                          <span>{item.verification_status.toUpperCase()}</span>
                        </span>

                        <button
                          onClick={() => handleVerify(item.id)}
                          disabled={verifyingId === item.id}
                          className="flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] disabled:opacity-50"
                        >
                          <RefreshCw size={13} className={verifyingId === item.id ? "animate-spin" : ""} />
                          <span>{verifyingId === item.id ? "Verifying..." : "Re-Verify"}</span>
                        </button>
                      </div>
                    </div>

                    {/* SHA-256 Hash Display */}
                    <div className="bg-[#FAF7FE] p-3 rounded-lg border border-[#E8E0EF] flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 overflow-hidden">
                        <span className="text-[10px] font-bold text-[#746B80] uppercase tracking-wider shrink-0">
                          SHA-256:
                        </span>
                        <span className="font-mono text-[#282235] text-[11px] truncate">{item.sha256}</span>
                      </div>
                      <button
                        onClick={() => handleCopy(item.sha256)}
                        className="flex items-center gap-1 text-[11px] text-[#6D3FC0] hover:text-[#43206F] shrink-0 font-medium ml-2"
                      >
                        {copiedHash === item.sha256 ? <Check size={13} /> : <Copy size={13} />}
                        <span>{copiedHash === item.sha256 ? "Copied" : "Copy"}</span>
                      </button>
                    </div>

                    {/* Provenance notes */}
                    {item.provenance_notes && (
                      <div className="text-xs text-[#746B80]">
                        <span className="font-semibold text-[#43206F]">Provenance &amp; Notes:</span>{" "}
                        {item.provenance_notes}
                      </div>
                    )}

                    {/* Verification result message */}
                    {msg && (
                      <div
                        className={`p-2.5 rounded-lg text-xs font-medium ${
                          msg.includes("verified")
                            ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                            : "bg-rose-50 text-rose-800 border border-rose-200"
                        }`}
                      >
                        {msg}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Tab 2: Standardized Evidence Packages */}
      {activeTab === "packages" && (
        <>
          {packages.length === 0 ? (
            <div className="bg-white rounded-xl border border-[#E8E0EF] p-12 text-center shadow-xs">
              <Archive size={40} className="mx-auto text-[#6D3FC0]/40 mb-3" />
              <h2 className="text-base font-bold text-[#43206F] mb-1">No Evidence Packages Recorded</h2>
              <p className="text-xs text-[#746B80] max-w-sm mx-auto mb-4">
                Evidence packages are created automatically during Local or Remote Forensics, or imported via offline Field Collector archives.
              </p>
              <button
                onClick={() => setIsPackageUploadOpen(true)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
              >
                Import .forenx.zip Archive
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {packages.map(pkg => (
                <div
                  key={pkg.id}
                  className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs space-y-4"
                >
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-[#FCEAF2] flex items-center justify-center text-[#D96A9B] shrink-0">
                        <Archive size={20} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-[#43206F] font-mono">
                            {pkg.package_filename}
                          </span>
                          <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full">
                            Manifest v{pkg.manifest_version}
                          </span>
                        </div>
                        <div className="text-xs text-[#746B80] mt-0.5">
                          Method: <strong>{pkg.acquisition_method}</strong> • Size:{" "}
                          <strong>{(pkg.byte_size / 1024).toFixed(1)} KB</strong> • Created:{" "}
                          {new Date(pkg.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs font-bold px-2.5 py-1 rounded-full flex items-center gap-1 ${
                          pkg.verification_status === "verified"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        <ShieldCheck size={14} />
                        <span>{pkg.verification_status.toUpperCase()}</span>
                      </span>

                      <button
                        onClick={() => setInspectingPackage(pkg)}
                        className="px-3 py-1 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE]"
                      >
                        Inspect Manifest
                      </button>
                    </div>
                  </div>

                  {/* Package SHA-256 */}
                  <div className="bg-[#FAF7FE] p-3 rounded-lg border border-[#E8E0EF] flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <span className="text-[10px] font-bold text-[#746B80] uppercase tracking-wider shrink-0">
                        External Package SHA-256:
                      </span>
                      <span className="font-mono text-[#282235] text-[11px] truncate">
                        {pkg.package_sha256}
                      </span>
                    </div>
                    <button
                      onClick={() => handleCopy(pkg.package_sha256)}
                      className="flex items-center gap-1 text-[11px] text-[#6D3FC0] hover:text-[#43206F] shrink-0 font-medium ml-2"
                    >
                      {copiedHash === pkg.package_sha256 ? <Check size={13} /> : <Copy size={13} />}
                      <span>{copiedHash === pkg.package_sha256 ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Modal: Upload Package */}
      {isPackageUploadOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-[#E8E0EF] space-y-5 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-[#E8E0EF] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-[#FCEAF2] flex items-center justify-center text-[#D96A9B]">
                  <Archive size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#43206F]">Import Portable Evidence Package</h3>
                  <p className="text-[11px] text-[#746B80]">Standardized .forenx.zip archive with cryptographic manifest</p>
                </div>
              </div>
              <button
                onClick={() => setIsPackageUploadOpen(false)}
                className="text-[#746B80] hover:text-[#43206F] p-1 rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            {packageUploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
                <AlertTriangle size={15} className="shrink-0" />
                <span>{packageUploadError}</span>
              </div>
            )}

            <form onSubmit={handlePackageUploadSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#282235] mb-1">
                  Select Evidence Package (.forenx.zip) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="file"
                  required
                  accept=".zip,.forenx.zip"
                  onChange={e => setPackageFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-[#746B80] file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-[#F2ECFA] file:text-[#6D3FC0] hover:file:bg-[#e6dbf5] cursor-pointer border border-[#E8E0EF] rounded-lg p-1.5"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#282235] mb-1">
                  Expected Package SHA-256 (Optional Transport Hash)
                </label>
                <input
                  type="text"
                  placeholder="e.g., e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                  value={expectedHash}
                  onChange={e => setExpectedHash(e.target.value)}
                  className="w-full px-3 py-2 bg-[#FAF7FE] border border-[#E8E0EF] rounded-lg text-xs font-mono focus:ring-1 focus:ring-[#6D3FC0] focus:outline-none"
                />
                <p className="text-[10px] text-[#746B80] mt-1">
                  If provided, Workbench guarantees strict match against transport custody records before extracting.
                </p>
              </div>

              <div className="bg-[#FAF7FE] p-3 rounded-lg border border-[#E8E0EF] text-[10px] text-[#746B80] space-y-1">
                <div className="font-semibold text-[#43206F]">Safe Ingestion Controls:</div>
                <ul className="list-disc list-inside space-y-0.5">
                  <li>Path traversal protection (<code className="font-mono">../</code> escapes rejected).</li>
                  <li>Max archive uncompressed limit of 1GB &amp; 10,000 files.</li>
                  <li>Dual-hash verification of each extracted artifact against inner manifest.</li>
                </ul>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#E8E0EF]">
                <button
                  type="button"
                  onClick={() => setIsPackageUploadOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] text-[#746B80] hover:bg-[#FAF7FE]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploadingPackage || !packageFile}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] disabled:opacity-50"
                >
                  {uploadingPackage ? "Verifying & Ingesting..." : "Ingest Package"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Inspect Package Manifest */}
      {inspectingPackage && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-[#E8E0EF] space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-[#E8E0EF] pb-3">
              <div>
                <h3 className="text-sm font-bold text-[#43206F]">Evidence Package Manifest</h3>
                <p className="text-[11px] font-mono text-[#746B80]">{inspectingPackage.package_filename}</p>
              </div>
              <button
                onClick={() => setInspectingPackage(null)}
                className="text-[#746B80] hover:text-[#43206F] p-1 rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-3 bg-[#FAF7FE] p-3 rounded-xl border border-[#E8E0EF]">
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Package ID</div>
                  <div className="font-mono text-[11px] text-[#43206F]">{inspectingPackage.id}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Method</div>
                  <div className="font-semibold text-[#282235]">{inspectingPackage.acquisition_method}</div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Verification Status</div>
                  <div className="font-bold text-emerald-700 capitalize">
                    {inspectingPackage.verification_status}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-[#746B80] uppercase font-bold">Artifacts Included</div>
                  <div className="font-semibold text-[#282235]">{inspectingPackage.artifact_count} artifacts</div>
                </div>
              </div>

              <div>
                <div className="text-[11px] font-bold text-[#43206F] mb-1">Raw manifest.json:</div>
                <pre className="bg-slate-900 text-slate-100 p-3 rounded-xl text-[10px] font-mono overflow-x-auto max-h-60">
                  {inspectingPackage.manifest_json || "No raw manifest stored."}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#E8E0EF]">
              <button
                onClick={() => setInspectingPackage(null)}
                className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
