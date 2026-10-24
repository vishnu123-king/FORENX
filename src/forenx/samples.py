"""
Sample evidence database generator and acquisition guidance for ForenX.
Provides pre-built sample databases for Chrome and Firefox, as well as OS-specific paths.
"""

from pathlib import Path
from typing import List, Dict, Any
from forenx.config import get_config
from tests.fixtures.synthetic_data import (
    create_synthetic_chromium_db,
    create_synthetic_firefox_db
)

OS_BROWSER_PATHS = [
  {
    "browser": "Google Chrome",
    "family": "Chromium",
    "artifact_file": "History",
    "sidecars": ["History-wal", "History-shm"],
    "paths": {
      "windows": "%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\History",
      "linux": "~/.config/google-chrome/Default/History",
      "macos": "~/Library/Application Support/Google/Chrome/Default/History"
    },
    "notes": "Close Chrome before copying so SQLite flushes Write-Ahead Logs (WAL) into the main database."
  },
  {
    "browser": "Microsoft Edge",
    "family": "Chromium",
    "artifact_file": "History",
    "sidecars": ["History-wal", "History-shm"],
    "paths": {
      "windows": "%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\History",
      "linux": "~/.config/microsoft-edge/Default/History",
      "macos": "~/Library/Application Support/Microsoft Edge/Default/History"
    },
    "notes": "Edge uses standard Chromium schema. Same precautions regarding active browser locks apply."
  },
  {
    "browser": "Mozilla Firefox",
    "family": "Firefox",
    "artifact_file": "places.sqlite",
    "sidecars": ["places.sqlite-wal", "places.sqlite-shm"],
    "paths": {
      "windows": "%APPDATA%\\Mozilla\\Firefox\\Profiles\\<profile_folder>\\places.sqlite",
      "linux": "~/.mozilla/firefox/<profile_folder>/places.sqlite",
      "macos": "~/Library/Application Support/Firefox/Profiles/<profile_folder>/places.sqlite"
    },
    "notes": "Contains bookmarks, visit history, and favicons. Profile folder has a random string prefix (e.g. '8xyz1234.default-release')."
  },
  {
    "browser": "Brave Browser",
    "family": "Chromium",
    "artifact_file": "History",
    "sidecars": ["History-wal", "History-shm"],
    "paths": {
      "windows": "%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\History",
      "linux": "~/.config/BraveSoftware/Brave-Browser/Default/History",
      "macos": "~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History"
    },
    "notes": "Compatible with standard Chromium History parser."
  }
]

def get_samples_manifest() -> List[Dict[str, Any]]:
    """Return available sample evidence packages with description."""
    return [
        {
            "id": "chromium_history_sample",
            "name": "Chromium History Database (Sample)",
            "filename": "History",
            "browser_family": "Chromium",
            "evidence_type": "chromium_history",
            "description": "Standard Chrome/Edge History SQLite database containing 4 realistic visit events, navigation transitions (LINK, TYPED), and 1 download record.",
            "event_count": 5
        },
        {
            "id": "firefox_places_sample",
            "name": "Firefox places.sqlite (Sample)",
            "filename": "places.sqlite",
            "browser_family": "Firefox",
            "evidence_type": "firefox_places",
            "description": "Mozilla Firefox places.sqlite database with 2 visit records and 1 bookmark entry.",
            "event_count": 3
        },
        {
            "id": "chromium_corrupt_sample",
            "name": "Corrupted SQLite Sample (Negative Test)",
            "filename": "corrupt_history.db",
            "browser_family": "Chromium",
            "evidence_type": "unknown",
            "description": "Malformed database file to test how the ForenX engine handles and reports corrupt headers without crashing.",
            "event_count": 0
        }
    ]

def generate_sample_file(sample_id: str, dest_dir: Path) -> Path:
    """Generate or retrieve a sample evidence database file in the destination folder."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    if sample_id == "chromium_history_sample":
        out_path = dest_dir / "History"
        create_synthetic_chromium_db(out_path)
        return out_path
    elif sample_id == "firefox_places_sample":
        out_path = dest_dir / "places.sqlite"
        create_synthetic_firefox_db(out_path)
        return out_path
    elif sample_id == "chromium_corrupt_sample":
        out_path = dest_dir / "corrupt_history.db"
        create_synthetic_chromium_db(out_path, anomaly="corrupt_file")
        return out_path
    else:
        raise ValueError(f"Unknown sample ID: {sample_id}")
