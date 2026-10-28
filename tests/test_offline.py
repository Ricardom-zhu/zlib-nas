"""Offline test: drive the real client/queue/store code against a mock EAPI.

The mock implements exactly the endpoints and payload shapes documented in
app/zlibrary.py, so this exercises login, the wishlist sync, search, the quota
gate and a streamed download without touching the network.

Run:  python3 tests/test_offline.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="zlib-nas-test-"))
os.environ["DATA_DIR"] = str(TMP)
os.environ["DOWNLOAD_DIR"] = str(TMP / "downloads")

from app import config  # noqa: E402  (import after DATA_DIR is set)

config.DATA_DIR = TMP
config.DOWNLOAD_DIR = TMP / "downloads"
config.ensure_dirs()

from app.queue import DownloadQueue, safe_filename  # noqa: E402
from app.store import Store  # noqa: E402
from app.zlibrary import ZlibClient, ZlibError  # noqa: E402

USER = {
    "id": 42,
    "name": "tester",
    "email": "tester@example.com",
    "downloads_limit": 10,
    "downloads_today": 3,
    "isPremium": 0,
}

BOOKS = [
    {
        "id": 1001,
        "hash": "aaa111",
        "title": "Deep Work",
        "author": "Cal Newport",
        "year": "2016",
        "language": "english",
        "publisher": "Grand Central",
        "extension": "epub",
        "filesize": 1024,
        "filesizeString": "1.0 KB",
        "cover": "http://127.0.0.1:{port}/cover.jpg",
        "description": "Focus.",
        "sha256": "deadbeef",
    },
    {
        "id": 1002,
        "hash": "bbb222",
        "title": "深度工作",
        "author": "卡尔·纽波特",
        "year": "2017",
        "language": "chinese",
        "publisher": "后浪",
        "extension": "pdf",
        "filesize": 2048,
        "filesizeString": "2.0 KB",
        "cover": "",
        "sha256": "cafebabe",
    },
]

REQUEST_LOG = []


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep the test output clean
        pass

    # ---------------------------------------------------------------- helpers

    def _json(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self):
        body = b"<html>check your browser</html>"
        self.send_response(403)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _pagination(self, page, limit, total):
        pages = max(1, (total + limit - 1) // limit)
        return {
            "current": page,
            "limit": limit,
            "total_items": total,
            "total_pages": pages,
            "next": page + 1 if page < pages else None,
        }

    # ------------------------------------------------------------------- GET

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        REQUEST_LOG.append(("GET", path))

        if path == "/eapi/user/profile":
            return self._json({"success": 1, "user": USER})

        if path == "/eapi/user/book/saved":
            page = int(parse_qs(parsed.query).get("page", ["1"])[0])
            limit = int(parse_qs(parsed.query).get("limit", ["20"])[0])
            sliced = BOOKS if page == 1 else []
            return self._json(
                {
                    "success": 1,
                    "books": sliced,
                    "pagination": self._pagination(page, limit, len(BOOKS)),
                }
            )

        if path == "/eapi/book/most-popular":
            return self._json(
                {"success": 1, "books": BOOKS, "pagination": self._pagination(1, 20, 2)}
            )

        if path == "/eapi/user/book/recommended":
            return self._json({"success": 1, "books": [BOOKS[0]]})

        if path.startswith("/eapi/book/") and path.endswith("/file"):
            parts = path.strip("/").split("/")
            book_id, book_hash = int(parts[2]), parts[3]
            book = next((b for b in BOOKS if b["id"] == book_id), None)
            if not book:
                return self._json({"success": 0, "error": "not found"})
            return self._json(
                {
                    "success": 1,
                    "file": {
                        "downloadLink": self.server.url(f"/dl/{book_hash}"),
                        "filename": book["title"],
                        "extension": book["extension"],
                        "filesize": book["filesize"],
                    },
                }
            )

        if path.startswith("/dl/"):
            payload = b"B" * 1024
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/cover.jpg":
            payload = b"\xff\xd8\xff\xd9"
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/blocked":
            return self._html()

        return self._json({"success": 0, "error": "unknown endpoint " + path})

    # ------------------------------------------------------------------ POST

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode()
        form = parse_qs(raw)
        REQUEST_LOG.append(("POST", path, raw))

        if path == "/eapi/user/login":
            if form.get("email", [""])[0] == "tester@example.com" and form.get(
                "password", [""]
            )[0] == "secret":
                return self._json({"success": 1, "user": USER})
            return self._json({"success": 0, "error": "wrong password"})

        if path == "/eapi/book/search":
            message = form.get("message", [""])[0]
            hits = [b for b in BOOKS if message.lower() in b["title"].lower() or not message]
            return self._json(
                {
                    "success": 1,
                    "books": hits,
                    "exactBooksCount": len(hits),
                    "pagination": self._pagination(
                        int(form.get("page", ["1"])[0]), 20, len(hits)
                    ),
                }
            )

        return self._json({"success": 0, "error": "unknown endpoint " + path})


def start_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.url = lambda path: f"http://127.0.0.1:{server.server_address[1]}{path}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class LocalClient(ZlibClient):
    """Same client, plain HTTP against the mock."""

    def __init__(self, port: int) -> None:
        super().__init__(domain="mock", cookies=None)
        self._port = port

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._port}"


# --------------------------------------------------------------------- checks

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        failures.append(name)


def main() -> int:
    server = start_server()
    port = server.server_address[1]
    client = LocalClient(port)
    store = Store(config.DB_FILE)

    print("login")
    user = client.login("tester@example.com", "secret")
    check("login returns the user", user.get("id") == 42)

    print("bad login")
    try:
        LocalClient(port).login("tester@example.com", "nope")
    except ZlibError as exc:
        check("wrong password raises", "wrong password" in str(exc), str(exc))
    else:
        check("wrong password raises", False, "no error")

    print("quota")
    quota = client.quota()
    check("quota limit", quota["limit"] == 10, quota)
    check("quota spent", quota["today"] == 3, quota)
    check("quota left", quota["left"] == 7, quota)

    print("account")
    account = client.account()
    check("account name", account["name"] == "tester", account)
    check("account premium false", account["premium"] is False, account)

    print("saved")
    page = client.saved(page=1, limit=50)
    check("saved count", len(page["books"]) == 2, page["books"])
    check("saved normalised title", page["books"][0]["title"] == "Deep Work")
    check("saved filesize string", page["books"][0]["filesize_text"] == "1.0 KB")
    check("saved single page", page["has_next"] is False, page)

    print("search")
    result = client.search("深度")
    check("search hit", len(result["books"]) == 1, result["books"])
    check("search exact count", result["exact"] == 1, result)
    last = REQUEST_LOG[-1][2]
    check("search sends message", "message=%E6%B7%B1%E5%BA%A6" in last, last)

    print("store")
    written = store.upsert_saved(page["books"])
    check("upsert rows", written == 2, written)
    check("upsert is idempotent", store.upsert_saved(page["books"]) == 2)
    check("saved count", store.saved_count() == 2, store.saved_count())
    listed = store.list_saved(limit=10)
    # The UI reads `id`; the column is called zlib_id, so the query aliases it.
    check("list aliases id", listed["books"][0].get("id") in (1001, 1002), listed["books"][0])
    check("list has every book", len(listed["books"]) == 2)
    check("list filters", len(store.list_saved(query="深度")["books"]) == 1)

    print("download (streamed)")
    destination = Path(config.DOWNLOAD_DIR) / safe_filename("Deep Work", "Cal Newport", "epub")
    check("safe filename", destination.name == "Cal Newport - Deep Work.epub", destination.name)
    progress = []
    size = client.download(1001, "aaa111", destination, lambda d, t: progress.append((d, t)))
    check("download size", size == 1024, size)
    check("file on disk", destination.stat().st_size == 1024)
    check("progress reported", bool(progress) and progress[-1][0] == 1024, progress[-1:])

    print("download record + has_download")
    record_id = store.create_download(
        {"id": 1001, "hash": "aaa111", "title": "Deep Work", "author": "Cal Newport", "extension": "epub"}
    )
    check("has_download true", store.has_download(1001, "aaa111") is True)
    check("has_download false", store.has_download(9999, "zzz") is False)

    print("queue: quota gate pauses")
    queue = DownloadQueue(store, lambda: client)
    queue._process(record_id)
    record = store.get_download(record_id)
    check("queue completed task", record["status"] == "done", record["status"])
    check("queue wrote bytes", record["bytes_done"] == 1024, record)

    # Squeeze the quota to zero and prove the queue refuses to spend.
    USER["downloads_today"] = 10
    second = store.create_download(
        {"id": 1002, "hash": "bbb222", "title": "深度工作", "author": "卡尔·纽波特", "extension": "pdf"}
    )
    queue._process(second)
    second_record = store.get_download(second)
    check("queue paused on empty quota", second_record["status"] == "paused", second_record)
    check("queue reports reason", queue.state()["paused"] is True, queue.state())
    USER["downloads_today"] = 3

    # Re-open the gate first: the previous check left the queue paused on quota,
    # which would short-circuit before the disk test ever runs.
    queue.resume()
    USER["downloads_today"] = 0
    print("queue: refuses to start on a full disk")
    # A half-written download wastes an allowance slot and leaves debris, so the
    # size check has to come before the mirror is touched at all.
    huge = store.create_download(
        {"id": 1003, "hash": "ccc333", "title": "需要整个磁盘的书", "author": "某人",
         "extension": "pdf", "filesize": 500 * 1024 ** 3}
    )
    # The gate sits before any network call, so no /file request may appear.
    file_requests = [r for r in REQUEST_LOG if "/file" in str(r[1])]
    queue._process(huge)
    huge_record = store.get_download(huge)
    check("disk gate marks it failed", huge_record["status"] == "failed", huge_record["status"])
    check("disk gate explains why", "disk space" in huge_record["error"], huge_record["error"])
    check(
        "disk gate never called the mirror",
        [r for r in REQUEST_LOG if "/file" in str(r[1])] == file_requests,
        REQUEST_LOG[-1:],
    )

    print("queue: resume clears the pause")
    queue.resume()
    state = queue.state()
    check("resume clears pause", state["paused"] is False, state)
    check("resume re-queues", state["queued"] >= 1, state)

    print("blocked mirror (HTML instead of JSON)")
    blocked = LocalClient(port)
    blocked._port = port
    try:
        blocked._request("GET", "/blocked")
    except ZlibError as exc:
        check("html body raises a readable error", "unexpected response" in str(exc), str(exc))
    else:
        check("html body raises a readable error", False, "no error")

    print("stats")
    counts = store.stats()
    check("stats counts the finished download", counts.get("done", 0) >= 1, counts)

    server.shutdown()
    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
