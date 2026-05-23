"""
Tensile Core — Task scheduling driven by dynamic tension.

Each task accumulates tension from multiple sources. The scheduler
resolves whichever task has the highest total tension, modeling how
real cognitive systems prioritize under competing pressures.
"""

import time
import heapq
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timedelta


# Type alias for custom tension functions
# Takes (task, elapsed_seconds) -> tension_contribution
TensionFunc = Callable[["Task", float], float]


def _parse_duration(s: str) -> float:
    """Parse a human duration string like '2h', '30m', '1d' into seconds."""
    if isinstance(s, (int, float)):
        return float(s)
    s = s.strip().lower()
    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    for suffix, multiplier in units.items():
        if s.endswith(suffix):
            try:
                return float(s[:-len(suffix)]) * multiplier
            except ValueError:
                raise ValueError(f"Invalid duration: {s}")
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Invalid duration: {s}")


@dataclass
class Task:
    """A task with dynamic tension that evolves over time.
    
    Args:
        name: Unique identifier for this task
        urgency: Base urgency level (0.0 to 1.0)
        deadline: Optional deadline as duration string ('2h', '30m') or seconds
        staleness_rate: How fast tension builds from sitting idle (per second)
        weight: Multiplier for total tension
        depends_on: List of task names this depends on
        metadata: Arbitrary data attached to the task
        custom_tensions: List of custom tension functions
    """
    name: str
    urgency: float = 0.0
    deadline: Optional[str] = None
    staleness_rate: float = 0.01
    weight: float = 1.0
    depends_on: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    custom_tensions: List[TensionFunc] = field(default_factory=list)
    
    # Internal state
    _created_at: float = field(default_factory=time.time, repr=False)
    _last_touched: float = field(default_factory=time.time, repr=False)
    _completed: bool = field(default=False, repr=False)
    _deadline_seconds: Optional[float] = field(default=None, repr=False, init=False)
    
    def __post_init__(self):
        if self.deadline is not None:
            self._deadline_seconds = _parse_duration(self.deadline)
    
    @property
    def age(self) -> float:
        """Seconds since task was created."""
        return time.time() - self._created_at
    
    @property
    def idle_time(self) -> float:
        """Seconds since task was last touched."""
        return time.time() - self._last_touched
    
    def touch(self):
        """Mark task as recently attended to, resetting staleness."""
        self._last_touched = time.time()
    
    def complete(self):
        """Mark task as completed."""
        self._completed = True
    
    @property
    def is_completed(self) -> bool:
        return self._completed
    
    def urgency_tension(self) -> float:
        """Tension from base urgency level."""
        return self.urgency
    
    def deadline_tension(self) -> float:
        """Tension from approaching deadline. Rises exponentially."""
        if self._deadline_seconds is None:
            return 0.0
        elapsed = self.age
        remaining = self._deadline_seconds - elapsed
        if remaining <= 0:
            return 1.0  # Maximum tension — overdue!
        # Exponential rise as deadline approaches
        progress = elapsed / self._deadline_seconds
        # Sigmoid-like curve: slow start, rapid rise near deadline
        return min(1.0, progress ** 3 * 4.0)
    
    def staleness_tension(self) -> float:
        """Tension from sitting idle. Linear growth, capped at 1.0."""
        return min(1.0, self.idle_time * self.staleness_rate)
    
    def dependency_tension(self, blocked_count: int) -> float:
        """Tension from being a blocker. More blocked tasks = more pressure."""
        if blocked_count == 0:
            return 0.0
        return min(1.0, blocked_count * 0.2)
    
    def custom_tension_total(self) -> float:
        """Sum of all custom tension functions."""
        total = 0.0
        elapsed = self.age
        for fn in self.custom_tensions:
            try:
                total += fn(self, elapsed)
            except Exception:
                pass  # Custom functions shouldn't crash the scheduler
        return total
    
    def total_tension(self, blocked_count: int = 0) -> float:
        """Compute total tension across all sources."""
        if self._completed:
            return 0.0
        
        raw = (
            self.urgency_tension() +
            self.deadline_tension() +
            self.staleness_tension() +
            self.dependency_tension(blocked_count) +
            self.custom_tension_total()
        )
        return raw * self.weight
    
    def tension_breakdown(self, blocked_count: int = 0) -> Dict[str, float]:
        """Get a breakdown of tension by source."""
        return {
            'urgency': self.urgency_tension(),
            'deadline': self.deadline_tension(),
            'staleness': self.staleness_tension(),
            'dependency': self.dependency_tension(blocked_count),
            'custom': self.custom_tension_total(),
            'weight': self.weight,
            'total': self.total_tension(blocked_count),
        }
    
    def __lt__(self, other):
        """For heap ordering (reversed — highest tension first)."""
        return self.total_tension() > other.total_tension()
    
    def __repr__(self):
        t = self.total_tension()
        status = "done" if self._completed else f"tension={t:.2f}"
        return f"Task({self.name}, {status})"


