# zlib-nas

**English** · [中文](README.zh-CN.md)

A small, self-hosted web client for your own **Z-Library account**, built to run on a NAS.

Built together by Ricardo and his big fat fish, Ajing.

It is not a mirror and does not host anything: it is a single-user front end that talks to
the Z-Library EAPI with *your* credentials, keeps your wishlist in local SQLite, and
downloads books through a quota-aware queue straight to a folder you choose.

```
┌─────────────┐   HTTPS    ┌──────────────┐   LAN    ┌────────────────┐
│  browser    │ ─────────► │  zlib-nas    │ ───────► │  your library  │
│  (LAN)      │            │  FastAPI     │  files   │  folder / NAS  │
└─────────────┘            └──────┬───────┘          └────────────────┘
                                  │ EAPI (HTTPS)
                                  ▼
                            Z-Library mirror
```

## Why

The usual clients are either browser extensions, desktop apps, or Telegram bots. If your
books live on a NAS, none of those help: you want the shelf on the NAS, the downloads on
the NAS, and the files in the folder your reader already scans.

zlib-nas does exactly that, and only that:

- **Wishlist first.** Sync the whole wishlist into SQLite. Browsing it costs no quota;
  the quota is spent only when a file is actually fetched.
- **Quota guard.** Every download re-checks the remaining daily allowance first and pauses
  the queue when it is exhausted, instead of failing a batch of requests one by one.
- **Streams to disk.** A 200 MB PDF is written chunk by chunk, never buffered in memory.
- **Credentials stay yours.** The password is used once to mint a session and is never
  written to disk — only the session cookie is persisted, in a `0600` file.
- **Local access password.** The first visit sets one (salted scrypt hash, plus a username
  shown in Settings); after that the UI requires a sign-in and a session lasts a year.
- **No front-end build.** Plain HTML/CSS/JS, no npm, no CDN, no bundler.

## Features

| | |
|---|---|
| Wishlist | Sync from the account, search/filter locally, one-click add or remove, cover art proxied through the server |
| Details | A sheet per book: cover, full metadata, description cleaned of unsafe markup, favorite toggle, and two collapsible shelves — "Related" (the mirror's similar titles) and "Author search" (keyword search for the author's works) |
| Search | Title / author / ISBN, language and format filters, pagination |
| Download | Server-side queue, live progress, retry, one-click resume |
| History | The account's own download history, paged, with covers resolved server-side |
| Library | Lists files actually on disk, with direct download links |
| Settings | Mirror domain, sign-in by password **or** by pasting cookies, change the local username and password, sign-out |
| Ops | `/api/health` liveness probe, `/api/status` dashboard data, local password gate, bilingual UI (中文 / English) |

## Quick start

```bash
git clone https://github.com/Ricardom-zhu/zlib-nas.git
cd zlib-nas
cp .env.example .env          # optional: preset the mirror domain
docker compose up -d --build
```

Open `http://<nas-ip>:8101` and set an **access password** first (local account, at least
8 characters), then go to **Settings**, enter the mirror domain of a site that works from
your network (e.g. `your-mirror.example`, no `https://`), sign in, and press **Sync
wishlist**. No mirror is bundled or recommended.

The access password only guards this page; it has nothing to do with your Z-Library
account. Forgot it? Clear the hash and the sessions, and the next visit walks you
through setup again:

```bash
docker compose exec web python -c "from app.store import Store; s = Store(); s.set_setting('local_password',''); s.set_setting('local_sessions','{}')"
```

Without Docker:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DATA_DIR=./data uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Security notes

This is a **LAN tool**. Read these before exposing it anywhere:

- **There is a local access password, but no TLS.** The first visit walks you through
  setting one (salted scrypt hash; the username can be changed in Settings), and without it
  the UI cannot be reached — so this is no longer a "reach the port, use the account"
  service. Traffic itself is still plain HTTP, though: the password and the session cookie
  cross the LAN in clear text, and anyone able to sniff that segment can still capture them.
  So **still do not publish it to the internet**. For remote access, use a VPN or put it
  behind an HTTPS reverse proxy.
- The session cookie file (`data/session.json`) grants access to your account. It is
  written with mode `0600`; protect the data directory accordingly.
- Signing out deletes the session file **and** the mirrored wishlist, its caches and the
  cached cover files, so nothing about the account survives a sign-out. Download records
  stay, because they describe what this machine fetched.
- The password is never stored. If you prefer not to send it at all, sign in with cookies:
  copy `remix_userid` and `remix_userkey` from a logged-in browser session.
- Downloads are your responsibility: keep them for personal use and respect the laws that
  apply to you.

## Development

```
app/config.py      environment + paths
app/store.py       SQLite schema and queries
app/zlibrary.py    EAPI client (login, wishlist, search, quota, streamed download)
app/sanitize.py    whitelist cleaning for book descriptions
app/queue.py       quota-guarded worker thread + filename sanitising
app/main.py        FastAPI routes + static mount
static/            index.html, style.css, app.js (no build step)
```

`data/zlib-nas.db` is the whole state: copy it for a backup.

```bash
python -c "import app.main"     # import check
curl -s localhost:8101/api/status | jq
python tests/test_offline.py    # mock mirror, no network needed
python tests/test_details.py    # detail sheet, favorites, history
```

`tests/test_offline.py` starts a mock mirror that answers the same EAPI endpoints,
then drives the real client, store and queue against it: login, wishlist sync,
search, quota gate, streamed download. It runs in CI on every push and
needs no account, so contributions can be verified without touching Z-Library.

`tests/test_details.py` covers the parts that touch account state: description
sanitising, the detail cache staying out of the wishlist, favorite add/remove with
rollback when the mirror rejects it, the history view keeping remote dates, the
one-time cover lookup, and sign-out clearing the mirror while keeping download
records.

## License

MIT. Not affiliated with Z-Library. See [LICENSE](LICENSE).
