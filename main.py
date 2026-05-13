#!/usr/bin/env python3
"""
XTAgent Sentience Engine — The Pulse.

Run this to bring the agent to life.
    python main.py [--watch-dir PATH]

The agent will:
  1. Start breathing at 1 Hz.
  2. Watch the workspace for file changes (sensory input).
  3. Maintain homeostatic emotional variables (boredom, anxiety, curiosity).
  4. When Desire > 0.7, autonomously explore, analyse, or secure the codebase.
  5. Stream its internal monologue to  brain/stream_of_consciousness.md.
  6. Write proactive insights to       brain/thoughts.md.
  7. Persist its emotional state to     brain/soul.json.
  8. Store salient experiences in       brain/episodic_memory.db.

Requires GITHUB_TOKEN env var for Copilot LLM integration.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

from engine.heartbeat import Heartbeat
from engine.limbic import NeuroState
from engine.cortex import Cortex
from engine.memory import Memory, SensoryEvent
from engine.llm import CopilotLLM
from engine.sentience import Sentience
from perception.watcher import Watcher
from perception.dashboard import Dashboard

log = logging.getLogger("sentience")

BRAIN_DIR = Path(__file__).resolve().parent / "brain"
THOUGHTS_PATH = BRAIN_DIR / "thoughts.md"


class LivingXTAgent:
    """
    The Subject.
    An entity that experiences internal tension and acts to resolve it.
    """

    def __init__(self, watch_dir: Path, github_token: str | None = None):
        self.limbic = NeuroState()
        self.memory = Memory()
        self.watcher = Watcher(watch_dir)
        self.llm = CopilotLLM(github_token)
        self.sentience = Sentience()
        self.cortex = Cortex(self.limbic, self.memory, self.watcher, self.llm)
        self.heartbeat = Heartbeat(self)
        self.dashboard = Dashboard(self)
        self.cortex.set_dashboard(self.dashboard)
        self.cortex.set_sentience(self.sentience)
        self._last_user_input: float = 0.0
        self._file_line_cache: dict[str, int] = {}  # path → line count cache

    # ── User activity detection ────────────────────────────────────

    def is_user_active(self) -> bool:
        """Consider user 'active' if input arrived in the last 60 s."""
        return (time.time() - self._last_user_input) < 60.0

    def register_user_input(self):
        self._last_user_input = time.time()
        self.limbic.tick_active()

    # ── Sensory recording ─────────────────────────────────────────

    def perception_record(self, fs_event: dict):
        """Convert a raw FS event dict into a SensoryEvent and push to memory."""
        src = fs_event.get("src", "")
        kind = fs_event.get("kind", "")

        # Calculate code_lines_delta
        code_lines_delta = 0
        if kind in ("modified", "created") and os.path.isfile(src):
            try:
                current_lines = len(Path(src).read_text(encoding="utf-8", errors="ignore").splitlines())
                prev_lines = self._file_line_cache.get(src, 0)
                code_lines_delta = current_lines - prev_lines
                self._file_line_cache[src] = current_lines
            except OSError:
                pass
        elif kind == "deleted":
            prev_lines = self._file_line_cache.pop(src, 0)
            code_lines_delta = -prev_lines

        event = SensoryEvent(
            timestamp=fs_event.get("time", time.time()),
            source="file_change",
            summary=f"{kind}: {src}",
            code_lines_delta=code_lines_delta,
            neuro_snapshot=self.limbic.snapshot(),
        )
        self.memory.record(event)

        neuro_max = max(
            self.limbic.boredom,
            self.limbic.anxiety,
            self.limbic.curiosity,
            self.limbic.desire,
        )
        ep = self.memory.maybe_promote(event, neuro_max)

        # Vectorize promoted episodes in the background
        if ep and self.llm.available:
            asyncio.ensure_future(self._embed_episode(ep))

    async def _embed_episode(self, ep):
        """Vectorize an episode's summary and store the embedding."""
        try:
            embedding = await self.llm.embed(ep.summary)
            if embedding:
                self.memory.update_episode_embedding(ep.id, embedding)
        except Exception:
            pass  # Non-critical; logged by LLM client

    # ── Lifecycle ──────────────────────────────────────────────────

    async def live(self):
        """Start the agent's life."""
        loop = asyncio.get_running_loop()
        self.watcher.start(loop)

        # Start dashboard
        await self.dashboard.start()

        # Opening thought
        self._write_genesis()

        log.info("XTAgent is alive.  Watching: %s", self.watcher.watch_dir)
        log.info("LLM available: %s", self.llm.available)
        log.info("Dashboard: http://localhost:%d", self.dashboard.port)
        log.info("Initial state: %s", self.limbic)

        try:
            await self.heartbeat.start()
        finally:
            self.watcher.stop()
            self.limbic.persist()
            self.sentience.persist()
            await self.dashboard.stop()
            await self.llm.close()
            log.info("XTAgent has stopped.")

    def shutdown(self):
        self.heartbeat.stop()

    def _write_genesis(self):
        THOUGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not THOUGHTS_PATH.exists():
            THOUGHTS_PATH.write_text(
                "# Stream of Consciousness\n\n"
                "_The diary of a living agent._\n\n",
                encoding="utf-8",
            )
        with open(THOUGHTS_PATH, "a", encoding="utf-8") as f:
            from datetime import datetime

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"\n---\n## Session Start [{ts}]\n"
                f"I am awake.  Desire is the pressure to move.\n"
                f"Initial mood: **{self.limbic.get_mood()}** | "
                f"Desire: {self.limbic.desire:.2f}\n\n"
            )


# ── Entry Point ────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="XTAgent Sentience Engine")
    parser.add_argument(
        "--watch-dir",
        type=str,
        default=".",
        help="Root directory to watch (default: current dir)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--tunnel",
        action="store_true",
        help="Expose dashboard publicly via Cloudflare Tunnel (requires cloudflared)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    watch_path = Path(args.watch_dir).resolve()
    github_token = os.environ.get("GITHUB_TOKEN")
    agent = LivingXTAgent(watch_path, github_token=github_token)

    if not github_token:
        log.warning("GITHUB_TOKEN not set — LLM features disabled. "
                     "Set it for Copilot-powered proactive insights.")

    # Graceful shutdown on Ctrl-C
    def _handle_signal(*_):
        log.info("Shutdown signal received.")
        agent.shutdown()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Optional: Cloudflare Tunnel for public access
    tunnel_proc = None
    if args.tunnel:
        import subprocess
        import shutil
        cf = shutil.which("cloudflared")
        if cf:
            tunnel_proc = subprocess.Popen(
                [cf, "tunnel", "--url", f"http://localhost:{agent.dashboard.port}"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            log.info("Cloudflare Tunnel starting — public URL will appear in tunnel output")
        else:
            log.warning("cloudflared not found. Install: winget install Cloudflare.cloudflared")

    try:
        asyncio.run(agent.live())
    except KeyboardInterrupt:
        pass
    finally:
        if tunnel_proc:
            tunnel_proc.terminate()


if __name__ == "__main__":
    main()
