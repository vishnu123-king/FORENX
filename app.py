"""
ForenX: Cross-Platform Browser Artifact Forensics and Evidence Validation Workbench.
Streamlit application entry point.
"""

import sys
from pathlib import Path
import json

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed. Please run 'pip install streamlit' to launch the web dashboard.")
    sys.exit(1)

from forenx.config import get_config
from forenx.database import init_db
from forenx.cases import (
    create_case, list_cases, get_case, get_global_statistics, archive_case
)
from forenx.acquisition import (
    import_evidence, list_case_evidence, verify_case_evidence_item, get_evidence
)
from forenx.services.analysis_service import run_case_analysis, list_case_analysis_runs
from forenx.events import list_events, get_timeline_breakdown
from forenx.validation import evaluate_validation, list_validation_runs
from forenx.reporting import export_case_html, export_timeline_csv, export_case_json
from forenx.audit import get_audit_entries, verify_audit_chain
from forenx.cli import seed_synthetic_case
from tests.fixtures.synthetic_data import get_ground_truth_manifest
from ui.styles import FORENX_CSS

# Page Configuration
st.set_page_config(
    page_title="ForenX — Forensics & Validation Workbench",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply ForenX Design System CSS
st.markdown(FORENX_CSS, unsafe_allow_html=True)

# Ensure database is initialized
init_db()

# Navigation Sidebar
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #E8E0EF; margin-bottom: 15px;">
            <div style="font-size: 22px; font-weight: 800; color: #43206F; letter-spacing: -0.5px;">
                <span style="color: #6D3FC0;">FOREN</span><span style="color: #D96A9B;">X</span>
            </div>
            <div style="font-size: 11px; color: #746B80; margin-top: 2px;">
                Browser Artifact Forensics &amp; Validation Workbench
            </div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Cases",
            "Evidence Vault",
            "Artifact Explorer",
            "Unified Timeline",
            "Validation Lab",
            "Reports",
            "Audit Log",
            "Settings",
            "About"
        ],
        label_visibility="collapsed"
    )

    st.markdown("<hr style='border: 0; border-top: 1px solid #E8E0EF; margin: 20px 0 10px 0;'>", unsafe_allow_html=True)

    # Active Case Selector in Sidebar
    cases = list_cases()
    active_case_id = st.session_state.get("active_case_id")
    case_options = {c.id: f"{c.name} ({c.id})" for c in cases}

    if cases:
        default_index = 0
        if active_case_id and active_case_id in case_options:
            default_index = list(case_options.keys()).index(active_case_id)

        selected_case_id = st.selectbox(
            "Active Investigation Case:",
            options=list(case_options.keys()),
            format_func=lambda x: case_options[x],
            index=default_index
        )
        st.session_state["active_case_id"] = selected_case_id
    else:
        st.info("No cases created yet.")
        selected_case_id = None

