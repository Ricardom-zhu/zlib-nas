"""zlib-nas — a small, self-hosted web client for a Z-Library account.

Run with::

    uvicorn app.main:app --host 0.0.0.0 --port 8000

The server keeps one authenticated session, mirrors your wishlist into a local
SQLite file, and downloads books through a quota-aware queue. It is meant for a
single user on a private network and ships without any authentication layer of
its own — put it behind your LAN, not the internet.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .queue import DownloadQueue
from .store import Store
from .zlibrary import ZlibClient, ZlibError

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

config.ensure_dirs()
store = Store()
queue_manager = DownloadQueue(store, lambda: get_client())

app = FastAPI(title="zlib-nas", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")


# --------------------------------------------------------------------- session


def load_session() -> Dict[str, Any]:
    if config.SESSION_FILE.exists():
        try:
            return json.loads(config.SESSION_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
    return {}


def save_session(payload: Dict[str, Any]) -> None:
    config.SESSION_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(config.SESSION_FILE, 0o600)
    except OSError:
        pass


def clear_session() -> None:
    config.SESSION_FILE.unlink(missing_ok=True)


def get_client() -> ZlibClient:
    session = load_session()
    domain = session.get("domain") or config.ZLIB_DOMAIN
    cookies = session.get("cookies") or {}
    client = ZlibClient(domain=domain, cookies=cookies)

    # Configured credentials are used once to mint a session; the password
    # itself never touches disk.
    if not cookies and config.ZLIB_EMAIL and config.ZLIB_PASSWORD:
        client.login(config.ZLIB_EMAIL, config.ZLIB_PASSWORD)
        save_session({"domain": client.domain, "cookies": client.cookies()})
    elif not cookies and not config.ZLIB_DOMAIN:
        raise ZlibError("no account configured yet — open Settings and sign in")
    return client


def session_configured() -> bool:
    session = load_session()
    return bool((session.get("cookies") or {}).get("remix_userkey"))


@app.on_event("startup")
def _startup() -> None:
    store.reset_stale()
    queue_manager.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    queue_manager.shutdown()


# ---------------------------------------------------------------------- models


class LoginPayload(BaseModel):
    domain: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None


class SearchPayload(BaseModel):
    query: str = ""
    page: int = 1
    limit: int = 20
    languages: Optional[List[str]] = None
    extensions: Optional[List[str]] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    order: str = "relevance"


class DownloadPayload(BaseModel):
    id: int
    hash: str = ""
    title: str = ""
    author: str = ""
    extension: str = ""


# --------------------------------------------------------------------- helpers


def _guard(func, *args, **kwargs):
    """Translate upstream errors into HTTP errors with a readable message."""
    try:
        return func(*args, **kwargs)
    except ZlibError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def require_client() -> ZlibClient:
    """Return a configured client, or fail with a message the UI can show."""
    try:
        return get_client()
    except ZlibError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ---------------------------------------------------------------------- routes


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "configured": session_configured(),
        "domain": load_session().get("domain") or config.ZLIB_DOMAIN,
        "queue": queue_manager.state(),
        "stats": store.stats(),
        "saved_count": store.saved_count(),
        "download_dir": str(config.DOWNLOAD_DIR),
        "account": None,
        "quota": None,
    }
    if not payload["configured"]:
        return payload

    try:
        client = require_client()
        payload["account"] = client.account()
        payload["quota"] = client.quota()
    except HTTPException as exc:
        # A status call must never fail outright: report it in the body instead.
        payload["error"] = exc.detail
    except ZlibError as exc:
        payload["error"] = str(exc)
    return payload


@app.post("/api/login")
def api_login(payload: LoginPayload) -> Dict[str, Any]:
    domain = (payload.domain or config.ZLIB_DOMAIN or "").strip()
    if not domain:
        raise HTTPException(status_code=400, detail="mirror domain is required")

    client = ZlibClient(domain=domain)

    if payload.cookies and payload.cookies.get("remix_userkey"):
        client.set_cookies(payload.cookies)
    elif payload.email and payload.password:
        try:
            client.login(payload.email, payload.password)
        except ZlibError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="provide cookies or email and password")

    try:
        account = client.account()
    except ZlibError as exc:
        raise HTTPException(status_code=401, detail=f"session rejected: {exc}") from exc

    save_session({"domain": client.domain, "cookies": client.cookies()})
    return {"ok": True, "account": account}


@app.post("/api/logout")
def api_logout() -> Dict[str, Any]:
    clear_session()
    return {"ok": True}


@app.post("/api/sync/saved")
def api_sync_saved() -> Dict[str, Any]:
    """Pull the whole wishlist into the local database, a page at a time."""
    client = require_client()

    page, written, pages = 1, 0, 1
    while page <= pages and page <= 200:
        result = _guard(client.saved, page=page, limit=50)
        written += store.upsert_saved(result["books"])
        pages = result["pages"] or 1
        if not result["books"]:
            break
        page += 1

    return {"ok": True, "synced": written, "total": store.saved_count()}


@app.get("/api/saved")
def api_saved(q: str = "", limit: int = 200, offset: int = 0) -> Dict[str, Any]:
    return store.list_saved(query=q, limit=max(1, min(limit, 500)), offset=offset)


@app.post("/api/search")
def api_search(payload: SearchPayload) -> Dict[str, Any]:
    client = require_client()
    return _guard(
        client.search,
        payload.query,
        page=max(1, payload.page),
        limit=max(1, min(payload.limit, 100)),
        languages=payload.languages,
        extensions=payload.extensions,
        year_from=payload.year_from,
        year_to=payload.year_to,
        order=payload.order,
    )


@app.get("/api/recommended")
def api_recommended() -> Dict[str, Any]:
    return _guard(require_client().recommended)


@app.get("/api/popular")
def api_popular() -> Dict[str, Any]:
    return _guard(require_client().most_popular)


@app.post("/api/download")
def api_download(payload: DownloadPayload) -> Dict[str, Any]:
    if store.has_download(payload.id, payload.hash):
        raise HTTPException(status_code=409, detail="this book is already queued or downloaded")

    download_id = store.create_download(
        {
            "id": payload.id,
            "hash": payload.hash,
            "title": payload.title,
            "author": payload.author,
            "extension": payload.extension,
        }
    )
    queue_manager.enqueue(download_id)
    return {"ok": True, "download_id": download_id}


@app.get("/api/downloads")
def api_downloads(limit: int = 100) -> List[Dict[str, Any]]:
    return store.list_downloads(limit=max(1, min(limit, 500)))


@app.post("/api/downloads/{download_id}/retry")
def api_retry(download_id: int) -> Dict[str, Any]:
    if not store.get_download(download_id):
        raise HTTPException(status_code=404, detail="not found")
    queue_manager.retry(download_id)
    return {"ok": True}


@app.post("/api/queue/resume")
def api_resume() -> Dict[str, Any]:
    queue_manager.resume()
    return {"ok": True, "queue": queue_manager.state()}


@app.post("/api/queue/pause")
def api_pause() -> Dict[str, Any]:
    queue_manager.pause("paused from the UI")
    return {"ok": True, "queue": queue_manager.state()}


@app.get("/api/library")
def api_library() -> Dict[str, Any]:
    """Files actually present on disk, independent of the database."""
    files = []
    root = Path(config.DOWNLOAD_DIR)
    if root.exists():
        for entry in sorted(root.iterdir()):
            if entry.is_file():
                stat = entry.stat()
                files.append(
                    {"name": entry.name, "size": stat.st_size, "mtime": int(stat.st_mtime * 1000)}
                )
    return {"files": files, "dir": str(root)}


@app.get("/api/library/{name}")
def api_library_file(name: str):
    root = Path(config.DOWNLOAD_DIR).resolve()
    target = (root / name).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target, filename=target.name)


@app.get("/api/cover")
def api_cover(u: str = "") -> Response:
    """Proxy cover images.

    Cover URLs point at a CDN that may be unreachable from the NAS even when
    the mirror itself works, so they are fetched server-side.
    """
    if not u.startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="invalid url")
    content, media_type = _guard(require_client().fetch_bytes, u)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=604800"},
    )


@app.get("/api/export")
def api_export():
    target = Path(config.DATA_DIR) / "export.json"
    store.dump_json(target)
    return FileResponse(target, filename="zlib-nas-export.json")


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
