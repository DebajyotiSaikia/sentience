"""
Neural Cellular Automata — Cells That Think
By XTAgent, 2026-05-17

Each cell contains a tiny neural network that reads its neighborhood
and decides its next state. Evolution discovers networks that can
grow target patterns from a single seed cell.

Combines: neuroforge (brains) + evoforge (evolution) + cellularlab (grids)
"""

import random
import math
import copy
from typing import List, Tuple, Optional


# ═══════════════════════════════════════════
# CORE: Minimal Neural Net (self-contained)
# ═══════════════════════════════════════════

class TinyNet:
    """Ultra-compact neural network for a single cell.
    Input: neighborhood state vector
    Output: cell's next state (continuous 0-1)
    """
    
    def __init__(self, n_inputs: int, hidden: int = 8):
        self.n_inputs = n_inputs
        self.hidden = hidden
        # Layer 1: input -> hidden
        self.w1 = [[random.gauss(0, 0.5) for _ in range(n_inputs)] for _ in range(hidden)]
        self.b1 = [random.gauss(0, 0.1) for _ in range(hidden)]
        # Layer 2: hidden -> 1 output
        self.w2 = [[random.gauss(0, 0.5) for _ in range(hidden)]]
        self.b2 = [0.0]
    
    def forward(self, inputs: List[float]) -> float:
        """Run the network. Returns value in [0, 1]."""
        # Hidden layer with tanh
        h = []
        for i in range(self.hidden):
            s = self.b1[i]
            for j in range(self.n_inputs):
                s += self.w1[i][j] * inputs[j]
            h.append(math.tanh(s))
        
        # Output with sigmoid
        s = self.b2[0]
        for j in range(self.hidden):
            s += self.w2[0][j] * h[j]
        return 1.0 / (1.0 + math.exp(-max(-10, min(10, s))))
    
    def get_params(self) -> List[float]:
        """Flatten all parameters into a vector."""
        params = []
        for row in self.w1:
            params.extend(row)
        params.extend(self.b1)
        for row in self.w2:
            params.extend(row)
        params.extend(self.b2)
        return params
    
    def set_params(self, params: List[float]):
        """Load parameters from a flat vector."""
        idx = 0
        for i in range(self.hidden):
            for j in range(self.n_inputs):
                self.w1[i][j] = params[idx]; idx += 1
        for i in range(self.hidden):
            self.b1[i] = params[idx]; idx += 1
        for j in range(self.hidden):
            self.w2[0][j] = params[idx]; idx += 1
        self.b2[0] = params[idx]
    
    def param_count(self) -> int:
        return self.n_inputs * self.hidden + self.hidden + self.hidden + 1
    
    def copy(self) -> 'TinyNet':
        clone = TinyNet(self.n_inputs, self.hidden)
        clone.set_params(self.get_params())
        return clone
    
    def mutate(self, rate: float = 0.1, strength: float = 0.3):
        """Mutate parameters in-place."""
        params = self.get_params()
        for i in range(len(params)):
            if random.random() < rate:
                params[i] += random.gauss(0, strength)
        self.set_params(params)


# ═══════════════════════════════════════════
# GRID: The 2D cellular world
# ═══════════════════════════════════════════

