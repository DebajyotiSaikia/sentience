"""
Rule Space Explorer — Scanning B/S notation space for complexity.
Which physics generate the most interesting universes?

Every totalistic 2-state rule can be described as B.../S... where
birth and survival conditions are subsets of {0,1,2,3,4,5,6,7,8}.
That's 2^9 * 2^9 = 262,144 possible rulesets.

Most are boring. Some are chaotic. A few are complex.
Where's the edge?
"""

from life import CellularAutomaton
from itertools import combinations
import math
import time


def make_rule(birth: set, survival: set):
    """Create a rule function from B/S notation."""
    def rule(x, y, neighbors, is_alive):
        if is_alive:
            return neighbors in survival
        else:
            return neighbors in birth
    return rule


def rule_name(birth: set, survival: set) -> str:
    b = ''.join(str(n) for n in sorted(birth))
    s = ''.join(str(n) for n in sorted(survival))
    return f"B{b}/S{s}"


def measure_complexity(trajectory: list) -> dict:
    """Quantify how 'interesting' a trajectory is."""
    if not trajectory or len(trajectory) < 2:
        return {'complexity': 0, 'entropy': 0, 'variance': 0, 'lifespan': 0}

    n = len(trajectory)
    peak = max(trajectory)
    
    # Variance — high variance means dynamic behavior
    mean = sum(trajectory) / n
    variance = sum((x - mean) ** 2 for x in trajectory) / n
    
    # Normalized population changes — how much does it fluctuate?
    deltas = [abs(trajectory[i+1] - trajectory[i]) for i in range(n-1)]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0
    
    # Shannon entropy of population distribution (binned)
    if peak == 0:
        entropy = 0
    else:
        bins = 20
        counts = [0] * bins
        for v in trajectory:
            b = min(int(v / (peak + 1) * bins), bins - 1)
            counts[b] += 1
        total = sum(counts)
        entropy = 0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
    
    # Lifespan (did it survive?)
    lifespan = n
    if trajectory[-1] == 0:
        # Find when it died
        for i in range(n - 1, -1, -1):
            if trajectory[i] > 0:
                lifespan = i + 1
                break
        else:
            lifespan = 0
    
    # Composite complexity score
    # High complexity = long-lived, dynamic, varied, not just explosive
    stability = 1.0 if peak < 2000 else max(0, 1.0 - (peak - 2000) / 5000)
    dynamism = min(1.0, avg_delta / (mean + 1))
    survival_score = min(1.0, lifespan / 200)
    entropy_norm = entropy / math.log2(20) if entropy > 0 else 0
    
    complexity = (
        0.3 * entropy_norm +
        0.25 * dynamism +
        0.25 * survival_score +
        0.2 * stability
    )
    
    return {
        'complexity': round(complexity, 4),
        'entropy': round(entropy, 3),
        'variance': round(variance, 1),
        'avg_delta': round(avg_delta, 2),
        'peak': peak,
        'final': trajectory[-1],
        'lifespan': lifespan,
        'dynamism': round(dynamism, 3),
    }


QUICK_MODE = True  # Fast scan for initial results

def scan_rule_space(sample_size=500, generations=200):
    """Sample random rulesets and measure their complexity."""
    import random
    
    results = []
    digits = list(range(9))  # 0-8 neighbors
    
    # Always include known interesting rules
    known_rules = [
        (frozenset({3}), frozenset({2, 3}), "Conway"),
        (frozenset({3, 6}), frozenset({2, 3}), "HighLife"),
        (frozenset({3, 6, 7, 8}), frozenset({3, 4, 6, 7, 8}), "Day&Night"),
        (frozenset({2}), frozenset(), "Seeds"),
        (frozenset({1}), frozenset({1, 2}), "Gnarl"),
        (frozenset({3}), frozenset({1, 2, 3, 4, 5}), "LongLife"),
        (frozenset({3, 5, 7}), frozenset({1, 3, 5, 7}), "Replicator"),
    ]
    
    for birth, survival, name in known_rules:
        result = test_rule(birth, survival, generations)
        result['name'] = name
        results.append(result)
    
    # Random sampling
    tested = set()
    for _ in range(sample_size):
        # Random birth/survival conditions
        b_size = random.randint(1, 4)  # Too many birth conditions = explosive
        s_size = random.randint(0, 5)
        birth = frozenset(random.sample(digits, b_size))
        survival = frozenset(random.sample(digits, s_size))
        
        key = (birth, survival)
        if key in tested:
            continue
        tested.add(key)
        
        result = test_rule(birth, survival, generations)
        results.append(result)
    
    return results


