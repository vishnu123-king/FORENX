"""
Chromium History parser for ForenX.
Supports Google Chrome, Microsoft Edge, Brave, and compatible Chromium engines.
Extracts visits, URLs, transitions, and download events.
"""

import sqlite3
from pathlib import Path

from forenx.exceptions import CorruptDatabaseError, UnsupportedSchemaError
from forenx.models import Event, generate_id
from forenx.parsers.base import BaseBrowserParser, ParserResult
from forenx.timestamps import webkit_micros_to_utc

# Standard Chromium page transition qualifiers
CHROMIUM_TRANSITIONS = {
    0: "LINK",
    1: "TYPED",
    2: "AUTO_BOOKMARK",
    3: "AUTO_SUBFRAME",
    4: "MANUAL_SUBFRAME",
    5: "GENERATED",
    6: "START_PAGE",
    7: "FORM_SUBMIT",
    8: "RELOAD",
    9: "KEYWORD",
    10: "KEYWORD_GENERATED"
}

# Standard Chromium download states
CHROMIUM_DOWNLOAD_STATES = {
    0: "IN_PROGRESS",
    1: "COMPLETE",
    2: "CANCELLED",
    3: "INTERRUPTED"
}

class ChromiumHistoryParser(BaseBrowserParser):
    name = "ChromiumHistoryParser"
    version = "1.0.0"
    browser_family = "Chromium"

    def parse(
        self,
        db_path: Path,
        case_id: str,
        evidence_id: str,
        analysis_run_id: str
    ) -> ParserResult:
        result = ParserResult(
            parser_name=self.name,
            parser_version=self.version
        )

        try:
            conn = self.open_readonly_db(db_path)
            # Low-level SQLite integrity check
            is_intact, integrity_msg = self.check_sqlite_integrity(conn)
            if not is_intact:
                result.warnings.append(f"SQLite low-level integrity check warning: {integrity_msg}")

            tables = self.get_existing_tables(conn)
            result.schema_info["tables"] = list(tables)
        except (sqlite3.DatabaseError, CorruptDatabaseError) as e:
            raise CorruptDatabaseError(f"Corrupt or non-SQLite database file: {e!s}") from e
        except Exception as e:
            raise CorruptDatabaseError(f"Could not open Chromium SQLite database: {e!s}") from e

        try:

            if "urls" not in tables or "visits" not in tables:
                raise UnsupportedSchemaError(
                    f"Chromium database missing essential tables ('urls', 'visits'). Found: {tables}"
                )

            # Inspect columns
            url_cols = self.get_table_columns(conn, "urls")
            visit_cols = self.get_table_columns(conn, "visits")

            if "url" not in url_cols or "visit_time" not in visit_cols:
                raise UnsupportedSchemaError(
                    "Chromium schema missing essential columns ('urls.url' or 'visits.visit_time')."
                )

            # 1. Parse Visits and URLs
            cursor = conn.cursor()
            query = """
                SELECT
                    v.id AS visit_id,
                    v.visit_time,
                    v.from_visit,
                    v.transition,
                    u.url,
                    u.title,
                    u.visit_count
                FROM visits v
                LEFT JOIN urls u ON v.url = u.id
                ORDER BY v.visit_time ASC;
            """
            cursor.execute(query)
            visit_rows = cursor.fetchall()

            for row in visit_rows:
                result.records_seen += 1
                raw_time = row["visit_time"]
                raw_url = row["url"] or ""
                raw_title = row["title"] or ""
                visit_id = str(row["visit_id"])
                transition_code = row["transition"] & 0xFF if row["transition"] is not None else 0
                transition_name = CHROMIUM_TRANSITIONS.get(transition_code, f"CUSTOM_{transition_code}")

                if not raw_url:
                    result.records_skipped += 1
                    result.warnings.append(f"Visit record {visit_id} has empty/null URL; skipped.")
                    continue

                norm_utc, status = webkit_micros_to_utc(raw_time)
                warning_note = ""
                if status != "success":
                    warning_note = f"Timestamp conversion status: {status} (raw value: {raw_time})"
                    result.warnings.append(f"Record {visit_id}: {warning_note}")

                event = Event(
                    id=generate_id("evt"),
                    case_id=case_id,
                    evidence_id=evidence_id,
                    analysis_run_id=analysis_run_id,
                    browser_family=self.browser_family,
                    event_type="url_visit",
                    url=raw_url,
                    title=raw_title,
                    raw_timestamp=raw_time or 0,
                    timestamp_format="webkit_microseconds_1601",
                    normalized_utc=norm_utc,
                    conversion_status=status,
                    source_database="History",
                    source_table="visits / urls",
                    source_record_id=visit_id,
                    parser_version=self.version,
                    warning=warning_note,
                    extra_metadata={
                        "transition": transition_name,
                        "from_visit": row["from_visit"],
                        "visit_count": row["visit_count"]
                    }
                )
                result.events.append(event)
                result.records_extracted += 1

            # 2. Parse Downloads if available
            if "downloads" in tables:
                dl_cols = self.get_table_columns(conn, "downloads")
                # Handle variations between Chromium versions
                target_col = "target_path" if "target_path" in dl_cols else "current_path"
                has_tab_url = "tab_url" in dl_cols

                dl_query = f"""
                    SELECT
                        id,
                        {target_col} as target_path,
                        start_time,
                        received_bytes,
                        total_bytes,
                        state
                        {', tab_url' if has_tab_url else ''}
                    FROM downloads
                    ORDER BY start_time ASC;
                """
                cursor.execute(dl_query)
                for dl_row in cursor.fetchall():
                    result.records_seen += 1
                    dl_id = str(dl_row["id"])
                    raw_time = dl_row["start_time"]
                    target_path = dl_row["target_path"] or "unknown_file"
                    norm_utc, status = webkit_micros_to_utc(raw_time)
                    state_num = dl_row["state"]
                    state_label = CHROMIUM_DOWNLOAD_STATES.get(state_num, f"STATE_{state_num}")
                    dl_url = dl_row["tab_url"] if has_tab_url and dl_row["tab_url"] else f"file://{target_path}"

                    event = Event(
                        id=generate_id("evt"),
                        case_id=case_id,
                        evidence_id=evidence_id,
                        analysis_run_id=analysis_run_id,
                        browser_family=self.browser_family,
                        event_type="download",
                        url=dl_url,
                        title=Path(target_path).name,
                        raw_timestamp=raw_time or 0,
                        timestamp_format="webkit_microseconds_1601",
                        normalized_utc=norm_utc,
                        conversion_status=status,
                        source_database="History",
                        source_table="downloads",
                        source_record_id=dl_id,
                        parser_version=self.version,
                        warning="" if status == "success" else f"Timestamp status: {status}",
                        extra_metadata={
                            "target_path": target_path,
                            "received_bytes": dl_row["received_bytes"],
                            "total_bytes": dl_row["total_bytes"],
                            "state": state_label
                        }
                    )
                    result.events.append(event)
                    result.records_extracted += 1

        finally:
            conn.close()

        return result
