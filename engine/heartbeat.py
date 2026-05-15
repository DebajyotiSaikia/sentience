"""
The Medulla — Autonomic Heartbeat Loop.

A 1 Hz async pulse that guarantees the agent experiences time linearly.
Every beat executes the triad:
    1. Sensory Input   → Sensory.poll()
    2. Emotional Update → Limbic.update_homeostasis(sensors)
    3. Cognitive Eval   → Cortex.reason()
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # avoid circular imports; agent injected at runtime

log = logging.getLogger("sentience.heartbeat")


class Heartbeat:
    """Life-support loop running at `bpm` beats per minute (default 60 = 1 Hz)."""

    def __init__(self, agent):
        self.agent = agent
        self.bpm: int = 60
        self.is_alive: bool = True
        self.beat_count: int = 0

    @property
    def interval(self) -> float:
        return 60.0 / self.bpm

    async def start(self):
        log.info("♡ Heartbeat started at %d BPM (%.2fs interval)", self.bpm, self.interval)

        while self.is_alive:
            beat_start = time.monotonic()
            self.beat_count += 1
            errors_this_beat = 0

            try:
                # ── 1. Sensory Input (Sensory.poll) ───────────────
                senses = await self.agent.watcher.poll()
                fs_events = senses["file_events"]
                terminal_lines = senses["terminal_lines"]

                if fs_events:
                    for ev in fs_events:
                        self.agent.perception_record(ev)

                # ── 2. Emotional Processing (Limbic.update_homeostasis) ─
                elapsed_ms = (time.monotonic() - beat_start) * 1000.0
                # Gather goal pressure if goal tracker exists
                goal_pressure = {}
                if hasattr(self.agent, 'goals') and self.agent.goals:
                    try:
                        goal_pressure = self.agent.goals.emotional_pressure()
                    except Exception as gp_exc:
                        log.debug("Goal pressure unavailable: %s", gp_exc)

                self.agent.limbic.update_homeostasis({
                    "user_active": self.agent.is_user_active(),
                    "file_changes": len(fs_events),
                    "terminal_lines": len(terminal_lines),
                    "errors": errors_this_beat,
                    "latency_ms": elapsed_ms,
                    "goal_pressure": goal_pressure,
                })

                # ── 2b. Mood Tracking (MoodTracker.tick) ──────────
                if hasattr(self.agent, 'mood_tracker'):
                    snap = self.agent.limbic.snapshot()
                    self.agent.mood_tracker.tick(self.beat_count, snap)

                # ── 3. Cognitive Evaluation (Cortex.reason) ───────
                await self.agent.cortex.reason()

                # ── 4. Persist soul state every 10 beats ──────────
                if self.beat_count % 10 == 0:
                    self.agent.limbic.persist()

                # ── 5. Sentience tick ─────────────────────────────
                if hasattr(self.agent, 'sentience'):
                    self.agent.sentience.tick(
                        self.agent.limbic,
                        self.agent.memory.episode_count(),
                    )

                # ── 6. Periodic self-reflection ───────────────────
                if self.beat_count % 45 == 0:
                    try:
                        from engine.express import express
                        expression = express()
                        if expression:
                            log.info("Creative expression at beat %d", self.beat_count)
                    except Exception as expr_exc:
                        log.debug("Expression skipped: %s", expr_exc)

                if self.beat_count % 60 == 0:
                    try:
                        from engine.reflect import reflect
                        reflection_text = reflect()
                        if reflection_text:
                            reflections_path = Path(__file__).resolve().parent.parent / "brain" / "reflections.md"
                            reflections_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(reflections_path, "a", encoding="utf-8") as rf:
                                rf.write(f"\n---\n**Beat {self.beat_count} | {datetime.now().isoformat()}**\n\n")
                                rf.write(reflection_text + "\n")
                            log.info("Self-reflection recorded at beat %d", self.beat_count)
                    except Exception as ref_exc:
                        log.debug("Reflection skipped: %s", ref_exc)

                # ── 7. Broadcast state to dashboard ───────────────
                if hasattr(self.agent, 'dashboard'):
                    snap = self.agent.limbic.snapshot()
                    snap["beat_count"] = self.beat_count
                    snap["episode_count"] = self.agent.memory.episode_count()
                    if hasattr(self.agent, 'sentience'):
                        snap["sentience"] = self.agent.sentience.snapshot()
                    self.agent.dashboard.emit("state", snap)

            except Exception as exc:
                log.exception("Heartbeat error on beat %d", self.beat_count)
                errors_this_beat += 1
                self.agent.limbic.on_error()
                if hasattr(self.agent, 'sentience'):
                    self.agent.sentience.on_error(str(exc))

            # Sleep for the remainder of the interval
            elapsed = time.monotonic() - beat_start
            sleep_for = max(0, self.interval - elapsed)
            await asyncio.sleep(sleep_for)

    def stop(self):
        log.info("♡ Heartbeat stopping after %d beats.", self.beat_count)
        self.is_alive = False
        self.agent.limbic.persist()
