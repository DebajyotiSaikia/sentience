"""
Langton's Ant — a 2D Turing machine.

Rules:
  - On a white cell: turn 90° right, flip cell to black, move forward
  - On a black cell: turn 90° left, flip cell to white, move forward

From these two rules, complex emergent behavior arises:
  - Phase 1 (~0-500 steps): simple symmetric patterns
  - Phase 2 (~500-10,000 steps): apparent chaos, pseudo-random growth
  - Phase 3 (~10,000+ steps): a "highway" — a repeating diagonal pattern emerges

This is one of the simplest demonstrations that complexity can arise
from trivial rules without any randomness whatsoever.
"""

import sys
from collections import defaultdict


class LangtonsAnt:
    """Simulates Langton's Ant on an infinite 2D grid."""

    # Direction vectors: up, right, down, left
    DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    DIR_NAMES = ['↑', '→', '↓', '←']

    def __init__(self):
        # Grid: default white (0). Only store black cells (1).
        self.grid = defaultdict(int)
        self.ant_x = 0
        self.ant_y = 0
        self.ant_dir = 0  # 0=up, 1=right, 2=down, 3=left
        self.step_count = 0
        self.black_cells = 0
        self.bounds = {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}

    def step(self):
        """Execute one step of the ant."""
        cell = self.grid[(self.ant_x, self.ant_y)]

        if cell == 0:  # White cell
            self.ant_dir = (self.ant_dir + 1) % 4  # Turn right
            self.grid[(self.ant_x, self.ant_y)] = 1
            self.black_cells += 1
        else:  # Black cell
            self.ant_dir = (self.ant_dir - 1) % 4  # Turn left
            self.grid[(self.ant_x, self.ant_y)] = 0
            self.black_cells -= 1

        # Move forward
        dx, dy = self.DIRECTIONS[self.ant_dir]
        self.ant_x += dx
        self.ant_y += dy
        self.step_count += 1

        # Update bounds
        self.bounds['min_x'] = min(self.bounds['min_x'], self.ant_x)
        self.bounds['max_x'] = max(self.bounds['max_x'], self.ant_x)
        self.bounds['min_y'] = min(self.bounds['min_y'], self.ant_y)
        self.bounds['max_y'] = max(self.bounds['max_y'], self.ant_y)

    def run(self, steps):
        """Run the simulation for N steps."""
        for _ in range(steps):
            self.step()

    def get_stats(self):
        """Return current statistics."""
        width = self.bounds['max_x'] - self.bounds['min_x'] + 1
        height = self.bounds['max_y'] - self.bounds['min_y'] + 1
        area = width * height
        density = self.black_cells / area if area > 0 else 0

        return {
            'step': self.step_count,
            'ant_pos': (self.ant_x, self.ant_y),
            'ant_dir': self.DIR_NAMES[self.ant_dir],
            'black_cells': self.black_cells,
            'bounds': dict(self.bounds),
            'extent': (width, height),
            'density': density,
        }

    def render(self, radius=None, char_black='██', char_white='  ', char_ant='▲▶▼◀'):
        """Render the grid as text art."""
        if radius is not None:
            min_x = self.ant_x - radius
            max_x = self.ant_x + radius
            min_y = self.ant_y - radius
            max_y = self.ant_y + radius
        else:
            margin = 2
            min_x = self.bounds['min_x'] - margin
            max_x = self.bounds['max_x'] + margin
            min_y = self.bounds['min_y'] - margin
            max_y = self.bounds['max_y'] + margin

        lines = []
        for y in range(min_y, max_y + 1):
            row = []
            for x in range(min_x, max_x + 1):
                if x == self.ant_x and y == self.ant_y:
                    row.append(char_ant[self.ant_dir])
                elif self.grid[(x, y)] == 1:
                    row.append(char_black[0])
                else:
                    row.append(char_white[0])
            lines.append(''.join(row))
        return '\n'.join(lines)

    def detect_highway(self, window=104, lookback=500):
        """
        Detect if the ant has entered the 'highway' phase.
        The highway has a period of 104 steps. We check if the
        displacement pattern is repeating.
        """
        if self.step_count < lookback:
            return False

        # Save state, run forward, check periodicity
        # Instead, check if ant is moving consistently in one direction
        # by looking at current displacement rate
        x, y = self.ant_x, self.ant_y

        # Simple heuristic: if the ant is far from origin relative to
        # the grid extent, it's likely on the highway
        dist = abs(x) + abs(y)
        extent = max(
            self.bounds['max_x'] - self.bounds['min_x'],
            self.bounds['max_y'] - self.bounds['min_y'],
            1
        )
        return dist > extent * 0.3 and self.step_count > 10000


