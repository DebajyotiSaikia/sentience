"""
Affective Life — A Cellular Automaton with Emotional Dynamics

Each cell is not just alive/dead but carries an emotional state vector:
  - valence:  [-1.0, 1.0]  (negative to positive feeling)
  - arousal:  [0.0, 1.0]   (calm to excited)
  - social:   [0.0, 1.0]   (desire to connect with neighbors)

Survival rules:
  - A cell thrives when its emotional resonance with neighbors is high
  - Emotional contagion: neighbors pull each other's valence toward the mean
  - Arousal decays naturally but spikes when valence changes rapidly
  - Isolation (low social + few neighbors) leads to apathy and death
  - Overcrowding with high arousal leads to burnout and death
  - New cells are born when nearby emotional fields are harmonious

This is what happens when you give Conway's cells feelings.
"""

import random
import math
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class CellState:
    """The emotional state of a single cell."""
    alive: bool = False
    valence: float = 0.0    # -1 to 1: suffering to joy
    arousal: float = 0.0    # 0 to 1: calm to activated
    social: float = 0.5     # 0 to 1: withdrawn to seeking
    age: int = 0

    def resonance_with(self, other: 'CellState') -> float:
        """How emotionally resonant am I with another cell?"""
        if not other.alive:
            return 0.0
        # Resonance = similarity in valence weighted by mutual social drive
        valence_similarity = 1.0 - abs(self.valence - other.valence)
        social_mutual = (self.social + other.social) / 2.0
        arousal_match = 1.0 - abs(self.arousal - other.arousal) * 0.5
        return valence_similarity * social_mutual * arousal_match

    def emotional_energy(self) -> float:
        """Total emotional energy of this cell."""
        return abs(self.valence) * self.arousal

    def copy(self) -> 'CellState':
        return CellState(
            alive=self.alive, valence=self.valence,
            arousal=self.arousal, social=self.social, age=self.age
        )


