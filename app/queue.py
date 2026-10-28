"""Quota-guarded download queue.

The daily download allowance is the real bottleneck, so the queue never lets a
batch run itself into a wall of errors: before each task it re-reads the
remaining quota and pauses the whole queue when the allowance is spent. A
paused queue resumes with one click once the quota has rolled over.

Files are streamed straight to disk, so a 200 MB PDF never lands in RAM.
"""

from __future__ import annotations

import os
import queue
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from . import config

_UNSAFE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# Keep this much free on top of the expected file size. The mirror's reported
# size is advisory, and the filesystem needs headroom of its own.
_DISK_MARGIN = 50 * 1024 * 1024


def safe_filename(title: str, author: str, extension: str) -> str:
    """Build a readable, filesystem-safe name: ``Author - Title.ext``."""
    stem = f"{author} - {title}" if author else title
    stem = _UNSAFE.sub(" ", stem)
    stem = re.sub(r"\s+", " ", stem).strip().strip(".")
    stem = stem[:150] or "book"
    extension = (extension or "bin").lstrip(".")
    return f"{stem}.{extension}"


class DownloadQueue:
    def __init__(self, store, client_factory: Callable[[], Any]) -> None:
        self.store = store
        self.client_factory = client_factory
        self._queue: "queue.Queue[int]" = queue.Queue()
        self._lock = threading.Lock()
        self._workers: list[threading.Thread] = []
        self._paused_reason = ""
        self._active: Dict[int, Dict[str, Any]] = {}
        self._stop = threading.Event()

    # ---------------------------------------------------------------- control

    def start(self) -> None:
        for index in range(config.MAX_CONCURRENT):
            worker = threading.Thread(
                target=self._worker_loop, name=f"zlib-dl-{index}", daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def shutdown(self) -> None:
        self._stop.set()

    def enqueue(self, download_id: int) -> None:
        self._queue.put(download_id)

    def resume(self) -> None:
        """Clear a quota pause and re-queue everything that is still pending."""
        with self._lock:
            self._paused_reason = ""
        for record in self.store.list_downloads(limit=500):
            if record["status"] in ("queued", "paused"):
                self.store.update_download(record["id"], status="queued", error="")
                self._queue.put(record["id"])

    def retry(self, download_id: int) -> None:
        record = self.store.get_download(download_id)
        if not record:
            return
        self.store.update_download(
            download_id, status="queued", error="", bytes_done=0, bytes_total=0
        )
        self.enqueue(download_id)

    def pause(self, reason: str) -> None:
        with self._lock:
            self._paused_reason = reason

    # ------------------------------------------------------------------ state

    def state(self) -> Dict[str, Any]:
        with self._lock:
            paused = self._paused_reason
            active = [dict(item) for item in self._active.values()]
        queued = sum(
            1 for record in self.store.list_downloads(limit=500) if record["status"] == "queued"
        )
        return {
            "paused": bool(paused),
            "paused_reason": paused,
            "active": active,
            "queued": queued,
            "workers": len(self._workers),
        }

    # ----------------------------------------------------------------- worker

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                download_id = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                self._process(download_id)
            except Exception as exc:  # never let one bad task kill the worker
                self.store.update_download(
                    download_id, status="failed", error=str(exc)[:500]
                )
            finally:
                self._queue.task_done()

    def _process(self, download_id: int) -> None:
        record = self.store.get_download(download_id)
        if not record or record["status"] not in ("queued", "paused"):
            return

        with self._lock:
            if self._paused_reason:
                self.store.update_download(download_id, status="paused")
                return

        try:
            client = self.client_factory()
        except Exception as exc:
            self.store.update_download(
                download_id, status="paused", error=f"not signed in: {exc}"[:400]
            )
            self.pause(f"the account is not usable: {exc}")
            return

        # Quota gate: check before spending anything.
        try:
            quota = client.quota()
        except Exception as exc:
            self.store.update_download(
                download_id, status="queued", error=f"quota check failed: {exc}"[:400]
            )
            self.pause(f"cannot read the download allowance: {exc}")
            return

        if quota["left"] <= config.QUOTA_RESERVE:
            self.store.update_download(download_id, status="paused", error="daily allowance reached")
            self.pause(
                f"daily allowance reached ({quota['today']}/{quota['limit']}) — "
                "the queue resumes when the allowance rolls over"
            )
            return

        filename = safe_filename(record["title"], record["author"], record["extension"])
        destination = Path(config.DOWNLOAD_DIR) / filename
        counter = 1
        while destination.exists():
            destination = Path(config.DOWNLOAD_DIR) / (
                f"{destination.stem} ({counter}){destination.suffix}"
            )
            counter += 1

        # Refuse up front rather than fail halfway through on a full disk: a
        # half-written file is worse than no file, and the allowance spent on
        # the partial attempt is already gone. A tight margin covers the fact
        # that the download's size is the mirror's claim, not a promise.
        backup = self._free_bytes(destination.parent)
        needed = int(record["filesize"] or 0)
        if needed > 0 and backup < needed + _DISK_MARGIN:
            self.store.update_download(
                download_id,
                status="failed",
                error=(
                    f"not enough disk space: {backup // (1024 * 1024)} MB free, "
                    f"{needed // (1024 * 1024)} MB needed"
                )[:500],
            )
            return

        self.store.update_download(
            download_id, status="running", filename=destination.name, path=str(destination), error=""
        )
        with self._lock:
            self._active[download_id] = {
                "id": download_id,
                "title": record["title"],
                "bytes_done": 0,
                "bytes_total": record["filesize"] if "filesize" in record else 0,
            }

        def on_progress(done: int, total: int) -> None:
            self.store.update_download(download_id, bytes_done=done, bytes_total=total)
            with self._lock:
                if download_id in self._active:
                    self._active[download_id]["bytes_done"] = done
                    self._active[download_id]["bytes_total"] = total

        try:
            size = client.download(record["zlib_id"], record["hash"], destination, on_progress)
        except Exception as exc:
            self.store.update_download(download_id, status="failed", error=str(exc)[:500])
            if destination.exists():
                destination.unlink(missing_ok=True)
        else:
            self.store.update_download(
                download_id, status="done", bytes_done=size, bytes_total=size, error=""
            )
            self._mirror(destination)
        finally:
            with self._lock:
                self._active.pop(download_id, None)

    @staticmethod
    def _free_bytes(path: Path) -> int:
        """Free space on the filesystem holding ``path``; 0 when it is unknown.

        Unknown free space must not block a download, so the quota gate above
        stays the authority and this is only a best-effort pre-flight.
        """
        try:
            return shutil.disk_usage(path).free
        except OSError:
            return 0

    def _mirror(self, path: Path) -> None:
        """Optionally expose the file in another folder (e.g. a library scan dir).

        A symlink is preferred; if the target is on a different filesystem or
        the link exists already, the step is skipped silently.
        """
        if not config.MIRROR_DIR:
            return
        try:
            config.MIRROR_DIR.mkdir(parents=True, exist_ok=True)
            link = Path(config.MIRROR_DIR) / path.name
            if not link.exists():
                os.symlink(path, link)
        except OSError:
            pass
