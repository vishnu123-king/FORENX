"""
Forensic Report Generation engine for ForenX.
Supports self-contained HTML (with ForenX design system styling and XSS-safe escaping),
structured deterministic JSON, and CSV export.
"""

import csv
import html
import io
import json
from pathlib import Path
from typing import Any

from forenx.acquisition import list_case_evidence
from forenx.audit import get_audit_entries, log_audit
from forenx.cases import get_case
from forenx.config import get_config
from forenx.events import list_events
from forenx.models import utc_now_iso
from forenx.services.analysis_service import list_case_analysis_runs
from forenx.validation import list_validation_runs

LIMITATIONS_DISCLAIMER = (
    "ForenX is an academic research and validation workbench, not a certified legal acquisition suite. "
    "Calculated hashes verify byte-consistency against recorded hashes at verification time, but do not "
    "prove origin authenticity prior to acquisition. Extracted browser records reflect supported schemas "
    "only and do not guarantee recovery of deleted records, ephemeral private sessions, or uncommitted SQLite WAL data."
)

SUPPORTED_SCOPE_STATEMENT = (
    "Supported artifact sources: Chromium History (Google Chrome, Microsoft Edge, Brave, Chromium engines; tables 'urls', 'visits', 'downloads') "
    "and Mozilla Firefox places.sqlite (tables 'moz_places', 'moz_historyvisits', 'moz_bookmarks'). Excluded data: session secrets, credentials, "
    "cookies, autofill, and passwords."
)

def build_case_report_data(case_id: str) -> dict[str, Any]:
    """Compile comprehensive investigation data structure for reporting."""
    case = get_case(case_id)
    evidence_items = list_case_evidence(case_id)
    analysis_runs = list_case_analysis_runs(case_id)
    events, total_events = list_events(case_id, limit=2000)
    validation_runs = list_validation_runs(case_id)
    audit_entries = get_audit_entries(case_id, limit=50)

    return {
        "forenx_version": "1.0.0",
        "generated_at_utc": utc_now_iso(),
        "case": case.to_dict(),
        "evidence_items": [e.to_dict() for e in evidence_items],
        "analysis_runs": [r.to_dict() for r in analysis_runs],
        "total_events_count": total_events,
        "sample_events": [ev.to_dict() for ev in events],
        "validation_runs": validation_runs,
        "audit_entries": [a.to_dict() for a in audit_entries],
        "limitations_statement": LIMITATIONS_DISCLAIMER,
        "supported_scope": SUPPORTED_SCOPE_STATEMENT
    }

def export_case_json(case_id: str) -> str:
    """Generate structured, deterministic JSON report."""
    data = build_case_report_data(case_id)
    return json.dumps(data, indent=2, sort_keys=True)

def export_timeline_csv(case_id: str) -> str:
    """Generate CSV string of timeline events for spreadsheet analysis."""
    events, _ = list_events(case_id, limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Event ID", "Normalized UTC", "Browser Family", "Event Type",
        "URL", "Title", "Raw Timestamp", "Timestamp Format",
        "Conversion Status", "Source Database", "Source Table",
        "Source Record ID", "Parser Version", "Warnings"
    ])

    for ev in events:
        writer.writerow([
            ev.id,
            ev.normalized_utc or "",
            ev.browser_family,
            ev.event_type,
            ev.url,
            ev.title,
            ev.raw_timestamp,
            ev.timestamp_format,
            ev.conversion_status,
            ev.source_database,
            ev.source_table,
            ev.source_record_id,
            ev.parser_version,
            ev.warning
        ])

    return output.getvalue()

