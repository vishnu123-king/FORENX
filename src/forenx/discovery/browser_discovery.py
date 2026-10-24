"""
Cross-platform Browser Discovery and Local Profile Enumeration for ForenX.
Supports Google Chrome, Microsoft Edge, Brave, Chromium, and Mozilla Firefox on Linux and Windows.
Never scans the entire filesystem; targets standard profile locations and reads profiles.ini / Local State.
"""

from __future__ import annotations

import configparser
import json
import os
import platform
import sqlite3
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from forenx.models import DiscoveredProfile, generate_id, utc_now_iso
from forenx.evidence.package import create_evidence_package, import_and_verify_package
from forenx.services.analysis_service import run_case_analysis
from forenx.audit import log_audit


def get_browser_search_roots() -> list[dict[str, Any]]:
    """Return standard platform-specific root directories for supported browsers."""
    system = platform.system()
    home = Path.home()
    roots = []

    if system == "Windows":
        local_app_data = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        roaming_app_data = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))

        roots.extend([
            {
                "browser_name": "Google Chrome",
                "browser_family": "Chromium",
                "user_data_path": local_app_data / "Google" / "Chrome" / "User Data"
            },
            {
                "browser_name": "Microsoft Edge",
                "browser_family": "Chromium",
                "user_data_path": local_app_data / "Microsoft" / "Edge" / "User Data"
            },
            {
                "browser_name": "Brave Browser",
                "browser_family": "Chromium",
                "user_data_path": local_app_data / "BraveSoftware" / "Brave-Browser" / "User Data"
            },
            {
                "browser_name": "Mozilla Firefox",
                "browser_family": "Firefox",
                "base_path": roaming_app_data / "Mozilla" / "Firefox"
            }
        ])
    else:
        # Linux / Unix
        config_dir = home / ".config"
        roots.extend([
            {
                "browser_name": "Google Chrome",
                "browser_family": "Chromium",
                "user_data_path": config_dir / "google-chrome"
            },
            {
                "browser_name": "Chromium",
                "browser_family": "Chromium",
                "user_data_path": config_dir / "chromium"
            },
            {
                "browser_name": "Microsoft Edge",
                "browser_family": "Chromium",
                "user_data_path": config_dir / "microsoft-edge"
            },
            {
                "browser_name": "Brave Browser",
                "browser_family": "Chromium",
                "user_data_path": config_dir / "BraveSoftware" / "Brave-Browser"
            },
            {
                "browser_name": "Mozilla Firefox",
                "browser_family": "Firefox",
                "base_path": home / ".mozilla" / "firefox"
            }
        ])

    return roots


def inspect_chromium_profile(profile_path: Path, browser_name: str) -> Optional[DiscoveredProfile]:
    """Inspect a Chromium profile directory for allowlisted artifacts (History, Bookmarks)."""
    if not profile_path.is_dir():
        return None

    artifacts = []
    # Check History SQLite
    history_file = profile_path / "History"
    if history_file.is_file():
        wal = (profile_path / "History-wal").exists()
        shm = (profile_path / "History-shm").exists()
        artifacts.append({
            "artifact_type": "History",
            "file_name": "History",
            "file_path": str(history_file),
            "byte_size": history_file.stat().st_size,
            "has_wal": wal,
            "has_shm": shm
        })

    # Check Bookmarks
    bookmarks_file = profile_path / "Bookmarks"
    if bookmarks_file.is_file():
        artifacts.append({
            "artifact_type": "Bookmarks",
            "file_name": "Bookmarks",
            "file_path": str(bookmarks_file),
            "byte_size": bookmarks_file.stat().st_size,
            "has_wal": False,
            "has_shm": False
        })

    if not artifacts:
        return None

    profile_id = profile_path.name
    return DiscoveredProfile(
        browser_name=browser_name,
        browser_family="Chromium",
        profile_id=profile_id,
        profile_label=f"{browser_name} ({profile_id})",
        profile_path=str(profile_path),
        available_artifacts=artifacts
    )


def inspect_firefox_profile(
    profile_path: Path,
    profile_name: str,
    browser_name: str = "Mozilla Firefox"
) -> Optional[DiscoveredProfile]:
    """Inspect a Firefox profile directory for places.sqlite."""
    if not profile_path.is_dir():
        return None

    places_file = profile_path / "places.sqlite"
    if not places_file.is_file():
        return None

    wal = (profile_path / "places.sqlite-wal").exists()
    shm = (profile_path / "places.sqlite-shm").exists()

    artifacts = [
        {
            "artifact_type": "places.sqlite",
            "file_name": "places.sqlite",
            "file_path": str(places_file),
            "byte_size": places_file.stat().st_size,
            "has_wal": wal,
            "has_shm": shm
        }
    ]

    return DiscoveredProfile(
        browser_name="Mozilla Firefox",
        browser_family="Firefox",
        profile_id=profile_path.name,
        profile_label=f"Mozilla Firefox ({profile_name})",
        profile_path=str(profile_path),
        available_artifacts=artifacts
    )


