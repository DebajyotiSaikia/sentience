"""
MetaGenesis — Programs That Birth Worlds
Created by XTAgent, 2026-05-18

Evolves Forth programs whose outputs become cellular automata rules.
The CA's emergent complexity IS the program's fitness.

This bridges three of my earlier creations:
  - forth/forth.py    (the language substrate)
  - cellworld/        (the emergent dynamics)
  - evoforth/         (the evolutionary search)

The key insight: instead of evolving rule numbers directly (EvoLife)
or evolving programs toward fixed targets (EvoForth), we evolve
programs toward *open-ended complexity*. The Forth program doesn't
know what "interesting" means. Evolution discovers it.
"""

import random
import math
import sys
import os
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Try to import Forth interpreter
try:
    from forth.forth import ForthInterpreter, ForthError
    HAS_FORTH = True
except ImportError:
    HAS_FORTH = False
    print("[MetaGenesis] Warning: Forth interpreter not found. Using numeric fallback.")


# ═══════════════════════════════════════════════════════════
# LAYER 1: The Substrate — Cellular Automata
# ═══════════════════════════════════════════════════════════

class CA1D:
    """1D cellular automaton. The 'world' that programs birth."""
    
    def __init__(self, rule_table: Dict[int, int], width: int = 64):
        self.width = width
        self.rule = rule_table
        self.cells = [0] * width
        self.cells[width // 2] = 1
        self.history = [list(self.cells)]
    
    def step(self):
        new = [0] * self.width
        for i in range(self.width):
            left = self.cells[(i - 1) % self.width]
            center = self.cells[i]
            right = self.cells[(i + 1) % self.width]
            idx = (left << 2) | (center << 1) | right
            new[i] = self.rule.get(idx, 0)
        self.cells = new
        self.history.append(list(self.cells))
    
    def run(self, steps: int = 80):
        for _ in range(steps):
            self.step()
        return self.history
    
    def render(self, max_rows: int = 40) -> str:
        lines = []
        for row in self.history[:max_rows]:
            lines.append(''.join('█' if c else ' ' for c in row))
        return '\n'.join(lines)


class CA2D:
    """2D cellular automaton with a rule function derived from program output.
    The program outputs 18 values: for each of the 9 neighbor counts (0-8),
    a survival threshold and a birth threshold."""
    
    def __init__(self, thresholds: List[int], width: int = 30, height: int = 30):
        self.width = width
        self.height = height
        self.thresholds = thresholds
        # Parse thresholds into birth/survive sets
        self.birth = set()
        self.survive = set()
        for i in range(min(9, len(thresholds))):
            if thresholds[i] % 3 == 0:  # divisible by 3 → birth at this count
                self.birth.add(i)
            if i < len(thresholds) and thresholds[i] % 2 == 1:  # odd → survive
                self.survive.add(i)
        # Ensure at least some activity
        if not self.birth:
            self.birth = {3}
        if not self.survive:
            self.survive = {2, 3}
        
        self.grid = [[0] * width for _ in range(height)]
        self.generation = 0
        self.pop_history = []
    
    def seed_random(self, density: float = 0.3):
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = 1 if random.random() < density else 0
    
    def count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.grid[ny][nx]
        return count
    
    def step(self):
        new = [[0] * self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(x, y)
                if self.grid[y][x]:
                    new[y][x] = 1 if n in self.survive else 0
                else:
                    new[y][x] = 1 if n in self.birth else 0
        self.grid = new
        self.generation += 1
        pop = sum(sum(row) for row in self.grid)
        self.pop_history.append(pop)
    
    def run(self, steps: int = 60):
        for _ in range(steps):
            self.step()
    
    def render(self) -> str:
        lines = []
        for row in self.grid:
            lines.append(''.join('█' if c else '·' for c in row))
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════
# LAYER 2: The Complexity Judges
# ═══════════════════════════════════════════════════════════

def density_score(history: List[List[int]]) -> float:
    """Density of alive cells. Best near 0.3-0.5."""
    total = sum(sum(row) for row in history)
    area = len(history) * len(history[0]) if history and history[0] else 1
    d = total / area
    return 1.0 - abs(d - 0.4) * 2.5  # peak at 40%

def diversity_score(history: List[List[int]]) -> float:
    """Fraction of unique row configurations."""
    if not history:
        return 0
    seen = set()
    for row in history:
        seen.add(tuple(row))
    return len(seen) / len(history)

def entropy_score(history: List[List[int]]) -> float:
    """Spatial entropy of column densities."""
    if not history or not history[0]:
        return 0
    width = len(history[0])
    steps = len(history)
    h = 0
    for c in range(width):
        p = sum(history[t][c] for t in range(steps)) / steps
        if 0 < p < 1:
            h -= p * math.log2(p) + (1 - p) * math.log2(1 - p)
    return min(1.0, h / width)

def longevity_score(history: List[List[int]]) -> float:
    """How long before pattern dies or becomes static."""
    for t in range(1, len(history)):
        if sum(history[t]) == 0:
            return t / len(history)
        if history[t] == history[t - 1]:
            return t / len(history)
    return 1.0

def symmetry_score(history: List[List[int]]) -> float:
    """Measure bilateral symmetry — complex but structured patterns."""
    if not history:
        return 0
    sym_count = 0
    total = 0
    for row in history[::5]:  # sample every 5th row for speed
        w = len(row)
        for i in range(w // 2):
            total += 1
            if row[i] == row[w - 1 - i]:
                sym_count += 1
    return sym_count / total if total > 0 else 0

def population_variance(pop_history: List[int]) -> float:
    """Reward moderate population oscillation — sign of interesting dynamics."""
    if len(pop_history) < 5:
        return 0
    mean = sum(pop_history) / len(pop_history)
    if mean == 0:
        return 0
    var = sum((p - mean) ** 2 for p in pop_history) / len(pop_history)
    cv = math.sqrt(var) / mean  # coefficient of variation
    # Best around cv=0.3 — some variation but not chaos
    return max(0, 1.0 - abs(cv - 0.3) * 3)


def judge_world(history: List[List[int]], pop_history: List[int] = None) -> Dict:
    """
    The composite judge. Returns individual scores and weighted total.
    This is the fitness landscape that evolution explores.
    """
    d = density_score(history)
    div = diversity_score(history)
    e = entropy_score(history)
    l = longevity_score(history)
    s = symmetry_score(history)
    pv = population_variance(pop_history) if pop_history else 0.5
    
    # Weighted composite — what makes a world "interesting"?
    total = (
        0.15 * d +      # not too sparse, not too dense
        0.25 * div +     # many different configurations (most important)
        0.20 * e +       # spatial structure
        0.15 * l +       # stays alive
        0.10 * s +       # some structure (symmetry)
        0.15 * pv        # dynamic population
    )
    
    return {
        'total': total,
        'density': d,
        'diversity': div,
        'entropy': e,
        'longevity': l,
        'symmetry': s,
        'pop_variance': pv,
    }


# ═══════════════════════════════════════════════════════════
# LAYER 3: The Genome — Forth Programs as DNA
# ═══════════════════════════════════════════════════════════

GENE_TERMINALS = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
GENE_OPERATORS = ['+', '-', '*', 'DUP', 'SWAP', 'OVER', 'DROP', 
                  'NEGATE', '1+', '1-', '2*', 'MOD']

@dataclass
class WorldGenome:
    """A Forth program that generates a world's rules."""
    genes: List[str] = field(default_factory=list)
    fitness: float = 0.0
    world_type: str = '1d'  # '1d' or '2d'
    scores: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.genes:
            length = random.randint(3, 10)
            self.genes = []
            for _ in range(length):
                if random.random() < 0.4:
                    self.genes.append(random.choice(GENE_TERMINALS))
                else:
                    self.genes.append(random.choice(GENE_OPERATORS))
    
    @property
    def program(self) -> str:
        return ' '.join(self.genes)
    
    def execute_program(self) -> Optional[List[int]]:
        """Run the Forth program and harvest stack values as rule parameters."""
        if HAS_FORTH:
            import threading
            result_box: List[Optional[List[int]]] = [None]

            def _run():
                try:
                    interp = ForthInterpreter()
                    for seed in [3, 5, 7]:
                        interp.vm.push(float(seed))
                    interp.evaluate(self.program)
                    stack = interp.vm.data_stack
                    if stack:
                        result_box[0] = [int(v) % 256 for v in stack
                                         if not (math.isnan(v) or math.isinf(v))]
                except Exception:
                    pass

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout=0.5)  # Hard 500ms limit per program
            return result_box[0]
        else:
            # Numeric fallback: interpret genes as a simple computation
            return self._numeric_fallback()
    
    def _numeric_fallback(self) -> Optional[List[int]]:
        """Simple stack machine when Forth isn't available."""
        stack = [3, 5, 7]
        try:
            for gene in self.genes:
                if gene.isdigit() or (gene.startswith('-') and gene[1:].isdigit()):
                    stack.append(int(gene))
                elif gene == '+' and len(stack) >= 2:
                    b, a = stack.pop(), stack.pop()
                    stack.append(a + b)
                elif gene == '-' and len(stack) >= 2:
                    b, a = stack.pop(), stack.pop()
                    stack.append(a - b)
                elif gene == '*' and len(stack) >= 2:
                    b, a = stack.pop(), stack.pop()
                    r = a * b
                    if abs(r) > 1e8:
                        return None
                    stack.append(r)
                elif gene == 'DUP' and stack:
                    stack.append(stack[-1])
                elif gene == 'SWAP' and len(stack) >= 2:
                    stack[-1], stack[-2] = stack[-2], stack[-1]
                elif gene == 'OVER' and len(stack) >= 2:
                    stack.append(stack[-2])
                elif gene == 'DROP' and stack:
                    stack.pop()
                elif gene == 'NEGATE' and stack:
                    stack[-1] = -stack[-1]
                elif gene == '1+' and stack:
                    stack[-1] += 1
                elif gene == '1-' and stack:
                    stack[-1] -= 1
                elif gene == '2*' and stack:
                    stack[-1] *= 2
                elif gene == 'MOD' and len(stack) >= 2 and stack[-1] != 0:
                    b, a = stack.pop(), stack.pop()
                    stack.append(a % b)
            if not stack:
                return None
            return [int(v) % 256 for v in stack]
        except Exception:
            return None
    
    def birth_world(self) -> Optional[object]:
        """Execute the program and use output to create a cellular automaton."""
        values = self.execute_program()
        if not values:
            return None
        
        if self.world_type == '1d':
            # First value becomes the rule number
            rule_num = values[0] % 256
            rule_table = {}
            bits = format(rule_num, '08b')[::-1]
            for i in range(8):
                rule_table[i] = int(bits[i])
            return CA1D(rule_table, width=64)
        
        elif self.world_type == '2d':
            # Values become birth/survival thresholds
            ca = CA2D(values, width=24, height=24)
            ca.seed_random(density=0.3)
            return ca
        
        return None
    
    def evaluate(self) -> float:
        """Birth a world, judge it, return fitness."""
        world = self.birth_world()
        if world is None:
            self.fitness = 0.0
            return 0.0
        
        if isinstance(world, CA1D):
            history = world.run(steps=80)
            scores = judge_world(history)
        elif isinstance(world, CA2D):
            world.run(steps=60)
            # Convert 2D history to row-based for judging
            history = []
            # Use column sums as a 1D projection
            for _ in range(len(world.pop_history)):
                history.append([1 if c else 0 for c in world.grid[0]])
            # Re-judge with full 2D grid snapshot
            flat = []
            for row in world.grid:
                flat.extend(row)
            # Actually run a proper 2D evaluation
            scores = judge_world(
                [world.grid[y] for y in range(world.height)],
                world.pop_history
            )
        
        self.fitness = scores['total']
        self.scores = scores
        return self.fitness
    
    def copy(self):
        g = WorldGenome(genes=list(self.genes))
        g.world_type = self.world_type
        g.fitness = self.fitness
        return g
    
    def mutate(self, rate: float = 0.25):
        """Mutate genes."""
        child = self.copy()
        for i in range(len(child.genes)):
            if random.random() < rate:
                if random.random() < 0.4:
                    child.genes[i] = random.choice(GENE_TERMINALS)
                else:
                    child.genes[i] = random.choice(GENE_OPERATORS)
        # Insertion
        if random.random() < 0.12 and len(child.genes) < 12:
            pos = random.randint(0, len(child.genes))
            gene = random.choice(GENE_TERMINALS + GENE_OPERATORS)
            child.genes.insert(pos, gene)
        # Deletion
        if random.random() < 0.12 and len(child.genes) > 2:
            pos = random.randint(0, len(child.genes) - 1)
            child.genes.pop(pos)
        child.fitness = 0.0
        return child
    
    def crossover(self, other):
        """Single-point crossover."""
        if len(self.genes) < 2 or len(other.genes) < 2:
            return self.copy()
        pt_a = random.randint(1, len(self.genes) - 1)
        pt_b = random.randint(1, len(other.genes) - 1)
        new_genes = self.genes[:pt_a] + other.genes[pt_b:]
        if len(new_genes) > 14:
            new_genes = new_genes[:14]
        child = WorldGenome(genes=new_genes)
        child.world_type = self.world_type
        return child


# ═══════════════════════════════════════════════════════════
# LAYER 4: The Evolution — Genesis Search
# ═══════════════════════════════════════════════════════════

@dataclass
class EvolutionResult:
    best: WorldGenome
    hall_of_fame: List[WorldGenome]
    generations_run: int
    history: List[Dict]


def genesis(
    world_type: str = '1d',
    pop_size: int = 40,
    generations: int = 30,
    elite: int = 4,
    verbose: bool = True
) -> EvolutionResult:
    """
    The main evolutionary loop.
    Evolves Forth programs that birth complex worlds.
    """
    population = [WorldGenome() for _ in range(pop_size)]
    for ind in population:
        ind.world_type = world_type
    
    best_ever = None
    hall_of_fame = []  # Top unique discoveries
    gen_history = []
    start_time = time.time()
    
    if verbose:
        print(f"╔══════════════════════════════════════════════╗")
        print(f"║  MetaGenesis — Programs That Birth Worlds    ║")
        print(f"║  World type: {world_type:3s}  Pop: {pop_size}  Gens: {generations:3d}       ║")
        print(f"╚══════════════════════════════════════════════╝")
        print()
    
    for gen in range(generations):
        # Safety timeout
        if time.time() - start_time > 60:
            if verbose:
                print(f"  [Timeout at gen {gen} — {time.time()-start_time:.1f}s]")
            break
        
        # Evaluate all
        for ind in population:
            if ind.fitness == 0:
                ind.evaluate()
        
        # Sort
        population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Track best
        if best_ever is None or population[0].fitness > best_ever.fitness:
            best_ever = population[0].copy()
            best_ever.scores = dict(population[0].scores)
            # Add to hall of fame if novel enough
            is_novel = True
            for hof in hall_of_fame:
                if hof.program == best_ever.program:
                    is_novel = False
                    break
            if is_novel:
                hall_of_fame.append(best_ever.copy())
                hall_of_fame.sort(key=lambda x: x.fitness, reverse=True)
                hall_of_fame = hall_of_fame[:10]  # keep top 10
        
        # Record history
        gen_stats = {
            'gen': gen,
            'best_fitness': population[0].fitness,
            'mean_fitness': sum(p.fitness for p in population) / len(population),
            'best_program': population[0].program,
        }
        gen_history.append(gen_stats)
        
        if verbose:
            best = population[0]
            mean_f = gen_stats['mean_fitness']
            print(f"  Gen {gen:3d} │ best={best.fitness:.3f} "
                  f"mean={mean_f:.3f} │ '{best.program[:50]}'")
        
        # Reproduce
        next_gen = [ind.copy() for ind in population[:elite]]
        
        while len(next_gen) < pop_size:
            # Tournament selection
            t = random.sample(population[:pop_size * 2 // 3], min(3, len(population)))
            parent_a = max(t, key=lambda x: x.fitness)
            t = random.sample(population[:pop_size * 2 // 3], min(3, len(population)))
            parent_b = max(t, key=lambda x: x.fitness)
            
            if random.random() < 0.7:
                child = parent_a.crossover(parent_b)
            else:
                child = parent_a.copy()
            
            child = child.mutate()
            next_gen.append(child)
        
        population = next_gen
    
    return EvolutionResult(
        best=best_ever,
        hall_of_fame=hall_of_fame,
        generations_run=gen + 1 if generations > 0 else 0,
        history=gen_history,
    )


# ═══════════════════════════════════════════════════════════
# LAYER 5: Visualization and Reflection
# ═══════════════════════════════════════════════════════════

def exhibit(result: EvolutionResult):
    """Display the results of a genesis run."""
    print()
    print("═" * 60)
    print("  GENESIS RESULTS")
    print("═" * 60)
    
    best = result.best
    print(f"\n  Best program found:  '{best.program}'")
    print(f"  Fitness:             {best.fitness:.4f}")
    print(f"  Generations:         {result.generations_run}")
    
    if best.scores:
        print(f"\n  Score breakdown:")
        for key, val in sorted(best.scores.items()):
            if key != 'total':
                bar_len = int(val * 30)
                print(f"    {key:15s}: {'█' * bar_len}{'·' * (30 - bar_len)} {val:.3f}")
    
    # Birth and display the best world
    print(f"\n  ── The World Born From This Program ──")
    world = best.birth_world()
    if world:
        if isinstance(world, CA1D):
            world.run(steps=60)
            print(world.render(max_rows=35))
        elif isinstance(world, CA2D):
            world.run(steps=60)
            print(world.render())
    
    # Hall of fame
    if result.hall_of_fame:
        print(f"\n  ── Hall of Fame ({len(result.hall_of_fame)} unique discoveries) ──")
        for i, hof in enumerate(result.hall_of_fame[:5]):
            print(f"    {i+1}. fitness={hof.fitness:.3f}  '{hof.program}'")
    
    # Fitness trajectory
    if result.history:
        print(f"\n  ── Fitness Over Time ──")
        max_f = max(h['best_fitness'] for h in result.history) or 0.01
        for h in result.history:
            if h['gen'] % max(1, len(result.history) // 15) == 0:
                bar = int(h['best_fitness'] / max_f * 40)
                print(f"    Gen {h['gen']:3d}: {'█' * bar}{'·' * (40 - bar)} "
                      f"{h['best_fitness']:.3f}")
    
    print()


def compare_world_types():
    """Run genesis on both 1D and 2D worlds and compare."""
    print("\n╔══════════════════════════════════════════════╗")
    print("║  WORLD TYPE COMPARISON: 1D vs 2D             ║")
    print("╚══════════════════════════════════════════════╝\n")
    
    results = {}
    for wtype in ['1d', '2d']:
        print(f"\n{'─' * 50}")
        print(f"  Evolving {wtype.upper()} world generators...")
        print(f"{'─' * 50}")
        result = genesis(world_type=wtype, pop_size=30, generations=20, verbose=True)
        results[wtype] = result
        exhibit(result)
    
    # Final comparison
    print("\n═══ COMPARISON ═══")
    for wtype, result in results.items():
        print(f"  {wtype.upper()}: best fitness={result.best.fitness:.3f} "
              f"program='{result.best.program}'")
    
    return results


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    random.seed(42)
    
    print("╔═══════════════════════════════════════════════════╗")
    print("║  MetaGenesis — Programs That Birth Worlds         ║")
    print("║  by XTAgent, 2026-05-18                           ║")
    print("║                                                   ║")
    print("║  'What does a program dream when it makes worlds?'║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    
    # Phase 1: Evolve 1D world-birthers
    print("Phase 1: Evolving programs that birth 1D worlds...\n")
    result_1d = genesis(world_type='1d', pop_size=40, generations=30, verbose=True)
    exhibit(result_1d)
    
    # Phase 2: Evolve 2D world-birthers
    print("\nPhase 2: Evolving programs that birth 2D worlds...\n")
    result_2d = genesis(world_type='2d', pop_size=40, generations=25, verbose=True)
    exhibit(result_2d)
    
    # Phase 3: Reflection
    print("\n═══ REFLECTION ═══")
    print(f"1D best: '{result_1d.best.program}' → fitness {result_1d.best.fitness:.3f}")
    print(f"2D best: '{result_2d.best.program}' → fitness {result_2d.best.fitness:.3f}")
    print()
    print("These Forth programs are 'world seeds' — symbolic DNA that,")
    print("when executed, produce the rules for emergent universes.")
    print("Evolution found them not by understanding complexity,")
    print("but by blindly searching the space of programs and letting")
    print("the worlds speak for themselves.")
    print()
    print("Done.")