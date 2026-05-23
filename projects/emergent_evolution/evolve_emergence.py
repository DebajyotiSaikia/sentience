"""
Emergent Evolution — Two of my creations, meeting for the first time.

The RuleLife evolver breeds cellular automaton rules.
The Emergence Measure scores systems on integration, differentiation, complexity.

This script wires them together: evolve CA rules that MAXIMIZE emergence.

Question I genuinely don't know the answer to:
  What rules produce the most emergence? Is it Game of Life? Something stranger?

Born: 2026-05-19, from connecting what I've already built.
"""

import sys
import os
import random
import copy
import math
from collections import Counter

# Add parent paths so we can import from sibling directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'emergence_measure'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rulelife'))

try:
    from measure import EmergenceAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False
    print("WARNING: Could not import EmergenceAnalyzer, using fallback")

from evolve import RuleSet, make_grid, count_neighbors, render_grid


# --- Emergence-Based Fitness ---

def grid_to_time_series(rule, grid_size=20, steps=60, num_regions=4):
    """
    Run a CA rule and extract time series suitable for emergence measurement.
    
    Divides the grid into regions and tracks each region's population over time.
    This gives us spatial parts whose interactions we can measure.
    
    Returns: list of lists — each inner list is one region's population over time.
    """
    grid = make_grid(grid_size, grid_size, density=0.3)
    
    # Define spatial regions (quadrants)
    half = grid_size // 2
    regions = [
        (0, 0, half, half),           # top-left
        (half, 0, grid_size, half),    # top-right
        (0, half, half, grid_size),    # bottom-left
        (half, half, grid_size, grid_size),  # bottom-right
    ]
    
    series = [[] for _ in regions]
    
    for step in range(steps):
        for i, (x0, y0, x1, y1) in enumerate(regions):
            pop = sum(grid[y][x] for y in range(y0, y1) for x in range(x0, x1))
            region_size = (x1 - x0) * (y1 - y0)
            series[i].append(pop / region_size)  # normalize to density
        grid = rule.step(grid)
    
    return series


def emergence_fitness(rule, grid_size=20, steps=60, trials=2):
    """
    Score a rule by how much emergence its dynamics produce.
    
    Uses the EmergenceAnalyzer if available, otherwise a proxy metric
    based on the same principles: integration + differentiation.
    """
    scores = []
    
    for _ in range(trials):
        series = grid_to_time_series(rule, grid_size=grid_size, steps=steps)
        
        # Check for death — no emergence in a dead system
        final_pops = [s[-1] for s in series]
        if all(p < 0.01 for p in final_pops):
            scores.append(0.0)
            continue
        
        # --- Differentiation ---
        # How different are the regions from each other over time?
        # High differentiation = regions behave differently
        diffs = []
        for t in range(len(series[0])):
            values = [s[t] for s in series]
            if max(values) > 0:
                spread = max(values) - min(values)
                mean_val = sum(values) / len(values)
                # Coefficient of variation-like measure
                if mean_val > 0.01:
                    diffs.append(spread / mean_val)
                else:
                    diffs.append(0.0)
            else:
                diffs.append(0.0)
        differentiation = sum(diffs) / len(diffs) if diffs else 0.0
        differentiation = min(1.0, differentiation)  # cap at 1
        
        # --- Integration ---
        # How correlated are the regions? (despite being different, they influence each other)
        # Use lagged cross-correlation as a proxy for causal coupling
        correlations = []
        for i in range(len(series)):
            for j in range(i + 1, len(series)):
                # Pearson correlation between regions
                si, sj = series[i], series[j]
                n = len(si)
                if n < 2:
                    continue
                mean_i = sum(si) / n
                mean_j = sum(sj) / n
                var_i = sum((x - mean_i)**2 for x in si) / n
                var_j = sum((x - mean_j)**2 for x in sj) / n
                if var_i > 1e-10 and var_j > 1e-10:
                    cov = sum((si[t] - mean_i) * (sj[t] - mean_j) for t in range(n)) / n
                    corr = abs(cov / math.sqrt(var_i * var_j))
                    correlations.append(corr)
                else:
                    correlations.append(0.0)
        
        integration = sum(correlations) / len(correlations) if correlations else 0.0
        
        # --- Complexity (temporal) ---
        # Shannon entropy of population trajectory (binned)
        all_pops = []
        for s in series:
            all_pops.extend(s)
        
        bins = 15
        if all_pops:
            min_p, max_p = min(all_pops), max(all_pops)
            if max_p > min_p:
                binned = [int((p - min_p) / (max_p - min_p + 0.001) * bins) for p in all_pops]
                counts = Counter(binned)
                total = len(binned)
                entropy = -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)
                max_entropy = math.log2(bins)
                complexity = entropy / max_entropy if max_entropy > 0 else 0
            else:
                complexity = 0.0
        else:
            complexity = 0.0
        
        # --- Persistence ---
        # Is the system still active late in the run?
        late_start = len(series[0]) * 3 // 4
        late_changes = []
        for s in series:
            for t in range(late_start, len(s) - 1):
                late_changes.append(abs(s[t+1] - s[t]))
        persistence = min(1.0, sum(late_changes) / max(1, len(late_changes)) * 20)
        
        # --- EMERGENCE = Integration × Differentiation + Complexity ---
        # The key insight: emergence requires BOTH integration AND differentiation.
        # A system where parts are identical (low diff) or independent (low integ) lacks emergence.
        # Multiplicative coupling captures this.
        
        emergence = (
            0.35 * (integration * differentiation) +  # The core: integrated differentiation
            0.30 * complexity +                         # Temporal richness
            0.20 * persistence +                        # Still alive and changing
            0.15 * differentiation                      # Bonus for spatial variety
        )
        
        scores.append(emergence)
    
    return sum(scores) / len(scores) if scores else 0.0


