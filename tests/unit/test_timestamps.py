"""
Unit tests for timestamp conversion and normalization.
"""

from forenx.timestamps import firefox_prtime_to_utc, webkit_micros_to_utc


def test_webkit_micros_to_utc_known_timestamp():
    # 2026-10-15 14:30:00 UTC = Unix 1792074600
    # WebKit = 1792074600 * 1,000,000 + 11644473600000000 = 13436548200000000
    webkit_ts = 13436548200000000
    iso_utc, status = webkit_micros_to_utc(webkit_ts)

    assert status == "success"
    assert iso_utc is not None
    assert "2026-10-15T14:30:00" in iso_utc

def test_webkit_micros_invalid_or_negative():
    iso_utc, status = webkit_micros_to_utc(-500)
    assert status == "zero"

    iso_utc, status = webkit_micros_to_utc(None)
    assert status == "invalid"

    iso_utc, status = webkit_micros_to_utc("invalid_string")
    assert status == "invalid"

def test_firefox_prtime_known_timestamp():
    # 2026-10-17 10:00:00 UTC = Unix 1792231200
    # Firefox PRTime = 1792231200 * 1,000,000 = 1792231200000000
    prtime_ts = 1792231200000000
    iso_utc, status = firefox_prtime_to_utc(prtime_ts)

    assert status == "success"
    assert iso_utc is not None
    assert "2026-10-17T10:00:00" in iso_utc

def test_firefox_prtime_zero_and_invalid():
    iso_utc, status = firefox_prtime_to_utc(0)
    assert status == "zero"

    iso_utc, status = firefox_prtime_to_utc(None)
    assert status == "invalid"
