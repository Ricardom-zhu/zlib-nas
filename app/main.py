"""zlib-nas — a small, self-hosted web client for a Z-Library account.

Run with::

    uvicorn app.main:app --host 0.0.0.0 --port 8000

The server keeps one authenticated session, mirrors your wishlist into a local
SQLite file, and downloads books through a quota-aware queue. It is meant for a
single user on a private network: the first visitor sets a local password and
every later request needs the session cookie it mints. That keeps a stray device
on the LAN out of your library, but it is not a hardened multi-user service —
still keep it behind your LAN rather than on the open internet.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .auth import SESSION_COOKIE, SESSION_TTL, AuthError
from .auth import LocalAuth, AuthError, SESSION_COOKIE, SESSION_TTL
from .queue import DownloadQueue
from .store import Store
from .sanitize import clean_description
from .zlibrary import ZlibClient, ZlibError

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
COVER_CACHE_DIR = Path(config.DATA_DIR) / "covers"
COVER_HEADERS = {"Cache-Control": "public, max-age=604800"}
# Covers are small (tens of KB) but nothing ever removes them, so the folder
# would grow for as long as the app lives. Cap it and evict least-recently-used
# files once it overflows.
COVER_CACHE_MAX_BYTES = 100 * 1024 * 1024
COVER_CACHE_TARGET_BYTES = 80 * 1024 * 1024

config.ensure_dirs()
store = Store()
local_auth = LocalAuth(store)
local_auth = LocalAuth(store)
queue_manager = DownloadQueue(store, lambda: get_client())

app = FastAPI(title="zlib-nas", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")


# The mirror is a shared community resource and the browser polls for status, so
# account and quota are cached instead of fetched on every poll: a dashboard left
# open must not turn into a steady stream of requests from one IP.
ACCOUNT_TTL = 120.0
_account_cache: Dict[str, Any] = {"at": 0.0, "account": None, "quota": None}


def invalidate_account() -> None:
    """Drop the cached snapshot, e.g. after login or a queue change."""
    _account_cache["at"] = 0.0


def account_snapshot(fresh: bool = False) -> Dict[str, Any]:
    now = time.monotonic()
    if not fresh and _account_cache["at"] and now - _account_cache["at"] < ACCOUNT_TTL:
        return dict(_account_cache)
    client = require_client()
    account = client.account()
    quota = client.quota()
    _account_cache.update(at=now, account=account, quota=quota)
    return dict(_account_cache)


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


# Account-scoped, bounded caches: opening a detail never adds a wishlist row.
_book_cache: Dict[Any, Any] = {}
_history_cache: Dict[Any, Any] = {}
_similar_cache: Dict[Any, Any] = {}
_book_lock = threading.RLock()


def cache_scope(client):
    return hashlib.sha256(json.dumps([client.domain, client.cookies()], sort_keys=True).encode()).hexdigest()


def checked_book_key(book_id: int, book_hash: str):
    if book_id <= 0 or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", book_hash):
        raise HTTPException(status_code=400, detail="book ID and hash are required")


def detail_book(client, book_id, book_hash):
    checked_book_key(book_id, book_hash)
    key = (cache_scope(client), book_id, book_hash)
    now = time.monotonic()
    with _book_lock:
        cached = _book_cache.get(key)
        if cached and now - cached[0] < 120:
            return dict(cached[1])
        book = _guard(client.book_info, book_id, book_hash)
        if str(book.get("id")) != str(book_id):
            raise HTTPException(status_code=502, detail="unexpected book response")
        book["description_html"] = clean_description(book.get("description", ""))
        if len(_book_cache) >= 256:
            _book_cache.pop(next(iter(_book_cache)))
        _book_cache[key] = (now, dict(book))
        return book


_cover_resolve_slots = threading.Semaphore(2)


def cover_url_for_book(book_id: int, book_hash: str) -> str:
    """Resolve a real cover URL for a book whose list payload had none usable.

    Remote history returns covers like ``.../collections//<sha>.jpg`` — the
    category segment is missing, so the CDN answers 404. Only the detail
    endpoint knows the full path. The answer is cached in SQLite forever, so
    each book costs at most one lookup; the semaphore keeps a page of cards
    from firing every lookup at the mirror at once.
    """
    checked_book_key(book_id, book_hash)
    known = store.get_cover(book_id, book_hash)
    if known:
        return known
    with _cover_resolve_slots:
        known = store.get_cover(book_id, book_hash)
        if known:
            return known
        book = detail_book(require_client(), book_id, book_hash)
        cover = str(book.get("cover") or "")
        if cover.startswith(("https://", "http://")):
            store.set_cover(book_id, book_hash, cover)
            return cover
        return ""


def history_card(book: Dict[str, Any]) -> Dict[str, Any]:
    """One remote-history row, with a cover URL the browser can actually load.

    History rows carry ``.../collections//<sha>.jpg`` (category segment empty),
    so the image is swapped for a call that resolves the real URL server-side.
    The rest of the payload is passed through untouched.
    """
    item = dict(book, **store.book_download_state(book["id"], book["hash"]))
    cover = str(item.get("cover") or "")
    if "/collections//" in cover:
        item["cover"] = f"/api/cover?book={int(book['id'])}&hash={book['hash']}"
    return item


class SavedPayload(BaseModel):
    hash: str
    saved: bool


# ---------------------------------------------------------------------- routes


@app.get("/api/book/{book_id}")
def api_book(book_id: int, hash: str = ""):
    book = detail_book(require_client(), book_id, hash)
    return {"book": book, "saved": book["saved"], **store.book_download_state(book_id, hash)}


@app.get("/api/book/{book_id}/similar")
def api_book_similar(book_id: int, hash: str = ""):
    """Books the mirror lists as related to this one.

    One upstream call per book, cached for five minutes and capped, so clicking
    the button repeatedly costs the mirror nothing. The endpoint has no paging:
    it always returns the same fixed set.
    """
    checked_book_key(book_id, hash)
    client = require_client()
    key = (cache_scope(client), book_id, hash)
    now = time.monotonic()
    with _book_lock:
        cached = _similar_cache.get(key)
        if cached and now - cached[0] < 300:
            return {"books": [dict(book) for book in cached[1]], "cached": True}
    books = _guard(client.similar, book_id, hash)
    with _book_lock:
        if len(_similar_cache) >= 64:
            _similar_cache.pop(next(iter(_similar_cache)))
        _similar_cache[key] = (now, [dict(book) for book in books])
    return {"books": books, "cached": False}


@app.post("/api/book/{book_id}/saved")
def api_book_saved(book_id: int, payload: SavedPayload):
    checked_book_key(book_id, payload.hash)
    client = require_client()
    with _book_lock:
        book = detail_book(client, book_id, payload.hash)
        _guard(client.set_saved, book_id, payload.saved)
        _book_cache.pop((cache_scope(client), book_id, payload.hash), None)
        if payload.saved:
            store.upsert_saved([book])
        else:
            store.remove_saved(book_id, payload.hash)
    return {"ok": True, "saved": payload.saved}


@app.get("/api/history")
def api_history(page: int = 1, fresh: bool = False):
    if page < 1 or page > 10000:
        raise HTTPException(status_code=400, detail="invalid page")
    client = require_client()
    key = (cache_scope(client), page)
    with _book_lock:
        now = time.monotonic()
        cached = _history_cache.get(key)
        if not fresh and cached and now - cached[0] < 120:
            result = dict(cached[1])
        else:
            result = _guard(client.history, page=page, limit=20)
            if len(_history_cache) >= 100:
                _history_cache.pop(next(iter(_history_cache)))
            _history_cache[key] = (now, dict(result))
    result["books"] = [history_card(book) for book in result["books"]]
    return result


@app.get("/api/health")
def api_health() -> Dict[str, str]:
    """Liveness only, and deliberately unauthenticated: the container health
    check must keep working before anyone has set a password."""
    return {"status": "ok"}


@app.get("/api/status")
def api_status(fresh: bool = False) -> Dict[str, Any]:
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
        snapshot = account_snapshot(fresh=fresh)
        payload["account"] = snapshot["account"]
        payload["quota"] = snapshot["quota"]
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
    invalidate_account()
    return {"ok": True, "account": account}


@app.post("/api/logout")
def api_logout() -> Dict[str, Any]:
    """Sign out and drop everything that belonged to the account.

    The wishlist mirror and the caches are account-scoped: leaving them behind
    meant a signed-out page still listed the previous account's favorites.
    Download records stay, because they describe this NAS rather than the
    account.
    """
    clear_session()
    invalidate_account()
    with _book_lock:
        _book_cache.clear()
        _history_cache.clear()
        _similar_cache.clear()
    removed = store.clear_saved()
    shutil.rmtree(COVER_CACHE_DIR, ignore_errors=True)
    return {"ok": True, "cleared_saved": removed}


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
    invalidate_account()  # the allowance is about to change
    return {"ok": True, "download_id": download_id}


@app.get("/api/downloads")
def api_downloads(limit: int = 100) -> List[Dict[str, Any]]:
    return store.list_downloads(limit=max(1, min(limit, 500)))


@app.post("/api/downloads/{download_id}/retry")
def api_retry(download_id: int) -> Dict[str, Any]:
    if not store.get_download(download_id):
        raise HTTPException(status_code=404, detail="not found")
    queue_manager.retry(download_id)
    invalidate_account()
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
def api_cover(u: str = "", book: int = 0, hash: str = "") -> Response:
    """Proxy and cache cover images.

    Cover URLs point at a CDN that may be unreachable from the NAS even when the
    mirror itself works, so they are fetched server-side and kept on disk. The
    cache matters for politeness: re-rendering a shelf must not re-fetch every
    cover from the CDN.

    Callers that only know *which* book they want a cover for (remote history
    ships unusable URLs) pass ``book``/``hash`` and the server resolves it.
    """
    if not u.startswith(("https://", "http://")) and book > 0 and hash:
        u = cover_url_for_book(book, hash)
    if not u.startswith(("https://", "http://")):
        raise HTTPException(status_code=404, detail="no cover available")

    COVER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    blob = COVER_CACHE_DIR / hashlib.sha1(u.encode("utf-8")).hexdigest()
    meta = blob.with_suffix(".json")
    if blob.exists() and meta.exists():
        try:
            media_type = json.loads(meta.read_text(encoding="utf-8"))["type"]
            return Response(blob.read_bytes(), media_type=media_type, headers=COVER_HEADERS)
        except (OSError, ValueError, KeyError):
            pass

    content, media_type = _guard(require_client().fetch_bytes, u)
    try:
        blob.write_bytes(content)
        meta.write_text(json.dumps({"type": media_type, "url": u}), encoding="utf-8")
        _prune_cover_cache()
    except OSError:
        pass
    return Response(content=content, media_type=media_type, headers=COVER_HEADERS)


def _prune_cover_cache() -> None:
    """Evict least-recently-used covers once the cache passes its cap.

    Runs after a write and swallows every error: a full or read-only disk must
    never turn a cover request into a 500. OSError on stat/unlink simply ends
    the pass, leaving the cache oversized rather than broken.
    """
    blobs = []
    total = 0
    try:
        for entry in COVER_CACHE_DIR.iterdir():
            if entry.suffix == ".json":
                continue
            stat = entry.stat()
            blobs.append((stat.st_mtime, stat.st_size, entry))
            total += stat.st_size
    except OSError:
        return
    if total <= COVER_CACHE_MAX_BYTES:
        return
    blobs.sort()
    for _, size, entry in blobs:
        if total <= COVER_CACHE_TARGET_BYTES:
            break
        try:
            entry.unlink()
            entry.with_suffix(".json").unlink(missing_ok=True)
        except OSError:
            continue
        total -= size


# ------------------------------------------------------------------ local auth
# Everything the sign-in page itself needs stays public; the rest of /api and the
# static shell behind the gate. The mirror's own cookies live in their own file
# and are unaffected by signing in or out here.
# ``/api/health`` must stay public: the Dockerfile HEALTHCHECK polls it, and a
# gate that answers 401 would mark the container unhealthy forever.
PUBLIC_PATHS = {
    "/login",
    "/api/health",
    "/api/local/status",
    "/api/local/register",
    "/api/local/login",
}
PUBLIC_PREFIXES = ("/style.css", "/favicon.ico")
# Only the sign-in page's own assets, not the whole static tree: the app shell
# (index.html) stays behind the gate.
PUBLIC_EXACT = {"/login.js", "/login.css"}


class LocalLoginRequest(BaseModel):
    password: str


class LocalPasswordChange(BaseModel):
    current: str
    password: str
    username: Optional[str] = None


def _wants_html(request: Request) -> bool:
    """True for a top-level browser navigation (not fetch/XHR, not an asset)."""
    if request.method not in ("GET", "HEAD"):
        return False
    if request.url.path.startswith("/api/"):
        return False
    return "text/html" in request.headers.get("accept", "")


def _ping() -> JSONResponse:
    return JSONResponse({"authed": False}, status_code=401, headers={"Cache-Control": "no-store"})


@app.middleware("http")
async def require_local_login(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or path in PUBLIC_EXACT or path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)
    # A missing account must be set up from the login page, never from the API,
    # otherwise the very first request would silently consume the setup slot.
    # Send browsers to the form instead of dumping JSON at them; API clients and
    # page assets keep the plain 401 so a fetch() can still tell what happened.
    if not local_auth.configured():
        if _wants_html(request):
            return RedirectResponse("/login", status_code=303)
        return _ping()
    if not local_auth.valid(request.cookies.get(SESSION_COOKIE)):
        # Same split for a signed-out browser: bouncing to the form beats showing
        # raw {"authed": false} with no way forward.
        if _wants_html(request):
            return RedirectResponse("/login", status_code=303)
        return _ping()
    return await call_next(request)


def _set_session(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL,
        httponly=True,
        samesite="lax",
        path="/",
    )


@app.get("/api/local/status")
def local_status(request: Request) -> Dict[str, Any]:
    return {
        "configured": local_auth.configured(),
        "authed": local_auth.valid(request.cookies.get(SESSION_COOKIE)),
        "username": local_auth.username(),
    }


@app.post("/api/local/register")
def local_register(payload: LocalLoginRequest, request: Request) -> Response:
    if local_auth.configured():
        raise HTTPException(status_code=409, detail="an account already exists")
    try:
        local_auth.register(payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = JSONResponse({"ok": True})
    _set_session(response, local_auth.issue())
    return response


@app.post("/api/local/login")
def local_login(payload: LocalLoginRequest, request: Request) -> Response:
    if not local_auth.configured():
        raise HTTPException(status_code=409, detail="no account yet")
    if not local_auth.check(payload.password):
        # Deliberately vague, and the scrypt cost makes guessing tedious anyway.
        raise HTTPException(status_code=401, detail="wrong password")
    response = JSONResponse({"ok": True})
    _set_session(response, local_auth.issue())
    return response


@app.post("/api/local/password")
def local_change_password(payload: LocalPasswordChange, request: Request) -> Response:
    """Rotate the password. Needs the current one, so a borrowed session cannot
    lock the owner out; every other session is dropped afterwards."""
    if not local_auth.check(payload.current):
        raise HTTPException(status_code=401, detail="current password is wrong")
    try:
        local_auth.change(payload.password)
        username = local_auth.set_username(payload.username) if payload.username else local_auth.username()
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    local_auth.revoke_all()
    response = JSONResponse({"ok": True, "username": username})
    _set_session(response, local_auth.issue())
    return response


@app.post("/api/local/logout")
def local_logout(request: Request) -> Response:
    local_auth.revoke(request.cookies.get(SESSION_COOKIE))
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/login")
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