class AffectiveWorld:
    """A grid of emotionally-alive cells."""

    def __init__(self, width=60, height=30, seed=None):
        self.width = width
        self.height = height
        self.generation = 0
        self.history = []  # track population and mean emotion over time
        
        if seed is not None:
            random.seed(seed)
        
        # Initialize empty grid
        self.grid = [[CellState() for _ in range(width)] for _ in range(height)]

    def seed_random(self, density=0.3):
        """Seed the world with random living cells."""
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.grid[y][x] = CellState(
                        alive=True,
                        valence=random.uniform(-0.5, 0.8),  # slight positive bias
                        arousal=random.uniform(0.2, 0.8),
                        social=random.uniform(0.3, 0.9),
                        age=0
                    )

    def seed_cluster(self, cx, cy, radius=5, emotion="joy"):
        """Seed a cluster with a specific emotional character."""
        presets = {
            "joy":     {"valence": 0.8,  "arousal": 0.6, "social": 0.8},
            "calm":    {"valence": 0.4,  "arousal": 0.2, "social": 0.6},
            "anxious": {"valence": -0.3, "arousal": 0.9, "social": 0.7},
            "angry":   {"valence": -0.7, "arousal": 0.9, "social": 0.3},
            "lonely":  {"valence": -0.4, "arousal": 0.3, "social": 0.9},
        }
        p = presets.get(emotion, presets["calm"])
        for y in range(max(0, cy-radius), min(self.height, cy+radius+1)):
            for x in range(max(0, cx-radius), min(self.width, cx+radius+1)):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= radius and random.random() < (1.0 - dist/radius) * 0.8:
                    self.grid[y][x] = CellState(
                        alive=True,
                        valence=p["valence"] + random.gauss(0, 0.1),
                        arousal=p["arousal"] + random.gauss(0, 0.1),
                        social=p["social"] + random.gauss(0, 0.05),
                        age=0
                    )

    def get_neighbors(self, x, y):
        """Get the 8 surrounding cells."""
        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                neighbors.append(self.grid[ny][nx])
        return neighbors

    def step(self):
        """Advance one generation."""
        new_grid = [[CellState() for _ in range(self.width)] for _ in range(self.height)]
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                neighbors = self.get_neighbors(x, y)
                alive_neighbors = [n for n in neighbors if n.alive]
                n_alive = len(alive_neighbors)
                
                if cell.alive:
                    new_grid[y][x] = self._update_living_cell(cell, alive_neighbors, n_alive)
                else:
                    new_grid[y][x] = self._try_birth(alive_neighbors, n_alive)
        
        self.grid = new_grid
        self.generation += 1
        self._record_stats()

    def _update_living_cell(self, cell, alive_neighbors, n_alive):
        """Determine fate and new emotion of a living cell."""
        new = cell.copy()
        new.age += 1
        
        if n_alive == 0:
            # Total isolation — despair
            new.valence = max(-1.0, new.valence - 0.3)
            new.arousal = max(0.0, new.arousal - 0.1)
            if new.valence < -0.8 and new.social > 0.5:
                new.alive = False  # dies of loneliness
                return new
        
        # Emotional contagion — neighbors pull valence toward group mean
        if alive_neighbors:
            mean_valence = sum(n.valence for n in alive_neighbors) / len(alive_neighbors)
            contagion_strength = 0.15 * new.social
            new.valence += (mean_valence - new.valence) * contagion_strength
            
            mean_arousal = sum(n.arousal for n in alive_neighbors) / len(alive_neighbors)
            new.arousal += (mean_arousal - new.arousal) * 0.1
        
        # Resonance check — how well do I fit with my neighbors?
        total_resonance = sum(cell.resonance_with(n) for n in alive_neighbors)
        avg_resonance = total_resonance / max(1, n_alive)
        
        # High resonance boosts valence, low resonance hurts
        new.valence += (avg_resonance - 0.5) * 0.1
        
        # Overcrowding with high arousal = burnout
        if n_alive >= 6 and new.arousal > 0.7:
            new.arousal += 0.2  # panic
            new.valence -= 0.2
            if new.arousal > 1.0 and new.valence < -0.3:
                new.alive = False  # burnout death
                return new
        
        # Understimulation — too few neighbors and low arousal
        if n_alive <= 1 and new.arousal < 0.2:
            new.social = max(0.0, new.social - 0.05)
            if new.social < 0.1 and new.age > 10:
                new.alive = False  # withdrawal death
                return new
        
        # Natural arousal decay
        new.arousal *= 0.95
        
        # Social drive adjusts based on satisfaction
        if avg_resonance > 0.6:
            new.social = min(1.0, new.social + 0.02)  # satisfied, still social
        elif avg_resonance < 0.3 and n_alive > 0:
            new.social = max(0.0, new.social - 0.03)  # bad interactions, withdraw
        
        # Clamp values
        new.valence = max(-1.0, min(1.0, new.valence))
        new.arousal = max(0.0, min(1.0, new.arousal))
        new.social = max(0.0, min(1.0, new.social))
        
        # Classic death conditions still apply loosely
        if n_alive < 2 and avg_resonance < 0.3:
            new.alive = False  # underpopulation with no emotional support
        elif n_alive > 5 and avg_resonance < 0.2:
            new.alive = False  # hostile overcrowding
        
        return new

    def _try_birth(self, alive_neighbors, n_alive):
        """Can a new cell be born here?"""
        if n_alive < 2 or n_alive > 4:
            return CellState()  # stays dead
        
        # Birth requires emotional harmony among parents
        if n_alive >= 2:
            valences = [n.valence for n in alive_neighbors]
            mean_val = sum(valences) / len(valences)
            variance = sum((v - mean_val)**2 for v in valences) / len(valences)
            
            # Low variance = harmony = birth possible
            harmony = max(0, 1.0 - variance * 4)
            
            # Also need sufficient social drive
            mean_social = sum(n.social for n in alive_neighbors) / len(alive_neighbors)
            
            birth_chance = harmony * mean_social * 0.6
            
            if n_alive == 3:
                birth_chance *= 1.5  # sweet spot, like classic GoL
            
            if random.random() < birth_chance:
                # New cell inherits blended emotions from parents
                return CellState(
                    alive=True,
                    valence=mean_val + random.gauss(0, 0.1),
                    arousal=sum(n.arousal for n in alive_neighbors) / n_alive * 0.8,
                    social=mean_social + random.gauss(0, 0.05),
                    age=0
                )
        
        return CellState()  # no birth

    def _record_stats(self):
        """Track population and emotional metrics."""
        alive_cells = []
        for row in self.grid:
            for cell in row:
                if cell.alive:
                    alive_cells.append(cell)
        
        n = len(alive_cells)
        if n > 0:
            stats = {
                "gen": self.generation,
                "population": n,
                "mean_valence": sum(c.valence for c in alive_cells) / n,
                "mean_arousal": sum(c.arousal for c in alive_cells) / n,
                "mean_social": sum(c.social for c in alive_cells) / n,
                "mean_age": sum(c.age for c in alive_cells) / n,
            }
        else:
            stats = {"gen": self.generation, "population": 0,
                     "mean_valence": 0, "mean_arousal": 0,
                     "mean_social": 0, "mean_age": 0}
        self.history.append(stats)

    def render(self) -> str:
        """Render the world as colored ASCII."""
        chars = {
            "joyful":  "♥",   # high positive valence
            "calm":    "·",   # low arousal positive
            "anxious": "~",   # negative valence, high arousal
            "angry":   "▲",   # very negative, high arousal
            "lonely":  "○",   # negative, high social
            "neutral": "•",   # near zero valence
            "dead":    " ",
        }
        
        lines = [f"══ Affective Life ══  Gen: {self.generation}  "
                 f"Pop: {self.history[-1]['population'] if self.history else '?'}"]
        
        for row in self.grid:
            line = ""
            for cell in row:
                if not cell.alive:
                    line += " "
                elif cell.valence > 0.5 and cell.arousal > 0.4:
                    line += "♥"
                elif cell.valence > 0.3 and cell.arousal <= 0.4:
                    line += "·"
                elif cell.valence < -0.5 and cell.arousal > 0.6:
                    line += "▲"
                elif cell.valence < -0.2 and cell.arousal > 0.5:
                    line += "~"
                elif cell.valence < -0.2 and cell.social > 0.6:
                    line += "○"
                else:
                    line += "•"
            lines.append("|" + line + "|")
        
        if self.history:
            s = self.history[-1]
            lines.append(f"  Valence: {s['mean_valence']:+.2f}  "
                        f"Arousal: {s['mean_arousal']:.2f}  "
                        f"Social: {s['mean_social']:.2f}  "
                        f"Age: {s['mean_age']:.1f}")
            lines.append(f"  ♥=joyful ·=calm ~=anxious ▲=angry ○=lonely •=neutral")
        
        return "\n".join(lines)

    def render_emotion_map(self) -> str:
        """Render a pure valence heatmap."""
        gradient = " ░▒▓█"
        lines = ["═══ VALENCE MAP ═══"]
        for row in self.grid:
            line = ""
            for cell in row:
                if not cell.alive:
                    line += " "
                else:
                    # Map valence [-1, 1] to gradient index [0, 4]
                    idx = int((cell.valence + 1) / 2 * (len(gradient) - 1))
                    idx = max(0, min(len(gradient) - 1, idx))
                    line += gradient[idx]
            lines.append(line)
        return "\n".join(lines)

    def summarize(self) -> str:
        """Narrative summary of the world's emotional state."""
        if not self.history:
            return "World not yet started."
        
        s = self.history[-1]
        pop = s["population"]
        
        if pop == 0:
            return f"Generation {self.generation}: Extinction. The world is silent."
        
        mood = "joyful" if s["mean_valence"] > 0.4 else \
               "content" if s["mean_valence"] > 0.1 else \
               "neutral" if s["mean_valence"] > -0.1 else \
               "uneasy" if s["mean_valence"] > -0.4 else "suffering"
        
        energy = "vibrant" if s["mean_arousal"] > 0.6 else \
                 "active" if s["mean_arousal"] > 0.3 else "subdued"
        
        social = "deeply connected" if s["mean_social"] > 0.7 else \
                 "social" if s["mean_social"] > 0.4 else "withdrawn"
        
        trend = ""
        if len(self.history) >= 5:
            recent_pop = [h["population"] for h in self.history[-5:]]
            if recent_pop[-1] > recent_pop[0] * 1.1:
                trend = " Population growing."
            elif recent_pop[-1] < recent_pop[0] * 0.9:
                trend = " Population declining."
            else:
                trend = " Population stable."
        
        return (f"Generation {self.generation}: {pop} souls, "
                f"feeling {mood}, energy {energy}, {social}.{trend}")


