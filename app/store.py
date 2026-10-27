"""SQLite persistence: synced wishlist, download records and settings.

Everything lives in one file under the data directory so backups are a single
``cp``. The schema is created on first start and is forward-compatible: new
columns are added with ``ALTER TABLE`` when missing.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS saved_books (
    zlib_id     INTEGER NOT NULL,
    hash        TEXT    NOT NULL DEFAULT '',
    title       TEXT    NOT NULL DEFAULT '',
    author      TEXT    NOT NULL DEFAULT '',
    year        TEXT    NOT NULL DEFAULT '',
    language    TEXT    NOT NULL DEFAULT '',
    publisher   TEXT    NOT NULL DEFAULT '',
    extension   TEXT    NOT NULL DEFAULT '',
    filesize    INTEGER NOT NULL DEFAULT 0,
    filesize_text TEXT  NOT NULL DEFAULT '',
    cover       TEXT    NOT NULL DEFAULT '',
    description TEXT    NOT NULL DEFAULT '',
    sha256      TEXT    NOT NULL DEFAULT '',
    synced_at   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (zlib_id, hash)
);

CREATE TABLE IF NOT EXISTS downloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    zlib_id     INTEGER NOT NULL,
    hash        TEXT    NOT NULL DEFAULT '',
    title       TEXT    NOT NULL DEFAULT '',
    author      TEXT    NOT NULL DEFAULT '',
    extension   TEXT    NOT NULL DEFAULT '',
    filename    TEXT    NOT NULL DEFAULT '',
    path        TEXT    NOT NULL DEFAULT '',
    status      TEXT    NOT NULL DEFAULT 'queued',
    error       TEXT    NOT NULL DEFAULT '',
    bytes_done  INTEGER NOT NULL DEFAULT 0,
    bytes_total INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL DEFAULT 0,
    updated_at  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status);
CREATE INDEX IF NOT EXISTS idx_downloads_book ON downloads(zlib_id, hash);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
"""


def _now() -> int:
    return int(time.time() * 1000)


class Store:
    def __init__(self, path=None) -> None:
        self.path = str(path or config.DB_FILE)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # -------------------------------------------------------------- settings

    def get_setting(self, key: str, default: str = "") -> str:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # ------------------------------------------------------------ saved books

    def upsert_saved(self, books: List[Dict[str, Any]]) -> int:
        """Insert or refresh wishlist rows. Returns how many rows were written."""
        if not books:
            return 0
        stamp = _now()
        rows = [
            (
                book.get("id"),
                book.get("hash") or "",
                book.get("title") or "",
                book.get("author") or "",
                str(book.get("year") or ""),
                book.get("language") or "",
                book.get("publisher") or "",
                book.get("extension") or "",
                int(book.get("filesize") or 0),
                book.get("filesize_text") or "",
                book.get("cover") or "",
                book.get("description") or "",
                book.get("sha256") or "",
                stamp,
            )
            for book in books
            if book.get("id")
        ]
        with self._lock, self._connect() as conn:
            conn.executemany(
                "INSERT INTO saved_books(zlib_id, hash, title, author, year, language, publisher, "
                "extension, filesize, filesize_text, cover, description, sha256, synced_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(zlib_id, hash) DO UPDATE SET "
                "title=excluded.title, author=excluded.author, year=excluded.year, "
                "language=excluded.language, publisher=excluded.publisher, "
                "extension=excluded.extension, filesize=excluded.filesize, "
                "filesize_text=excluded.filesize_text, cover=excluded.cover, "
                "description=excluded.description, sha256=excluded.sha256, "
                "synced_at=excluded.synced_at",
                rows,
            )
        return len(rows)

    def list_saved(
        self, query: str = "", limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        where, params = "", []
        if query:
            where = "WHERE title LIKE ? OR author LIKE ?"
            params = [f"%{query}%", f"%{query}%"]
        with self._lock, self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS n FROM saved_books {where}", params
            ).fetchone()["n"]
            rows = conn.execute(
                # `zlib_id AS id`: the UI speaks the same vocabulary as the API,
                # where a book is identified by `id` and `hash`.
                f"SELECT zlib_id AS id, hash, title, author, year, language, publisher, "
                f"extension, filesize, filesize_text, cover, description, sha256, synced_at "
                f"FROM saved_books {where} ORDER BY synced_at DESC, title "
                "LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
        return {"books": [dict(row) for row in rows], "total": total}

    def saved_hashes(self) -> set:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT sha256 FROM saved_books WHERE sha256 != ''").fetchall()
        return {row["sha256"] for row in rows}

    def saved_count(self) -> int:
        with self._lock, self._connect() as conn:
            return conn.execute("SELECT COUNT(*) AS n FROM saved_books").fetchone()["n"]

    # -------------------------------------------------------------- downloads

    def create_download(self, book: Dict[str, Any]) -> int:
        stamp = _now()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO downloads(zlib_id, hash, title, author, extension, status, "
                "created_at, updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (
                    book.get("id"),
                    book.get("hash") or "",
                    book.get("title") or "",
                    book.get("author") or "",
                    book.get("extension") or "",
                    "queued",
                    stamp,
                    stamp,
                ),
            )
            return int(cursor.lastrowid)

    def update_download(self, download_id: int, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self._lock, self._connect() as conn:
            conn.execute(
                f"UPDATE downloads SET {assignments} WHERE id = ?",
                list(fields.values()) + [download_id],
            )

    def get_download(self, download_id: int) -> Optional[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM downloads WHERE id = ?", (download_id,)).fetchone()
        return dict(row) if row else None

    def list_downloads(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM downloads ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def has_download(self, zlib_id: int, book_hash: str) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM downloads WHERE zlib_id = ? AND hash = ? "
                "AND status IN ('done','running','queued') LIMIT 1",
                (zlib_id, book_hash),
            ).fetchone()
        return row is not None

    def reset_stale(self) -> int:
        """Mark interrupted downloads as failed after a restart."""
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "UPDATE downloads SET status = 'failed', error = 'interrupted by restart', "
                "updated_at = ? WHERE status IN ('running','queued')",
                (_now(),),
            )
            return cursor.rowcount

    def stats(self) -> Dict[str, int]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM downloads GROUP BY status"
            ).fetchall()
        return {row["status"]: row["n"] for row in rows}

    # ----------------------------------------------------------------- export

    def dump_json(self, path) -> None:
        with self._lock, self._connect() as conn:
            payload = {
                "saved_books": [dict(row) for row in conn.execute("SELECT * FROM saved_books")],
                "downloads": [dict(row) for row in conn.execute("SELECT * FROM downloads")],
                "settings": {
                    row["key"]: row["value"] for row in conn.execute("SELECT * FROM settings")
                },
            }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
