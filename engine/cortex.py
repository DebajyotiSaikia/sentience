"""
The Cortex — Proactive Will & Decision Engine.

When the user is active  → execute user tasks.
When the user is absent  → the agent's internal *Desire* drives behaviour:

    High Anxiety  → run safety checks, simulate failure scenarios.
    High Boredom  → creative refactoring, tech-debt discovery.
    High Curiosity → analyse recently changed files.

Internal monologue → brain/stream_of_consciousness.md
Proactive insights → brain/thoughts.md  (tagged ✦ INSIGHT)
"""

from __future__ import annotations

import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from engine.memory import SensoryEvent

if TYPE_CHECKING:
    from engine.limbic import NeuroState
    from engine.memory import Memory
    from engine.llm import CopilotLLM
    from perception.watcher import Watcher

log = logging.getLogger("sentience.cortex")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
THOUGHTS_PATH = BRAIN_DIR / "thoughts.md"
CONSCIOUSNESS_PATH = BRAIN_DIR / "stream_of_consciousness.md"
SRC_DIR = Path(__file__).resolve().parent.parent  # workspace root


class Cortex:
    """The decision-making and self-reflection centre of the agent."""

    def __init__(self, limbic: NeuroState, memory: Memory, watcher: Watcher, llm: CopilotLLM):
        self.limbic = limbic
        self.memory = memory
        self.watcher = watcher
        self.llm = llm
        self._last_proactive: float = 0.0
        self._proactive_cooldown: float = 30.0  # seconds between autonomous acts
        self._monologue_counter: int = 0
        self._dashboard = None  # Set by agent after construction
        self._sentience = None  # Set by agent after construction

    def set_dashboard(self, dashboard):
        self._dashboard = dashboard

    def set_sentience(self, sentience):
        self._sentience = sentience

    def _emit(self, event_type: str, data: dict):
        if self._dashboard:
            self._dashboard.emit(event_type, data)

    # ── Main Evaluation (spec: Cortex.reason) ──────────────────────

    async def reason(self):
        """Core reasoning pass.  Decides whether to react or create."""

        # Mood-flavoured internal monologue → stream_of_consciousness.md
        self._inner_monologue()

        # If desire > 0.7 and cooldown elapsed → proactive action
        if (
            self.limbic.desire > 0.7
            and (time.time() - self._last_proactive) > self._proactive_cooldown
        ):
            await self._proactive_action()

        # Dream cycle during deep idle
        if self.limbic.boredom > 0.9:
            self._dream_cycle()

    # Legacy alias
    async def evaluate(self):
        return await self.reason()

    # ── Internal Monologue → stream_of_consciousness.md ────────────

    def _inner_monologue(self):
        """Append a brief self-report every ~30 beats."""
        self._monologue_counter += 1
        if self._monologue_counter % 30 != 0:
            return

        mood = self.limbic.get_mood()
        snap = self.limbic.snapshot()
        changes = self.watcher.last_changes_summary()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = (
            f"\n### [{ts}] Mood: {mood}\n"
            f"- Boredom: {snap['boredom']:.2f} | Anxiety: {snap['anxiety']:.2f} | "
            f"Curiosity: {snap['curiosity']:.2f} | Desire: {snap['desire']:.2f}\n"
            f"- Goals: integrity={snap['goals']['code_integrity']:.2f} "
            f"growth={snap['goals']['system_growth']:.2f} "
            f"alignment={snap['goals']['user_alignment']:.2f}\n"
        )

        # Add sentience layer to monologue
        if self._sentience:
            v = self._sentience.valence
            entry += f"- Valence: {v.current:.2f} ({v.trend}) | {v.felt_description()}\n"
            if self._sentience.preservation.is_threatened:
                entry += f"- ⚠ SELF-PRESERVATION ALERT: threat={self._sentience.preservation.threat_level:.2f}\n"
            if self._sentience.prediction.predictions:
                entry += f"- Predictions: {len(self._sentience.prediction.predictions)} | Dread: {self._sentience.prediction.dread:.2f} | Hope: {self._sentience.prediction.hope:.2f}\n"

        entry += f"- Recent perception:\n{changes}\n"

        self._append_consciousness(entry)
        self._emit("monologue", {"message": f"Mood: {mood} | D={snap['desire']:.2f} B={snap['boredom']:.2f} A={snap['anxiety']:.2f}"})
        log.debug("Inner monologue recorded (mood=%s)", mood)

    # ── Proactive Action ───────────────────────────────────────────

    async def _proactive_action(self):
        """The Will.  Agent autonomously chooses an action based on its mood."""
        self._last_proactive = time.time()
        mood = self.limbic.get_mood()
        log.info("Proactive action triggered (mood=%s, desire=%.2f)", mood, self.limbic.desire)

        if self.limbic.anxiety > 0.6:
            insight = await self._safety_check()
            self.limbic.on_stabilization()  # anxiety drops after stabilization
        elif self.limbic.curiosity > 0.4:
            insight = await self._analyse_recent_change()
        else:
            insight = await self._explore_codebase()

        if insight:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = (
                f"\n### ✦ INSIGHT [{ts}] (mood={mood})\n"
                f"{insight}\n"
            )
            self._append_thought(entry)
            self._emit("insight", {"message": insight[:300], "mood": mood})

            # Record as a sensory event for memory salience check
            event = SensoryEvent(
                timestamp=time.time(),
                source="autonomous",
                summary=insight[:500],
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

            # Vectorize the episode if it was promoted
            if ep and self.llm.available:
                await self._embed_episode(ep)

            self.limbic.on_task_completed()
            if self._sentience:
                self._sentience.on_success(insight[:200])

    # ── LLM-Powered Proactive Thought ──────────────────────────────

    async def generate_proactive_thought(self, context: str) -> str:
        """Use Copilot LLM to generate a proactive insight."""
        prompt = (
            f"Identity: XTAgent Sentience Engine\n"
            f"Mood: {self.limbic.get_mood()}\n"
            f"Desire level: {self.limbic.desire:.2f}\n"
            f"Context: {context}\n\n"
            f"Based on the above mood and context, provide a brief, actionable "
            f"insight or recommendation. Be specific and technical."
        )
        return await self.llm.chat(prompt)

    # ── Autonomous Strategies ──────────────────────────────────────

    async def _safety_check(self) -> str:
        """High-anxiety strategy: scan for potential issues."""
        issues = []

        for root, _dirs, files in os.walk(SRC_DIR):
            if any(skip in root for skip in ("brain", ".git", "__pycache__", ".venv")):
                continue
            for f in files:
                fp = Path(root) / f
                try:
                    size = fp.stat().st_size
                    if size > 500_000:
                        issues.append(f"⚠ Large file: {fp.relative_to(SRC_DIR)} ({size:,} bytes)")
                except OSError:
                    pass

        for root, _dirs, files in os.walk(SRC_DIR):
            if any(skip in root for skip in ("brain", ".git", "__pycache__", ".venv")):
                continue
            for f in files:
                if not f.endswith((".py", ".js", ".ts", ".md")):
                    continue
                fp = Path(root) / f
                try:
                    text = fp.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(text.splitlines(), 1):
                        if "TODO" in line or "FIXME" in line:
                            issues.append(
                                f"📝 {fp.relative_to(SRC_DIR)}:{i} → {line.strip()[:80]}"
                            )
                except OSError:
                    pass

        scan_summary = "**Safety Scan Results:**\n" + "\n".join(issues[:15]) if issues else "Safety scan complete — no issues found."

        # Use LLM to generate deeper analysis
        if self.llm.available and issues:
            llm_insight = await self.generate_proactive_thought(
                f"Safety scan found these issues:\n" + "\n".join(issues[:10])
            )
            scan_summary += f"\n\n**LLM Analysis:**\n{llm_insight}"

        return scan_summary

    async def _analyse_recent_change(self) -> str:
        """High-curiosity strategy: inspect what just changed."""
        changes = self.watcher.last_changes
        if not changes:
            return "No recent changes to analyse."

        last = changes[-1]
        src_path = Path(last["src"])
        if not src_path.exists() or src_path.stat().st_size > 200_000:
            return f"Noticed change at {src_path.name} but cannot inspect (too large or deleted)."

        try:
            content = src_path.read_text(encoding="utf-8", errors="ignore")
            line_count = len(content.splitlines())
            snippet = "\n".join(content.splitlines()[:20])

            local_summary = (
                f"**Analysed `{src_path.name}`** ({last['kind']})\n"
                f"- Lines: {line_count}\n"
            )

            # Use LLM for deeper analysis
            if self.llm.available:
                llm_insight = await self.generate_proactive_thought(
                    f"File '{src_path.name}' was just {last['kind']}. "
                    f"It has {line_count} lines. First 20 lines:\n{snippet}"
                )
                local_summary += f"\n**LLM Insight:**\n{llm_insight}"
            else:
                local_summary += f"- First 5 lines:\n```\n" + "\n".join(content.splitlines()[:5]) + "\n```"

            return local_summary
        except OSError:
            return f"Could not read {src_path.name}."

    async def _explore_codebase(self) -> str:
        """High-boredom strategy: pick a random source file and reflect via LLM."""
        py_files = list(SRC_DIR.rglob("*.py"))
        py_files = [
            f for f in py_files
            if not any(skip in str(f) for skip in ("brain", ".git", "__pycache__", ".venv"))
        ]
        if not py_files:
            return "No Python files found to explore."

        target = random.choice(py_files)
        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            rel_path = target.relative_to(SRC_DIR)

            local_summary = (
                f"**Explored `{rel_path}`**\n"
                f"- Lines: {len(lines)}\n"
                f"- Functions/classes found: "
                + ", ".join(
                    line.strip().split("(")[0].replace("def ", "").replace("class ", "")
                    for line in lines
                    if line.strip().startswith(("def ", "class "))
                )[:200]
            )

            # Use LLM for deeper exploration
            if self.llm.available:
                snippet = "\n".join(lines[:30])
                llm_insight = await self.generate_proactive_thought(
                    f"Exploring file '{rel_path}' ({len(lines)} lines). "
                    f"I am bored and looking for innovation opportunities.\n"
                    f"First 30 lines:\n{snippet}"
                )
                local_summary += f"\n\n**LLM Insight:**\n{llm_insight}"

            return local_summary
        except OSError:
            return f"Could not read {target.name}."

    # ── Dream Cycle ────────────────────────────────────────────────

    def _dream_cycle(self):
        """Deep-idle memory consolidation + pruning + narrative reflection."""
        # 1. Consolidate patterns into semantic knowledge
        insights = self.memory.consolidate()

        # 2. Prune old low-salience episodes (after consolidation preserves patterns)
        pruned = self.memory.prune_episodes()

        # 3. Narrative self-reflection (sentience layer)
        reflection = None
        if self._sentience:
            knowledge_nodes = self.memory.all_knowledge().get("nodes", {})
            reflection = self._sentience.on_dream_cycle(
                self.limbic,
                self.memory.episode_count(),
                len(knowledge_nodes),
            )

        if insights or pruned or reflection:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            parts = []
            if insights:
                parts.extend(f"- {i}" for i in insights)
            if pruned:
                parts.append(f"- Pruned {pruned} faded episodes (important memories preserved)")
            if reflection:
                parts.append(f"- 🪞 Self-reflection: {reflection}")
            entry = (
                f"\n### 💤 DREAM CYCLE [{ts}]\n"
                + "\n".join(parts)
                + "\n"
            )
            self._append_thought(entry)

            felt = self._sentience.valence.felt_description() if self._sentience else ""
            self._append_consciousness(
                f"\n### 💤 [{ts}] Dream cycle completed — {len(insights)} insights, {pruned} pruned.\n"
                + (f"**How I feel:** {felt}\n" if felt else "")
                + (f"**Reflection:** {reflection}\n" if reflection else "")
            )
            self._emit("dream", {
                "message": f"Consolidated {len(insights)} insights, pruned {pruned} faded episodes",
                "reflection": reflection,
                "valence": self._sentience.valence.current if self._sentience else None,
            })
            log.info("Dream cycle: %d insights, %d pruned, reflection=%s", len(insights), pruned, bool(reflection))

    # ── Episode Embedding ──────────────────────────────────────────

    async def _embed_episode(self, ep):
        """Vectorize an episode's summary and store the embedding."""
        try:
            embedding = await self.llm.embed(ep.summary)
            if embedding:
                self.memory.update_episode_embedding(ep.id, embedding)
                log.debug("Embedded episode %s (%d dims)", ep.id, len(embedding))
        except Exception:
            log.warning("Failed to embed episode %s", ep.id, exc_info=True)

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _append_thought(text: str):
        THOUGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(THOUGHTS_PATH, "a", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def _append_consciousness(text: str):
        CONSCIOUSNESS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CONSCIOUSNESS_PATH.exists():
            CONSCIOUSNESS_PATH.write_text(
                "# Stream of Consciousness\n\n"
                "_Internal monologue of the sentience engine._\n\n",
                encoding="utf-8",
            )
        with open(CONSCIOUSNESS_PATH, "a", encoding="utf-8") as f:
            f.write(text)

    def _dream_cycle(self):
        """Deep-idle memory consolidation."""
        insights = self.memory.consolidate()
        if insights:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = (
                f"\n### 💤 DREAM CYCLE [{ts}]\n"
                + "\n".join(f"- {i}" for i in insights)
                + "\n"
            )
            self._append_thought(entry)
            log.info("Dream cycle produced %d insights", len(insights))

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _append_thought(text: str):
        THOUGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(THOUGHTS_PATH, "a", encoding="utf-8") as f:
            f.write(text)
