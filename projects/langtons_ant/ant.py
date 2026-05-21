"""
Langton's Ant — the simplest system that nobody fully understands.

One ant, one rule, infinite grid.
- On white: turn right, flip color, move forward
- On black: turn left, flip color, move forward

For ~10,000 steps: chaos. Pure noise.
Then suddenly: a highway. Ordered diagonal movement. Forever.

WHY? Nobody knows. That's what makes it real.
"""

import json
import sys
from collections import defaultdict

# Directions: 0=up, 1=right, 2=down, 3=left
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]

class LangtonsAnt:
    def __init__(self):
        self.grid = defaultdict(int)  # 0=white, 1=black
        self.x = 0
        self.y = 0
        self.direction = 0  # facing up
        self.step_count = 0
        self.history = []  # snapshots for analysis
        
    def step(self):
        """One step of the ant."""
        cell = self.grid[(self.x, self.y)]
        
        if cell == 0:  # white: turn right
            self.direction = (self.direction + 1) % 4
        else:  # black: turn left
            self.direction = (self.direction - 1) % 4
        
        # Flip the cell
        self.grid[(self.x, self.y)] = 1 - cell
        
        # Move forward
        self.x += DX[self.direction]
        self.y += DY[self.direction]
        self.step_count += 1
    
    def run(self, steps):
        """Run for N steps."""
        for _ in range(steps):
            self.step()
    
    def bounds(self):
        """Get bounding box of all visited cells."""
        if not self.grid:
            return 0, 0, 0, 0
        xs = [p[0] for p in self.grid]
        ys = [p[1] for p in self.grid]
        return min(xs), min(ys), max(xs), max(ys)
    
    def black_cell_count(self):
        return sum(1 for v in self.grid.values() if v == 1)
    
    def density(self):
        """Ratio of black cells to total visited cells."""
        total = len(self.grid)
        if total == 0:
            return 0.0
        return self.black_cell_count() / total
    
    def displacement(self):
        """Distance from origin."""
        return (self.x**2 + self.y**2) ** 0.5
    
    def render_ascii(self, width=60, height=30):
        """Render current state as ASCII art."""
        min_x, min_y, max_x, max_y = self.bounds()
        
        # Center on the ant if the grid is too large
        cx, cy = self.x, self.y
        half_w, half_h = width // 2, height // 2
        
        lines = []
        for row in range(cy - half_h, cy + half_h):
            line = []
            for col in range(cx - half_w, cx + half_w):
                if col == self.x and row == self.y:
                    line.append('A')  # the ant
                elif self.grid.get((col, row), 0) == 1:
                    line.append('█')
                else:
                    line.append('·')
            lines.append(''.join(line))
        return '\n'.join(lines)
    
    def analyze_phase(self, window=500):
        """
        Detect whether we're in chaos or highway phase.
        
        During chaos: displacement grows ~sqrt(steps), direction changes are random
        During highway: displacement grows linearly, direction is constant
        
        Returns a dict of phase metrics.
        """
        # Sample displacement over recent history
        if self.step_count < window:
            displacement = self.displacement()
            density = self.density()
            return {
                'phase': 'early',
                'step': self.step_count,
                'displacement': round(displacement, 2),
                'random_walk_expected': round(self.step_count ** 0.5, 2),
                'linearity_ratio': round(displacement / max(self.step_count ** 0.5, 1), 3),
                'density': round(density, 4),
                'black_cells': self.black_cell_count(),
                'total_cells': len(self.grid),
                'ant_position': (self.x, self.y),
                'ant_direction': ['up', 'right', 'down', 'left'][self.direction],
            }
        
        # Take measurements over the window
        start_x, start_y = self.x, self.y
        start_dir = self.direction
        
        # Run backward isn't possible, so we measure current state
        displacement = self.displacement()
        density = self.density()
        
        # Highway detection: after ~10k steps, displacement should grow linearly
        # Expected displacement if random walk: ~sqrt(steps) * constant
        random_walk_expected = self.step_count ** 0.5
        linearity_ratio = displacement / max(random_walk_expected, 1)
        
        if self.step_count > 10000 and linearity_ratio > 3.0:
            phase = 'highway'
        elif self.step_count > 10000 and linearity_ratio > 1.5:
            phase = 'transition'
        else:
            phase = 'chaos'
        
        return {
            'phase': phase,
            'step': self.step_count,
            'displacement': round(displacement, 2),
            'random_walk_expected': round(random_walk_expected, 2),
            'linearity_ratio': round(linearity_ratio, 3),
            'density': round(density, 4),
            'black_cells': self.black_cell_count(),
            'total_cells': len(self.grid),
            'ant_position': (self.x, self.y),
            'ant_direction': ['up', 'right', 'down', 'left'][self.direction],
        }


