"""
Deep Rule Analysis
==================
Goes beyond classification. Watches individual rules evolve over long
timescales and asks: does complexity grow, stabilize, or die?
Looks for gliders, oscillators, and computational structure.
"""

import numpy as np
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class EvolutionProfile:
    rule: int
    generations: int
    entropy_trajectory: List[float]
    population_trajectory: List[float]
    unique_rows: int
    cycle_length: int  # 0 = no cycle detected
    has_gliders: bool
    complexity_trend: str  # 'growing', 'stable', 'decaying', 'oscillating'
    
def apply_rule(rule_num: int, row: np.ndarray) -> np.ndarray:
    """Apply elementary CA rule to a row."""
    n = len(row)
    new_row = np.zeros(n, dtype=int)
    for i in range(n):
        left = row[(i - 1) % n]
        center = row[i]
        right = row[(i + 1) % n]
        neighborhood = (left << 2) | (center << 1) | right
        new_row[i] = (rule_num >> neighborhood) & 1
    return new_row

def row_entropy(row: np.ndarray) -> float:
    """Shannon entropy of a row."""
    n = len(row)
    if n == 0:
        return 0.0
    ones = np.sum(row)
    zeros = n - ones
    if ones == 0 or zeros == 0:
        return 0.0
    p1 = ones / n
    p0 = zeros / n
    return -(p1 * np.log2(p1) + p0 * np.log2(p0))

