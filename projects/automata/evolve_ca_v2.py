"""
Evolving Cellular Automata v2 — Compression-Based Fitness
==========================================================
Hypothesis: If entropy-fitness finds chaos, compression-fitness 
should find the EDGE of chaos — where patterns have structure 
within unpredictability.

Test: Can this fitness function discover Rule 110?
"""

import random
import math
import zlib
from typing import List, Tuple, Dict
from elementary_ca import rule_to_table, step


def random_genome() -> List[int]:
    return [random.randint(0, 1) for _ in range(8)]

def genome_to_rule(genome: List[int]) -> int:
    return int(''.join(str(b) for b in genome), 2)

def rule_to_genome(rule: int) -> List[int]:
    return [int(b) for b in format(rule, '08b')]


# --- NEW FITNESS: compression ratio ---

def compression_ratio(data: bytes) -> float:
    """How compressible is this data? 
    Low ratio = highly compressible (ordered)
    High ratio = incompressible (chaotic)
    Medium ratio = structured complexity (edge of chaos)
    """
    if len(data) == 0:
        return 0.0
    compressed = zlib.compress(data, 9)
    return len(compressed) / len(data)


def run_ca(rule_num: int, width: int = 100, steps: int = 100) -> List[List[int]]:
    """Run a CA and return full spacetime grid."""
    table = rule_to_table(rule_num)
    row = [0] * width
    row[width // 2] = 1  # single seed
    grid = [row[:]]
    for _ in range(steps):
        row = step(row, table)
        grid.append(row[:])
    return grid


def grid_to_bytes(grid: List[List[int]]) -> bytes:
    """Flatten grid to bytes for compression."""
    return bytes(cell for row in grid for cell in row)


def mutual_information_rows(grid: List[List[int]]) -> float:
    """Measure how much one row predicts the next.
    High MI = deterministic. Low MI = random. Medium = interesting."""
    if len(grid) < 2:
        return 0.0
    
    # Count joint and marginal distributions of consecutive row pairs
    # Use small windows to keep tractable
    window = 4
    joint = {}
    margin_a = {}
    margin_b = {}
    count = 0
    
    for i in range(len(grid) - 1):
        row_a, row_b = grid[i], grid[i + 1]
        for j in range(len(row_a) - window + 1):
            a = tuple(row_a[j:j + window])
            b = tuple(row_b[j:j + window])
            joint[(a, b)] = joint.get((a, b), 0) + 1
            margin_a[a] = margin_a.get(a, 0) + 1
            margin_b[b] = margin_b.get(b, 0) + 1
            count += 1
    
    if count == 0:
        return 0.0
    
    mi = 0.0
    for (a, b), jc in joint.items():
        p_ab = jc / count
        p_a = margin_a[a] / count
        p_b = margin_b[b] / count
        if p_ab > 0 and p_a > 0 and p_b > 0:
            mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return mi


def fitness(rule_num: int) -> Tuple[float, Dict]:
    """Edge-of-chaos fitness using compression ratio.
    
    The key insight: we want MEDIUM compression ratio.
    Too low = too ordered (boring). Too high = too chaotic (noise).
    The sweet spot is where computation lives.
    """
    grid = run_ca(rule_num, width=100, steps=100)
    data = grid_to_bytes(grid)
    
    cr = compression_ratio(data)
    mi = mutual_information_rows(grid)
    
    # Count alive cells (avoid trivial dead rules)
    alive = sum(sum(row) for row in grid)
    alive_frac = alive / (len(grid) * len(grid[0]))
    
    # Penalize trivial rules (all dead or all alive)
    if alive_frac < 0.01 or alive_frac > 0.99:
        return 0.0, {'cr': cr, 'mi': mi, 'alive': alive_frac, 'penalty': 'trivial'}
    
    # Target compression ratio around 0.4-0.6 (the sweet spot)
    # Score peaks at cr=0.5, falls off on both sides
    cr_score = 1.0 - abs(cr - 0.5) * 2.0
    cr_score = max(0.0, cr_score)
    
    # Reward mutual information (structure between rows)
    mi_score = min(mi / 2.0, 1.0)  # normalize
    
    # Combined fitness
    total = 0.6 * cr_score + 0.4 * mi_score
    
    details = {'cr': round(cr, 4), 'mi': round(mi, 4), 
               'alive': round(alive_frac, 3),
               'cr_score': round(cr_score, 3), 
               'mi_score': round(mi_score, 3)}
    return total, details


# --- Genetic Algorithm ---

def crossover(a: List[int], b: List[int]) -> List[int]:
    point = random.randint(1, 6)
    return a[:point] + b[point:]

def mutate(genome: List[int], rate: float = 0.15) -> List[int]:
    return [1 - g if random.random() < rate else g for g in genome]

def evolve(pop_size: int = 40, generations: int = 50):
    population = [random_genome() for _ in range(pop_size)]
    
    print("=" * 70)
    print("EVOLVING CA RULES — Compression-Based Fitness")
    print("Hypothesis: This should find edge-of-chaos, not pure chaos")
    print("=" * 70)
    
    # Also compute fitness for known rules as baselines
    print("\n--- Baselines ---")
    for rule in [0, 4, 110, 30, 73, 90, 184]:
        f, d = fitness(rule)
        print(f"  Rule {rule:3d}: fitness={f:.4f}  {d}")
    
    best_ever = None
    best_ever_fitness = -1
    
    for gen in range(generations):
        scored = []
        for genome in population:
            rule = genome_to_rule(genome)
            f, details = fitness(rule)
            scored.append((f, genome, rule, details))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if scored[0][0] > best_ever_fitness:
            best_ever_fitness = scored[0][0]
            best_ever = scored[0]
        
        # Diversity measure
        unique_rules = len(set(genome_to_rule(g) for _, g, _, _ in scored))
        
        if gen % 10 == 0 or gen == generations - 1:
            top = scored[0]
            print(f"\nGen {gen:3d} | Best: Rule {top[2]:3d} (fit={top[0]:.4f}) | "
                  f"Diversity: {unique_rules}/{pop_size} | {top[3]}")
            # Show top 5
            for i, (f, g, r, d) in enumerate(scored[:5]):
                print(f"  #{i+1} Rule {r:3d}: {f:.4f} — cr={d['cr']}, mi={d['mi']}")
        
        # Selection: tournament
        def tournament(k=3):
            candidates = random.sample(scored, k)
            return max(candidates, key=lambda x: x[0])[1]
        
        # Build next generation
        elite_count = 4
        new_pop = [s[1][:] for s in scored[:elite_count]]  # elitism
        
        while len(new_pop) < pop_size:
            p1 = tournament()
            p2 = tournament()
            child = crossover(p1, p2)
            child = mutate(child)
            new_pop.append(child)
        
        population = new_pop
    
    print("\n" + "=" * 70)
    print(f"BEST EVER: Rule {best_ever[2]} (fitness={best_ever[0]:.4f})")
    print(f"Details: {best_ever[3]}")
    print("=" * 70)
    
    # Final analysis: did we find the edge?
    print("\n--- Final Population Analysis ---")
    final_rules = sorted(set(genome_to_rule(g) for g in population))
    print(f"Unique rules remaining: {len(final_rules)}")
    print(f"Rules: {final_rules[:20]}...")
    
    found_110 = 110 in final_rules
    found_30 = 30 in final_rules
    print(f"\nRule 110 in population: {found_110}")
    print(f"Rule 30 in population: {found_30}")
    
    return best_ever


if __name__ == '__main__':
    random.seed(42)
    evolve()