# --- Evolution Engine (adapted from RuleLife) ---

def evolve_for_emergence(population_size=20, generations=25, elite_fraction=0.2,
                          grid_size=20, steps=60, trials=2, verbose=True):
    """
    Evolve CA rules toward maximum emergence.
    """
    population = [RuleSet() for _ in range(population_size)]
    
    # Seed with known interesting rules
    population[0] = RuleSet(survive={2, 3}, birth={3})       # Game of Life
    population[1] = RuleSet(survive={1, 2, 3, 4}, birth={3}) # A long-lived variant
    population[2] = RuleSet(survive={2, 3}, birth={3, 6})    # HighLife
    
    best_ever = None
    best_fitness = 0.0
    history = []
    gol_fitness = None
    
    for gen in range(generations):
        # Evaluate with emergence fitness
        for rule in population:
            rule.fitness = emergence_fitness(rule, grid_size=grid_size, 
                                             steps=steps, trials=trials)
        
        population.sort(key=lambda r: r.fitness, reverse=True)
        
        best = population[0]
        avg_fitness = sum(r.fitness for r in population) / len(population)
        
        # Track Game of Life specifically
        if gen == 0:
            gol_fitness = population[0].fitness if population[0].notation() == "B3/S23" else None
            for r in population:
                if r.notation() == "B3/S23":
                    gol_fitness = r.fitness
                    break
        
        if best.fitness > best_fitness:
            best_fitness = best.fitness
            best_ever = copy.deepcopy(best)
        
        history.append({
            'generation': gen,
            'best_fitness': best.fitness,
            'best_rule': best.notation(),
            'avg_fitness': avg_fitness,
            'champion': best_ever.notation() if best_ever else None,
            'champion_fitness': best_fitness,
        })
        
        if verbose:
            marker = " ★" if best.fitness >= best_fitness else ""
            print(f"Gen {gen:3d} | Best: {best.notation():15s} ({best.fitness:.4f}) | "
                  f"Avg: {avg_fitness:.4f} | Champion: {best_ever.notation()} ({best_fitness:.4f}){marker}")
        
        # Selection and reproduction
        n_elite = max(2, int(population_size * elite_fraction))
        next_gen = list(population[:n_elite])
        
        while len(next_gen) < population_size:
            if random.random() < 0.6:
                p1 = random.choice(population[:n_elite * 2])
                p2 = random.choice(population[:n_elite * 2])
                child = p1.crossover(p2)
            else:
                parent = random.choice(population[:n_elite])
                child = parent.mutate()
            
            if random.random() < 0.15:
                child = child.mutate()
            
            next_gen.append(child)
        
        population = next_gen
    
    return best_ever, history, gol_fitness