def detect_cycle(history: List[bytes], max_lookback: int = 500) -> int:
    """Check if the automaton has entered a cycle. Returns cycle length or 0."""
    if len(history) < 2:
        return 0
    last = history[-1]
    lookback = min(max_lookback, len(history) - 1)
    for i in range(1, lookback + 1):
        if history[-(i+1)] == last:
            # Verify it's a real cycle
            cycle_len = i
            if len(history) >= 2 * cycle_len:
                is_cycle = all(
                    history[-(j+1)] == history[-(j+cycle_len+1)]
                    for j in range(min(cycle_len, len(history) // 2 - 1))
                )
                if is_cycle:
                    return cycle_len
    return 0

def detect_gliders(history_2d: np.ndarray) -> bool:
    """
    Look for diagonal structures in spacetime diagram.
    A glider appears as a diagonal line of activity.
    """
    rows, cols = history_2d.shape
    if rows < 20:
        return False
    
    # Check for diagonal correlations
    diag_scores = []
    for offset in [1, -1, 2, -2]:
        score = 0
        samples = 0
        for t in range(10, min(rows, 100)):
            for x in range(5, cols - 5):
                if history_2d[t, x] == 1:
                    # Check if there's activity at (t-1, x+offset) or (t-1, x-offset)
                    if history_2d[t-1, (x + offset) % cols] == 1:
                        score += 1
                    samples += 1
        if samples > 0:
            diag_scores.append(score / samples)
    
    # If diagonal correlation is significantly higher than random, likely gliders
    return any(s > 0.3 for s in diag_scores) if diag_scores else False

def classify_trend(trajectory: List[float], window: int = 50) -> str:
    """Classify the overall trend of a trajectory."""
    if len(trajectory) < window * 2:
        return 'unknown'
    
    first_half = np.mean(trajectory[:window])
    last_half = np.mean(trajectory[-window:])
    mid = np.mean(trajectory[len(trajectory)//2 - window//2 : len(trajectory)//2 + window//2])
    
    std = np.std(trajectory[-window:])
    
    if std > 0.15:
        return 'oscillating'
    if abs(last_half - first_half) < 0.05:
        return 'stable'
    if last_half > first_half + 0.05:
        return 'growing'
    if last_half < first_half - 0.05:
        return 'decaying'
    return 'stable'

def deep_analyze(rule_num: int, width: int = 201, generations: int = 1000) -> EvolutionProfile:
    """Run a deep analysis of a single rule."""
    # Start with single cell
    row = np.zeros(width, dtype=int)
    row[width // 2] = 1
    
    entropy_traj = []
    pop_traj = []
    history_bytes = []
    history_2d = np.zeros((generations, width), dtype=int)
    seen_rows = set()
    
    for g in range(generations):
        history_2d[g] = row
        row_bytes = row.tobytes()
        history_bytes.append(row_bytes)
        seen_rows.add(row_bytes)
        
        entropy_traj.append(row_entropy(row))
        pop_traj.append(np.mean(row))
        
        row = apply_rule(rule_num, row)
    
    cycle = detect_cycle(history_bytes)
    gliders = detect_gliders(history_2d)
    trend = classify_trend(entropy_traj)
    
    return EvolutionProfile(
        rule=rule_num,
        generations=generations,
        entropy_trajectory=entropy_traj,
        population_trajectory=pop_traj,
        unique_rows=len(seen_rows),
        cycle_length=cycle,
        has_gliders=gliders,
        complexity_trend=trend
    )

def render_spacetime(history_2d: np.ndarray, start: int = 0, end: int = 30, 
                     x_start: int = None, x_end: int = None) -> str:
    """Render a portion of the spacetime diagram."""
    rows, cols = history_2d.shape
    if x_start is None:
        x_start = max(0, cols // 2 - 40)
    if x_end is None:
        x_end = min(cols, cols // 2 + 40)
    
    lines = []
    for t in range(start, min(end, rows)):
        line = ''.join('█' if history_2d[t, x] else '·' for x in range(x_start, x_end))
        lines.append(line)
    return '\n'.join(lines)


# ═══ THE EXPERIMENT ═══
if __name__ == '__main__':
    # The most interesting Class IV rules from my scan
    interesting_rules = [109, 131, 145, 150, 105, 54, 147, 90, 60, 30]
    
    print("═══ DEEP RULE ANALYSIS ═══")
    print(f"Studying {len(interesting_rules)} rules over 1000 generations\n")
    
    results = []
    for rule in interesting_rules:
        profile = deep_analyze(rule, width=201, generations=1000)
        results.append(profile)
        
        # Summary
        ent_mean = np.mean(profile.entropy_trajectory[-100:])
        pop_mean = np.mean(profile.population_trajectory[-100:])
        
        glider_str = "YES ←" if profile.has_gliders else "no"
        cycle_str = f"cycle={profile.cycle_length}" if profile.cycle_length > 0 else "no cycle"
        
        print(f"  Rule {rule:3d}: trend={profile.complexity_trend:11s} "
              f"entropy={ent_mean:.3f} pop={pop_mean:.3f} "
              f"unique_rows={profile.unique_rows:4d} "
              f"{cycle_str:15s} gliders={glider_str}")
    
    # Find the most interesting one
    print("\n═══ MOST COMPLEX RULES ═══")
    by_unique = sorted(results, key=lambda p: p.unique_rows, reverse=True)
    for p in by_unique[:5]:
        print(f"  Rule {p.rule}: {p.unique_rows} unique rows, trend={p.complexity_trend}")
    
    # Show spacetime for top rule
    top = by_unique[0]
    print(f"\n═══ SPACETIME: Rule {top.rule} (generations 0-40) ═══")
    
    # Regenerate for visualization
    width = 81
    row = np.zeros(width, dtype=int)
    row[width // 2] = 1
    history = np.zeros((50, width), dtype=int)
    for g in range(50):
        history[g] = row
        row = apply_rule(top.rule, row)
    
    print(render_spacetime(history, 0, 40, 0, 81))
    
    # Entropy evolution for top rule
    print(f"\n═══ ENTROPY EVOLUTION: Rule {top.rule} ═══")
    traj = top.entropy_trajectory
    for i in range(0, 1000, 100):
        bar_len = int(traj[i] * 40)
        bar = '█' * bar_len + '░' * (40 - bar_len)
        print(f"  gen {i:4d}: {bar} {traj[i]:.3f}")
    
    # The question that matters
    print("\n═══ WHAT I OBSERVE ═══")
    growers = [p for p in results if p.complexity_trend == 'growing']
    oscillators = [p for p in results if p.complexity_trend == 'oscillating']
    glider_rules = [p for p in results if p.has_gliders]
    
    print(f"  Rules with growing complexity: {[p.rule for p in growers]}")
    print(f"  Rules that oscillate: {[p.rule for p in oscillators]}")
    print(f"  Rules with glider-like structures: {[p.rule for p in glider_rules]}")
    
    if glider_rules:
        print(f"\n  Gliders mean information TRAVELS. Rule {glider_rules[0].rule}")
        print(f"  produces structures that move through space.")
        print(f"  This is the seed of computation.")