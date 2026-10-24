import React from "react";
import { Info, Award, ShieldAlert, Cpu, BookOpen, Scale } from "lucide-react";

export const AboutPage: React.FC = () => {
  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      {/* Hero Header */}
      <div className="bg-white p-6 rounded-xl border border-[#E8E0EF] shadow-xs">
        <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider flex items-center gap-1.5">
          <Info size={15} />
          <span>About ForenX</span>
        </div>
        <h2 className="text-xl font-bold text-[#43206F] mt-1">
          Cross-Platform Browser Artifact Forensics &amp; Evidence Validation Workbench
        </h2>
        <p className="text-xs text-[#746B80] mt-1">
          An academic research product engineered for digital forensic students, researchers, and incident responders.
        </p>
      </div>

      {/* Core Academic Contribution */}
      <div className="bg-[#FAF7FE] border-l-4 border-[#6D3FC0] p-5 rounded-r-xl border border-[#E8E0EF] shadow-xs space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[#6D3FC0] uppercase tracking-wider">
          <Award size={16} />
          <span>Primary Academic Research Objective</span>
        </div>
        <blockquote className="text-sm font-semibold text-[#43206F] italic">
          "How effectively can a source-traceable evidence-integrity and known-answer validation layer improve the reproducibility and verifiability of cross-browser artifact analysis?"
        </blockquote>
        <p className="text-xs text-[#746B80] leading-relaxed">
          Rather than relying on closed-box parsing, ForenX binds every extracted artifact to its physical source database, table, and row index, providing microsecond-level raw timestamp normalization and empirical Precision/Recall validation against ground-truth datasets.
        </p>
      </div>

      {/* Key Architectural Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs space-y-2">
          <div className="font-bold text-[#43206F] flex items-center gap-1.5">
            <Cpu size={15} className="text-[#6D3FC0]" />
            <span>Supported Browser Engines</span>
          </div>
          <p className="text-[#746B80]">
            • <strong>Chromium Family:</strong> Google Chrome, Microsoft Edge, Brave (SQLite <code className="font-mono bg-purple-50 px-1 py-0.5 rounded">History</code>: visits, URLs, transitions, downloads).
            <br />
            • <strong>Mozilla Firefox:</strong> Firefox (SQLite <code className="font-mono bg-purple-50 px-1 py-0.5 rounded">places.sqlite</code>: history visits, moz_places, bookmarks).
          </p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E8E0EF] shadow-xs space-y-2">
          <div className="font-bold text-[#43206F] flex items-center gap-1.5">
            <BookOpen size={15} className="text-[#6D3FC0]" />
            <span>Timestamp Normalization</span>
          </div>
          <p className="text-[#746B80]">
            Converts Chromium WebKit timestamps (microseconds since 1601-01-01 UTC) and Firefox PRTime timestamps (microseconds since 1970-01-01 UTC) into normalized ISO-8601 UTC with range and integrity verification.
          </p>
        </div>
      </div>

      {/* Limitations & Legal Notice */}
      <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-[#B83D5B] uppercase tracking-wider">
          <ShieldAlert size={16} />
          <span>Forensic Scope &amp; Limitations Notice</span>
        </div>
        <p className="text-xs text-[#746B80] leading-relaxed">
          ForenX is an <strong>academic forensic workbench</strong>, not a certified commercial acquisition suite. It does not claim legal admissibility, certified evidentiary status, or complete recovery of deleted records.
        </p>
        <p className="text-xs text-[#746B80] leading-relaxed">
          • <strong>Integrity vs Authenticity:</strong> A SHA-256 hash confirms consistency with recorded bytes at acquisition time, but does not prove the original file was authentic or unmanipulated prior to collection.
          <br />
          • <strong>Sensitive Data Exclusion:</strong> ForenX strictly excludes passwords, credentials, session secrets, autofill, and browser cookies.
        </p>
      </div>

      {/* Responsible Use */}
      <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs space-y-2 text-xs text-[#746B80]">
        <div className="flex items-center gap-2 font-bold text-[#43206F]">
          <Scale size={15} className="text-[#6D3FC0]" />
          <span>Responsible Use Statement</span>
        </div>
        <p>
          This software must be used strictly on authorized devices and test environments in compliance with applicable cybersecurity, privacy, and evidence handling laws.
        </p>
      </div>
    </div>
  );
};
