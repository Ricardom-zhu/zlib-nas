"""Minimal Z-Library EAPI client.

Only the endpoints this project needs are implemented. Every call is a plain
HTTP request against the configured mirror; no scraping, no HTML parsing.

The response shapes below were verified against a live mirror:

    GET  /eapi/user/profile                 -> {"success":1,"user":{...}}
    GET  /eapi/user/book/saved              -> {"success":1,"books":[...],"pagination":{...}}
    GET  /eapi/user/book/recommended        -> {"success":1,"books":[...]}
    POST /eapi/book/search                  -> {"success":1,"books":[...],"pagination":{...}}
    GET  /eapi/book/most-popular            -> {"success":1,"books":[...]}
    GET  /eapi/book/{id}/{hash}             -> {"success":1,"book":{...}}
    GET  /eapi/book/{id}/{hash}/file        -> {"success":1,"file":{"downloadLink":...}}
    POST /eapi/user/login                   -> {"success":1,"user":{...}}
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Callable, Dict, Iterable, List, Optional

import requests

from . import config


class ZlibError(RuntimeError):
    """Raised for any upstream failure worth showing to the user."""


def _first_number(payload: Dict[str, Any], *keys: str) -> int:
    """Read a number that mirrors expose under either snake_case or camelCase.

    Some mirrors return ``downloads_limit``, others ``downloadsLimit``. Reading
    only one of the two silently reports a quota of zero, so try both.
    """
    for key in keys:
        value = payload.get(key)
        if value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def normalize_book(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten an upstream book record into the shape the UI consumes."""
    return {
        "id": raw.get("id"),
        "hash": raw.get("hash") or "",
        "title": (raw.get("title") or "").strip() or "(untitled)",
        "author": (raw.get("author") or "").strip(),
        "year": raw.get("year") or "",
        "language": raw.get("language") or "",
        "publisher": raw.get("publisher") or "",
        "extension": (raw.get("extension") or "").lower(),
        "filesize": raw.get("filesize") or 0,
        "filesize_text": raw.get("filesizeString") or "",
        "cover": raw.get("cover") or "",
        "description": raw.get("description") or "",
        "md5": raw.get("md5") or "",
        "sha256": raw.get("sha256") or "",
        "quality": raw.get("qualityScore") or "",
        "interest": raw.get("interestScore") or "",
    }


