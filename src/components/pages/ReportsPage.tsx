import React, { useState, useEffect } from "react";
import { Case } from "../../types/forenx";
import { FileText, Download, FileSpreadsheet, Code2, AlertCircle, Eye } from "lucide-react";

interface ReportsPageProps {
  activeCase: Case | null;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ activeCase }) => {
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = async () => {
    if (!activeCase) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/cases/${activeCase.id}/report`);
      const json = await res.json();
      if (json.success) {
        setReportData(json.data);
      } else {
        throw new Error(json.error || "Failed to load report data");
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [activeCase?.id]);

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <FileText size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">Select an active investigation case to generate and export forensic reports.</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Export Banner */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider">
            Investigative Documentation &amp; Reporting
          </div>
          <h2 className="text-lg font-bold text-[#43206F]">
            Export Traceable Forensics Reports
          </h2>
          <p className="text-xs text-[#746B80] mt-0.5">
            Generates self-contained, XSS-safe HTML reports with ForenX typography and CSS, structured deterministic JSON, and timeline CSV tables.
          </p>
        </div>

        {reportData && (
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              onClick={() => downloadFile(reportData.html, `forenx_report_${activeCase.id}.html`, "text/html")}
              className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors shadow-sm"
            >
              <Download size={14} />
              <span>Export HTML</span>
            </button>

            <button
              onClick={() => downloadFile(reportData.json, `forenx_findings_${activeCase.id}.json`, "application/json")}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] transition-colors"
            >
              <Code2 size={14} />
              <span>Export JSON</span>
            </button>

            <button
              onClick={() => downloadFile(reportData.csv, `forenx_timeline_${activeCase.id}.csv`, "text/csv")}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-[#E8E0EF] bg-white text-[#43206F] hover:bg-[#FAF7FE] transition-colors"
            >
              <FileSpreadsheet size={14} />
              <span>Export CSV</span>
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-[#746B80]">Compiling investigation report bundle...</div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      ) : reportData?.html ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[#43206F] uppercase tracking-wider flex items-center gap-1.5">
              <Eye size={14} className="text-[#6D3FC0]" />
              <span>Report Live Preview</span>
            </h3>
            <span className="text-[11px] text-[#746B80]">Self-contained HTML view</span>
          </div>

          <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs overflow-hidden h-[650px]">
            <iframe
              srcDoc={reportData.html}
              title="Forensic Report Preview"
              className="w-full h-full border-0"
              sandbox="allow-same-origin"
            />
          </div>
        </div>
      ) : null}
    </div>
  );
};
