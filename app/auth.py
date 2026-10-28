"""Local sign-in: one password standing between the LAN and the mirror.

The app is meant for one person on a private network, so this is deliberately
minimal — no user table, no e-mail, no reset flow. The first visitor sets a
password (stored only as a salted scrypt hash), then every session gets a random
token in an ``HttpOnly`` cookie. Nothing here talks to Z-Library; the mirror
credentials live in their own session file and are untouched by this layer.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from typing import Dict, Optional

# scrypt costs ~120 ms per attempt at N=2**15 on a NAS CPU: slow enough to make
# guessing tedious, fast enough that signing in feels instant. OpenSSL's default
# 32 MB memory cap rejects N=2**15, so request twice that explicitly — otherwise
# the hash silently has to fall back to a weaker N. Raise maxmem together with N.
SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_MAXMEM = 2 ** 15, 8, 1, 64 * 1024 * 1024
MIN_PASSWORD = 8
MAX_PASSWORD = 256

SESSION_COOKIE = "zlib_local"
# A year: this is a home LAN tool, and re-typing a password on a phone every day
# is exactly the kind of friction that gets authentication ripped back out.
SESSION_TTL = 365 * 24 * 3600


class AuthError(RuntimeError):
    """Bad input or a failed sign-in, with a message meant for the UI."""


def _hash(password: str, salt: bytes, n: int = SCRYPT_N, r: int = SCRYPT_R, p: int = SCRYPT_P) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=32,
        maxmem=SCRYPT_MAXMEM,
    )


def encode_password(password: str) -> str:
    """Return ``scrypt$<salt hex>$<digest hex>``."""
    validate_password(password)
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_hash(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash.

    The cost parameters live in this module, not in the stored string, so old
    hashes are checked with the parameters they were written with and only get
    upgraded the next time the password is set.
    """
    try:
        scheme, salt_hex, digest_hex = stored.split("$", 2)
        if scheme != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = _hash(password, bytes.fromhex(salt_hex))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, actual)


def validate_password(password: str) -> None:
    if not isinstance(password, str):
        raise AuthError("password must be a string")
    if len(password) < MIN_PASSWORD:
        raise AuthError(f"password must be at least {MIN_PASSWORD} characters")
    if len(password) > MAX_PASSWORD:
        raise AuthError("password is too long")


class LocalAuth:
    """Password hash and live sessions, both persisted through ``settings``.

    ``settings`` is the existing key/value table, so the account survives a
    container rebuild along with everything else in the SQLite file.
    """

    HASH_KEY = "local_password"
    SESSION_KEY = "local_sessions"
    NAME_KEY = "local_username"
    DEFAULT_NAME = "admin"

    def __init__(self, settings) -> None:
        self._settings = settings
        self._lock = threading.RLock()

    # ---------------------------------------------------------------- password
    def configured(self) -> bool:
        return bool(self._settings.get_setting(self.HASH_KEY, ""))

    def username(self) -> str:
        return self._settings.get_setting(self.NAME_KEY, self.DEFAULT_NAME) or self.DEFAULT_NAME

    def set_username(self, username: str) -> str:
        """Rename the local account. Cosmetic: the password is what guards it."""
        name = (username or "").strip()
        if not name:
            return self.username()
        if len(name) > 64 or any(ch.isspace() for ch in name):
            raise AuthError("username must be one word, up to 64 characters")
        self._settings.set_setting(self.NAME_KEY, name)
        return name

    def register(self, password: str) -> None:
        """Set the password. Only possible while none exists."""
        with self._lock:
            if self.configured():
                raise AuthError("an account already exists")
            self._settings.set_setting(self.HASH_KEY, encode_password(password))
            # A fresh start invalidates anything signed in before it.
            self._settings.set_setting(self.SESSION_KEY, "{}")

    def check(self, password: str) -> bool:
        stored = self._settings.get_setting(self.HASH_KEY, "")
        return bool(stored) and verify_password(password, stored)

    def change(self, password: str) -> None:
        with self._lock:
            self._settings.set_setting(self.HASH_KEY, encode_password(password))

    # ---------------------------------------------------------------- sessions
    def _sessions(self) -> Dict[str, float]:
        try:
            raw = json.loads(self._settings.get_setting(self.SESSION_KEY, "{}") or "{}")
        except ValueError:
            return {}
        now = time.time()
        if not isinstance(raw, dict):
            return {}
        return {token: float(exp) for token, exp in raw.items() if isinstance(exp, (int, float)) and exp > now}

    def _save(self, sessions: Dict[str, float]) -> None:
        self._settings.set_setting(self.SESSION_KEY, json.dumps(sessions))

    def issue(self) -> str:
        """Create a session token and return it."""
        with self._lock:
            sessions = self._sessions()
            token = secrets.token_urlsafe(32)
            sessions[token] = time.time() + SESSION_TTL
            # Cheap bound: an old browser left syncing should not grow this file.
            if len(sessions) > 20:
                for stale in sorted(sessions, key=sessions.get)[: len(sessions) - 20]:
                    sessions.pop(stale, None)
            self._save(sessions)
            return token

    def valid(self, token: Optional[str]) -> bool:
        if not token:
            return False
        with self._lock:
            return token in self._sessions()

    def revoke(self, token: Optional[str]) -> None:
        if not token:
            return
        with self._lock:
            sessions = self._sessions()
            if sessions.pop(token, None) is not None:
                self._save(sessions)

    def revoke_all(self) -> None:
        with self._lock:
            self._save({})
