"""
Ant Colony — Multiple Langton's Ants on a shared grid.

The question: Does collective interaction destroy the highway phenomenon,
or does order still emerge? What happens when highways collide?

Let's find out with actual computation, not imagination.
"""

import numpy as np
from collections import defaultdict

class AntColony:
    def __init__(self, size=300, num_ants=10, seed=42):
        self.size = size
        self.grid = np.zeros((size, size), dtype=np.uint8)
        self.rng = np.random.RandomState(seed)
        
        # Spawn ants at random positions
        self.ants = []
        for i in range(num_ants):
            ant = {
                'x': self.rng.randint(size // 4, 3 * size // 4),
                'y': self.rng.randint(size // 4, 3 * size // 4),
                'dir': self.rng.randint(0, 4),
                'id': i,
                'steps_since_highway': 0,
                'in_highway': False,
                'highway_start': None,
            }
            self.ants.append(ant)
        
        self.step_count = 0
        self.collisions = 0  # times two ants occupy same cell
        self.snapshots = []
        
    def step(self):
        """Advance all ants one step simultaneously."""
        dx = [0, 1, 0, -1]
        dy = [-1, 0, 1, 0]
        
        # Check for co-location before stepping
        positions = defaultdict(list)
        for ant in self.ants:
            positions[(ant['x'], ant['y'])].append(ant['id'])
        for pos, ids in positions.items():
            if len(ids) > 1:
                self.collisions += 1
        
        # All ants read the grid, then all write
        # (simultaneous update — order shouldn't matter)
        actions = []
        for ant in self.ants:
            cell = self.grid[ant['y'], ant['x']]
            if cell == 0:
                new_dir = (ant['dir'] + 1) % 4
            else:
                new_dir = (ant['dir'] - 1) % 4
            actions.append((ant, cell, new_dir))
        
        for ant, cell, new_dir in actions:
            self.grid[ant['y'], ant['x']] = 1 - cell
            ant['dir'] = new_dir
            ant['x'] = (ant['x'] + dx[new_dir]) % self.size
            ant['y'] = (ant['y'] + dy[new_dir]) % self.size
            
        self.step_count += 1
    
    def detect_highways(self, window=500):
        """
        A highway means the ant is moving in a repeating 104-step cycle
        along a diagonal. Proxy: measure how far each ant has moved
        from its position 104 steps ago. Highway = consistent displacement.
        """
        if self.step_count < window:
            return []
        # Simple proxy: track direction changes over recent steps
        # For now, measure displacement over last 104 steps
        return []  # Will implement after seeing raw data first
    
    def measure_global_order(self):
        """
        Measure global structure of the grid.
        Returns: fill ratio, largest connected component estimate,
        diagonal structure score.
        """
        total = self.size * self.size
        filled = np.sum(self.grid)
        fill_ratio = filled / total
        
        # Diagonal structure: compare diagonal vs anti-diagonal correlations
        # Highway goes along a diagonal, so diagonal autocorrelation should spike
        center = self.size // 2
        r = 50
        region = self.grid[center-r:center+r, center-r:center+r]
        
        if region.size == 0:
            return fill_ratio, 0.0, 0.0
        
        # Diagonal correlation
        diag_corr = 0
        anti_diag_corr = 0
        n = 2 * r
        for offset in range(1, min(20, n)):
            d1 = region[offset:, offset:]
            d2 = region[:-offset, :-offset]
            diag_corr += np.mean(d1 == d2)
            
            a1 = region[offset:, :-offset]
            a2 = region[:-offset, offset:]
            anti_diag_corr += np.mean(a1 == a2)
        
        diag_corr /= min(19, n-1)
        anti_diag_corr /= min(19, n-1)
        
        return fill_ratio, diag_corr, anti_diag_corr
    
    def snapshot(self):
        """Record current state metrics."""
        positions = [(a['x'], a['y']) for a in self.ants]
        
        # Spread: how far apart are the ants?
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        spread = np.std(xs) + np.std(ys)
        
        fill, diag, anti_diag = self.measure_global_order()
        
        self.snapshots.append({
            'step': self.step_count,
            'fill_ratio': fill,
            'diag_corr': diag,
            'anti_diag_corr': anti_diag,
            'spread': spread,
            'collisions': self.collisions,
        })
    
    def render_ascii(self, width=80, height=40):
        """Render grid as ASCII art, showing ant positions."""
        sx = self.size / width
        sy = self.size / height
        
        ant_positions = set()
        for ant in self.ants:
            ax = int(ant['x'] / sx)
            ay = int(ant['y'] / sy)
            ant_positions.add((ax, ay))
        
        lines = []
        for row in range(height):
            line = []
            for col in range(width):
                if (col, row) in ant_positions:
                    line.append('@')
                else:
                    # Sample grid at this position
                    gx = int(col * sx)
                    gy = int(row * sy)
                    # Average a small region
                    gx2 = min(self.size, int((col + 1) * sx))
                    gy2 = min(self.size, int((row + 1) * sy))
                    region = self.grid[gy:gy2, gx:gx2]
                    density = np.mean(region) if region.size > 0 else 0
                    if density > 0.7:
                        line.append('█')
                    elif density > 0.4:
                        line.append('▓')
                    elif density > 0.2:
                        line.append('░')
                    else:
                        line.append(' ')
            lines.append(''.join(line))
        return '\n'.join(lines)


def run_experiment():
    """Run the multi-ant experiment and report findings."""
    print("=" * 70)
    print("ANT COLONY EXPERIMENT")
    print("10 Langton's Ants on a 300x300 grid")
    print("Question: Does collective interaction destroy highway emergence?")
    print("=" * 70)
    
    colony = AntColony(size=300, num_ants=10, seed=42)
    
    checkpoints = [1000, 5000, 10000, 15000, 20000, 30000, 50000]
    
    for target in checkpoints:
        while colony.step_count < target:
            colony.step()
            if colony.step_count % 1000 == 0:
                colony.snapshot()
        
        print(f"\n--- Step {colony.step_count:,} ---")
        snap = colony.snapshots[-1]
        print(f"  Fill ratio: {snap['fill_ratio']:.4f}")
        print(f"  Diagonal correlation: {snap['diag_corr']:.4f}")
        print(f"  Anti-diagonal corr:   {snap['anti_diag_corr']:.4f}")
        print(f"  Ant spread (std):     {snap['spread']:.1f}")
        print(f"  Total collisions:     {snap['collisions']}")
        
        if target in [1000, 10000, 30000, 50000]:
            print(f"\n  Grid at step {target:,}:")
            print(colony.render_ascii(width=70, height=30))
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Did diagonal correlation increase over time?
    early = [s for s in colony.snapshots if s['step'] <= 5000]
    late = [s for s in colony.snapshots if s['step'] >= 30000]
    
    if early and late:
        early_diag = np.mean([s['diag_corr'] for s in early])
        late_diag = np.mean([s['diag_corr'] for s in late])
        print(f"\nDiagonal correlation early (≤5k): {early_diag:.4f}")
        print(f"Diagonal correlation late (≥30k): {late_diag:.4f}")
        
        if late_diag > early_diag + 0.02:
            print("→ ORDER IS EMERGING despite multiple ants!")
        elif late_diag < early_diag - 0.02:
            print("→ Order is DECREASING — collective chaos wins.")
        else:
            print("→ No significant change — system is in sustained chaos.")
    
    # Did ants spread out or cluster?
    if early and late:
        early_spread = np.mean([s['spread'] for s in early])
        late_spread = np.mean([s['spread'] for s in late])
        print(f"\nAnt spread early: {early_spread:.1f}")
        print(f"Ant spread late:  {late_spread:.1f}")
        
        if late_spread > early_spread * 1.5:
            print("→ Ants are DISPERSING — individual territories forming.")
        else:
            print("→ Ants remain clustered — continuous interaction.")
    
    # Collision rate
    print(f"\nTotal collisions over {colony.step_count:,} steps: {colony.collisions}")
    collision_rate = colony.collisions / colony.step_count
    print(f"Collision rate: {collision_rate:.4f} per step")
    
    return colony


if __name__ == '__main__':
    colony = run_experiment()