# Render Selected View
if page == "Overview":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Forensic Operations Overview</h1>
            <div class="forenx-subtitle">Real-time repository statistics, integrity status, and recent investigation activity.</div>
        </div>
    """, unsafe_allow_html=True)

    stats = get_global_statistics()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Cases", stats["total_cases"])
    col2.metric("Evidence Items", stats["total_evidence"])
    col3.metric("Analysis Runs", stats["total_analysis_runs"])
    col4.metric("Extracted Events", stats["total_events"])
    col5.metric("Integrity Failures", stats["verification_failures"])

    st.markdown("<br>", unsafe_allow_html=True)

    if stats["total_cases"] == 0:
        st.markdown("""
            <div class="forenx-card" style="text-align: center; padding: 40px 20px;">
                <h3 style="color: #43206F;">No Investigation Cases Found</h3>
                <p style="color: #746B80; max-width: 500px; margin: 10px auto 20px auto;">
                    Initialize your forensic repository by creating an active investigation or loading the synthetic academic research dataset.
                </p>
            </div>
        """, unsafe_allow_html=True)

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Explore Synthetic Demo Dataset", type="primary", use_container_width=True):
                with st.spinner("Generating synthetic test cases and running validation..."):
                    res = seed_synthetic_case()
                    st.success(f"Loaded synthetic case: {res['case_name']}")
                    st.rerun()
    else:
        st.subheader("Recent Cases")
        case_rows = [{"ID": c.id, "Name": c.name, "Status": c.status.upper(), "Investigator": c.investigator_label or "Unassigned", "Updated": c.updated_at} for c in cases[:5]]
        st.dataframe(case_rows, use_container_width=True)

elif page == "Cases":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Investigation Cases</h1>
            <div class="forenx-subtitle">Create, preserve, and manage digital forensic cases with full provenance tracking.</div>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Case Directory", "Create New Case"])

    with tab1:
        search = st.text_input("Search cases by name, description, or investigator:")
        status_filter = st.selectbox("Status Filter:", ["all", "active", "archived", "closed"])
        filtered_cases = list_cases(status_filter=status_filter, search_query=search)

        for c in filtered_cases:
            with st.expander(f"📁 {c.name} ({c.id}) — {c.status.upper()}", expanded=(c.id == selected_case_id)):
                st.write(f"**Description:** {c.description or 'No description provided.'}")
                st.write(f"**Investigator:** {c.investigator_label or 'Unassigned'}")
                st.write(f"**Created:** {c.created_at} | **Updated:** {c.updated_at}")
                st.write(f"**Notes:** {c.notes or 'None'}")
                if st.button(f"Set as Active Case: {c.id}", key=f"sel_{c.id}"):
                    st.session_state["active_case_id"] = c.id
                    st.rerun()

    with tab2:
        with st.form("new_case_form"):
            c_name = st.text_input("Case Name *", placeholder="e.g. Incident 2026-B91 — Suspect Browser Audit")
            c_desc = st.text_area("Case Description", placeholder="Summary of investigation objectives...")
            c_inv = st.text_input("Lead Investigator Label", placeholder="e.g. Senior Analyst J. Doe")
            c_notes = st.text_area("Initial Provenance & Evidence Notes")
            submitted = st.form_submit_button("Create Case", type="primary")

            if submitted:
                if not c_name.strip():
                    st.error("Case name is required.")
                else:
                    new_case = create_case(name=c_name, description=c_desc, investigator_label=c_inv, notes=c_notes)
                    st.success(f"Case '{new_case.name}' created with ID: {new_case.id}")
                    st.session_state["active_case_id"] = new_case.id
                    st.rerun()

elif page == "Evidence Vault":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Evidence Vault &amp; Integrity Verification</h1>
            <div class="forenx-subtitle">Acquire authorized browser artifact databases, compute SHA-256 hashes, and verify integrity.</div>
        </div>
    """, unsafe_allow_html=True)

    if not selected_case_id:
        st.warning("Please select or create an investigation case first.")
    else:
        curr_case = get_case(selected_case_id)
        st.info(f"Active Case: **{curr_case.name}** (`{curr_case.id}`)")

        tab_ev1, tab_ev2 = st.tabs(["Evidence Inventory", "Import Evidence File"])

        with tab_ev1:
            evidence_items = list_case_evidence(selected_case_id)
            if not evidence_items:
                st.info("No evidence registered in this case vault yet.")
            else:
                for item in evidence_items:
                    with st.container():
                        col_e1, col_e2, col_e3 = st.columns([3, 2, 1])
                        with col_e1:
                            st.markdown(f"**📄 {item.filename}** (`{item.id}`)")
                            st.caption(f"Type: {item.evidence_type} | Size: {item.byte_size:,} bytes")
                            st.markdown(f"<code style='font-size: 11px;'>SHA-256: {item.sha256}</code>", unsafe_allow_html=True)
                        with col_e2:
                            st.caption(f"Imported: {item.imported_at}")
                            st.caption(f"Notes: {item.provenance_notes or 'None'}")
                        with col_e3:
                            badge_color = "#287D60" if item.verification_status == "verified" else "#B83D5B"
                            st.markdown(f"<span style='color: {badge_color}; font-weight: bold;'>Status: {item.verification_status.upper()}</span>", unsafe_allow_html=True)
                            if st.button("Re-verify Hash", key=f"ver_{item.id}"):
                                with st.spinner("Recomputing SHA-256..."):
                                    v_res = verify_case_evidence_item(item.id)
                                    if v_res["is_match"]:
                                        st.success("Integrity verified: SHA-256 matches recorded hash.")
                                    else:
                                        st.error(f"INTEGRITY FAILURE: computed {v_res.get('calculated_sha256')}")
                                    st.rerun()
                        st.markdown("<hr style='border: 0; border-top: 1px solid #E8E0EF; margin: 10px 0;'>", unsafe_allow_html=True)

        with tab_ev2:
            st.markdown("Upload or stage an authorized browser database file (e.g. `History` from Chrome/Edge, or `places.sqlite` from Firefox).")
            up_file = st.file_uploader("Select Evidence File:", type=["sqlite", "db", ""])
            notes = st.text_input("Acquisition / Provenance Notes:")

            if up_file is not None:
                if st.button("Acquire into Vault", type="primary"):
                    cfg = get_config()
                    staging_path = cfg.data_dir / "user_uploads" / up_file.name
                    staging_path.parent.mkdir(parents=True, exist_ok=True)
                    staging_path.write_bytes(up_file.getvalue())

                    try:
                        evi = import_evidence(
                            case_id=selected_case_id,
                            source_file_path=staging_path,
                            provenance_notes=notes
                        )
                        st.success(f"Evidence acquired: {evi.filename} (SHA-256: {evi.sha256[:16]}...)")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Acquisition error: {str(err)}")