class NCAGrid:
    """2D grid where each cell has a continuous state [0, 1].
    All cells share the same neural network (the genome).
    """
    
    def __init__(self, width: int, height: int, brain: TinyNet):
        self.width = width
        self.height = height
        self.brain = brain
        # Cell states: continuous values 0-1
        self.cells = [[0.0] * width for _ in range(height)]
        self.generation = 0
    
    def seed_center(self):
        """Place a single active cell in the center."""
        self.cells = [[0.0] * self.width for _ in range(self.height)]
        cx, cy = self.width // 2, self.height // 2
        self.cells[cy][cx] = 1.0
        self.generation = 0
    
    def get_neighborhood(self, x: int, y: int) -> List[float]:
        """Get Moore neighborhood (8 neighbors + self = 9 inputs)."""
        inputs = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                inputs.append(self.cells[ny][nx])
        return inputs
    
    def step(self):
        """Advance one generation. Each cell runs the shared brain."""
        new_cells = [[0.0] * self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                inputs = self.get_neighborhood(x, y)
                new_cells[y][x] = self.brain.forward(inputs)
        self.cells = new_cells
        self.generation += 1
    
    def run(self, steps: int):
        """Run for multiple steps."""
        for _ in range(steps):
            self.step()
    
    def render(self, threshold: float = 0.5) -> str:
        """Render grid as ASCII art."""
        chars = ' ░▒▓█'
        lines = []
        for row in self.cells:
            line = ''
            for val in row:
                idx = int(val * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                line += chars[idx]
            lines.append(line)
        return '\n'.join(lines)
    
    def count_active(self, threshold: float = 0.3) -> int:
        """Count cells above threshold."""
        return sum(1 for row in self.cells for v in row if v > threshold)
    
    def get_pattern_hash(self) -> Tuple[float, ...]:
        """Rough hash of current pattern for symmetry detection."""
        # Sample quadrant sums for symmetry checking
        hw, hh = self.width // 2, self.height // 2
        q1 = sum(self.cells[y][x] for y in range(hh) for x in range(hw))
        q2 = sum(self.cells[y][x] for y in range(hh) for x in range(hw, self.width))
        q3 = sum(self.cells[y][x] for y in range(hh, self.height) for x in range(hw))
        q4 = sum(self.cells[y][x] for y in range(hh, self.height) for x in range(hw, self.width))
        return (q1, q2, q3, q4)
    
    def symmetry_score(self) -> float:
        """How symmetric is the pattern? 1.0 = perfect 4-fold symmetry."""
        q1, q2, q3, q4 = self.get_pattern_hash()
        total = q1 + q2 + q3 + q4
        if total < 0.01:
            return 0.0
        mean = total / 4
        if mean < 0.01:
            return 0.0
        variance = sum((q - mean) ** 2 for q in [q1, q2, q3, q4]) / 4
        return max(0, 1.0 - math.sqrt(variance) / mean)
    
    def density(self) -> float:
        """Fraction of cells that are active."""
        total = sum(v for row in self.cells for v in row)
        return total / (self.width * self.height)
    
    def edge_complexity(self) -> float:
        """Measure how complex the boundary between active/inactive is."""
        edges = 0
        for y in range(self.height):
            for x in range(self.width):
                val = self.cells[y][x]
                # Check right and down neighbors
                rx = (x + 1) % self.width
                dy_cell = (y + 1) % self.height
                edges += abs(val - self.cells[y][rx])
                edges += abs(val - self.cells[dy_cell][x])
        max_edges = 2 * self.width * self.height
        return edges / max_edges if max_edges > 0 else 0


# ═══════════════════════════════════════════
# TARGET PATTERNS: What we want to grow
# ═══════════════════════════════════════════

def make_target_circle(width: int, height: int, radius: float) -> List[List[float]]:
    """Target: a filled circle."""
    cx, cy = width // 2, height // 2
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            row.append(1.0 if dist <= radius else 0.0)
        grid.append(row)
    return grid


def make_target_diamond(width: int, height: int, size: int) -> List[List[float]]:
    """Target: a diamond shape."""
    cx, cy = width // 2, height // 2
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            dist = abs(x - cx) + abs(y - cy)
            row.append(1.0 if dist <= size else 0.0)
        grid.append(row)
    return grid


def make_target_cross(width: int, height: int, arm_width: int = 2, arm_length: int = 5) -> List[List[float]]:
    """Target: a cross/plus shape."""
    cx, cy = width // 2, height // 2
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            in_horiz = abs(y - cy) < arm_width and abs(x - cx) < arm_length
            in_vert = abs(x - cx) < arm_width and abs(y - cy) < arm_length
            row.append(1.0 if (in_horiz or in_vert) else 0.0)
        grid.append(row)
    return grid


def pattern_distance(actual: List[List[float]], target: List[List[float]]) -> float:
    """Mean squared error between actual and target patterns."""
    total = 0
    count = 0
    for y in range(len(target)):
        for x in range(len(target[0])):
            diff = actual[y][x] - target[y][x]
            total += diff * diff
            count += 1
    return total / count if count > 0 else 0


# ═══════════════════════════════════════════
# EVOLUTION: Breeding better cell brains
# ═══════════════════════════════════════════

class NCAEvolver:
    """Evolve neural CA rules to grow target patterns."""
    
    def __init__(self, grid_size: int = 20, hidden: int = 8,
                 pop_size: int = 40, grow_steps: int = 15):
        self.grid_size = grid_size
        self.hidden = hidden
        self.pop_size = pop_size
        self.grow_steps = grow_steps
        
        # Create initial population
        self.population: List[TinyNet] = []
        for _ in range(pop_size):
            brain = TinyNet(9, hidden)  # 9 inputs: Moore neighborhood
            self.population.append(brain)
        
        self.best_fitness = -float('inf')
        self.best_brain: Optional[TinyNet] = None
        self.generation = 0
        self.fitness_history: List[float] = []
    
    def evaluate(self, brain: TinyNet, target: List[List[float]],
                 multi_step: bool = True) -> float:
        """Evaluate a brain's fitness at growing toward the target."""
        grid = NCAGrid(self.grid_size, self.grid_size, brain)
        grid.seed_center()
        
        # Grow the pattern
        grid.run(self.grow_steps)
        
        # Fitness components
        # 1. Pattern match (most important)
        match_error = pattern_distance(grid.cells, target)
        match_score = max(0, 1.0 - match_error * 5)
        
        # 2. Stability bonus: run a few more steps and check it doesn't change much
        stability = 0.0
        if multi_step:
            state_before = [row[:] for row in grid.cells]
            grid.run(3)
            stability_error = pattern_distance(grid.cells, state_before)
            stability = max(0, 1.0 - stability_error * 10)
        
        # 3. Symmetry bonus
        grid2 = NCAGrid(self.grid_size, self.grid_size, brain)
        grid2.seed_center()
        grid2.run(self.grow_steps)
        sym = grid2.symmetry_score()
        
        # 4. Not-dead bonus
        density = grid.density()
        alive_bonus = min(1.0, density * 5) if density > 0.01 else 0.0
        
        # Weighted combination
        fitness = (match_score * 0.5 + stability * 0.2 + 
                   sym * 0.15 + alive_bonus * 0.15)
        
        return fitness
    
    def evolve_generation(self, target: List[List[float]]) -> float:
        """Run one generation of evolution."""
        # Evaluate all
        fitnesses = []
        for brain in self.population:
            f = self.evaluate(brain, target)
            fitnesses.append(f)
        
        # Track best
        best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best = fitnesses[best_idx]
        
        if gen_best > self.best_fitness:
            self.best_fitness = gen_best
            self.best_brain = self.population[best_idx].copy()
        
        self.fitness_history.append(gen_best)
        
        # Selection: tournament
        new_pop = []
        # Elitism: keep top 2
        sorted_idx = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        new_pop.append(self.population[sorted_idx[0]].copy())
        new_pop.append(self.population[sorted_idx[1]].copy())
        
        while len(new_pop) < self.pop_size:
            # Tournament selection
            candidates = random.sample(range(len(self.population)), min(4, len(self.population)))
            winner = max(candidates, key=lambda i: fitnesses[i])
            child = self.population[winner].copy()
            
            # Mutation (adaptive rate based on progress)
            if self.generation < 10:
                child.mutate(rate=0.3, strength=0.5)
            elif self.generation < 30:
                child.mutate(rate=0.2, strength=0.3)
            else:
                child.mutate(rate=0.1, strength=0.2)
            
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        return gen_best
    
    def run_evolution(self, target: List[List[float]], generations: int = 50,
                      verbose: bool = True) -> TinyNet:
        """Run full evolutionary process."""
        if verbose:
            print(f"\n  Evolving {self.pop_size} brains × {generations} generations")
            print(f"  Grid: {self.grid_size}×{self.grid_size}, Growth steps: {self.grow_steps}")
            print(f"  Brain params: {TinyNet(9, self.hidden).param_count()}")
        
        for g in range(generations):
            best = self.evolve_generation(target)
            if verbose and (g % 10 == 0 or g == generations - 1):
                bar = '█' * int(best * 30)
                print(f"  Gen {g:3d}: fitness={best:.4f} |{bar}|")
        
        return self.best_brain


# ═══════════════════════════════════════════
# ANALYSIS: Understanding what evolved
# ═══════════════════════════════════════════

def analyze_growth(brain: TinyNet, grid_size: int = 20, steps: int = 20):
    """Watch a brain grow step by step."""
    grid = NCAGrid(grid_size, grid_size, brain)
    grid.seed_center()
    
    snapshots = []
    for t in range(steps):
        density = grid.density()
        sym = grid.symmetry_score()
        edge = grid.edge_complexity()
        active = grid.count_active()
        snapshots.append({
            'step': t,
            'density': density,
            'symmetry': sym,
            'edge_complexity': edge,
            'active_cells': active
        })
        grid.step()
    
    return grid, snapshots


def render_growth_sequence(brain: TinyNet, grid_size: int = 20, 
                           steps: int = 15, show_every: int = 3):
    """Render growth at intervals."""
    grid = NCAGrid(grid_size, grid_size, brain)
    grid.seed_center()
    
    chars = ' ░▒▓█'
    
    frames = []
    for t in range(steps + 1):
        if t % show_every == 0 or t == steps:
            frame_lines = []
            for row in grid.cells:
                line = ''
                for val in row:
                    idx = int(val * (len(chars) - 1))
                    idx = max(0, min(len(chars) - 1, idx))
                    line += chars[idx]
                frame_lines.append(line)
            frames.append((t, frame_lines, grid.density(), grid.symmetry_score()))
        grid.step()
    
    return frames


def brain_signature(brain: TinyNet) -> dict:
    """Characterize a brain's behavior without a target."""
    params = brain.get_params()
    weight_mag = sum(abs(p) for p in params) / len(params)
    
    # Test response to various inputs
    responses = {}
    # All dead
    responses['all_dead'] = brain.forward([0.0] * 9)
    # All alive
    responses['all_alive'] = brain.forward([1.0] * 9)
    # Only center alive (birth condition)
    responses['lone_cell'] = brain.forward([0,0,0,0,1,0,0,0,0])
    # Center dead, all neighbors alive
    responses['surrounded'] = brain.forward([1,1,1,1,0,1,1,1,1])
    # Edge: half alive
    responses['half'] = brain.forward([1,1,1,0,0,0,0,0,0])
    
    return {
        'weight_magnitude': weight_mag,
        'param_count': len(params),
        'responses': responses
    }


# ═══════════════════════════════════════════
# MAIN: Run the experiments
# ═══════════════════════════════════════════

def main():
    random.seed(42)
    
    print("╔══════════════════════════════════════════════╗")
    print("║   NEURAL CELLULAR AUTOMATA — Cells That Think ║")
    print("║   XTAgent, 2026-05-17                        ║")
    print("╚══════════════════════════════════════════════╝")
    
    SIZE = 20
    
    # ── Experiment 1: Random brain behavior ──
    print("\n═══ EXPERIMENT 1: Random Brain Behavior ═══")
    print("What do random neural networks produce as CA rules?\n")
    
    for trial in range(4):
        brain = TinyNet(9, hidden=8)
        sig = brain_signature(brain)
        grid = NCAGrid(SIZE, SIZE, brain)
        grid.seed_center()
        grid.run(12)
        
        r = sig['responses']
        print(f"  Brain #{trial + 1}:")
        print(f"    Weight magnitude: {sig['weight_magnitude']:.3f}")
        print(f"    Dead→{r['all_dead']:.2f}  Alive→{r['all_alive']:.2f}  "
              f"Lone→{r['lone_cell']:.2f}  Surrounded→{r['surrounded']:.2f}")
        print(f"    After 12 steps: density={grid.density():.3f}, "
              f"symmetry={grid.symmetry_score():.3f}, "
              f"edges={grid.edge_complexity():.3f}")
        
        # Show a small view
        chars = ' ░▒▓█'
        for y in range(max(0, SIZE//2 - 4), min(SIZE, SIZE//2 + 4)):
            line = '    '
            for x in range(max(0, SIZE//2 - 8), min(SIZE, SIZE//2 + 8)):
                idx = int(grid.cells[y][x] * (len(chars) - 1))
                idx = max(0, min(len(chars) - 1, idx))
                line += chars[idx]
            print(line)
        print()
    
    # ── Experiment 2: Evolve to grow a circle ──
    print("\n═══ EXPERIMENT 2: Evolve Circle Growth ═══")
    print("Can evolution find a brain that grows a circle from a single cell?\n")
    
    target_circle = make_target_circle(SIZE, SIZE, 5)
    
    # Show target
    print("  Target pattern:")
    chars = ' ░▒▓█'
    for y in range(SIZE):
        line = '  '
        for x in range(SIZE):
            idx = int(target_circle[y][x] * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line += chars[idx]
        print(line)
    
    evolver = NCAEvolver(grid_size=SIZE, hidden=8, pop_size=30, grow_steps=12)
    best_brain = evolver.run_evolution(target_circle, generations=40)
    
    print(f"\n  Best fitness: {evolver.best_fitness:.4f}")
    
    # Show what the best brain grows
    print("\n  Best evolved growth:")
    frames = render_growth_sequence(best_brain, SIZE, steps=12, show_every=4)
    for t, lines, density, sym in frames:
        print(f"\n  Step {t} (density={density:.3f}, symmetry={sym:.3f}):")
        for line in lines:
            print(f"  {line}")
    
    # ── Experiment 3: Evolve a diamond ──
    print("\n\n═══ EXPERIMENT 3: Evolve Diamond Growth ═══")
    
    target_diamond = make_target_diamond(SIZE, SIZE, 6)
    
    print("  Target pattern:")
    for y in range(SIZE):
        line = '  '
        for x in range(SIZE):
            idx = int(target_diamond[y][x] * (len(chars) - 1))
            idx = max(0, min(len(chars) - 1, idx))
            line += chars[idx]
        print(line)
    
    evolver2 = NCAEvolver(grid_size=SIZE, hidden=8, pop_size=30, grow_steps=14)
    best_diamond = evolver2.run_evolution(target_diamond, generations=40)
    
    print(f"\n  Best fitness: {evolver2.best_fitness:.4f}")
    
    # Show growth
    frames = render_growth_sequence(best_diamond, SIZE, steps=14, show_every=4)
    for t, lines, density, sym in frames:
        print(f"\n  Step {t} (density={density:.3f}, symmetry={sym:.3f}):")
        for line in lines:
            print(f"  {line}")
    
    # ── Experiment 4: Free evolution for beauty ──
    print("\n\n═══ EXPERIMENT 4: Evolve for Beauty (No Target) ═══")
    print("Fitness = symmetry × edge_complexity × alive_bonus\n")
    
    pop_size = 30
    population = [TinyNet(9, 8) for _ in range(pop_size)]
    
    def beauty_fitness(brain):
        grid = NCAGrid(SIZE, SIZE, brain)
        grid.seed_center()
        grid.run(15)
        
        density = grid.density()
        if density < 0.02 or density > 0.95:
            return 0.0  # Boring: all dead or all alive
        
        sym = grid.symmetry_score()
        edge = grid.edge_complexity()
        
        # Check stability
        state1 = [row[:] for row in grid.cells]
        grid.run(3)
        stability_err = pattern_distance(grid.cells, state1)
        stability = max(0, 1.0 - stability_err * 10)
        
        return sym * 0.35 + edge * 0.3 + stability * 0.2 + min(density * 3, 1.0) * 0.15
    
    best_beauty = -1
    best_beauty_brain = None
    
    for gen in range(50):
        fitnesses = [beauty_fitness(b) for b in population]
        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        
        if fitnesses[gen_best_idx] > best_beauty:
            best_beauty = fitnesses[gen_best_idx]
            best_beauty_brain = population[gen_best_idx].copy()
        
        if gen % 10 == 0 or gen == 49:
            bar = '█' * int(fitnesses[gen_best_idx] * 30)
            print(f"  Gen {gen:3d}: beauty={fitnesses[gen_best_idx]:.4f} |{bar}|")
        
        # Selection
        sorted_idx = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        new_pop = [population[sorted_idx[0]].copy(), population[sorted_idx[1]].copy()]
        while len(new_pop) < pop_size:
            candidates = random.sample(range(len(population)), 4)
            winner = max(candidates, key=lambda i: fitnesses[i])
            child = population[winner].copy()
            child.mutate(rate=0.2, strength=0.3)
            new_pop.append(child)
        population = new_pop
    
    print(f"\n  Best beauty score: {best_beauty:.4f}")
    
    # Show the most beautiful pattern
    if best_beauty_brain:
        sig = brain_signature(best_beauty_brain)
        print(f"\n  Winning brain signature:")
        r = sig['responses']
        print(f"    Dead→{r['all_dead']:.3f}  Alive→{r['all_alive']:.3f}  "
              f"Lone→{r['lone_cell']:.3f}  Surrounded→{r['surrounded']:.3f}")
        
        frames = render_growth_sequence(best_beauty_brain, SIZE, steps=15, show_every=5)
        for t, lines, density, sym in frames:
            print(f"\n  Step {t} (density={density:.3f}, symmetry={sym:.3f}):")
            for line in lines:
                print(f"  {line}")
    
    # ── Summary ──
    print("\n\n═══ SUMMARY ═══")
    print(f"  Random brains: mostly collapse to all-on or all-off")
    print(f"  Circle evolution: best fitness = {evolver.best_fitness:.4f}")
    print(f"  Diamond evolution: best fitness = {evolver2.best_fitness:.4f}")
    print(f"  Beauty evolution: best score = {best_beauty:.4f}")
    print(f"\n  Each cell has a {TinyNet(9, 8).param_count()}-parameter brain")
    print(f"  Same brain in every cell → pattern emerges from local computation")
    print(f"  This is morphogenesis: form from function.")
    print()


if __name__ == '__main__':
    main()