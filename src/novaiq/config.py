"""Central configuration, loaded from environment variables (.env or Secrets)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional at runtime
    pass

# Project paths
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

DECORATIONS_PATH = DATA_DIR / "decorations.json"
STATE_DB_PATH = DATA_DIR / "state.db"


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


@dataclass
class Settings:
    """Runtime settings resolved from the environment."""

    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    text_model: str = field(default_factory=lambda: _env("NOVAIQ_TEXT_MODEL", "gpt-5.6-luna"))
    image_model: str = field(default_factory=lambda: _env("NOVAIQ_IMAGE_MODEL", "gpt-image-2"))
    image_size: str = field(default_factory=lambda: _env("NOVAIQ_IMAGE_SIZE", "1024x1024"))
    image_quality: str = field(default_factory=lambda: _env("NOVAIQ_IMAGE_QUALITY", "low"))

    wp_url: str = field(default_factory=lambda: _env("WP_URL").rstrip("/"))
    wp_username: str = field(default_factory=lambda: _env("WP_USERNAME"))
    wp_app_password: str = field(default_factory=lambda: _env("WP_APP_PASSWORD"))

    # NOVAIQ Connector plugin (custom-header auth; bypasses Authorization stripping)
    novaiq_api_key: str = field(default_factory=lambda: _env("NOVAIQ_API_KEY"))

    openalex_mailto: str = field(default_factory=lambda: _env("OPENALEX_MAILTO"))
    ncbi_api_key: str = field(default_factory=lambda: _env("NCBI_API_KEY"))

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_wordpress(self) -> bool:
        return bool(self.wp_url and self.wp_username and self.wp_app_password)

    @property
    def has_connector(self) -> bool:
        return bool(self.wp_url and self.novaiq_api_key)


def get_settings() -> Settings:
    """Return a fresh Settings snapshot (re-reads the environment each call)."""
    return Settings()