elif page == "Artifact Explorer":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Artifact Explorer</h1>
            <div class="forenx-subtitle">Inspect low-level schemas, table structures, and run forensic extractions.</div>
        </div>
    """, unsafe_allow_html=True)

    if not selected_case_id:
        st.warning("Please select a case.")
    else:
        evidence_items = list_case_evidence(selected_case_id)
        runs = list_case_analysis_runs(selected_case_id)

        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            st.write(f"Registered evidence items: **{len(evidence_items)}** | Previous analysis runs: **{len(runs)}**")
        with col_run2:
            if st.button("Run Forensic Extraction", type="primary", use_container_width=True):
                with st.spinner("Executing read-only SQLite parser on working copy..."):
                    try:
                        run = run_case_analysis(selected_case_id)
                        st.success(f"Extraction complete: {run.records_extracted} records extracted, {run.warnings_count} warnings.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

        st.subheader("Analysis Runs History")
        if not runs:
            st.info("No analysis runs recorded for this case.")
        else:
            run_table = [
                {
                    "Run ID": r.id,
                    "Started": r.started_at,
                    "Completed": r.completed_at,
                    "Status": r.status.upper(),
                    "Records Seen": r.records_seen,
                    "Extracted": r.records_extracted,
                    "Warnings": r.warnings_count
                }
                for r in runs
            ]
            st.dataframe(run_table, use_container_width=True)

elif page == "Unified Timeline":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Unified Event Timeline</h1>
            <div class="forenx-subtitle">Chronological cross-browser timeline with raw timestamp retention and source traceability.</div>
        </div>
    """, unsafe_allow_html=True)

    if not selected_case_id:
        st.warning("Please select a case.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            browser_f = st.selectbox("Browser Family:", ["all", "Chromium", "Firefox"])
        with col_f2:
            type_f = st.selectbox("Event Type:", ["all", "url_visit", "download", "bookmark"])
        with col_f3:
            search_t = st.text_input("Filter URL / Title:")

        events, total_count = list_events(
            case_id=selected_case_id,
            browser_family=browser_f,
            event_type=type_f,
            search_term=search_t,
            limit=200
        )

        st.caption(f"Displaying **{len(events)}** of **{total_count}** matching timeline events.")

        if not events:
            st.info("No matching timeline events found.")
        else:
            table_data = [
                {
                    "Normalized UTC": ev.normalized_utc or "OUT_OF_RANGE",
                    "Browser": ev.browser_family,
                    "Type": ev.event_type,
                    "URL": ev.url,
                    "Title": ev.title or "",
                    "Raw Timestamp": ev.raw_timestamp,
                    "Source Table": f"{ev.source_database}:{ev.source_table}#{ev.source_record_id}",
                    "Status": ev.conversion_status
                }
                for ev in events
            ]
            st.dataframe(table_data, use_container_width=True)

elif page == "Validation Lab":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Validation Lab &amp; Ground-Truth Testing</h1>
            <div class="forenx-subtitle">Core Academic Contribution: evaluate extraction accuracy against known-answer test manifests.</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="notice-academic">
            <strong>ForenX Academic Research Objective:</strong><br>
            "How effectively can a source-traceable evidence-integrity and known-answer validation layer improve the reproducibility and verifiability of cross-browser artifact analysis?"
        </div>
    """, unsafe_allow_html=True)

    if not selected_case_id:
        st.warning("Please select a case.")
    else:
        manifest = get_ground_truth_manifest()
        st.write(f"Ground-Truth Evaluation Manifest: **{len(manifest)}** expected records.")

        if st.button("Execute Known-Answer Validation", type="primary"):
            events, _ = list_events(selected_case_id, limit=5000)
            with st.spinner("Evaluating expected vs actual records..."):
                val_res = evaluate_validation(
                    case_id=selected_case_id,
                    expected_manifest=manifest,
                    actual_events=events,
                    dataset_version="bench-groundtruth-v1.0"
                )
                st.success("Validation completed!")
                st.rerun()

        # Display Validation Run History
        v_runs = list_validation_runs(selected_case_id)
        if v_runs:
            latest = v_runs[0]
            col_v1, col_v2, col_v3, col_v4, col_v5 = st.columns(5)
            col_v1.metric("Precision", f"{latest['precision']*100:.1f}%" if latest['precision'] is not None else "N/A")
            col_v2.metric("Recall", f"{latest['recall']*100:.1f}%" if latest['recall'] is not None else "N/A")
            col_v3.metric("Expected Events", latest["expected_count"])
            col_v4.metric("Matched Events", latest["matched_count"])
            col_v5.metric("Missing Events", latest["missing_count"])

            st.markdown(f"**Latest Run Summary:** {latest['result_summary']}")

            details = latest.get("details", {})
            if details.get("field_mismatches"):
                st.warning(f"Field Mismatches: {len(details['field_mismatches'])}")
                st.json(details["field_mismatches"])

elif page == "Reports":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Forensic Investigation Reports</h1>
            <div class="forenx-subtitle">Export deterministic, traceable reports in HTML, JSON, and CSV.</div>
        </div>
    """, unsafe_allow_html=True)

    if not selected_case_id:
        st.warning("Please select a case.")
    else:
        st.subheader("Generate Export Bundle")
        col_r1, col_r2, col_r3 = st.columns(3)

        html_content = export_case_html(selected_case_id)
        json_content = export_case_json(selected_case_id)
        csv_content = export_timeline_csv(selected_case_id)

        with col_r1:
            st.download_button(
                label="Download HTML Report",
                data=html_content,
                file_name=f"forenx_report_{selected_case_id}.html",
                mime="text/html",
                use_container_width=True
            )
        with col_r2:
            st.download_button(
                label="Download JSON Findings",
                data=json_content,
                file_name=f"forenx_findings_{selected_case_id}.json",
                mime="application/json",
                use_container_width=True
            )
        with col_r3:
            st.download_button(
                label="Download CSV Timeline",
                data=csv_content,
                file_name=f"forenx_timeline_{selected_case_id}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Report Preview (HTML)")
        st.components.v1.html(html_content, height=600, scrolling=True)