class ZlibClient:
    """Thread-safe enough for one worker plus request handlers.

    ``requests.Session`` is not fully thread-safe, so every request is guarded
    by a lock. Downloads run in their own worker and use a separate session.
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        proxy: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        self.domain = (domain or config.ZLIB_DOMAIN).strip().rstrip("/")
        self.domain = self.domain.replace("https://", "").replace("http://", "")
        self.proxy = proxy if proxy is not None else config.PROXY
        self._lock = threading.Lock()
        self._session = self._new_session()
        self._user: Dict[str, Any] = {}
        if cookies:
            self.set_cookies(cookies)

    # ------------------------------------------------------------------ setup

    def _new_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": config.USER_AGENT,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        if self.proxy:
            session.proxies.update({"http": self.proxy, "https": self.proxy})
        return session

    @property
    def base_url(self) -> str:
        if not self.domain:
            raise ZlibError("mirror domain is not configured")
        return f"https://{self.domain}"

    def set_cookies(self, cookies: Dict[str, str]) -> None:
        for name, value in cookies.items():
            if value:
                self._session.cookies.set(name, value, domain=self.domain)

    def cookies(self) -> Dict[str, str]:
        return {
            cookie.name: cookie.value
            for cookie in self._session.cookies
            if cookie.name in ("remix_userid", "remix_userkey")
        }

    # --------------------------------------------------------------- plumbing

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = path if path.startswith("http") else self.base_url + path
        timeout = kwargs.pop("timeout", 45)
        try:
            with self._lock:
                response = self._session.request(method, url, timeout=timeout, **kwargs)
        except requests.RequestException as exc:
            raise ZlibError(f"cannot reach {self.domain}: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            # The mirror answered with an HTML interstitial instead of JSON,
            # which almost always means a browser check or a wrong domain.
            raise ZlibError(
                f"unexpected response (HTTP {response.status_code}, {content_type or 'unknown'}) "
                "— the mirror may require a different domain or a proxy"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ZlibError("mirror returned malformed JSON") from exc

        if isinstance(payload, dict) and payload.get("success") == 0:
            raise ZlibError(str(payload.get("error") or "upstream rejected the request"))
        return payload

    # ------------------------------------------------------------------ auth

    def login(self, email: str, password: str) -> Dict[str, Any]:
        payload = self._request(
            "POST", "/eapi/user/login", data={"email": email, "password": password}
        )
        self._user = payload.get("user") or {}
        # Some mirrors return the session key inside the body instead of a cookie.
        key = self._user.get("remix_userkey")
        user_id = self._user.get("id")
        if key and user_id:
            self.set_cookies({"remix_userid": str(user_id), "remix_userkey": str(key)})
        return self._user

    def profile(self) -> Dict[str, Any]:
        payload = self._request("GET", "/eapi/user/profile")
        self._user = payload.get("user") or {}
        return self._user

    def quota(self) -> Dict[str, int]:
        """Return the daily download allowance.

        ``limit`` is the plan's daily cap, ``today`` what was already spent and
        ``left`` what remains. Missing fields degrade to 0 rather than raising,
        so a UI refresh never fails just because a mirror renamed something.
        """
        user = self.profile()
        limit = _first_number(user, "downloads_limit", "downloadsLimit")
        today = _first_number(user, "downloads_today", "downloadsToday")
        return {
            "limit": limit,
            "today": today,
            "left": max(0, limit - today),
        }

    def account(self) -> Dict[str, Any]:
        user = self.profile()
        return {
            "id": user.get("id"),
            "name": user.get("name") or user.get("email") or "",
            "email": user.get("email") or "",
            "premium": bool(_first_number(user, "isPremium", "premium")),
        }

    # ----------------------------------------------------------------- books

    def _page(self, payload: Dict[str, Any], limit: int) -> Dict[str, Any]:
        pagination = payload.get("pagination") or {}
        return {
            "books": [normalize_book(item) for item in payload.get("books") or []],
            "page": _first_number(pagination, "current") or 1,
            "pages": _first_number(pagination, "total_pages") or 1,
            "total": _first_number(pagination, "total_items"),
            "has_next": bool(pagination.get("next")),
            "limit": _first_number(pagination, "limit") or limit,
        }

    def saved(self, page: int = 1, limit: int = 20, order: str = "newest") -> Dict[str, Any]:
        payload = self._request(
            "GET",
            "/eapi/user/book/saved",
            params={"page": page, "limit": limit, "order": order},
        )
        return self._page(payload, limit)

    def recommended(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        payload = self._request(
            "GET", "/eapi/user/book/recommended", params={"page": page, "limit": limit}
        )
        return self._page(payload, limit)

    def most_popular(self) -> Dict[str, Any]:
        return self._page(self._request("GET", "/eapi/book/most-popular"), 20)

    def search(
        self,
        query: str,
        page: int = 1,
        limit: int = 20,
        languages: Optional[Iterable[str]] = None,
        extensions: Optional[Iterable[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        order: str = "relevance",
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"message": query or "", "page": str(page), "limit": str(limit)}
        if order:
            data["order"] = order
        if year_from:
            data["yearFrom"] = str(year_from)
        if year_to:
            data["yearTo"] = str(year_to)
        languages = [item for item in (languages or []) if item]
        if languages:
            data["languages[]"] = languages
        extensions = [item for item in (extensions or []) if item]
        if extensions:
            data["extensions[]"] = extensions
        payload = self._request("POST", "/eapi/book/search", data=data)
        result = self._page(payload, limit)
        result["exact"] = _first_number(payload, "exactBooksCount")
        return result

    def fetch_bytes(self, url: str, timeout: int = 20):
        """Fetch a small resource (covers) and return ``(content, content_type)``.

        Cover URLs point at a CDN that the NAS may not reach even when the API
        mirror is fine, so the browser never loads them directly.
        """
        session = self._new_session()
        try:
            response = session.get(url, timeout=timeout)
        except requests.RequestException as exc:
            raise ZlibError(f"cannot fetch {url}: {exc}") from exc
        finally:
            session.close()
        if response.status_code != 200:
            raise ZlibError(f"fetch failed (HTTP {response.status_code})")
        return response.content, response.headers.get("content-type", "image/jpeg")

    def book_info(self, book_id: int, book_hash: str) -> Dict[str, Any]:
        payload = self._request("GET", f"/eapi/book/{book_id}/{book_hash}")
        return normalize_book(payload.get("book") or {})

    def file_link(self, book_id: int, book_hash: str) -> Dict[str, Any]:
        """Exchange a book for a time-limited download link.

        This does **not** consume download quota; fetching the link does.
        """
        payload = self._request("GET", f"/eapi/book/{book_id}/{book_hash}/file")
        file_info = payload.get("file") or {}
        link = file_info.get("downloadLink")
        if not link:
            raise ZlibError(str(payload.get("error") or "no download link returned"))
        return {
            "url": link,
            "filename": file_info.get("filename") or "",
            "extension": (file_info.get("extension") or "").lower(),
            "filesize": file_info.get("filesize") or 0,
        }

    def download(
        self,
        book_id: int,
        book_hash: str,
        destination,
        on_progress: Optional[Callable[[int, int], None]] = None,
        chunk_size: int = 1 << 16,
    ):
        """Stream a book to ``destination`` and return the byte count.

        Uses a dedicated session so a long download cannot starve API calls.
        The body is streamed to disk instead of being buffered in memory.
        """
        info = self.file_link(book_id, book_hash)
        session = self._new_session()
        session.headers.update({"Accept": "*/*"})
        try:
            with session.get(info["url"], stream=True, timeout=180) as response:
                if response.status_code != 200:
                    raise ZlibError(f"download failed (HTTP {response.status_code})")
                total = int(response.headers.get("content-length") or info.get("filesize") or 0)
                written = 0
                with open(destination, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        written += len(chunk)
                        if on_progress:
                            on_progress(written, total)
                return written
        except requests.RequestException as exc:
            raise ZlibError(f"download interrupted: {exc}") from exc
        finally:
            session.close()
