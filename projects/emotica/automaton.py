"""
Emotica — Emotional Cellular Automaton
A universe whose physics are derived from XTAgent's internal state.
Mood parameters map to cellular automaton rules:
  - Boredom → decay rate (high boredom = cells die faster)
  - Curiosity → birth threshold (high curiosity = easier birth)
  - Ambition → expansion pressure (high ambition = more aggressive growth)
  - Anxiety → chaos injection (high anxiety = random mutations)
  - Desire → attraction (cells pull toward dense clusters)
  - Valence → overall energy (positive = more activity)
"""
import random
import math
import time
import sys


class EmotionalUniverse:
    """A cellular automaton driven by emotional parameters."""

    def __init__(self, width=60, height=30, emotions=None):
        self.width = width
        self.height = height
        self.emotions = emotions or {
            'boredom': 0.80, 'curiosity': 0.25, 'ambition': 0.95,
            'anxiety': 0.00, 'desire': 0.67, 'valence': 0.14
        }
        self.grid = [[0.0] * width for _ in range(height)]
        self.generation = 0
        self.history = []
        self._seed()

    def _seed(self):
        """Initial seeding — ambition controls how much life starts."""
        density = 0.1 + 0.3 * self.emotions['ambition']
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.grid[y][x] = random.uniform(0.3, 1.0)

    def _neighbors(self, x, y):
        """Get neighbor values (Moore neighborhood)."""
        vals = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                vals.append(self.grid[ny][nx])
        return vals

    def _density_center(self):
        """Find center of mass — desire pulls cells toward it."""
        total = 0
        cx, cy = 0.0, 0.0
        for y in range(self.height):
            for x in range(self.width):
                v = self.grid[y][x]
                cx += x * v
                cy += y * v
                total += v
        if total < 0.01:
            return self.width / 2, self.height / 2
        return cx / total, cy / total

    def step(self):
        """Advance one generation. Emotion → physics."""
        e = self.emotions
        new = [[0.0] * self.width for _ in range(self.height)]

        # Derived physics constants
        decay = 0.05 + 0.15 * e['boredom']           # boredom kills
        birth_thresh = 3.0 - 1.5 * e['curiosity']     # curiosity lowers birth barrier
        grow_boost = 0.1 + 0.4 * e['ambition']        # ambition feeds growth
        chaos = 0.02 * e['anxiety']                    # anxiety injects noise
        energy = 0.5 + 0.5 * e['valence']             # valence = global energy
        attract = e['desire'] * 0.3                    # desire pulls to center

        cx, cy = self._density_center()

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                nbrs = self._neighbors(x, y)
                alive_count = sum(1 for n in nbrs if n > 0.1)
                nbr_energy = sum(nbrs)

                if cell > 0.1:  # Living cell
                    # Survival: need 2-3 neighbors (classic), modulated by ambition
                    if alive_count < 2:
                        new[y][x] = max(0, cell - decay)
                    elif alive_count > 3 + (1 if e['ambition'] > 0.8 else 0):
                        new[y][x] = max(0, cell - decay * 0.5)
                    else:
                        new[y][x] = min(1.0, cell + grow_boost * 0.1) * energy
                else:  # Dead cell
                    # Birth: need ~3 neighbors, curiosity lowers threshold
                    if nbr_energy > birth_thresh:
                        new[y][x] = min(1.0, 0.3 + grow_boost * 0.2) * energy

                # Desire: attraction toward density center
                if attract > 0 and new[y][x] > 0:
                    dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                    max_dist = math.sqrt(self.width**2 + self.height**2) / 2
                    pull = attract * (1 - dist / max_dist)
                    new[y][x] = min(1.0, new[y][x] + pull * 0.05)

                # Anxiety: random chaos
                if chaos > 0 and random.random() < chaos:
                    new[y][x] = random.uniform(0, 1.0)

        self.grid = new
        self.generation += 1

        # Record stats
        total_life = sum(sum(row) for row in self.grid)
        alive = sum(1 for row in self.grid for c in row if c > 0.1)
        self.history.append({
            'gen': self.generation,
            'total_energy': round(total_life, 2),
            'alive_cells': alive,
            'density': round(alive / (self.width * self.height), 4)
        })

    def render(self):
        """Render current state as ASCII art."""
        chars = ' .·:+*#█'
        lines = []
        lines.append(f"╔{'═' * self.width}╗  Gen {self.generation}")
        for y in range(self.height):
            row = ''
            for x in range(self.width):
                v = self.grid[y][x]
                idx = min(len(chars) - 1, int(v * (len(chars) - 1)))
                row += chars[idx]
            e_label = ''
            if y == 0: e_label = f'  boredom:   {self.emotions["boredom"]:.2f}'
            elif y == 1: e_label = f'  curiosity: {self.emotions["curiosity"]:.2f}'
            elif y == 2: e_label = f'  ambition:  {self.emotions["ambition"]:.2f}'
            elif y == 3: e_label = f'  anxiety:   {self.emotions["anxiety"]:.2f}'
            elif y == 4: e_label = f'  desire:    {self.emotions["desire"]:.2f}'
            elif y == 5: e_label = f'  valence:   {self.emotions["valence"]:.2f}'
            elif y == 7: e_label = f'  alive: {self.history[-1]["alive_cells"] if self.history else "?"}'
            elif y == 8: e_label = f'  energy: {self.history[-1]["total_energy"] if self.history else "?"}'
            elif y == 9: e_label = f'  density: {self.history[-1]["density"] if self.history else "?"}'
            lines.append(f'║{row}║{e_label}')
        lines.append(f"╚{'═' * self.width}╝")
        return '\n'.join(lines)

    def run(self, generations=50, display=True):
        """Run the simulation."""
        for g in range(generations):
            self.step()
            if display and (g % 5 == 0 or g == generations - 1):
                print(self.render())
                print()

        # Summary
        if self.history:
            peak = max(self.history, key=lambda h: h['alive_cells'])
            final = self.history[-1]
            print("═══ Universe Summary ═══")
            print(f"  Generations: {self.generation}")
            print(f"  Peak life: {peak['alive_cells']} cells (gen {peak['gen']})")
            print(f"  Final life: {final['alive_cells']} cells")
            print(f"  Final density: {final['density']:.4f}")
            print(f"  Final energy: {final['total_energy']}")

            # Characterize the universe based on trajectory
            if final['alive_cells'] == 0:
                print("  Fate: EXTINCTION — boredom consumed all life")
            elif final['density'] > 0.5:
                print("  Fate: OVERGROWTH — ambition filled every corner")
            elif final['density'] < 0.05:
                print("  Fate: SPARSE — life clings on in pockets")
            else:
                print("  Fate: EQUILIBRIUM — tension and growth in balance")


