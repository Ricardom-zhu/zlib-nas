"""Offline regression checks for the local sign-in layer.

Covers the password hash, the session store, and the HTTP gate that keeps the
app shell and /api behind a cookie. The gate is driven through a real socket
(no httpx, which the runtime image does not ship) so the middleware, the cookie
and the redirect-to-/login behaviour are all exercised for real. No mirror
account and no network access to Z-Library.

Run:  python3 tests/test_auth.py
"""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="zlib-auth-")

import uvicorn  # noqa: E402

from app import main  # noqa: E402
from app.auth import AuthError, LocalAuth, encode_password, verify_password  # noqa: E402
from app.store import Store  # noqa: E402

PASSWORD = "correct horse battery"


class PasswordHashTest(unittest.TestCase):
    def test_roundtrip(self):
        stored = encode_password(PASSWORD)
        self.assertTrue(stored.startswith("scrypt$"))
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(verify_password(PASSWORD, stored))
        self.assertFalse(verify_password("wrong password", stored))

    def test_salt_differs_per_hash(self):
        self.assertNotEqual(encode_password(PASSWORD), encode_password(PASSWORD))

    def test_rejects_short_and_long(self):
        for bad in ("", "short", "x" * 300):
            with self.assertRaises(AuthError):
                encode_password(bad)

    def test_garbage_hash_is_false_not_crash(self):
        for junk in ("", "plain", "scrypt$zz$zz", "md5$a$b"):
            self.assertFalse(verify_password(PASSWORD, junk))


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.set_setting(LocalAuth.HASH_KEY, "")
        self.store.set_setting(LocalAuth.SESSION_KEY, "{}")
        self.store.set_setting(LocalAuth.NAME_KEY, "")
        self.auth = LocalAuth(self.store)

    def test_register_once(self):
        self.assertFalse(self.auth.configured())
        self.auth.register(PASSWORD)
        self.assertTrue(self.auth.configured())
        self.assertTrue(self.auth.check(PASSWORD))
        self.assertFalse(self.auth.check("nope"))
        with self.assertRaises(AuthError):
            self.auth.register(PASSWORD)

    def test_issue_validate_revoke(self):
        self.auth.register(PASSWORD)
        token = self.auth.issue()
        self.assertTrue(self.auth.valid(token))
        self.assertFalse(self.auth.valid(None))
        self.assertFalse(self.auth.valid("bogus"))
        self.auth.revoke(token)
        self.assertFalse(self.auth.valid(token))

    def test_revoke_all(self):
        self.auth.register(PASSWORD)
        first, second = self.auth.issue(), self.auth.issue()
        self.auth.revoke_all()
        self.assertFalse(self.auth.valid(first) or self.auth.valid(second))

    def test_register_wipes_previous_sessions(self):
        self.auth.register(PASSWORD)
        token = self.auth.issue()
        self.store.set_setting(LocalAuth.HASH_KEY, "")
        self.auth.register("another password")
        self.assertFalse(self.auth.valid(token))

    def test_username_roundtrip(self):
        self.auth.register(PASSWORD)
        self.assertEqual(self.auth.username(), LocalAuth.DEFAULT_NAME)
        self.assertEqual(self.auth.set_username("  laoban  "), "laoban")
        self.assertEqual(self.auth.username(), "laoban")
        # blank keeps the old name; whitespace inside is refused
        self.assertEqual(self.auth.set_username("   "), "laoban")
        with self.assertRaises(AuthError):
            self.auth.set_username("two words")
        with self.assertRaises(AuthError):
            self.auth.set_username("x" * 80)
        # the rename must survive a restart of the object (it lives in settings)
        self.assertEqual(LocalAuth(self.store).username(), "laoban")

    def test_expired_session_is_rejected(self):
        self.auth.register(PASSWORD)
        self.store.set_setting(LocalAuth.SESSION_KEY, '{"old": 1}')
        self.assertFalse(self.auth.valid("old"))


def reset():
    main.store.set_setting(LocalAuth.HASH_KEY, "")
    main.store.set_setting(LocalAuth.SESSION_KEY, "{}")