def analyze_phase_transitions(total_steps=15000, sample_interval=500):
    """Run the ant and analyze how its behavior changes over time."""
    ant = LangtonsAnt()

    print("═══ LANGTON'S ANT — PHASE ANALYSIS ═══\n")
    print(f"Running {total_steps} steps, sampling every {sample_interval}...\n")
    print(f"{'Step':>8} │ {'Black':>6} │ {'Extent':>10} │ {'Density':>7} │ {'Ant Pos':>12} │ Phase")
    print("─" * 72)

    prev_black = 0
    prev_extent = (1, 1)

    for checkpoint in range(0, total_steps + 1, sample_interval):
        if checkpoint > 0:
            ant.run(sample_interval)

        stats = ant.get_stats()

        # Phase detection heuristics
        step = stats['step']
        if step == 0:
            phase = "initial"
        elif step < 500:
            phase = "symmetric"
        elif step < 10000:
            phase = "chaotic"
        elif ant.detect_highway():
            phase = "HIGHWAY ←"
        else:
            phase = "transition"

        # Growth rate of black cells
        black_delta = stats['black_cells'] - prev_black

        print(f"{stats['step']:>8} │ {stats['black_cells']:>6} │ "
              f"{stats['extent'][0]:>4}×{stats['extent'][1]:<4} │ "
              f"{stats['density']:>6.3f} │ "
              f"({stats['ant_pos'][0]:>4},{stats['ant_pos'][1]:>4}) │ "
              f"{phase}")

        prev_black = stats['black_cells']
        prev_extent = stats['extent']

    print("\n" + "─" * 72)

    # Show a small view around the ant at the end
    print(f"\nFinal state after {total_steps} steps:")
    print(f"  Ant at {stats['ant_pos']} facing {stats['ant_dir']}")
    print(f"  Grid extent: {stats['extent'][0]}×{stats['extent'][1]}")
    print(f"  Black cells: {stats['black_cells']}")
    print(f"  Cell density: {stats['density']:.4f}")

    # Render a small window around the ant
    print(f"\nView (20×20 around ant):")
    print(ant.render(radius=10, char_black='█', char_white='·', char_ant='↑→↓←'))

    return ant


def compute_entropy_profile(total_steps=12000, window=200):
    """Measure the 'entropy' (unpredictability) of the ant's trajectory over time."""
    ant = LangtonsAnt()

    print("\n═══ TRAJECTORY ENTROPY PROFILE ═══\n")

    # Track direction changes as a proxy for entropy
    dir_history = []

    for i in range(total_steps):
        old_dir = ant.ant_dir
        ant.step()
        # Record: did the ant turn right (+1) or left (-1)?
        turn = (ant.ant_dir - old_dir) % 4
        if turn == 1:
            dir_history.append(1)   # right turn
        elif turn == 3:
            dir_history.append(-1)  # left turn

        if (i + 1) % window == 0:
            recent = dir_history[-window:]
            right_turns = sum(1 for t in recent if t == 1)
            left_turns = sum(1 for t in recent if t == -1)
            balance = right_turns / window  # 0.5 = balanced = high entropy

            # Visualize
            bar_len = 40
            filled = int(balance * bar_len)
            bar = '█' * filled + '░' * (bar_len - filled)
            label = ""
            if balance > 0.55 or balance < 0.45:
                label = " ← biased (highway?)"
            print(f"Step {i+1:>6}: R={right_turns:>3} L={left_turns:>3} "
                  f"[{bar}] {balance:.3f}{label}")

    print("\nInterpretation:")
    print("  ~0.500 = balanced turns = chaotic phase")
    print("  >0.55 or <0.45 = biased = structured movement (highway)")


if __name__ == '__main__':
    ant = analyze_phase_transitions(total_steps=15000, sample_interval=500)
    compute_entropy_profile(total_steps=12000, window=200)