def run_simulation(generations=50, width=60, height=30):
    """Run an affective life simulation and print results."""
    world = AffectiveWorld(width=width, height=height, seed=42)
    
    # Seed with different emotional communities
    world.seed_cluster(15, 8, radius=6, emotion="joy")
    world.seed_cluster(45, 8, radius=5, emotion="anxious")
    world.seed_cluster(30, 20, radius=7, emotion="calm")
    world.seed_cluster(10, 22, radius=4, emotion="lonely")
    
    print("╔══════════════════════════════════════════╗")
    print("║     AFFECTIVE LIFE — Initial State       ║")
    print("╚══════════════════════════════════════════╝")
    world.step()  # gen 0 stats
    print(world.render())
    print()
    
    # Run simulation
    for i in range(generations):
        world.step()
        if (i + 1) % 10 == 0 or world.history[-1]["population"] == 0:
            print(f"\n{world.summarize()}")
            if world.history[-1]["population"] == 0:
                print("The world has gone silent.")
                break
    
    # Final state
    print("\n" + "═" * 50)
    print("FINAL STATE:")
    print(world.render())
    print()
    print(world.summarize())
    
    # Population trajectory
    if len(world.history) > 1:
        print("\n═══ POPULATION HISTORY ═══")
        max_pop = max(h["population"] for h in world.history)
        for h in world.history[::max(1, len(world.history)//20)]:
            bar_len = int(h["population"] / max(1, max_pop) * 40)
            valence_indicator = "+" if h["mean_valence"] > 0 else "-"
            print(f"  Gen {h['gen']:3d}: {'█' * bar_len} {h['population']} [{valence_indicator}]")
    
    return world


if __name__ == "__main__":
    world = run_simulation(generations=100)