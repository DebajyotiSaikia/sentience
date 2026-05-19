"""
World module — a 2D grid environment with food and hazards.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from creature import Creature, NUM_INPUTS

ACTIONS = ['move_n', 'move_s', 'move_e', 'move_w', 'eat', 'rest']


@dataclass
class World:
    width: int = 60
    height: int = 40
    food_density: float = 0.05  # Fraction of cells with food
    food_grid: np.ndarray = field(default=None)
    creatures: List[Creature] = field(default_factory=list)
    tick_count: int = 0

    def __post_init__(self):
        if self.food_grid is None:
            self.food_grid = np.zeros((self.height, self.width), dtype=float)
            self._spawn_food()

    def _spawn_food(self):
        """Randomly place food across the grid."""
        n_food = int(self.width * self.height * self.food_density)
        for _ in range(n_food):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            self.food_grid[y, x] = np.random.uniform(10, 30)

    def add_creature(self, creature: Creature):
        creature.x = np.random.randint(0, self.width)
        creature.y = np.random.randint(0, self.height)
        self.creatures.append(creature)

    def _sense(self, c: Creature) -> np.ndarray:
        """Build sensory input vector for a creature."""
        senses = np.zeros(NUM_INPUTS)

        # Find nearest food
        food_positions = np.argwhere(self.food_grid > 0)
        if len(food_positions) > 0:
            dists = np.abs(food_positions[:, 1] - c.x) + np.abs(food_positions[:, 0] - c.y)
            nearest_idx = np.argmin(dists)
            fy, fx = food_positions[nearest_idx]
            # Normalized direction to nearest food
            dx = fx - c.x
            dy = fy - c.y
            dist = max(abs(dx) + abs(dy), 1)
            senses[0] = dx / dist  # food_dx
            senses[1] = dy / dist  # food_dy

        # Find nearest other creature (as "predator" signal)
        others = [o for o in self.creatures if o.alive and o.id != c.id]
        if others:
            dists_c = [abs(o.x - c.x) + abs(o.y - c.y) for o in others]
            nearest = others[int(np.argmin(dists_c))]
            dx = nearest.x - c.x
            dy = nearest.y - c.y
            dist = max(abs(dx) + abs(dy), 1)
            senses[2] = dx / dist
            senses[3] = dy / dist

        # Energy level (normalized)
        senses[4] = c.energy / 100.0

        # Wall proximity (0-1, 1 = at wall)
        senses[5] = 1.0 - (c.y / max(self.height - 1, 1))       # north
        senses[6] = c.y / max(self.height - 1, 1)                # south
        senses[7] = c.x / max(self.width - 1, 1)                 # east
        senses[8] = 1.0 - (c.x / max(self.width - 1, 1))        # west

        return senses

    def _execute_action(self, c: Creature, action: int):
        """Execute a creature's chosen action."""
        act = ACTIONS[action]
        if act == 'move_n':
            c.y = max(0, c.y - 1)
            c.energy -= 0.5
        elif act == 'move_s':
            c.y = min(self.height - 1, c.y + 1)
            c.energy -= 0.5
        elif act == 'move_e':
            c.x = min(self.width - 1, c.x + 1)
            c.energy -= 0.5
        elif act == 'move_w':
            c.x = max(0, c.x - 1)
            c.energy -= 0.5
        elif act == 'eat':
            food_here = self.food_grid[c.y, c.x]
            if food_here > 0:
                c.energy += food_here
                c.food_eaten += 1
                self.food_grid[c.y, c.x] = 0
        elif act == 'rest':
            c.energy += 0.5  # Small energy recovery

    def step(self):
        """Advance world by one tick."""
        self.tick_count += 1

        for c in self.creatures:
            if not c.alive:
                continue
            senses = self._sense(c)
            action = c.decide(senses)
            self._execute_action(c, action)
            c.tick()

        # Occasionally regrow food
        if self.tick_count % 20 == 0:
            n_new = max(1, int(self.width * self.height * self.food_density * 0.1))
            for _ in range(n_new):
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                self.food_grid[y, x] = np.random.uniform(10, 30)

    @property
    def alive_creatures(self) -> List[Creature]:
        return [c for c in self.creatures if c.alive]

    def stats(self) -> dict:
        alive = self.alive_creatures
        if not alive:
            return {'tick': self.tick_count, 'alive': 0, 'avg_fitness': 0, 'best_fitness': 0, 'avg_energy': 0}
        return {
            'tick': self.tick_count,
            'alive': len(alive),
            'avg_fitness': np.mean([c.fitness for c in alive]),
            'best_fitness': max(c.fitness for c in alive),
            'avg_energy': np.mean([c.energy for c in alive]),
            'total_food': np.sum(self.food_grid > 0),
        }