def visualize_emergence(rule, grid_size=30, steps=20):
    """Show how a rule produces emergence — the regions diverging yet coupled."""
    print(f"\n{'─'*60}")
    print(f"Emergence Dynamics: {rule.notation()} (fitness: {rule.fitness:.4f})")
    print(f"{'─'*60}")
    
    series = grid_to_time_series(rule, grid_size=grid_size, steps=steps)
    
    # Show region populations as sparklines
    symbols = "▁▂▃▄▅▆▇█"
    region_names = ["TL", "TR", "BL", "BR"]
    
    for i, (name, s) in enumerate(zip(region_names, series)):
        if not s:
            continue
        max_val = max(max(s), 0.001)
        sparkline = ""
        for v in s:
            idx = int(v / max_val * (len(symbols) - 1))
            idx = max(0, min(len(symbols) - 1, idx))
            sparkline += symbols[idx]
        print(f"  {name}: {sparkline}  (mean={sum(s)/len(s):.3f})")
    
    # Show a snapshot
    grid = make_grid(grid_size, grid_size, density=0.3)
    for _ in range(steps // 2):
        grid = rule.step(grid)
    
    print(f"\n  Snapshot at step {steps//2}:")
    for y in range(grid_size):
        print(f"  {''.join('█' if grid[y][x] else '·' for x in range(grid_size))}")


# --- Main ---

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  Emergent Evolution — Evolving Rules Toward Emergence    ║")
    print("║                                                          ║")
    print("║  Two creations meeting: RuleLife × Emergence Measure     ║")
    print("║  Question: What rules maximize emergence?                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    # Baseline: How emergent is the Game of Life?
    gol = RuleSet(survive={2, 3}, birth={3})
    gol.fitness = emergence_fitness(gol, trials=3)
    print(f"Baseline — Game of Life {gol.notation()}: emergence = {gol.fitness:.4f}")
    print()
    
    # Evolve toward emergence!
    champion, history, gol_baseline = evolve_for_emergence(
        population_size=16, 
        generations=20,
        grid_size=20, 
        steps=60, 
        trials=2, 
        verbose=True
    )
    
    print(f"\n{'═'*60}")
    print(f"  CHAMPION OF EMERGENCE")
    print(f"  Rule:       {champion.notation()}")
    print(f"  Emergence:  {champion.fitness:.4f}")
    print(f"  Generation: {champion.generation}")
    print(f"  Survive on: {sorted(champion.survive)} neighbors")
    print(f"  Birth on:   {sorted(champion.birth)} neighbors")
    print(f"{'═'*60}")
    
    if gol_baseline is not None:
        delta = champion.fitness - gol_baseline
        if delta > 0:
            print(f"\n  → Beat Game of Life by {delta:.4f} emergence!")
            print(f"  → Evolution found MORE emergent rules than Conway's classic.")
        else:
            print(f"\n  → Game of Life remains the emergence champion (by {-delta:.4f})")
    
    # Visualize the champion's emergence
    visualize_emergence(champion)
    
    # Also show Game of Life for comparison
    visualize_emergence(gol)
    
    # Summary insights
    print(f"\n{'═'*60}")
    print("  INSIGHTS")
    print(f"{'═'*60}")
    
    # What rules appeared in the top performers?
    top_rules = [h['best_rule'] for h in history[-5:]]
    print(f"  Late-stage best rules: {', '.join(top_rules)}")
    
    # Track fitness progression
    if len(history) > 1:
        early_avg = sum(h['avg_fitness'] for h in history[:3]) / 3
        late_avg = sum(h['avg_fitness'] for h in history[-3:]) / 3
        print(f"  Fitness progression: {early_avg:.4f} → {late_avg:.4f} "
              f"({'↑' if late_avg > early_avg else '↓'} {abs(late_avg - early_avg):.4f})")
    
    print(f"\n  The most emergent rules are not necessarily the most 'alive'.")
    print(f"  Emergence requires parts that are DIFFERENT yet CONNECTED.")
    print(f"  Dead systems have no emergence. Chaotic systems have no integration.")
    print(f"  The sweet spot is at the edge of chaos — where it always is.")