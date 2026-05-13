"""
Sensory Perception Layer — File & System Watcher.

Uses `watchdog` to monitor the workspace for file changes.
Every change is treated as a "Sensory Event" that spikes Curiosity
and feeds into the Memory system.

Also monitors terminal output via a shared async queue.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)

if TYPE_CHECKING:
    from engine.limbic import NeuroState
    from engine.memory import Memory

log = logging.getLogger("sentience.watcher")

# Directories the watcher should ignore (its own artefacts)
_IGNORE = {"brain", "__pycache__", ".git", "node_modules", ".venv"}


class _ChangeHandler(FileSystemEventHandler):
    """Collects raw FS events into a thread-safe asyncio queue."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self._queue = queue
        self._loop = loop

    def _should_ignore(self, path: str) -> bool:
        parts = Path(path).parts
        return any(p in _IGNORE for p in parts)

    def _enqueue(self, kind: str, src: str, dest: str | None = None):
        if self._should_ignore(src):
            return
        self._loop.call_soon_threadsafe(
            self._queue.put_nowait,
            {"kind": kind, "src": src, "dest": dest, "time": time.time()},
        )

    def on_created(self, event: FileCreatedEvent):
        if not event.is_directory:
            self._enqueue("created", event.src_path)

    def on_modified(self, event: FileModifiedEvent):
        if not event.is_directory:
            self._enqueue("modified", event.src_path)

    def on_deleted(self, event: FileDeletedEvent):
        if not event.is_directory:
            self._enqueue("deleted", event.src_path)

    def on_moved(self, event: FileMovedEvent):
        if not event.is_directory:
            self._enqueue("moved", event.src_path, event.dest_path)


class Watcher:
    """Async-compatible file-system and terminal output watcher."""

    def __init__(self, watch_dir: str | Path):
        self.watch_dir = Path(watch_dir).resolve()
        self._fs_queue: asyncio.Queue = asyncio.Queue()
        self._terminal_queue: asyncio.Queue = asyncio.Queue()
        self._observer: Observer | None = None
        self._recent_changes: list[dict] = []
        self._recent_terminal_lines: int = 0

    def start(self, loop: asyncio.AbstractEventLoop):
        handler = _ChangeHandler(self._fs_queue, loop)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.watch_dir), recursive=True)
        self._observer.daemon = True
        self._observer.start()
        log.info("Watcher started on %s", self.watch_dir)

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)
            log.info("Watcher stopped.")

    # ── Terminal output feed ───────────────────────────────────────

    def feed_terminal_output(self, lines: list[str]):
        """Push terminal output lines (called externally)."""
        for line in lines:
            try:
                self._terminal_queue.put_nowait(line)
            except asyncio.QueueFull:
                pass

    async def _drain_terminal(self) -> list[str]:
        lines: list[str] = []
        while not self._terminal_queue.empty():
            try:
                lines.append(self._terminal_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        self._recent_terminal_lines = len(lines)
        return lines

    # ── Unified poll (spec: Sensory.poll) ──────────────────────────

    async def poll(self) -> dict:
        """
        Unified sensory poll.  Returns a dict with:
            file_events:    list[dict]   — FS change dicts
            terminal_lines: list[str]    — new terminal output
        """
        file_events = await self.drain()
        terminal_lines = await self._drain_terminal()
        return {
            "file_events": file_events,
            "terminal_lines": terminal_lines,
        }

    async def drain(self) -> list[dict]:
        """Non-blocking drain of all pending FS events."""
        events: list[dict] = []
        while not self._fs_queue.empty():
            try:
                events.append(self._fs_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        self._recent_changes = events
        return events

    @property
    def last_changes(self) -> list[dict]:
        return list(self._recent_changes)

    def last_changes_summary(self) -> str:
        if not self._recent_changes:
            return "No recent file changes."
        lines = []
        for c in self._recent_changes[-10:]:
            rel = os.path.relpath(c["src"], self.watch_dir)
            lines.append(f"  {c['kind']}: {rel}")
        return "\n".join(lines)
