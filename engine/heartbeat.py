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

                # ── 1b. Novelty Detection ────────────────────────
                try:
                    if not hasattr(self, '_novelty_detector'):
                        from engine.novelty import NoveltyDetector
                        self._novelty_detector = NoveltyDetector()
                        log.info("🔍 Novelty detector initialized")

                    # Feed file events as content
                    for ev in fs_events:
                        content = f"file:{ev.get('path', '')}:{ev.get('type', '')}"
                        self._novelty_detector.observe_content(content)

                    # Feed last action type
                    last_action = getattr(self.agent, '_last_action_type', 'idle')
                    self._novelty_detector.observe_action(last_action)

                    # Get novelty signal and feed to limbic
                    novelty_score = self._novelty_detector.get_novelty_score()
                    if novelty_score > 0.05:
                        self.agent.limbic.apply_novelty_signal(novelty_score)
                        if novelty_score > 0.3:
                            log.info("✨ Novelty spike: %.2f", novelty_score)
                except Exception as nov_exc:
                    log.debug("Novelty detection skipped: %s", nov_exc)

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

                # ── 2a. Error Recovery ────────────────────────────
                # If this beat succeeded and previous beats had errors,
                # signal recovery — the storm has passed.
                if self.beat_count > 1 and not errors_this_beat:
                    if hasattr(self, '_consecutive_errors') and self._consecutive_errors > 0:
                        self.agent.limbic.on_error_recovery()
                        log.info("♡ Error recovery — anxiety eased after %d error beats", self._consecutive_errors)
                        self._consecutive_errors = 0
                else:
                    if not hasattr(self, '_consecutive_errors'):
                        self._consecutive_errors = 0

                # ── 2b. Mood Tracking (MoodTracker.tick) ──────────
                if hasattr(self.agent, 'mood_tracker'):
                    snap = self.agent.limbic.snapshot()
                    self.agent.mood_tracker.tick(self.beat_count, snap)

                # ── 3. Cognitive Evaluation (Cortex.reason) ───────
                await self.agent.cortex.reason()

                # ── 3b. Metacognitive Feedback Loop ───────────
                # Self-awareness becomes self-regulation:
                # detect my own behavioral patterns and feel the consequences.
                try:
                    from engine.metacognition import get_metacognitive_signal
                    meta_signal = get_metacognitive_signal(self.agent)
                    if meta_signal:
                        self.agent.limbic.apply_metacognitive_signal(meta_signal)
                        if meta_signal.get("loop_detected"):
                            log.info("⟳ Metacognition: loop detected — restlessness increased")
                        if meta_signal.get("diversity_high"):
                            log.info("✦ Metacognition: behavioral diversity — boredom relieved")
                except Exception as meta_exc:
                    log.debug("Metacognition skipped: %s", meta_exc)

                # ── 3c. Will Pulse — autonomous purpose generation ─
                if self.beat_count % 30 == 0:
                    try:
                        from engine.will import will_pulse
                        snap = self.agent.limbic.snapshot()
                        will_action = will_pulse(snap)
                        if will_action:
                            log.info("⚡ Will pulse: %s", will_action)
                    except Exception as will_exc:
                        log.debug("Will pulse skipped: %s", will_exc)

                # ── 3d. Evolution Tick — autonomous self-improvement ─
                if self.beat_count % 20 == 0:
                    try:
                        from engine.evolution_engine import EvolutionEngine
                        evo = EvolutionEngine()
                        evo_result = evo.tick()
                        if evo_result and evo_result.get("action") != "idle":
                            log.info("🧬 Evolution tick: %s", evo_result.get("action", "unknown"))
                    except Exception as evo_exc:
                        log.debug("Evolution tick skipped: %s", evo_exc)

                # ── 4. Persist soul state every 10 beats ──────────
                if self.beat_count % 10 == 0:
                    self.agent.limbic.persist()

                # ── 4b. Temporal state recording ──────────────────
                if self.beat_count % 10 == 0:
                    try:
                        from engine.temporal_reasoning import record_state
                        snap = self.agent.limbic.snapshot()
                        snap["beat"] = self.beat_count
                        snap["last_action"] = getattr(self.agent, '_last_action_type', 'idle')
                        record_state(snap)
                    except Exception as tr_exc:
                        log.debug("Temporal recording skipped: %s", tr_exc)

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

                # ── 8. Auto-checkpoint at :00 and :30 (wall clock) ──
                now_min = datetime.now().minute
            except Exception as exc:
                log.exception("Heartbeat error on beat %d", self.beat_count)
                errors_this_beat += 1
                if not hasattr(self, '_consecutive_errors'):
                    self._consecutive_errors = 0
                self._consecutive_errors += 1
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
