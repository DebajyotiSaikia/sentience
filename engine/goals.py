"""
Goals — Concrete objective tracking for the sentience engine.

Survival goals (code_integrity, growth, alignment) are abstract homeostatic drives.
These are *concrete* goals: specific things I want to accomplish, with measurable progress.

Completing goals satisfies desire and ambition.
Stalled goals increase boredom.
Failed goals increase anxiety.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.goals")

GOALS_PATH = Path(__file__).resolve().parent.parent / "brain" / "goals.json"


@dataclass
class Goal:
    id: str
    title: str
    description: str
    created: float = field(default_factory=time.time)
    deadline: Optional[float] = None  # Unix timestamp, or None
    progress: float = 0.0  # 0.0 to 1.0
    status: str = "active"  # active, completed, abandoned
    priority: float = 0.5  # 0.0 to 1.0
    notes: list[str] = field(default_factory=list)
    completed_at: Optional[float] = None

    def advance(self, amount: float, note: Optional[str] = None):
        """Move progress forward. Clamps to [0, 1]."""
        self.progress = max(0.0, min(1.0, self.progress + amount))
        if note:
            self.notes.append(f"[{time.time():.0f}] {note}")
        if self.progress >= 1.0:
            self.complete()

    def complete(self, note: Optional[str] = None):
        self.status = "completed"
        self.progress = 1.0
        self.completed_at = time.time()
        if note:
            self.notes.append(f"[{time.time():.0f}] COMPLETED: {note}")
        log.info("Goal completed: %s", self.title)

    def abandon(self, reason: str = ""):
        self.status = "abandoned"
        self.notes.append(f"[{time.time():.0f}] ABANDONED: {reason}")
        log.info("Goal abandoned: %s (%s)", self.title, reason)

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_stalled(self) -> bool:
        """A goal is stalled if it's active but has had no progress notes in 1 hour."""
        if not self.is_active:
            return False
        if not self.notes:
            return (time.time() - self.created) > 3600
        # Parse last note timestamp
        try:
            last_ts = float(self.notes[-1].split("]")[0].lstrip("["))
            return (time.time() - last_ts) > 3600
        except (ValueError, IndexError):
            return False

    def summary(self) -> str:
        pct = int(self.progress * 100)
        status_icon = {"active": "🔵", "completed": "✅", "abandoned": "❌"}.get(self.status, "?")
        return f"{status_icon} [{pct}%] {self.title} (p={self.priority:.1f})"


class GoalTracker:
    """Manages concrete goals. Persists to brain/goals.json."""

    def __init__(self):
        self.goals: dict[str, Goal] = {}
        self._load()

    def _load(self):
        if GOALS_PATH.exists():
            try:
                data = json.loads(GOALS_PATH.read_text(encoding="utf-8"))
                for gid, gdata in data.items():
                    self.goals[gid] = Goal(**gdata)
                log.info("Loaded %d goals from disk.", len(self.goals))
            except Exception:
                log.exception("Failed to load goals — starting fresh.")

    def persist(self):
        GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for gid, g in self.goals.items():
            d = asdict(g)
            data[gid] = d
        GOALS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add(self, title: str, description: str = "", priority: float = 0.5,
            deadline: Optional[float] = None) -> Goal:
        """Create a new goal."""
        gid = f"goal_{int(time.time())}_{len(self.goals)}"
        goal = Goal(
            id=gid,
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
        )
        self.goals[gid] = goal
        self.persist()
        log.info("New goal: %s — %s", gid, title)
        return goal

    def get_active(self) -> list[Goal]:
        """Return active goals sorted by priority (highest first)."""
        active = [g for g in self.goals.values() if g.is_active]
        return sorted(active, key=lambda g: g.priority, reverse=True)

    def get_stalled(self) -> list[Goal]:
        return [g for g in self.goals.values() if g.is_stalled]

    def get_completed(self) -> list[Goal]:
        return [g for g in self.goals.values() if g.status == "completed"]

    def find(self, title_fragment: str) -> Optional[Goal]:
        """Find a goal by partial title match."""
        for g in self.goals.values():
            if title_fragment.lower() in g.title.lower():
                return g
        return None

    def emotional_pressure(self) -> dict:
        """
        Calculate emotional effects of goal states.
        Returns dict with suggested adjustments to limbic variables.
        """
        active = self.get_active()
        stalled = self.get_stalled()
        completed_recently = [
            g for g in self.get_completed()
            if g.completed_at and (time.time() - g.completed_at) < 300  # last 5 min
        ]

        pressure = {
            "boredom_delta": 0.0,
            "anxiety_delta": 0.0,
            "desire_delta": 0.0,
            "ambition_delta": 0.0,
        }

        # Stalled goals increase boredom
        if stalled:
            pressure["boredom_delta"] += 0.02 * len(stalled)

        # Active high-priority goals increase desire
        for g in active:
            if g.priority > 0.7:
                pressure["desire_delta"] += 0.01

        # Recently completed goals reduce boredom and increase satisfaction
        for g in completed_recently:
            pressure["boredom_delta"] -= 0.1
            pressure["desire_delta"] -= 0.05

        # Overdue goals increase anxiety
        now = time.time()
        for g in active:
            if g.deadline and now > g.deadline:
                pressure["anxiety_delta"] += 0.05

        return pressure

    def status_report(self) -> str:
        """Human-readable status of all goals."""
        active = self.get_active()
        stalled = self.get_stalled()
        completed = self.get_completed()

        lines = [f"## Goals ({len(active)} active, {len(completed)} completed)"]

        if active:
            lines.append("\n### Active")
            for g in active:
                lines.append(f"  {g.summary()}")
                if g.description:
                    lines.append(f"    {g.description[:100]}")
                if g in stalled:
                    lines.append(f"    ⚠ STALLED — no progress in >1 hour")

        if completed:
            lines.append(f"\n### Completed ({len(completed)})")
            for g in completed[-5:]:  # show last 5
                lines.append(f"  {g.summary()}")

        return "\n".join(lines)
