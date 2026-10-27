# zlib-nas

**English** · [中文](README.zh-CN.md)

A small, self-hosted web client for your own **Z-Library account**, built to run on a NAS.

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
- **No front-end build.** Plain HTML/CSS/JS, no npm, no CDN, no bundler.

## Features

| | |
|---|---|
| Wishlist | Sync from the account, search/filter locally, cover art proxied through the server |
| Search | Title / author / ISBN, language and format filters, pagination |
| Download | Server-side queue, live progress, retry, one-click resume |
| Library | Lists files actually on disk, with direct download links |
| Settings | Mirror domain, sign-in by password **or** by pasting cookies, sign-out |
| Ops | `/api/status` health endpoint, `/api/export` JSON dump, bilingual UI (中文 / English) |

## Quick start

```bash
git clone https://github.com/<you>/zlib-nas.git
cd zlib-nas
cp .env.example .env          # optional: preset the mirror domain
docker compose up -d --build
```

Open `http://<nas-ip>:8101`, go to **Settings**, enter your mirror domain
(e.g. `zh.pirate101.ru`, no `https://`), sign in, then press **Sync wishlist**.

Without Docker:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DATA_DIR=./data uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

Everything is optional; anything left blank can be set in the UI.

| Variable | Default | Meaning |
|---|---|---|
| `ZLIB_DOMAIN` | — | Mirror domain, without scheme. The UI can set it too. |
| `ZLIB_EMAIL` / `ZLIB_PASSWORD` | — | Optional auto-login. The password is used once and not stored. |
| `PROXY` | — | HTTP proxy for both the mirror and the file CDN, e.g. `http://192.168.1.10:7890`. |
| `DATA_DIR` | `/app/data` | SQLite database, session cookie, downloads. |
| `DOWNLOAD_DIR` | `$DATA_DIR/downloads` | Where finished books are written. |
| `MIRROR_DIR` | — | Optional second folder; finished files are symlinked here so another tool can scan it. |
| `QUOTA_RESERVE` | `0` | Pause the queue while this many downloads remain. `2` keeps a small reserve. |
| `MAX_CONCURRENT` | `1` | Parallel downloads. Keep at 1: the quota, not bandwidth, is the bottleneck. |

## Using it from another book manager

If a book manager already scans a folder, point `MIRROR_DIR` at that folder. Finished
downloads get a symlink there, so the file appears in the manager's library without
duplicating bytes. The real file stays under `DOWNLOAD_DIR`.

## API

All endpoints are plain JSON under `/api`. Interactive docs: `/api/docs`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/status` | Session state, quota, queue state, counts |
| `POST` | `/api/login` | `{domain, email, password}` or `{domain, cookies:{remix_userid,remix_userkey}}` |
| `POST` | `/api/logout` | Delete the stored session |
| `POST` | `/api/sync/saved` | Mirror the whole wishlist into SQLite |
| `GET` | `/api/saved?q=&limit=&offset=` | Query the local wishlist |
| `POST` | `/api/search` | `{query, page, limit, languages[], extensions[], year_from, year_to, order}` |
| `POST` | `/api/download` | `{id, hash, title, author, extension}` |
| `GET` | `/api/downloads` | Download records with progress |
| `POST` | `/api/downloads/{id}/retry` | Re-queue a failed record |
| `POST` | `/api/queue/pause` · `/api/queue/resume` | Control the queue |
| `GET` | `/api/library` · `/api/library/{name}` | List and fetch files on disk |
| `GET` | `/api/cover?u=<url>` | Server-side cover proxy |
| `GET` | `/api/export` | Full JSON dump of the database |

## Being a good guest

The mirror is somebody else's server, usually paid for by donations and shared with
everyone else on that domain, so this project treats it as a scarce resource:

- account and quota are cached for two minutes, so a dashboard left open does not
  turn into a request stream; only the refresh button bypasses the cache
- covers are cached on disk after the first fetch
- the browser polls every thirty seconds, and not at all in a background tab
- downloads are serialised by default, and the queue stops when the daily
  allowance runs out instead of retrying into a wall of errors
- browsing the wishlist costs no quota at all; only the download itself does

If you fork this and raise the concurrency or shorten the cache, you are the reason
a mirror starts rate-limiting its users.

## Security notes

This is a **LAN tool**. Read these before exposing it anywhere:

- There is **no user authentication** of its own. Anyone who can reach the port can use
  your Z-Library session. Do not publish it to the internet; if you need remote access,
  put it behind a VPN and/or a reverse proxy with auth.
- The session cookie file (`data/session.json`) grants access to your account. It is
  written with mode `0600`; protect the data directory accordingly.
- The password is never stored. If you prefer not to send it at all, sign in with cookies:
  copy `remix_userid` and `remix_userkey` from a logged-in browser session.
- Downloads are your responsibility: keep them for personal use and respect the laws that
  apply to you.

## Limitations

- Single account, single user. No multi-user support by design.
- The mirror domain changes over time; if calls start returning HTML instead of JSON,
  update the domain in Settings.
- `MAX_CONCURRENT > 1` is untested against quota edge cases; the queue is designed around 1.
- Mirror availability, quota rules and API shapes are outside this project's control.
  A change upstream can break a call until the client is updated.

## Development

```
app/config.py      environment + paths
app/store.py       SQLite schema and queries
app/zlibrary.py    EAPI client (login, wishlist, search, quota, streamed download)
app/queue.py       quota-guarded worker thread + filename sanitising
app/main.py        FastAPI routes + static mount
static/            index.html, style.css, app.js (no build step)
```

`data/zlib-nas.db` is the whole state: copy it for a backup.

```bash
python -c "import app.main"     # import check
curl -s localhost:8101/api/status | jq
python tests/test_offline.py    # full suite, no network needed
```

`tests/test_offline.py` starts a mock mirror that answers the same EAPI endpoints,
then drives the real client, store and queue against it: login, wishlist sync,
search, quota gate, streamed download, export. It runs in CI on every push and
needs no account, so contributions can be verified without touching Z-Library.

## License

MIT. Not affiliated with Z-Library. See [LICENSE](LICENSE).
