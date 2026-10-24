"""
Configuration management for ForenX.
"""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(os.environ.get("FORENX_DATA_DIR", Path.cwd() / "forenx_workspace"))

@dataclass
class ForenXConfig:
    data_dir: Path = DEFAULT_DATA_DIR
    max_import_size_bytes: int = 500 * 1024 * 1024  # 500MB
    display_timezone: str = "UTC"
    log_level: str = "INFO"
    app_version: str = "1.0.0"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "forenx_app.sqlite"

    @property
    def evidence_dir(self) -> Path:
        return self.data_dir / "evidence_vault"

    @property
    def working_dir(self) -> Path:
        return self.data_dir / "working_copies"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "exported_reports"

    def ensure_directories(self) -> None:
        """Create necessary storage directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

_global_config = ForenXConfig()

def get_config() -> ForenXConfig:
    return _global_config

def set_config(config: ForenXConfig) -> None:
    global _global_config
    _global_config = config
    _global_config.ensure_directories()
