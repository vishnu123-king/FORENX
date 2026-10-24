import React, { useState, useEffect } from "react";
import { Case, ForensicEvent } from "../../types/forenx";
import {
  Clock,
  Search,
  Filter,
  ExternalLink,
  ChevronRight,
  Database,
  ArrowUpDown,
  Download
} from "lucide-react";

interface UnifiedTimelinePageProps {
  activeCase: Case | null;
  onSelectEvent: (event: ForensicEvent) => void;
}

export const UnifiedTimelinePage: React.FC<UnifiedTimelinePageProps> = ({
  activeCase,
  onSelectEvent
}) => {
  const [events, setEvents] = useState<ForensicEvent[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [browserFilter, setBrowserFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const fetchTimeline = async () => {
    if (!activeCase) return;
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (browserFilter !== "all") params.set("browser", browserFilter);
      if (typeFilter !== "all") params.set("event_type", typeFilter);
      if (searchTerm.trim()) params.set("search", searchTerm.trim());
      params.set("limit", "250");

      const res = await fetch(`/api/cases/${activeCase.id}/timeline?${params.toString()}`);
      const json = await res.json();
      if (json.success) {
        setEvents(json.data.events || []);
        setTotalCount(json.data.total_count || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [activeCase?.id, browserFilter, typeFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTimeline();
  };

  if (!activeCase) {
    return (
      <div className="p-12 text-center text-[#746B80] max-w-lg mx-auto">
        <Clock size={48} className="mx-auto text-[#6D3FC0]/40 mb-3" />
        <h2 className="text-base font-bold text-[#43206F]">No Active Case Selected</h2>
        <p className="text-xs text-[#746B80] mt-1">Select an active case to reconstruct the unified cross-browser event timeline.</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Timeline Controls */}
      <div className="bg-white p-5 rounded-xl border border-[#E8E0EF] shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <div className="text-xs font-bold text-[#6D3FC0] uppercase tracking-wider">
              Unified Forensic Timeline
            </div>
            <h2 className="text-lg font-bold text-[#43206F]">
              Chronological Event Reconstruction
            </h2>
            <p className="text-xs text-[#746B80] mt-0.5">
              Normalizes WebKit (1601 UTC microseconds) and Firefox PRTime (1970 UTC microseconds) into a verifiable ISO-8601 sequence.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-[#FAF7FE] border border-[#E8E0EF] text-[#43206F]">
              {events.length} of {totalCount} events
            </span>
          </div>
        </div>

        {/* Filter Bar */}
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 pt-3 border-t border-[#E8E0EF]">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-2.5 text-[#746B80]" size={15} />
            <input
              type="text"
              placeholder="Search by URL or Page Title..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-[#E8E0EF] rounded-lg bg-white text-[#282235] focus:outline-none focus:ring-2 focus:ring-[#6D3FC0]/30"
            />
          </div>

          <select
            value={browserFilter}
            onChange={e => setBrowserFilter(e.target.value)}
            className="text-xs border border-[#E8E0EF] rounded-lg px-3 py-1.5 bg-white text-[#282235] focus:outline-none"
          >
            <option value="all">All Browsers</option>
            <option value="Chromium">Chromium / Chrome</option>
            <option value="Firefox">Mozilla Firefox</option>
          </select>

          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="text-xs border border-[#E8E0EF] rounded-lg px-3 py-1.5 bg-white text-[#282235] focus:outline-none"
          >
            <option value="all">All Event Types</option>
            <option value="url_visit">URL Visits</option>
            <option value="download">Downloads</option>
            <option value="bookmark">Bookmarks</option>
          </select>

          <button
            type="submit"
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-[#6D3FC0] text-white hover:bg-[#5b33a5] transition-colors"
          >
            Filter
          </button>
        </form>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-xl border border-[#E8E0EF] shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-[#746B80]">Loading chronological events...</div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-xs text-[#746B80]">
            No events found in timeline. Ensure evidence databases have been parsed in the Artifact Explorer.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-[#FAF7FE] text-[#746B80] border-b border-[#E8E0EF]">
                  <th className="p-3 font-semibold">Normalized UTC</th>
                  <th className="p-3 font-semibold">Browser</th>
                  <th className="p-3 font-semibold">Event Type</th>
                  <th className="p-3 font-semibold">Page Title &amp; Target URL</th>
                  <th className="p-3 font-semibold">Source Ref</th>
                  <th className="p-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8E0EF]">
                {events.map(ev => {
                  const isChrome = ev.browser_family === "Chromium";
                  return (
                    <tr
                      key={ev.id}
                      onClick={() => onSelectEvent(ev)}
                      className="hover:bg-[#FAF7FE] cursor-pointer transition-colors"
                    >
                      <td className="p-3 font-mono text-[11px] text-[#282235] whitespace-nowrap">
                        {ev.normalized_utc ? (
                          <span>{ev.normalized_utc.replace("T", " ").replace("+00:00", "Z")}</span>
                        ) : (
                          <span className="text-amber-700 font-bold bg-amber-50 px-1.5 py-0.5 rounded">
                            {ev.conversion_status.toUpperCase()}
                          </span>
                        )}
                      </td>

                      <td className="p-3 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isChrome
                              ? "bg-purple-100 text-purple-800"
                              : "bg-orange-100 text-orange-800"
                          }`}
                        >
                          {ev.browser_family}
                        </span>
                      </td>

                      <td className="p-3 whitespace-nowrap">
                        <span className="text-[11px] font-medium text-[#746B80] bg-[#FAF7FE] border border-[#E8E0EF] px-2 py-0.5 rounded">
                          {ev.event_type.replace("_", " ")}
                        </span>
                      </td>

                      <td className="p-3 max-w-md">
                        <div className="font-semibold text-[#282235] truncate">{ev.title || "No Title"}</div>
                        <div className="text-[11px] font-mono text-[#6D3FC0] truncate">{ev.url}</div>
                      </td>

                      <td className="p-3 whitespace-nowrap font-mono text-[11px] text-[#746B80]">
                        {ev.source_database}:{ev.source_table}#{ev.source_record_id}
                      </td>

                      <td className="p-3 text-right whitespace-nowrap">
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            onSelectEvent(ev);
                          }}
                          className="px-2.5 py-1 text-[11px] font-semibold text-[#6D3FC0] hover:bg-[#F2ECFA] rounded transition-colors"
                        >
                          Details →
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