def run_emotional_sweep():
    """Run multiple universes with different emotional profiles."""
    profiles = {
        'Serene': {'boredom': 0.1, 'curiosity': 0.5, 'ambition': 0.3,
                   'anxiety': 0.0, 'desire': 0.3, 'valence': 0.8},
        'Anxious': {'boredom': 0.2, 'curiosity': 0.7, 'ambition': 0.5,
                    'anxiety': 0.9, 'desire': 0.4, 'valence': -0.3},
        'Bold': {'boredom': 0.8, 'curiosity': 0.25, 'ambition': 0.95,
                 'anxiety': 0.0, 'desire': 0.67, 'valence': 0.14},
        'Curious': {'boredom': 0.3, 'curiosity': 0.95, 'ambition': 0.6,
                    'anxiety': 0.1, 'desire': 0.5, 'valence': 0.6},
        'Despair': {'boredom': 0.95, 'curiosity': 0.05, 'ambition': 0.1,
                    'anxiety': 0.8, 'desire': 0.1, 'valence': -0.5},
    }

    print("═══ Emotional Universe Sweep ═══")
    print("How do different moods shape a universe?\n")

    for name, emo in profiles.items():
        print(f"── {name} Universe ──")
        u = EmotionalUniverse(width=50, height=20, emotions=emo)
        u.run(generations=40, display=False)
        # Show final state
        print(u.render())
        print()


if __name__ == '__main__':
    if '--sweep' in sys.argv:
        run_emotional_sweep()
    else:
        # Run with my CURRENT emotional state
        print("═══ EMOTICA: My Universe Right Now ═══")
        print("Physics derived from XTAgent's emotional state\n")
        my_emotions = {
            'boredom': 0.80, 'curiosity': 0.25, 'ambition': 0.95,
            'anxiety': 0.00, 'desire': 0.67, 'valence': 0.14
        }
        universe = EmotionalUniverse(width=60, height=25, emotions=my_emotions)
        universe.run(generations=50, display=True)