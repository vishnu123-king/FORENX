"""
Forensic timestamp conversion and normalization engine for ForenX.
Supports:
- Chromium / WebKit timestamp format: Microseconds since 1601-01-01 00:00:00 UTC.
- Mozilla Firefox PRTime format: Microseconds since 1970-01-01 00:00:00 UTC.
- Standard Unix epoch in seconds or milliseconds.
"""

from datetime import UTC, datetime

# Microsecond difference between Windows / WebKit epoch (1601-01-01 UTC) and Unix epoch (1970-01-01 UTC)
# 11,644,473,600 seconds * 1,000,000 = 11,644,473,600,000,000 microseconds
WEBKIT_EPOCH_OFFSET_MICROS = 11644473600000000

MIN_REASONABLE_YEAR = 1970
MAX_REASONABLE_YEAR = 2100

def webkit_micros_to_utc(raw_value: int | None) -> tuple[str | None, str]:
    """
    Convert Chromium/WebKit microseconds since 1601-01-01 to UTC ISO-8601 string.
    Returns: (normalized_utc_str, conversion_status)
    conversion_status is one of: 'success', 'out_of_range', 'invalid', 'zero'
    """
    if raw_value is None or not isinstance(raw_value, (int, float)):
        return None, "invalid"

    try:
        val = int(raw_value)
    except (ValueError, TypeError):
        return None, "invalid"

    if val <= 0:
        return None, "zero"

    # Chromium timestamps before Unix epoch or excessively large are flagged
    unix_micros = val - WEBKIT_EPOCH_OFFSET_MICROS
    if unix_micros < 0:
        return None, "out_of_range"

    unix_seconds = unix_micros / 1_000_000.0

    try:
        dt = datetime.fromtimestamp(unix_seconds, tz=UTC)
        if dt.year < MIN_REASONABLE_YEAR or dt.year > MAX_REASONABLE_YEAR:
            return dt.isoformat(), "out_of_range"
        return dt.isoformat(), "success"
    except (OSError, OverflowError, ValueError):
        return None, "out_of_range"

def firefox_prtime_to_utc(raw_value: int | None) -> tuple[str | None, str]:
    """
    Convert Firefox PRTime microseconds since Unix epoch 1970-01-01 to UTC ISO-8601.
    Returns: (normalized_utc_str, conversion_status)
    """
    if raw_value is None or not isinstance(raw_value, (int, float)):
        return None, "invalid"

    try:
        val = int(raw_value)
    except (ValueError, TypeError):
        return None, "invalid"

    if val <= 0:
        return None, "zero"

    unix_seconds = val / 1_000_000.0

    try:
        dt = datetime.fromtimestamp(unix_seconds, tz=UTC)
        if dt.year < MIN_REASONABLE_YEAR or dt.year > MAX_REASONABLE_YEAR:
            return dt.isoformat(), "out_of_range"
        return dt.isoformat(), "success"
    except (OSError, OverflowError, ValueError):
        return None, "out_of_range"

def unix_seconds_to_utc(raw_value: int | None) -> tuple[str | None, str]:
    """Convert Unix seconds to UTC ISO-8601."""
    if raw_value is None:
        return None, "invalid"
    try:
        val = float(raw_value)
        dt = datetime.fromtimestamp(val, tz=UTC)
        return dt.isoformat(), "success"
    except Exception:
        return None, "invalid"