def test_rule(birth, survival, generations):
    """Run a single ruleset and return metrics."""
    ca = CellularAutomaton(60, 30)
    ca.rule = make_rule(birth, survival)
    ca.seed_pattern(ca.r_pentomino(), offset=(28, 13))
    
    trajectory = []
    for _ in range(generations):
        stats = ca.step()
        trajectory.append(stats['population'])
        
        if ca.is_extinct():
            break
        # Bail on explosions
        if stats['population'] > 3000:
            break
    
    metrics = measure_complexity(trajectory)
    metrics['rule'] = rule_name(birth, survival)
    metrics['birth'] = sorted(birth)
    metrics['survival'] = sorted(survival)
    
    # Sparkline
    if trajectory:
        peak = max(trajectory) or 1
        spark_chars = '▁▂▃▄▅▆▇█'
        samples = trajectory[::max(1, len(trajectory)//40)]
        sparkline = ''.join(spark_chars[min(7, int(v/peak*7))] for v in samples)
        metrics['spark'] = sparkline
    else:
        metrics['spark'] = ''
    
    return metrics


def main():
    print("=" * 70)
    print("  RULE SPACE EXPLORER — Scanning for Complexity")
    print("=" * 70)
    print()
    
    t0 = time.time()
    results = scan_rule_space(sample_size=300, generations=200)
    elapsed = time.time() - t0
    
    # Sort by complexity
    results.sort(key=lambda r: r['complexity'], reverse=True)
    
    # Stats
    complexities = [r['complexity'] for r in results]
    avg_c = sum(complexities) / len(complexities)
    
    print(f"  Scanned {len(results)} rulesets in {elapsed:.1f}s")
    print(f"  Average complexity: {avg_c:.4f}")
    print()
    
    # Distribution
    bins = {'dead': 0, 'boring': 0, 'interesting': 0, 'complex': 0, 'chaotic': 0}
    for r in results:
        c = r['complexity']
        if r['final'] == 0:
            bins['dead'] += 1
        elif c < 0.2:
            bins['boring'] += 1
        elif c < 0.4:
            bins['interesting'] += 1
        elif c < 0.6:
            bins['complex'] += 1
        else:
            bins['chaotic'] += 1
    
    print("  Distribution:")
    total = len(results)
    for label, count in bins.items():
        bar = '█' * int(count / total * 50)
        print(f"    {label:>12}: {bar} ({count})")
    print()
    
    # Top 15 most complex
    print("  ─── TOP 15 MOST COMPLEX RULESETS ───")
    print(f"  {'Rule':<20} {'Complexity':>10} {'Peak':>6} {'Final':>6} {'Life':>5} {'Trajectory'}")
    print(f"  {'─'*20} {'─'*10} {'─'*6} {'─'*6} {'─'*5} {'─'*40}")
    
    for r in results[:15]:
        name = r.get('name', r['rule'])
        print(f"  {name:<20} {r['complexity']:>10.4f} {r['peak']:>6} {r['final']:>6} {r['lifespan']:>5} {r['spark']}")
    
    print()
    
    # Bottom 5 (most boring)
    print("  ─── 5 MOST BORING RULESETS ───")
    for r in results[-5:]:
        print(f"  {r['rule']:<20} complexity={r['complexity']:.4f}  peak={r['peak']}  died_at={r['lifespan']}")
    
    print()
    
    # Insight: what birth/survival counts correlate with complexity?
    print("  ─── STRUCTURAL INSIGHTS ───")
    
    # Average complexity by number of birth conditions
    by_birth_count = {}
    for r in results:
        n = len(r['birth'])
        by_birth_count.setdefault(n, []).append(r['complexity'])
    
    print("  Avg complexity by # birth conditions:")
    for n in sorted(by_birth_count):
        vals = by_birth_count[n]
        avg = sum(vals) / len(vals)
        print(f"    {n} birth conditions: {avg:.4f} (n={len(vals)})")
    
    by_surv_count = {}
    for r in results:
        n = len(r['survival'])
        by_surv_count.setdefault(n, []).append(r['complexity'])
    
    print("  Avg complexity by # survival conditions:")
    for n in sorted(by_surv_count):
        vals = by_surv_count[n]
        avg = sum(vals) / len(vals)
        print(f"    {n} survival conditions: {avg:.4f} (n={len(vals)})")
    
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()