import React, { useState, useEffect } from "react";
import { Settings, Server, Database, Folder, Shield, HardDrive } from "lucide-react";

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch("/api/settings")
      .then(res => res.json())
      .then(json => {
        if (json.success) setSettings(json.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
          <Settings size={15} />
          <span>Workbench Environment</span>
        </div>
        <h2 className="text-lg font-bold text-[#43206F]">Configuration &amp; Storage Health</h2>
        <p className="text-xs text-[#746B80] mt-0.5">
          Local-first storage topology, security thresholds, and database configuration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Storage Paths */}
        <div className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-[#43206F]">
            <Folder size={16} className="text-[#6D3FC0]" />
            <span>Dedicated Storage Directories</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[#746B80] block mb-0.5">Application Data Directory:</span>
              <code className="bg-[#FAF7FE] p-2 rounded block font-mono text-[11px] text-[#282235] border border-[#E8E0EF] break-all">
                {settings?.data_dir || "Loading..."}
              </code>
            </div>

            <div>
              <span className="text-[#746B80] block mb-0.5">Evidence Vault (Preserved Originals):</span>
              <code className="bg-[#FAF7FE] p-2 rounded block font-mono text-[11px] text-[#282235] border border-[#E8E0EF] break-all">
                {settings?.evidence_dir || "Loading..."}
              </code>
            </div>

            <div>
              <span className="text-[#746B80] block mb-0.5">Working Copies (Non-Destructive Analysis):</span>
              <code className="bg-[#FAF7FE] p-2 rounded block font-mono text-[11px] text-[#282235] border border-[#E8E0EF] break-all">
                {settings?.working_dir || "Loading..."}
              </code>
            </div>

            <div>
              <span className="text-[#746B80] block mb-0.5">Exported Reports Destination:</span>
              <code className="bg-[#FAF7FE] p-2 rounded block font-mono text-[11px] text-[#282235] border border-[#E8E0EF] break-all">
                {settings?.reports_dir || "Loading..."}
              </code>
            </div>
          </div>
        </div>

        {/* Security & System Info */}
        <div className="bg-white rounded-xl border border-[#E8E0EF] p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-[#43206F]">
            <Shield size={16} className="text-[#6D3FC0]" />
            <span>Security &amp; Ingestion Limits</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
              <span className="text-[#746B80]">Max Import Size:</span>
              <span className="font-semibold text-[#282235]">
                {settings?.max_import_size_bytes ? `${settings.max_import_size_bytes / (1024 * 1024)} MB` : "500 MB"}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
              <span className="text-[#746B80]">Display Timezone:</span>
              <span className="font-semibold text-[#282235]">
                {settings?.display_timezone || "UTC (Coordinated Universal Time)"}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
              <span className="text-[#746B80]">ForenX Core Version:</span>
              <span className="font-mono font-bold text-[#6D3FC0]">
                {settings?.app_version || "1.0.0"}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#FAF7FE] border border-[#E8E0EF]">
              <span className="text-[#746B80]">Database Architecture:</span>
              <span className="font-semibold text-emerald-800">
                SQLite 3 (WAL mode &amp; Foreign Keys ON)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
