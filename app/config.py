"""Configuration, read from environment with sane defaults."""

from __future__ import annotations

import os
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    return (value if value is not None else default).strip()


DATA_DIR = Path(_env("DATA_DIR", "/app/data"))
DOWNLOAD_DIR = Path(_env("DOWNLOAD_DIR", "")) if _env("DOWNLOAD_DIR") else DATA_DIR / "downloads"
MIRROR_DIR = Path(_env("MIRROR_DIR")) if _env("MIRROR_DIR") else None

# Z-Library mirror domain, without scheme. No default: swap in a site that is
# reachable from your network, e.g. "your-mirror.example".
ZLIB_DOMAIN = _env("ZLIB_DOMAIN")
# Optional auto-login credentials. The password is used once and never stored;
# only the resulting session cookie is persisted.
ZLIB_EMAIL = _env("ZLIB_EMAIL")
ZLIB_PASSWORD = _env("ZLIB_PASSWORD")
# Optional HTTP proxy for reaching the mirror and the file CDN.
PROXY = _env("PROXY")

PORT = int(_env("PORT", "8000"))
# One download at a time by default: the daily quota is the bottleneck, not bandwidth.
MAX_CONCURRENT = max(1, int(_env("MAX_CONCURRENT", "1")))
PAGE_SIZE = max(1, min(100, int(_env("PAGE_SIZE", "20"))))
# Stop the queue when the remaining daily quota drops to this value.
QUOTA_RESERVE = max(0, int(_env("QUOTA_RESERVE", "0")))

SESSION_FILE = DATA_DIR / "session.json"
DB_FILE = DATA_DIR / "zlib-nas.db"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