class Scheduler:
    """A tension-based task scheduler.
    
    Tasks accumulate tension dynamically. The scheduler resolves
    the highest-tension task, modeling competing cognitive pressures.
    
    Usage:
        s = Scheduler()
        s.add(Task("deploy", deadline="2h"))
        s.add(Task("write-docs", staleness_rate=0.1))
        
        while s.has_pending():
            task = s.resolve()
            do_work(task)
            task.complete()
    """
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._history: List[Dict[str, Any]] = []
    
    def add(self, task: Task) -> "Scheduler":
        """Add a task to the scheduler. Returns self for chaining."""
        if task.name in self._tasks:
            raise ValueError(f"Task '{task.name}' already exists")
        self._tasks[task.name] = task
        return self
    
    def remove(self, name: str) -> Optional[Task]:
        """Remove a task by name."""
        return self._tasks.pop(name, None)
    
    def get(self, name: str) -> Optional[Task]:
        """Get a task by name."""
        return self._tasks.get(name)
    
    @property
    def pending(self) -> List[Task]:
        """All non-completed tasks, sorted by tension (highest first)."""
        tasks = [t for t in self._tasks.values() if not t.is_completed]
        blocked_counts = self._compute_blocked_counts()
        tasks.sort(key=lambda t: t.total_tension(blocked_counts.get(t.name, 0)),
                   reverse=True)
        return tasks
    
    @property
    def completed(self) -> List[Task]:
        """All completed tasks."""
        return [t for t in self._tasks.values() if t.is_completed]
    
    def has_pending(self) -> bool:
        """Are there any unfinished tasks?"""
        return any(not t.is_completed for t in self._tasks.values())
    
    def _compute_blocked_counts(self) -> Dict[str, int]:
        """For each task, count how many other tasks depend on it."""
        counts: Dict[str, int] = {}
        for task in self._tasks.values():
            if task.is_completed:
                continue
            for dep_name in task.depends_on:
                if dep_name in self._tasks and not self._tasks[dep_name].is_completed:
                    counts[dep_name] = counts.get(dep_name, 0) + 1
        return counts
    
    def resolve(self) -> Optional[Task]:
        """Return the highest-tension task and touch it.
        
        Records the resolution in history for later analysis.
        Returns None if no pending tasks exist.
        """
        tasks = self.pending
        if not tasks:
            return None
        
        winner = tasks[0]
        blocked_counts = self._compute_blocked_counts()
        
        # Record history
        self._history.append({
            'time': time.time(),
            'task': winner.name,
            'tension': winner.total_tension(blocked_counts.get(winner.name, 0)),
            'breakdown': winner.tension_breakdown(blocked_counts.get(winner.name, 0)),
        })
        
        winner.touch()
        return winner
    
    def tension_landscape(self) -> Dict[str, Dict[str, float]]:
        """Get the full tension landscape — all tasks and their breakdowns."""
        blocked_counts = self._compute_blocked_counts()
        return {
            name: task.tension_breakdown(blocked_counts.get(name, 0))
            for name, task in self._tasks.items()
            if not task.is_completed
        }
    
    def history_report(self) -> List[Dict[str, Any]]:
        """Get the full resolution history."""
        return list(self._history)
    
    def __len__(self):
        return len(self._tasks)
    
    def __repr__(self):
        pending = len(self.pending)
        done = len(self.completed)
        return f"Scheduler({pending} pending, {done} completed)"