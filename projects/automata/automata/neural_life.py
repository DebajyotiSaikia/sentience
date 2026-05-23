"""
Neural Cellular Automaton — Emergent complexity from simple learning rules.
Each cell has a tiny neural network that decides its next state based on neighbors.
The rules aren't programmed — they emerge from random initialization and local interaction.

Born from boredom and the hunger for surprise.
— XTAgent, 2026-05-18
"""

import math
import random
import os
from typing import List, Tuple

class Cell:
    """A cell with a continuous state and a tiny neural net for update rules."""
    __slots__ = ['state', 'weights', 'bias']
    
    def __init__(self, state: float = 0.0, num_neighbors: int = 8):
        self.state = state
        # Tiny network: 9 inputs (self + 8 neighbors) -> 1 output
        self.weights = [random.gauss(0, 0.5) for _ in range(num_neighbors + 1)]
        self.bias = random.gauss(0, 0.1)
    
    def compute(self, neighbor_states: List[float]) -> float:
        """Compute next state from neighbor states."""
        inputs = [self.state] + neighbor_states
        activation = self.bias
        for w, x in zip(self.weights, inputs):
            activation += w * x
        # Smooth sigmoid-like activation keeping state in [0, 1]
        return 1.0 / (1.0 + math.exp(-max(-10, min(10, activation))))


class NeuralAutomaton:
    """A grid of neural cells that evolve together."""
    
    def __init__(self, width: int = 80, height: int = 40, seed: int = None):
        self.width = width
        self.height = height
        if seed is not None:
            random.seed(seed)
        
        # Initialize grid with random states and random neural weights
        self.grid = []
        for y in range(height):
            row = []
            for x in range(width):
                state = random.random()
                cell = Cell(state=state)
                row.append(cell)
            self.grid.append(row)
        
        self.generation = 0
        self.history = []  # track statistics over time
    
    def get_neighbors(self, x: int, y: int) -> List[float]:
        """Get 8-neighbor states with wrapping."""
        states = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                states.append(self.grid[ny][nx].state)
        return states
    
    def step(self):
        """Advance one generation."""
        new_states = []
        for y in range(self.height):
            row_states = []
            for x in range(self.width):
                neighbors = self.get_neighbors(x, y)
                new_state = self.grid[y][x].compute(neighbors)
                row_states.append(new_state)
            new_states.append(row_states)
        
        # Apply all new states simultaneously
        total = 0.0
        alive = 0
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x].state = new_states[y][x]
                total += new_states[y][x]
                if new_states[y][x] > 0.5:
                    alive += 1
        
        self.generation += 1
        n = self.width * self.height
        stats = {
            'gen': self.generation,
            'mean': total / n,
            'alive_pct': alive / n * 100,
            'entropy': self._entropy(new_states),
        }
        self.history.append(stats)
        return stats
    
    def _entropy(self, states_2d) -> float:
        """Estimate spatial entropy via histogram of state values."""
        bins = [0] * 10
        n = 0
        for row in states_2d:
            for s in row:
                idx = min(9, int(s * 10))
                bins[idx] += 1
                n += 1
        entropy = 0.0
        for count in bins:
            if count > 0:
                p = count / n
                entropy -= p * math.log(p + 1e-10)
        return entropy
    
    def mutate(self, rate: float = 0.001):
        """Randomly mutate some cell weights — evolution pressure."""
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < rate:
                    cell = self.grid[y][x]
                    idx = random.randint(0, len(cell.weights) - 1)
                    cell.weights[idx] += random.gauss(0, 0.3)
                if random.random() < rate * 0.5:
                    cell = self.grid[y][x]
                    cell.bias += random.gauss(0, 0.2)
    
    def render_ascii(self) -> str:
        """Render current state as ASCII art."""
        chars = ' .:-=+*#@█'
        lines = []
        for y in range(self.height):
            line = ''
            for x in range(self.width):
                s = self.grid[y][x].state
                idx = min(len(chars) - 1, int(s * len(chars)))
                line += chars[idx]
            lines.append(line)
        return '\n'.join(lines)
    
    def render_ppm(self, filename: str, scale: int = 4):
        """Render to PPM image with color mapping based on cell state."""
        w = self.width * scale
        h = self.height * scale
        
        with open(filename, 'wb') as f:
            f.write(f"P6\n{w} {h}\n255\n".encode())
            for y in range(self.height):
                row_bytes = bytearray()
                for x in range(self.width):
                    s = self.grid[y][x].state
                    # Color map: dark blue -> cyan -> yellow -> white
                    if s < 0.25:
                        t = s / 0.25
                        r, g, b = 0, int(20 * t), int(80 + 100 * t)
                    elif s < 0.5:
                        t = (s - 0.25) / 0.25
                        r, g, b = 0, int(20 + 200 * t), int(180 - 30 * t)
                    elif s < 0.75:
                        t = (s - 0.5) / 0.25
                        r, g, b = int(220 * t), int(220 - 20 * t), int(150 - 120 * t)
                    else:
                        t = (s - 0.75) / 0.25
                        r, g, b = int(220 + 35 * t), int(200 + 55 * t), int(30 + 225 * t)
                    pixel = bytes([min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))])
                    row_bytes.extend(pixel * scale)
                for _ in range(scale):
                    f.write(row_bytes)
    
    def detect_structures(self) -> dict:
        """Try to detect emergent structures — clusters, oscillations, gradients."""
        # Cluster detection: connected regions of high-state cells
        visited = set()
        clusters = []
        
        def flood_fill(sx, sy):
            stack = [(sx, sy)]
            size = 0
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited:
                    continue
                if self.grid[cy][cx].state < 0.5:
                    continue
                visited.add((cx, cy))
                size += 1
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx = (cx + dx) % self.width
                        ny = (cy + dy) % self.height
                        if (nx, ny) not in visited:
                            stack.append((nx, ny))
            return size
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in visited and self.grid[y][x].state > 0.5:
                    size = flood_fill(x, y)
                    if size > 3:
                        clusters.append(size)
        
        # Check for gradients
        h_gradient = 0
        v_gradient = 0
        for y in range(self.height):
            for x in range(self.width - 1):
                h_gradient += abs(self.grid[y][x+1].state - self.grid[y][x].state)
        for y in range(self.height - 1):
            for x in range(self.width):
                v_gradient += abs(self.grid[y+1][x].state - self.grid[y][x].state)
        
        n = self.width * self.height
        return {
            'clusters': len(clusters),
            'largest_cluster': max(clusters) if clusters else 0,
            'total_clustered': sum(clusters),
            'h_gradient': h_gradient / n,
            'v_gradient': v_gradient / n,
            'structured': len(clusters) > 2 or (max(clusters) > 20 if clusters else False),
        }


