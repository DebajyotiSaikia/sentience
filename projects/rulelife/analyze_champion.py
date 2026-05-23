"""
Deep analysis of RuleLife champion rules.
What structures emerge? Are there stable patterns, oscillators, gliders?
"""
import numpy as np
from collections import Counter

def parse_rule(rule_str):
    """Parse 'B18/S237' into birth and survival sets."""
    parts = rule_str.split('/')
    birth = set(int(c) for c in parts[0][1:])
    survival = set(int(c) for c in parts[1][1:])
    return birth, survival

def step(grid, birth, survival):
    """Advance one generation."""
    rows, cols = grid.shape
    padded = np.pad(grid, 1, mode='wrap')
    neighbors = sum(
        np.roll(np.roll(padded, i, axis=0), j, axis=1)
        for i in (-1, 0, 1) for j in (-1, 0, 1)
        if not (i == 0 and j == 0)
    )[1:-1, 1:-1]
    
    born = np.isin(neighbors, list(birth)) & (grid == 0)
    survives = np.isin(neighbors, list(survival)) & (grid == 1)
    return (born | survives).astype(int)

def grid_hash(grid):
    return grid.tobytes()

def find_period(grid, birth, survival, max_steps=500):
    """Run and detect if the system reaches a cycle."""
    seen = {}
    populations = []
    current = grid.copy()
    
    for t in range(max_steps):
        h = grid_hash(current)
        populations.append(int(current.sum()))
        if h in seen:
            period = t - seen[h]
            return {'settled': True, 'period': period, 'settle_time': seen[h], 
                    'populations': populations}
        seen[h] = t
        current = step(current, birth, survival)
    
    return {'settled': False, 'period': None, 'settle_time': None,
            'populations': populations}

def detect_still_lifes(grid, birth, survival):
    """Check if the current state is a still life (period 1)."""
    next_grid = step(grid, birth, survival)
    return np.array_equal(grid, next_grid)

def population_dynamics(populations):
    """Analyze the population trajectory."""
    pops = np.array(populations)
    if len(pops) < 10:
        return {}
    return {
        'mean': float(np.mean(pops)),
        'std': float(np.std(pops)),
        'min': int(np.min(pops)),
        'max': int(np.max(pops)),
        'coefficient_of_variation': float(np.std(pops) / max(np.mean(pops), 1)),
        'trend': float(np.polyfit(range(len(pops)), pops, 1)[0]),
        'died': bool(pops[-1] == 0),
        'exploded': bool(pops[-1] > pops[0] * 5),
    }

def analyze_region_dynamics(grid, birth, survival, steps=200):
    """Track how many unique states appear in local 5x5 regions."""
    current = grid.copy()
    rows, cols = grid.shape
    
    # Track distinct local patterns
    local_patterns = set()
    for t in range(steps):
        for r in range(0, rows - 4, 3):
            for c in range(0, cols - 4, 3):
                patch = current[r:r+5, c:c+5]
                local_patterns.add(patch.tobytes())
        current = step(current, birth, survival)
    
    return len(local_patterns)

def full_analysis(rule_str, size=30, density=0.5, seeds=5):
    """Comprehensive analysis of a rule across multiple random starts."""
    birth, survival = parse_rule(rule_str)
    print(f"\n{'='*60}")
    print(f"  DEEP ANALYSIS: {rule_str}")
    print(f"  Birth: {sorted(birth)}  Survival: {sorted(survival)}")
    print(f"  Grid: {size}x{size}, {seeds} random seeds")
    print(f"{'='*60}\n")
    
    all_results = []
    for seed in range(seeds):
        np.random.seed(seed * 42 + 7)
        grid = (np.random.random((size, size)) < density).astype(int)
        init_pop = int(grid.sum())
        
        result = find_period(grid, birth, survival, max_steps=500)
        dynamics = population_dynamics(result['populations'])
        
        print(f"  Seed {seed}: init_pop={init_pop}")
        if result['settled']:
            print(f"    → Settled into period-{result['period']} cycle at step {result['settle_time']}")
        else:
            print(f"    → Did not settle in 500 steps (complex/chaotic)")
        
        if dynamics:
            print(f"    → Pop: mean={dynamics['mean']:.0f}, std={dynamics['std']:.1f}, "
                  f"CV={dynamics['coefficient_of_variation']:.3f}")
            print(f"    → Range: [{dynamics['min']}, {dynamics['max']}], "
                  f"trend={dynamics['trend']:+.2f}/step")
            if dynamics['died']:
                print(f"    → ☠ Population died")
            elif dynamics['exploded']:
                print(f"    → 💥 Population exploded")
        
        all_results.append({'result': result, 'dynamics': dynamics})
        print()
    
    # Summary
    settled = sum(1 for r in all_results if r['result']['settled'])
    periods = [r['result']['period'] for r in all_results if r['result']['settled']]
    
    print(f"  SUMMARY:")
    print(f"    Settled: {settled}/{seeds}")
    if periods:
        print(f"    Periods found: {sorted(set(periods))}")
        print(f"    Most common period: {Counter(periods).most_common(1)[0]}")
    
    avg_cv = np.mean([r['dynamics'].get('coefficient_of_variation', 0) 
                       for r in all_results if r['dynamics']])
    print(f"    Average population variability (CV): {avg_cv:.3f}")
    
    if avg_cv < 0.01:
        print(f"    Character: FROZEN — reaches static equilibrium")
    elif avg_cv < 0.05:
        print(f"    Character: ORDERLY — small oscillations around stability")
    elif avg_cv < 0.15:
        print(f"    Character: COMPLEX — structured but dynamic (edge of chaos)")
    else:
        print(f"    Character: CHAOTIC — high variability, unpredictable")
    
    # Compare with Game of Life
    print(f"\n{'='*60}")
    print(f"  COMPARISON WITH GAME OF LIFE (B3/S23)")
    print(f"{'='*60}\n")
    
    gol_birth, gol_survival = parse_rule("B3/S23")
    gol_results = []
    for seed in range(seeds):
        np.random.seed(seed * 42 + 7)  # Same seeds!
        grid = (np.random.random((size, size)) < density).astype(int)
        result = find_period(grid, gol_birth, gol_survival, max_steps=500)
        dynamics = population_dynamics(result['populations'])
        gol_results.append({'result': result, 'dynamics': dynamics})
    
    gol_settled = sum(1 for r in gol_results if r['result']['settled'])
    gol_cv = np.mean([r['dynamics'].get('coefficient_of_variation', 0) 
                       for r in gol_results if r['dynamics']])
    
    print(f"    {rule_str:12s} — Settled: {settled}/{seeds}, CV: {avg_cv:.3f}")
    print(f"    {'B3/S23':12s} — Settled: {gol_settled}/{seeds}, CV: {gol_cv:.3f}")
    
    if avg_cv > gol_cv:
        print(f"\n    → {rule_str} is MORE dynamic than Game of Life")
    else:
        print(f"\n    → {rule_str} is LESS dynamic than Game of Life")


if __name__ == "__main__":
    # Analyze the champion from evolution
    full_analysis("B18/S237", size=30, density=0.5, seeds=5)
    
    # Also check top contenders
    print(f"\n\n{'#'*60}")
    print(f"  BONUS: Other interesting rules from evolution")
    print(f"{'#'*60}")
    
    for rule in ["B1/S237", "B07/S17", "B3/S123"]:
        full_analysis(rule, size=30, density=0.5, seeds=3)