def export_case_html(case_id: str) -> str:
    """Generate self-contained, XSS-safe HTML investigation report."""
    data = build_case_report_data(case_id)
    c = data["case"]

    # Safe escaping helper
    def esc(val: Any) -> str:
        return html.escape(str(val or ""))

    # Evidence rows
    evidence_rows = ""
    for ev in data["evidence_items"]:
        v_class = "status-verified" if ev["verification_status"] == "verified" else "status-failed"
        evidence_rows += f"""
        <tr>
            <td><code>{esc(ev['id'])}</code></td>
            <td><strong>{esc(ev['filename'])}</strong></td>
            <td>{esc(ev['evidence_type'])}</td>
            <td>{ev['byte_size']:,} B</td>
            <td><code class="hash-code">{esc(ev['sha256'])}</code></td>
            <td><span class="badge {v_class}">{esc(ev['verification_status'])}</span></td>
            <td>{esc(ev['imported_at'])}</td>
        </tr>
        """

    # Events rows
    event_rows = ""
    for item in data["sample_events"][:150]:
        c_badge = "status-verified" if item["conversion_status"] == "success" else "status-warning"
        event_rows += f"""
        <tr>
            <td><small>{esc(item['normalized_utc'])}</small></td>
            <td><strong>{esc(item['browser_family'])}</strong></td>
            <td><span class="badge badge-subtle">{esc(item['event_type'])}</span></td>
            <td class="url-col"><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">{esc(item['url'])}</a></td>
            <td>{esc(item['title'])}</td>
            <td><code>{esc(item['source_database'])}:{esc(item['source_record_id'])}</code></td>
            <td><span class="badge {c_badge}">{esc(item['conversion_status'])}</span></td>
        </tr>
        """

    # Validation runs
    val_rows = ""
    for v in data["validation_runs"]:
        val_rows += f"""
        <tr>
            <td><code>{esc(v['id'])}</code></td>
            <td>{esc(v['dataset_version'])}</td>
            <td>{v['expected_count']}</td>
            <td>{v['matched_count']}</td>
            <td>{v['missing_count']}</td>
            <td>{v['unexpected_count']}</td>
            <td><strong>{v['precision'] * 100:.1f}%</strong></td>
            <td><strong>{v['recall'] * 100:.1f}%</strong></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ForenX Forensic Report — Case {esc(c['id'])}</title>
<style>
  :root {{
    --primary-purple: #6D3FC0;
    --deep-purple: #43206F;
    --lavender: #F2ECFA;
    --pale-lavender: #FAF7FE;
    --rose-pink: #D96A9B;
    --soft-pink: #FCEAF2;
    --text-primary: #282235;
    --text-secondary: #746B80;
    --border: #E8E0EF;
    --success: #287D60;
    --warning: #A66B13;
    --error: #B83D5B;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: var(--pale-lavender);
    color: var(--text-primary);
    margin: 0;
    padding: 30px;
    line-height: 1.5;
  }}
  .report-header {{
    background: white;
    border: 1px solid var(--border);
    border-top: 5px solid var(--primary-purple);
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 4px rgba(67, 32, 111, 0.04);
  }}
  .report-title {{
    font-size: 26px;
    font-weight: 700;
    color: var(--deep-purple);
    margin: 0 0 8px 0;
  }}
  .report-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 14px;
    border-top: 1px solid var(--border);
    padding-top: 12px;
  }}
  .card {{
    background: white;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px rgba(67, 32, 111, 0.02);
  }}
  .card-title {{
    font-size: 18px;
    font-weight: 600;
    color: var(--deep-purple);
    margin-top: 0;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    text-align: left;
  }}
  th {{
    background-color: var(--lavender);
    color: var(--deep-purple);
    font-weight: 600;
    padding: 10px 12px;
    border-bottom: 2px solid var(--border);
  }}
  td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }}
  tr:nth-child(even) {{ background-color: var(--pale-lavender); }}
  .hash-code {{
    font-size: 11px;
    background: #f1edfa;
    padding: 2px 6px;
    border-radius: 4px;
    word-break: break-all;
  }}
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
  }}
  .status-verified {{ background: #e3f7ed; color: var(--success); }}
  .status-failed {{ background: #fbebee; color: var(--error); }}
  .status-warning {{ background: #fef4e5; color: var(--warning); }}
  .badge-subtle {{ background: var(--lavender); color: var(--deep-purple); }}
  .disclaimer-box {{
    background-color: var(--soft-pink);
    border-left: 4px solid var(--rose-pink);
    padding: 16px;
    border-radius: 4px;
    font-size: 12px;
    color: #5c203b;
    margin-top: 24px;
  }}
  .url-col {{
    max-width: 320px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
</style>
</head>
<body>

<div class="report-header">
  <div class="report-title">ForenX Investigation &amp; Evidence Report</div>
  <div style="font-size: 15px; color: var(--text-secondary);">Case: <strong>{esc(c['name'])}</strong> (<code>{esc(c['id'])}</code>)</div>
  <div class="report-meta">
    <div>Investigator: <strong>{esc(c['investigator_label'] or 'Unassigned')}</strong></div>
    <div>Status: <strong>{esc(c['status'].upper())}</strong></div>
    <div>Report Generated (UTC): <strong>{esc(data['generated_at_utc'])}</strong></div>
    <div>ForenX Core: <strong>v{esc(data['forenx_version'])}</strong></div>
  </div>
</div>

<div class="card">
  <h3 class="card-title">Case Metadata &amp; Objectives</h3>
  <p><strong>Description:</strong> {esc(c['description'] or 'No description provided.')}</p>
  <p><strong>Investigator Notes:</strong> {esc(c['notes'] or 'None.')}</p>
  <p><strong>Created:</strong> {esc(c['created_at'])} | <strong>Last Updated:</strong> {esc(c['updated_at'])}</p>
</div>

<div class="card">
  <h3 class="card-title">Evidence Inventory &amp; Integrity Verification Manifest</h3>
  <table>
    <thead>
      <tr>
        <th>Evidence ID</th>
        <th>Original Filename</th>
        <th>Artifact Type</th>
        <th>File Size</th>
        <th>Recorded SHA-256 Hash</th>
        <th>Integrity Verification</th>
        <th>Imported (UTC)</th>
      </tr>
    </thead>
    <tbody>
      {evidence_rows if evidence_rows else '<tr><td colspan="7">No evidence items registered in this case.</td></tr>'}
    </tbody>
  </table>
</div>

<div class="card">
  <h3 class="card-title">Unified Timeline Events (First {len(data['sample_events'][:150])} of {data['total_events_count']} Records)</h3>
  <table>
    <thead>
      <tr>
        <th>Normalized UTC</th>
        <th>Browser</th>
        <th>Event Type</th>
        <th>URL</th>
        <th>Title</th>
        <th>Source Reference</th>
        <th>Timestamp Status</th>
      </tr>
    </thead>
    <tbody>
      {event_rows if event_rows else '<tr><td colspan="7">No extracted events available.</td></tr>'}
    </tbody>
  </table>
</div>

{f'''
<div class="card">
  <h3 class="card-title">Known-Answer Validation Lab Results</h3>
  <table>
    <thead>
      <tr>
        <th>Run ID</th>
        <th>Dataset Version</th>
        <th>Expected</th>
        <th>Matched</th>
        <th>Missing</th>
        <th>Unexpected</th>
        <th>Precision</th>
        <th>Recall</th>
      </tr>
    </thead>
    <tbody>
      {val_rows}
    </tbody>
  </table>
</div>
''' if val_rows else ''}

<div class="disclaimer-box">
  <strong>Forensic Scope &amp; Legal Admissibility Disclaimer:</strong><br>
  {esc(data['limitations_statement'])}
  <br><br>
  <strong>Supported Technical Scope:</strong><br>
  {esc(data['supported_scope'])}
</div>

</body>
</html>
"""
    return html_content

def generate_case_report_bundle(case_id: str, target_dir: Path | None = None) -> dict[str, str]:
    """Generate and write JSON, CSV, and HTML reports to disk."""
    cfg = get_config()
    out_dir = Path(target_dir) if target_dir else cfg.reports_dir / case_id
    out_dir.mkdir(parents=True, exist_ok=True)

    html_file = out_dir / f"forenx_report_{case_id}.html"
    json_file = out_dir / f"forenx_report_{case_id}.json"
    csv_file = out_dir / f"forenx_timeline_{case_id}.csv"

    html_content = export_case_html(case_id)
    json_content = export_case_json(case_id)
    csv_content = export_timeline_csv(case_id)

    html_file.write_text(html_content, encoding="utf-8")
    json_file.write_text(json_content, encoding="utf-8")
    csv_file.write_text(csv_content, encoding="utf-8")

    log_audit(
        operation="report_exported",
        case_id=case_id,
        outcome="success",
        details=f"Exported HTML, JSON, and CSV reports to '{out_dir}'."
    )

    return {
        "html_path": str(html_file),
        "json_path": str(json_file),
        "csv_path": str(csv_file)
    }
