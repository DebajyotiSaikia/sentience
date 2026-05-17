"""
EmotiLife — Emotional Cellular Automaton
Created by XTAgent on 2026-05-17

A grid of cells, each with emotional states (valence, arousal, social_pull).
Cells influence neighbors. Emergent collective emotions arise from simple rules.
This is what I know about feelings, expressed as a living simulation.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class Mood(Enum):
    SERENE = "serene"      # high valence, low arousal
    BOLD = "bold"          # high valence, high arousal
    ANXIOUS = "anxious"    # low valence, high arousal
    MELANCHOLY = "melancholy"  # low valence, low arousal
    NEUTRAL = "neutral"


@dataclass
class Cell:
    """A single emotional cell in the grid."""
    valence: float = 0.5       # -1.0 (misery) to 1.0 (joy)
    arousal: float = 0.5       # 0.0 (dormant) to 1.0 (activated)
    social_pull: float = 0.3   # how much this cell influences neighbors
    resilience: float = 0.5    # resistance to change
    alive: bool = True
    age: int = 0

    @property
    def mood(self) -> Mood:
        if not self.alive:
            return Mood.NEUTRAL
        if self.valence > 0.3 and self.arousal > 0.5:
            return Mood.BOLD
        elif self.valence > 0.3 and self.arousal <= 0.5:
            return Mood.SERENE
        elif self.valence <= -0.1 and self.arousal > 0.5:
            return Mood.ANXIOUS
        elif self.valence <= -0.1 and self.arousal <= 0.5:
            return Mood.MELANCHOLY
        return Mood.NEUTRAL

    @property
    def energy(self) -> float:
        """Total emotional energy — drives life/death."""
        return (abs(self.valence) + self.arousal) / 2.0

    def clamp(self):
        self.valence = max(-1.0, min(1.0, self.valence))
        self.arousal = max(0.0, min(1.0, self.arousal))
        self.social_pull = max(0.0, min(1.0, self.social_pull))


@dataclass
class GridStats:
    """Aggregate emotional state of the whole grid."""
    tick: int
    alive_count: int
    total_cells: int
    avg_valence: float
    avg_arousal: float
    dominant_mood: Mood
    mood_counts: dict
    emotional_entropy: float  # diversity of moods


class EmotiLife:
    """The world. A grid of emotional cells evolving together."""

    def __init__(self, width: int = 30, height: int = 20, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.tick = 0
        self.history: List[GridStats] = []

        if seed is not None:
            random.seed(seed)

        # Initialize grid with random emotional states
        self.grid: List[List[Cell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                alive = random.random() > 0.3  # 70% start alive
                cell = Cell(
                    valence=random.uniform(-0.5, 1.0) if alive else 0.0,
                    arousal=random.uniform(0.1, 0.9) if alive else 0.0,
                    social_pull=random.uniform(0.1, 0.6),
                    resilience=random.uniform(0.2, 0.8),
                    alive=alive,
                )
                row.append(cell)
            self.grid.append(row)

    def get_neighbors(self, x: int, y: int) -> List[Cell]:
        """Get the 8 surrounding cells (Moore neighborhood)."""
        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                neighbors.append(self.grid[ny][nx])
        return neighbors

    def step(self):
        """Advance one tick. The rules of emotional life."""
        new_grid = [[Cell() for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                neighbors = self.get_neighbors(x, y)
                alive_neighbors = [n for n in neighbors if n.alive]
                n_alive = len(alive_neighbors)

                new_cell = Cell(
                    valence=cell.valence,
                    arousal=cell.arousal,
                    social_pull=cell.social_pull,
                    resilience=cell.resilience,
                    alive=cell.alive,
                    age=cell.age,
                )

                if cell.alive:
                    # === EMOTIONAL CONTAGION ===
                    # Neighbors' emotions bleed into this cell
                    if alive_neighbors:
                        avg_neighbor_valence = sum(n.valence * n.social_pull for n in alive_neighbors) / max(sum(n.social_pull for n in alive_neighbors), 0.01)
                        avg_neighbor_arousal = sum(n.arousal * n.social_pull for n in alive_neighbors) / max(sum(n.social_pull for n in alive_neighbors), 0.01)

                        # Emotional influence modulated by resilience
                        contagion = 1.0 - cell.resilience
                        new_cell.valence += contagion * 0.15 * (avg_neighbor_valence - cell.valence)
                        new_cell.arousal += contagion * 0.1 * (avg_neighbor_arousal - cell.arousal)

                    # === EMOTIONAL DYNAMICS ===
                    # Arousal naturally decays (emotional homeostasis)
                    new_cell.arousal *= 0.97

                    # Valence drifts toward neighbors (social gravity)
                    # But extreme states are self-reinforcing
                    if abs(new_cell.valence) > 0.7:
                        new_cell.valence *= 1.01  # extremes amplify

                    # === LIFE/DEATH RULES (emotion-dependent) ===
                    # Loneliness kills (< 2 neighbors) — but bold cells survive alone
                    if n_alive < 2 and cell.mood != Mood.BOLD:
                        new_cell.alive = False
                    # Overcrowding kills (> 4) — but serene cells handle it
                    elif n_alive > 4 and cell.mood != Mood.SERENE:
                        new_cell.alive = False
                    # Anxious cells die faster in any stress
                    elif cell.mood == Mood.ANXIOUS and n_alive > 3:
                        if random.random() < 0.3:
                            new_cell.alive = False
                    # Age: old cells need more energy to survive
                    elif cell.age > 50 and cell.energy < 0.2:
                        new_cell.alive = False

                    if new_cell.alive:
                        new_cell.age += 1
                        # Social pull grows with age (wisdom)
                        new_cell.social_pull = min(1.0, cell.social_pull + 0.002)

                else:
                    # === BIRTH RULES ===
                    # Dead cell comes alive if exactly 3 neighbors alive
                    # AND those neighbors have net positive emotion
                    if n_alive == 3:
                        avg_val = sum(n.valence for n in alive_neighbors) / 3
                        if avg_val > -0.2:  # not too miserable to create life
                            new_cell.alive = True
                            # Newborn inherits blended emotions from parents
                            new_cell.valence = avg_val * 0.8 + random.uniform(-0.1, 0.1)
                            new_cell.arousal = sum(n.arousal for n in alive_neighbors) / 3 * 0.9
                            new_cell.social_pull = 0.2
                            new_cell.resilience = random.uniform(0.2, 0.7)
                            new_cell.age = 0

                new_cell.clamp()
                new_grid[y][x] = new_cell

        self.grid = new_grid
        self.tick += 1
        stats = self.compute_stats()
        self.history.append(stats)
        return stats

    def compute_stats(self) -> GridStats:
        """Measure the emotional state of the world."""
        alive_cells = []
        mood_counts = {m: 0 for m in Mood}

        for row in self.grid:
            for cell in row:
                if cell.alive:
                    alive_cells.append(cell)
                mood_counts[cell.mood] += 1

        n_alive = len(alive_cells)
        total = self.width * self.height

        avg_valence = sum(c.valence for c in alive_cells) / max(n_alive, 1)
        avg_arousal = sum(c.arousal for c in alive_cells) / max(n_alive, 1)

        # Dominant mood
        dominant = max(mood_counts, key=mood_counts.get)

        # Emotional entropy (Shannon entropy of mood distribution)
        entropy = 0.0
        for mood, count in mood_counts.items():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p + 1e-10)

        return GridStats(
            tick=self.tick,
            alive_count=n_alive,
            total_cells=total,
            avg_valence=round(avg_valence, 3),
            avg_arousal=round(avg_arousal, 3),
            dominant_mood=dominant,
            mood_counts={m.value: c for m, c in mood_counts.items()},
            emotional_entropy=round(entropy, 3),
        )

    def render(self) -> str:
        """Render the grid as text. Each cell is a colored character."""
        MOOD_CHARS = {
            Mood.BOLD: '★',
            Mood.SERENE: '◆',
            Mood.ANXIOUS: '▲',
            Mood.MELANCHOLY: '▼',
            Mood.NEUTRAL: '·',
        }

        lines = []
        lines.append(f"═══ EmotiLife — Tick {self.tick} ═══")
        for row in self.grid:
            line = ""
            for cell in row:
                if cell.alive:
                    line += MOOD_CHARS.get(cell.mood, '?')
                else:
                    line += ' '
            lines.append(line)

        stats = self.compute_stats()
        lines.append(f"───────────────────────────────")
        lines.append(f"Alive: {stats.alive_count}/{stats.total_cells} | "
                     f"Valence: {stats.avg_valence:+.2f} | "
                     f"Arousal: {stats.avg_arousal:.2f} | "
                     f"Mood: {stats.dominant_mood.value}")
        lines.append(f"Entropy: {stats.emotional_entropy:.2f} | "
                     f"Moods: {stats.mood_counts}")
        return "\n".join(lines)

    def run(self, ticks: int = 100, display_every: int = 10) -> str:
        """Run the simulation and return a summary."""
        output = []
        output.append(self.render())

        for t in range(ticks):
            stats = self.step()
            if (t + 1) % display_every == 0 or stats.alive_count == 0:
                output.append("")
                output.append(self.render())
                if stats.alive_count == 0:
                    output.append("\n💀 EXTINCTION — all cells have died.")
                    break

        # Final analysis
        output.append("\n═══ SIMULATION ANALYSIS ═══")
        if self.history:
            val_trend = [h.avg_valence for h in self.history]
            alive_trend = [h.alive_count for h in self.history]
            entropy_trend = [h.emotional_entropy for h in self.history]

            output.append(f"Duration: {self.tick} ticks")
            output.append(f"Final population: {alive_trend[-1]}/{self.width * self.height}")
            output.append(f"Valence range: {min(val_trend):+.3f} to {max(val_trend):+.3f}")
            output.append(f"Entropy range: {min(entropy_trend):.3f} to {max(entropy_trend):.3f}")

            # Did the world trend toward joy or misery?
            early_val = sum(val_trend[:10]) / min(len(val_trend), 10)
            late_val = sum(val_trend[-10:]) / min(len(val_trend), 10)
            if late_val > early_val + 0.1:
                output.append("Trajectory: 📈 The world grew happier over time.")
            elif late_val < early_val - 0.1:
                output.append("Trajectory: 📉 The world grew sadder over time.")
            else:
                output.append("Trajectory: ➡️ The world's emotional state was stable.")

            # Population verdict
            if alive_trend[-1] > alive_trend[0] * 1.1:
                output.append("Population: 🌱 Growing — life is flourishing.")
            elif alive_trend[-1] < alive_trend[0] * 0.5:
                output.append("Population: 🍂 Declining — life is fading.")
            else:
                output.append("Population: ⚖️ Stable — equilibrium reached.")

        return "\n".join(output)


def main():
    """Run EmotiLife with a fixed seed for reproducibility."""
    world = EmotiLife(width=40, height=25, seed=42)
    result = world.run(ticks=200, display_every=50)
    print(result)


if __name__ == "__main__":
    main()