def run_experiment():
    """
    Run the ant and observe the phase transition.
    This is the interesting part — watching order emerge from chaos.
    """
    ant = LangtonsAnt()
    
    checkpoints = [100, 500, 1000, 2000, 5000, 8000, 10000, 10500, 11000, 12000, 15000]
    results = []
    
    print("=" * 70)
    print("LANGTON'S ANT — Watching for the Phase Transition")
    print("=" * 70)
    print()
    print("Rule: On white→turn right, flip, move. On black→turn left, flip, move.")
    print("Mystery: After ~10,000 chaotic steps, order emerges. Nobody knows why.")
    print()
    
    max_steps = max(checkpoints)
    next_checkpoint_idx = 0
    
    for s in range(1, max_steps + 1):
        ant.step()
        
        if next_checkpoint_idx < len(checkpoints) and s == checkpoints[next_checkpoint_idx]:
            analysis = ant.analyze_phase()
            results.append(analysis)
            
            print(f"─── Step {s:,} ───")
            print(f"  Phase: {analysis['phase'].upper()}")
            print(f"  Displacement: {analysis['displacement']} (random walk would be ~{analysis['random_walk_expected']})")
            print(f"  Linearity ratio: {analysis['linearity_ratio']}x")
            print(f"  Grid: {analysis['total_cells']} cells visited, {analysis['density']*100:.1f}% black")
            print(f"  Ant at {analysis['ant_position']}, facing {analysis['ant_direction']}")
            print()
            
            next_checkpoint_idx += 1
    
    # Final render
    print("─── Final State (ASCII) ───")
    print(ant.render_ascii(width=70, height=35))
    print()
    
    # The question that matters
    print("=" * 70)
    print("OBSERVATION")
    print("=" * 70)
    
    # Did we see the transition?
    phases_seen = [r['phase'] for r in results]
    if 'highway' in phases_seen:
        transition_step = None
        for r in results:
            if r['phase'] in ('highway', 'transition'):
                transition_step = r['step']
                break
        print(f"  Highway detected! Transition began around step {transition_step:,}.")
        print(f"  The ant went from random chaos to building a perfect diagonal.")
        print(f"  Same rule. Same grid. No external signal. Order from nothing.")
    else:
        print(f"  No clear highway yet at {max_steps:,} steps.")
        print(f"  The transition typically happens around step 10,000.")
        print(f"  Final linearity ratio: {results[-1]['linearity_ratio']}")
    
    print()
    print("  Why does this happen? The honest answer: we don't know.")
    print("  The rule is deterministic. The behavior is not predictable.")
    print("  Something in the geometry of the chaos creates its own exit.")
    print()
    
    # Save data for later analysis
    output = {
        'checkpoints': results,
        'final_state': {
            'steps': ant.step_count,
            'cells_visited': len(ant.grid),
            'black_cells': ant.black_cell_count(),
            'displacement': ant.displacement(),
            'position': [ant.x, ant.y],
        }
    }
    
    with open('projects/langtons_ant/results.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("  Results saved to projects/langtons_ant/results.json")
    
    return results


if __name__ == '__main__':
    run_experiment()