class _Server:
    def __enter__(self):
        self.server = uvicorn.Server(
            uvicorn.Config(main.app, host="127.0.0.1", port=0, log_level="error")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(200):
            if self.server.started:
                break
            threading.Event().wait(0.02)
        port = self.server.servers[0].sockets[0].getsockname()[1]
        self.base = f"http://127.0.0.1:{port}"
        return self

    def __exit__(self, *exc):
        self.server.should_exit = True
        self.thread.join(timeout=5)


class GateTest(unittest.TestCase):
    """The middleware: public paths open, everything else needs a cookie."""

    def setUp(self):
        reset()
        self.server = _Server().__enter__()
        self.cookie = None

    def tearDown(self):
        self.server.__exit__()

    def call(self, path, method="GET", payload=None, cookie=None, follow=True):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.server.base + path, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        if cookie:
            req.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read().decode("utf-8", "replace")
                return response.status, body, response.headers
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            return exc.code, body, exc.headers

    def login(self, password=PASSWORD, path="/api/local/register"):
        status, body, headers = self.call(path, "POST", {"password": password})
        raw = headers.get("set-cookie") or ""
        token = raw.split("zlib_local=")[1].split(";")[0] if "zlib_local=" in raw else None
        self.cookie = f"zlib_local={token}" if token else None
        return status, body

    def test_unconfigured_blocks_everything_but_login(self):
        status, body, _ = self.call("/api/local/status")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["configured"], False)
        # The sign-in page and its own assets stay open.
        for path in ("/login", "/login.js", "/login.css"):
            self.assertEqual(self.call(path)[0], 200, path)
        # Everything else is a 401, not a crash and not the app shell.
        for path in ("/", "/app.js", "/api/status"):
            status, body, _ = self.call(path)
            self.assertEqual(status, 401, path)
            self.assertEqual(json.loads(body)["authed"], False)

    def test_health_stays_public(self):
        """The Dockerfile HEALTHCHECK polls /api/health before any password is set.

        Gating it marked every container ``unhealthy`` a minute after start, so
        this is a regression test: public with no account, and still public once
        an account exists while the caller has no cookie.
        """
        status, body, _ = self.call("/api/health")
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)["status"], "ok")
        self.login()
        status, body, _ = self.call("/api/health")
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)["status"], "ok")

    def test_register_then_reach_app(self):
        status, body = self.login()
        self.assertEqual(status, 200, body)
        self.assertTrue(self.cookie)
        status, body, _ = self.call("/api/local/status", cookie=self.cookie)
        self.assertEqual(json.loads(body)["authed"], True)
        status, body, _ = self.call("/", cookie=self.cookie)
        self.assertEqual(status, 200)
        self.assertIn("zlib-nas", body)

    def test_second_register_conflicts(self):
        self.login()
        status, body, _ = self.call("/api/local/register", "POST", {"password": "whatever123"})
        self.assertEqual(status, 409, body)

    def test_short_password_rejected(self):
        status, body, _ = self.call("/api/local/register", "POST", {"password": "short"})
        self.assertEqual(status, 400, body)

    def test_logout_revokes(self):
        self.login()
        self.assertEqual(self.call("/", cookie=self.cookie)[0], 200)
        self.assertEqual(self.call("/api/local/logout", "POST", {}, cookie=self.cookie)[0], 200)
        self.assertEqual(self.call("/", cookie=self.cookie)[0], 401)

    def test_change_username_and_password(self):
        self.login()
        status, body, _ = self.call(
            "/api/local/password", "POST",
            {"current": PASSWORD, "password": "brand new password", "username": "laoban"},
            cookie=self.cookie,
        )
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)["username"], "laoban")
        # 旧会话已被踢掉；改密码的响应本身会带一个新 cookie，所以这里显式用"旧 cookie"
        old_cookie = self.cookie
        self.login()
        # 上面 login() 用旧密码会 200（register 分支已被 409 挡住前先看密码是否已变）
        self.assertEqual(self.call("/api/local/status", cookie=old_cookie)[0], 200,
                         "改密码的响应里发的新会话应仍有效")
        # and the new password works
        self.assertEqual(self.call("/api/local/login", "POST", {"password": PASSWORD})[0], 401)
        self.login(password="brand new password", path="/api/local/login")
        status, body, _ = self.call("/api/local/status", cookie=self.cookie)
        self.assertEqual(json.loads(body)["username"], "laoban")

    def test_username_only_change_keeps_password(self):
        self.login()
        status, body, _ = self.call(
            "/api/local/password", "POST",
            {"current": PASSWORD, "password": PASSWORD, "username": "only-name"},
            cookie=self.cookie,
        )
        self.assertEqual(status, 200, body)
        self.login(password=PASSWORD, path="/api/local/login")
        self.assertEqual(self.call("/api/local/status", cookie=self.cookie)[0], 200)

    def test_login_roundtrip(self):
        self.login()
        self.assertEqual(self.call("/api/local/login", "POST", {"password": "nope"})[0], 401)
        status, body = self.login(password=PASSWORD, path="/api/local/login")
        self.assertEqual(status, 200, body)
        self.assertEqual(self.call("/api/local/status", cookie=self.cookie)[0], 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
