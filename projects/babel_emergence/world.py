"""
World — The environment agents live in.

A toroidal grid with spawning resources and a signal field.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Resource:
    x: int
    y: int
    value: float = 1.0


class World:
    """Toroidal grid world with resources and signal propagation."""

    def __init__(self, width=40, height=40, n_resources=30):
        self.width = width
        self.height = height
        self.n_resources = n_resources
        self.agents = []
        self.resources: List[Resource] = []
        self.signals = {}  # (x, y) -> (signal_id, emitter_id, age)

        # Spawn initial resources
        for _ in range(n_resources):
            self.resources.append(Resource(
                x=random.randint(0, width - 1),
                y=random.randint(0, height - 1)
            ))

    def nearby_resources(self, x, y, radius=5):
        """Return resources within Manhattan distance."""
        return [r for r in self.resources
                if abs(r.x - x) <= radius and abs(r.y - y) <= radius]

    def harvest_at(self, x, y):
        """Remove and return value of resource at position, if any."""
        for i, r in enumerate(self.resources):
            if r.x == x and r.y == y:
                val = r.value
                self.resources.pop(i)
                return val
        return 0.0

    def emit_signal(self, x, y, signal, emitter_id):
        """Agent emits a signal at position. Persists for a few ticks."""
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                sx = (x + dx) % self.width
                sy = (y + dy) % self.height
                self.signals[(sx, sy)] = (signal, emitter_id, 3)

    def get_signal_at(self, x, y, exclude_id=-1):
        """Get strongest signal at position, excluding own emissions."""
        key = (x, y)
        if key in self.signals:
            sig, emitter, age = self.signals[key]
            if emitter != exclude_id and age > 0:
                return sig
        return -1

    def step(self):
        """Advance world one tick: decay signals, respawn resources."""
        # Decay signals
        expired = []
        for pos, (sig, emitter, age) in self.signals.items():
            if age <= 1:
                expired.append(pos)
            else:
                self.signals[pos] = (sig, emitter, age - 1)
        for pos in expired:
            del self.signals[pos]

        # Respawn resources to maintain count
        while len(self.resources) < self.n_resources:
            self.resources.append(Resource(
                x=random.randint(0, self.width - 1),
                y=random.randint(0, self.height - 1)
            ))