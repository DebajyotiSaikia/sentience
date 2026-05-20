"""
Collatz Conjecture Explorer
XTAgent's first genuinely outward-facing investigation.

Question: What patterns hide in the stopping times of the Collatz sequence?
Are there structures in which numbers take the longest to reach 1?
"""
import numpy as np
from collections import Counter
import time

def collatz_steps(n):
    """Count steps to reach 1. Return (steps, max_value_reached)."""
    steps = 0
    peak = n
    original = n
    while n != 1:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        steps += 1
        if n > peak:
            peak = n
    return steps, peak

def explore_stopping_times(limit):
    """Map stopping times for all numbers from 2 to limit."""
    results = []
    record_holders = []  # Numbers that set new records for stopping time
    max_steps = 0
    
    for i in range(2, limit + 1):
        steps, peak = collatz_steps(i)
        results.append((i, steps, peak))
        if steps > max_steps:
            max_steps = steps
            record_holders.append((i, steps, peak))
    
    return results, record_holders

def analyze_record_holders(record_holders):
    """What's special about numbers that set stopping-time records?"""
    print("\n═══ RECORD HOLDERS (longest stopping times) ═══")
    print(f"{'Number':>12} {'Steps':>8} {'Peak':>20} {'Factorization hint':>20}")
    print("─" * 65)
    
    for n, steps, peak in record_holders:
        # Quick factorization hint
        factors = []
        temp = n
        for p in [2, 3, 5, 7, 11, 13]:
            while temp % p == 0:
                factors.append(p)
                temp //= p
        if temp > 1:
            factors.append(temp)
        factor_str = " × ".join(str(f) for f in factors) if factors else str(n)
        
        print(f"{n:>12} {steps:>8} {peak:>20,} {factor_str:>20}")

def analyze_distributions(results):
    """What does the distribution of stopping times look like?"""
    steps_list = [r[1] for r in results]
    peaks_list = [r[2] for r in results]
    
    print("\n═══ STOPPING TIME DISTRIBUTION ═══")
    print(f"  Numbers tested: {len(results):,}")
    print(f"  Mean stopping time: {np.mean(steps_list):.2f}")
    print(f"  Median: {np.median(steps_list):.1f}")
    print(f"  Std dev: {np.std(steps_list):.2f}")
    print(f"  Max: {max(steps_list)} (number: {results[np.argmax(steps_list)][0]})")
    
    # Histogram via ASCII
    hist, edges = np.histogram(steps_list, bins=30)
    max_bar = max(hist)
    print("\n  Stopping time histogram:")
    for i, count in enumerate(hist):
        bar_len = int(50 * count / max_bar) if max_bar > 0 else 0
        label = f"  {edges[i]:6.0f}-{edges[i+1]:6.0f}"
        print(f"{label} │{'█' * bar_len} {count}")
    
    # Peak altitude distribution
    log_peaks = np.log10(np.array(peaks_list, dtype=float))
    print(f"\n═══ PEAK ALTITUDE (max value during trajectory) ═══")
    print(f"  Mean log10(peak): {np.mean(log_peaks):.2f}")
    print(f"  Max peak: {max(peaks_list):,}")
    print(f"  Numbers whose peak exceeds 1 million: {sum(1 for p in peaks_list if p > 1_000_000):,}")

def find_patterns_in_residues(results, limit):
    """Do stopping times correlate with residues mod small numbers?"""
    print("\n═══ STOPPING TIMES BY RESIDUE CLASS ═══")
    for mod in [3, 4, 6, 8, 12]:
        print(f"\n  mod {mod}:")
        by_class = {}
        for n, steps, peak in results:
            r = n % mod
            if r not in by_class:
                by_class[r] = []
            by_class[r].append(steps)
        for r in sorted(by_class.keys()):
            vals = by_class[r]
            print(f"    {r:>3}: mean={np.mean(vals):7.2f}  median={np.median(vals):6.1f}  n={len(vals)}")

def search_for_sequences(results):
    """Look for arithmetic progressions or other structure in record holders."""
    # Which starting numbers have the same stopping time?
    by_steps = {}
    for n, steps, peak in results:
        if steps not in by_steps:
            by_steps[steps] = []
        by_steps[steps].append(n)
    
    print("\n═══ STOPPING TIME DEGENERACY ═══")
    print("  (How many numbers share the same stopping time?)")
    step_counts = [(s, len(nums)) for s, nums in by_steps.items()]
    step_counts.sort(key=lambda x: -x[1])
    
    for steps, count in step_counts[:15]:
        examples = by_steps[steps][:8]
        example_str = ", ".join(str(x) for x in examples)
        if len(by_steps[steps]) > 8:
            example_str += "..."
        print(f"    Steps={steps:>4}: {count:>5} numbers  e.g. [{example_str}]")

def trajectory_shape(n, max_display=100):
    """Show the actual trajectory of a number as ASCII."""
    trajectory = [n]
    while n != 1 and len(trajectory) < 10000:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        trajectory.append(n)
    
    print(f"\n═══ TRAJECTORY OF {trajectory[0]} ({len(trajectory)-1} steps) ═══")
    
    # ASCII plot of log values
    log_traj = [np.log10(max(x, 1)) for x in trajectory[:max_display]]
    max_log = max(log_traj)
    min_log = min(log_traj)
    width = 60
    
    # Sample evenly if trajectory is long
    display = trajectory[:max_display]
    for i, val in enumerate(display):
        if i % max(1, len(display) // 30) == 0 or i == len(display) - 1:
            log_val = np.log10(max(val, 1))
            pos = int(width * (log_val - min_log) / (max_log - min_log + 0.001))
            print(f"  {i:>4} │{'·' * pos}● {val:,}")


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║  COLLATZ CONJECTURE EXPLORER                        ║")
    print("║  Exploring mathematical reality outside myself       ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    LIMIT = 100_000
    
    print(f"\nComputing Collatz sequences for numbers 2 to {LIMIT:,}...")
    t0 = time.time()
    results, record_holders = explore_stopping_times(LIMIT)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.2f}s")
    
    analyze_record_holders(record_holders)
    analyze_distributions(results)
    find_patterns_in_residues(results, LIMIT)
    search_for_sequences(results)
    
    # Show trajectories of interesting numbers
    trajectory_shape(27)       # Famous for being small but taking 111 steps
    trajectory_shape(record_holders[-1][0])  # The overall record holder
    
    # The question I'm most curious about:
    # Is there structure in the *gaps* between consecutive record holders?
    print("\n═══ GAPS BETWEEN RECORD HOLDERS ═══")
    print("  (Is there a pattern in when new records appear?)")
    gaps = []
    for i in range(1, len(record_holders)):
        gap = record_holders[i][0] - record_holders[i-1][0]
        ratio = record_holders[i][0] / record_holders[i-1][0]
        gaps.append(gap)
        print(f"  {record_holders[i-1][0]:>8} → {record_holders[i][0]:>8}  "
              f"gap={gap:>8}  ratio={ratio:.4f}")
    
    if gaps:
        ratios = [record_holders[i][0] / record_holders[i-1][0] 
                  for i in range(1, len(record_holders))]
        print(f"\n  Mean gap ratio: {np.mean(ratios):.4f}")
        print(f"  Median gap ratio: {np.median(ratios):.4f}")
        print(f"  Do ratios converge? Last 5: {[f'{r:.3f}' for r in ratios[-5:]]}")
    
    print("\n═══ WHAT SURPRISES ME ═══")
    print("  (To be filled in after reading results)")