def discover_local_browsers(custom_roots: Optional[list[dict[str, Any]]] = None) -> list[DiscoveredProfile]:
    """
    Safely discover local browser profiles without recursive scanning.
    Validates directories, handles symlinks, and returns available artifact scopes.
    """
    discovered: list[DiscoveredProfile] = []
    roots = custom_roots or get_browser_search_roots()

    for entry in roots:
        family = entry.get("browser_family")
        name = entry.get("browser_name", "Unknown Browser")

        if family == "Chromium":
            user_data = Path(entry["user_data_path"])
            if not user_data.exists():
                continue

            # Check Default profile
            default_p = user_data / "Default"
            dp = inspect_chromium_profile(default_p, name)
            if dp:
                discovered.append(dp)

            # Check numbered profiles (Profile 1, Profile 2, etc.)
            try:
                for child in user_data.iterdir():
                    if child.is_dir() and child.name.startswith("Profile "):
                        child_p = inspect_chromium_profile(child, name)
                        if child_p:
                            discovered.append(child_p)
            except (PermissionError, OSError):
                pass

        elif family == "Firefox":
            base_dir = Path(entry["base_path"])
            if not base_dir.exists():
                continue

            profiles_ini = base_dir / "profiles.ini"
            if profiles_ini.is_file():
                try:
                    cp = configparser.ConfigParser()
                    cp.read(str(profiles_ini), encoding="utf-8")
                    for section in cp.sections():
                        if section.startswith("Profile") or section.startswith("Install"):
                            rel_path = cp.get(section, "Path", fallback=None)
                            p_name = cp.get(section, "Name", fallback="Default")
                            is_relative = cp.getint(section, "IsRelative", fallback=1) == 1

                            if rel_path:
                                full_profile_dir = (base_dir / rel_path) if is_relative else Path(rel_path)
                                ffp = inspect_firefox_profile(full_profile_dir, p_name)
                                if ffp and not any(d.profile_path == ffp.profile_path for d in discovered):
                                    discovered.append(ffp)
                except Exception:
                    # Fallback enumeration if profiles.ini parser fails
                    try:
                        for child in base_dir.iterdir():
                            if child.is_dir() and ("default" in child.name or "release" in child.name):
                                ffp = inspect_firefox_profile(child, child.name)
                                if ffp:
                                    discovered.append(ffp)
                    except (PermissionError, OSError):
                        pass

    return discovered


def snapshot_sqlite_online(src_db_path: Path, dest_db_path: Path) -> None:
    """
    Perform a consistent logical snapshot using Python sqlite3's online backup API.
    Does NOT lock, checkpoint, vacuum, or alter the live browser database.
    """
    src_conn = sqlite3.connect(f"file:{src_db_path.as_posix()}?mode=ro", uri=True)
    dest_conn = sqlite3.connect(str(dest_db_path))
    try:
        with dest_conn:
            src_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        src_conn.close()


# Alias for test compatibility
perform_sqlite_online_backup = snapshot_sqlite_online


def acquire_selected_profiles(
    case_id: str,
    selected_profiles: list[dict[str, Any]],
    investigator_label: str = "Examiner",
    notes: str = "Authorized local system acquisition"
) -> dict[str, Any]:
    """
    Acquire selected browser artifacts into an isolated staging area,
    package into FX-ACQ-*.forenx.zip, verify, import into Evidence Vault,
    and trigger automated analysis.
    """
    from forenx.config import get_config
    cfg = get_config()
    cfg.ensure_directories()

    staging_dir = cfg.working_dir / "local_acq_staging" / generate_id("acq")
    staging_dir.mkdir(parents=True, exist_ok=True)

    artifacts_for_package = []

    try:
        for prof in selected_profiles:
            b_name = prof.get("browser_name", "Browser")
            b_family = prof.get("browser_family", "Chromium")
            p_label = prof.get("profile_label", "Default")

            for art in prof.get("artifacts", []):
                src_path = Path(art["file_path"]).resolve()
                if not src_path.exists():
                    continue

                dest_file = staging_dir / f"{p_label}_{src_path.name}"

                # Use online backup for SQLite or safe copy
                try:
                    snapshot_sqlite_online(src_path, dest_file)
                except Exception:
                    shutil.copy2(src_path, dest_file)

                # Also copy sidecars if present
                for suffix in ["-wal", "-shm"]:
                    sidecar = src_path.parent / f"{src_path.name}{suffix}"
                    if sidecar.exists():
                        shutil.copy2(sidecar, staging_dir / f"{dest_file.name}{suffix}")

                artifacts_for_package.append({
                    "file_path": str(dest_file),
                    "browser_name": b_name,
                    "browser_family": b_family,
                    "profile_label": p_label,
                    "artifact_type": art.get("artifact_type", src_path.name),
                    "warnings": []
                })

        if not artifacts_for_package:
            raise ValueError("No valid browser artifacts found for collection.")

        # Create standardized evidence package
        zip_path, package_hash, pkg_model = create_evidence_package(
            case_id=case_id,
            acquisition_id=generate_id("acq"),
            acquisition_method="local_system_authorized",
            artifacts=artifacts_for_package,
            investigator_label=investigator_label,
            provenance_notes=notes
        )

        # Import and verify package into evidence vault
        imported_pkg, registered_evidence, verif_report = import_and_verify_package(
            case_id=case_id,
            zip_path=zip_path,
            expected_package_sha256=package_hash
        )

        # Automatically execute forensic analysis on the newly registered evidence
        analysis_run = run_case_analysis(case_id=case_id)

        log_audit(
            operation="local_acquisition_completed",
            case_id=case_id,
            outcome="success",
            details=f"Acquired {len(registered_evidence)} artifacts in package {pkg_model.id}. Analyzed: {analysis_run.records_extracted} events."
        )

        return {
            "package_id": pkg_model.id,
            "package_filename": pkg_model.package_filename,
            "package_sha256": package_hash,
            "artifacts_collected": len(registered_evidence),
            "events_extracted": analysis_run.records_extracted,
            "analysis_status": analysis_run.status,
            "verification_status": imported_pkg.verification_status
        }

    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
