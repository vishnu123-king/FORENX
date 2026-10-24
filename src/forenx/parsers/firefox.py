"""
Mozilla Firefox places.sqlite parser for ForenX.
Extracts visits, URLs, page titles, transitions, and bookmarks.
"""

import sqlite3
from pathlib import Path

from forenx.exceptions import CorruptDatabaseError, UnsupportedSchemaError
from forenx.models import Event, generate_id
from forenx.parsers.base import BaseBrowserParser, ParserResult
from forenx.timestamps import firefox_prtime_to_utc

FIREFOX_VISIT_TYPES = {
    1: "LINK",
    2: "TYPED",
    3: "BOOKMARK",
    4: "EMBED",
    5: "REDIRECT_PERMANENT",
    6: "REDIRECT_TEMPORARY",
    7: "DOWNLOAD",
    8: "FRAMED_LINK",
    9: "RELOAD"
}

class FirefoxPlacesParser(BaseBrowserParser):
    name = "FirefoxPlacesParser"
    version = "1.0.0"
    browser_family = "Firefox"

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
            is_intact, integrity_msg = self.check_sqlite_integrity(conn)
            if not is_intact:
                result.warnings.append(f"SQLite low-level integrity check warning: {integrity_msg}")

            tables = self.get_existing_tables(conn)
            result.schema_info["tables"] = list(tables)
        except (sqlite3.DatabaseError, CorruptDatabaseError) as e:
            raise CorruptDatabaseError(f"Corrupt or non-SQLite database file: {e!s}") from e
        except Exception as e:
            raise CorruptDatabaseError(f"Could not open Firefox SQLite database: {e!s}") from e

        try:

            if "moz_places" not in tables:
                raise UnsupportedSchemaError(
                    f"Firefox database missing required table 'moz_places'. Found: {tables}"
                )

            cursor = conn.cursor()

            # 1. Parse Visits if moz_historyvisits table exists
            if "moz_historyvisits" in tables:
                hv_cols = self.get_table_columns(conn, "moz_historyvisits")
                pl_cols = self.get_table_columns(conn, "moz_places")

                if "place_id" in hv_cols and "visit_date" in hv_cols and "url" in pl_cols:
                    visit_query = """
                        SELECT
                            v.id AS visit_id,
                            v.from_visit,
                            v.visit_date,
                            v.visit_type,
                            p.url,
                            p.title,
                            p.visit_count
                        FROM moz_historyvisits v
                        JOIN moz_places p ON v.place_id = p.id
                        ORDER BY v.visit_date ASC;
                    """
                    cursor.execute(visit_query)
                    for row in cursor.fetchall():
                        result.records_seen += 1
                        raw_time = row["visit_date"]
                        raw_url = row["url"] or ""
                        raw_title = row["title"] or ""
                        visit_id = str(row["visit_id"])

                        if not raw_url:
                            result.records_skipped += 1
                            result.warnings.append(f"Firefox visit {visit_id} has empty URL; skipped.")
                            continue

                        norm_utc, status = firefox_prtime_to_utc(raw_time)
                        warning_note = ""
                        if status != "success":
                            warning_note = f"Firefox timestamp status: {status} (raw: {raw_time})"
                            result.warnings.append(f"Record {visit_id}: {warning_note}")

                        v_type_num = row["visit_type"] or 0
                        v_type_name = FIREFOX_VISIT_TYPES.get(v_type_num, f"TYPE_{v_type_num}")

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
                            timestamp_format="prtime_microseconds_1970",
                            normalized_utc=norm_utc,
                            conversion_status=status,
                            source_database="places.sqlite",
                            source_table="moz_historyvisits / moz_places",
                            source_record_id=visit_id,
                            parser_version=self.version,
                            warning=warning_note,
                            extra_metadata={
                                "visit_type": v_type_name,
                                "from_visit": row["from_visit"],
                                "visit_count": row["visit_count"]
                            }
                        )
                        result.events.append(event)
                        result.records_extracted += 1

            # 2. Parse Bookmarks if moz_bookmarks table exists
            if "moz_bookmarks" in tables:
                bm_cols = self.get_table_columns(conn, "moz_bookmarks")
                if "fk" in bm_cols and "title" in bm_cols and "dateadded" in bm_cols:
                    bm_query = """
                        SELECT
                            b.id AS bm_id,
                            b.title AS bm_title,
                            b.dateAdded,
                            b.lastModified,
                            p.url
                        FROM moz_bookmarks b
                        JOIN moz_places p ON b.fk = p.id
                        WHERE b.type = 1
                        ORDER BY b.dateAdded ASC;
                    """
                    try:
                        cursor.execute(bm_query)
                        for bm_row in cursor.fetchall():
                            result.records_seen += 1
                            raw_time = bm_row["dateAdded"]
                            bm_url = bm_row["url"] or ""
                            bm_title = bm_row["bm_title"] or ""
                            bm_id = str(bm_row["bm_id"])

                            norm_utc, status = firefox_prtime_to_utc(raw_time)
                            event = Event(
                                id=generate_id("evt"),
                                case_id=case_id,
                                evidence_id=evidence_id,
                                analysis_run_id=analysis_run_id,
                                browser_family=self.browser_family,
                                event_type="bookmark",
                                url=bm_url,
                                title=bm_title,
                                raw_timestamp=raw_time or 0,
                                timestamp_format="prtime_microseconds_1970",
                                normalized_utc=norm_utc,
                                conversion_status=status,
                                source_database="places.sqlite",
                                source_table="moz_bookmarks",
                                source_record_id=bm_id,
                                parser_version=self.version,
                                warning="" if status == "success" else f"Timestamp status: {status}",
                                extra_metadata={
                                    "last_modified_raw": bm_row["lastModified"]
                                }
                            )
                            result.events.append(event)
                            result.records_extracted += 1
                    except sqlite3.OperationalError as e:
                        result.warnings.append(f"Failed to query Firefox bookmarks: {e!s}")

        finally:
            conn.close()

        return result