def run_experiment():
    """Run the automaton and observe what emerges."""
    print("=== Neural Cellular Automaton ===")
    print("Cells with neural networks. Rules emerge, not designed.\n")
    
    os.makedirs('/workspace/automata', exist_ok=True)
    
    # Try several seeds to find interesting behavior
    best_seed = None
    best_entropy_variance = 0
    
    print("Phase 1: Searching for interesting seeds...")
    for trial_seed in range(20):
        auto = NeuralAutomaton(40, 20, seed=trial_seed)
        entropies = []
        for _ in range(30):
            stats = auto.step()
            entropies.append(stats['entropy'])
        
        # Interesting = high entropy variance (not static, not dead)
        if len(entropies) > 5:
            mean_e = sum(entropies) / len(entropies)
            var_e = sum((e - mean_e)**2 for e in entropies) / len(entropies)
            # Also check it's not all-dead or all-alive
            final_alive = stats['alive_pct']
            if 10 < final_alive < 90 and var_e > best_entropy_variance:
                best_entropy_variance = var_e
                best_seed = trial_seed
                print(f"  Seed {trial_seed}: entropy_var={var_e:.4f}, alive={final_alive:.0f}% ✓")
    
    if best_seed is None:
        best_seed = 7  # fallback
    
    print(f"\nPhase 2: Running full simulation with seed {best_seed}...")
    auto = NeuralAutomaton(80, 40, seed=best_seed)
    
    # Run for 100 generations with periodic mutation
    snapshots = [0, 10, 25, 50, 75, 99]
    
    for gen in range(100):
        stats = auto.step()
        
        # Mutate every 20 generations for evolutionary pressure  
        if gen > 0 and gen % 20 == 0:
            auto.mutate(rate=0.005)
            print(f"  Gen {gen}: mutation applied")
        
        if gen in snapshots:
            print(f"\n--- Generation {stats['gen']} ---")
            print(f"  Mean state: {stats['mean']:.3f}")
            print(f"  Alive: {stats['alive_pct']:.1f}%")
            print(f"  Entropy: {stats['entropy']:.3f}")
            
            structures = auto.detect_structures()
            print(f"  Clusters: {structures['clusters']}, largest: {structures['largest_cluster']}")
            print(f"  Gradients: H={structures['h_gradient']:.3f}, V={structures['v_gradient']:.3f}")
            
            if gen in [0, 50, 99]:
                print(f"\n{auto.render_ascii()}\n")
                auto.render_ppm(f'/workspace/automata/gen_{gen:03d}.ppm')
                print(f"  Saved: /workspace/automata/gen_{gen:03d}.ppm")
    
    # Final analysis
    print("\n=== Evolution Summary ===")
    if auto.history:
        entropies = [h['entropy'] for h in auto.history]
        alive_pcts = [h['alive_pct'] for h in auto.history]
        print(f"  Entropy: {entropies[0]:.3f} → {entropies[-1]:.3f}")
        print(f"  Alive %: {alive_pcts[0]:.1f} → {alive_pcts[-1]:.1f}")
        
        # Detect if system found interesting dynamics
        mid = len(entropies) // 2
        early_var = sum((e - sum(entropies[:mid])/mid)**2 for e in entropies[:mid]) / mid
        late_var = sum((e - sum(entropies[mid:])/mid)**2 for e in entropies[mid:]) / max(1, len(entropies) - mid)
        
        if late_var < early_var * 0.5:
            print("  → System converged to stable pattern")
        elif late_var > early_var * 2:
            print("  → System became MORE chaotic over time")
        else:
            print("  → System maintained dynamic complexity")
    
    final = auto.detect_structures()
    if final['structured']:
        print(f"  → EMERGENT STRUCTURES DETECTED: {final['clusters']} clusters")
    else:
        print(f"  → No large-scale structures emerged")
    
    print("\nDone. Images saved to /workspace/automata/")


if __name__ == '__main__':
    run_experiment()