elif page == "Audit Log":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Audit Log &amp; Cryptographic Chain of Custody</h1>
            <div class="forenx-subtitle">Tamper-evident log of all operations with SHA-256 hash chaining.</div>
        </div>
    """, unsafe_allow_html=True)

    is_intact, errors = verify_audit_chain()
    if is_intact:
        st.success("Audit Log Integrity: CRYPTOGRAPHIC CHAIN INTACT (VERIFIED)")
    else:
        st.error(f"Audit Log Integrity: TAMPER DETECTED ({len(errors)} errors)")
        for err in errors:
            st.write(f"- {err}")

    entries = get_audit_entries(limit=100)
    audit_data = [
        {
            "Timestamp (UTC)": a.timestamp_utc,
            "Operation": a.operation,
            "Case ID": a.case_id or "",
            "Outcome": a.outcome.upper(),
            "Details": a.details,
            "Entry Hash": a.entry_hash[:16] + "..."
        }
        for a in entries
    ]
    st.dataframe(audit_data, use_container_width=True)

elif page == "Settings":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">Settings &amp; Environment</h1>
            <div class="forenx-subtitle">Local storage directories, limits, and database health.</div>
        </div>
    """, unsafe_allow_html=True)

    cfg = get_config()
    st.write(f"**Data Directory:** `{cfg.data_dir}`")
    st.write(f"**Evidence Vault:** `{cfg.evidence_dir}`")
    st.write(f"**Working Directory:** `{cfg.working_dir}`")
    st.write(f"**Max Import Size:** `{cfg.max_import_size_bytes / (1024*1024):.0f} MB`")
    st.write(f"**Display Timezone:** `{cfg.display_timezone}`")
    st.write(f"**Version:** `{cfg.app_version}`")

elif page == "About":
    st.markdown("""
        <div class="forenx-header">
            <h1 class="forenx-title">About ForenX</h1>
            <div class="forenx-subtitle">Academic research context, architecture, and responsible use.</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        ### Academic Research Objective
        *"How effectively can a source-traceable evidence-integrity and known-answer validation layer improve the reproducibility and verifiability of cross-browser artifact analysis?"*

        ### Core Capabilities
        1. **Controlled Evidence Acquisition:** Non-destructive import with pre- and post-copy SHA-256 verification.
        2. **Multi-Browser Schema Parsers:** Extraction from Chromium `History` (Chrome, Edge) and Mozilla Firefox `places.sqlite`.
        3. **Normalized Timeline Reconstruction:** Microsecond-accurate WebKit and PRTime timestamp normalization to ISO-8601 UTC.
        4. **Known-Answer Validation Engine:** Precision, recall, and mismatch benchmarking against controlled ground-truth datasets.
        5. **Cryptographic Audit Log:** Tamper-evident SHA-256 chained operation logs.
        6. **Traceable Multi-Format Reporting:** Self-contained HTML, JSON, and CSV exports.

        ### Scope & Limitations
        ForenX is an academic research and validation workbench, not a certified forensic acquisition suite.
        Hashing establishes byte-consistency at verification time, not source authenticity prior to copying.
        Passwords, credentials, session secrets, and autofill values are strictly excluded.
    """)
