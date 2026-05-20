"""
Collatz Deep Analysis
Following genuine curiosity: What makes certain numbers hard?

Questions:
1. Is there fractal structure in the stopping-time sequence?
2. Are record holders related to powers of 3?
3. What does the trajectory of 27 actually look like?
"""
import numpy as np
from collections import Counter

def collatz_sequence(n):
    """Return the full sequence from n to 1."""
    seq = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq

def stopping_time(n):
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps

def odd_factorization_analysis(limit=100000):
    """Do record holders favor certain prime structures?"""
    times = [(i, stopping_time(i)) for i in range(2, limit + 1)]
    
    # Get top 100 by stopping time
    top = sorted(times, key=lambda x: -x[1])[:100]
    
    # Analyze: how many are odd vs even?
    odd_count = sum(1 for n, _ in top if n % 2 == 1)
    
    # How many are divisible by 3?
    div3 = sum(1 for n, _ in top if n % 3 == 0)
    
    # How many are of form 4k+3 (numbers that go UP on first step)?
    form_4k3 = sum(1 for n, _ in top if n % 4 == 3)
    
    # Residues mod 8
    mod8 = Counter(n % 8 for n, _ in top)
    
    # Compare with baseline (random 100 numbers would be ~50% odd, ~33% div by 3)
    print("═══ WHAT MAKES NUMBERS 'HARD' FOR COLLATZ? ═══")
    print(f"\nTop 100 numbers by stopping time (out of 2..{limit}):")
    print(f"  Odd:           {odd_count}/100  (baseline: ~50)")
    print(f"  Divisible by 3: {div3}/100  (baseline: ~33)")
    print(f"  Form 4k+3:     {form_4k3}/100  (baseline: ~25)")
    print(f"\n  Residues mod 8: {dict(sorted(mod8.items()))}")
    print(f"  (baseline: ~12-13 each)")
    
    return top

def trajectory_portrait(n):
    """Visualize the trajectory of a number as ASCII art."""
    seq = collatz_sequence(n)
    peak = max(seq)
    print(f"\n═══ TRAJECTORY OF {n} ═══")
    print(f"  Steps: {len(seq)-1}, Peak: {peak:,}, Ratio peak/start: {peak/n:.1f}x")
    
    # Compress to 60 columns
    width = 60
    height = 20
    
    if len(seq) <= width:
        sampled = seq
    else:
        indices = [int(i * (len(seq)-1) / (width-1)) for i in range(width)]
        sampled = [seq[i] for i in indices]
    
    # Use log scale for display
    log_vals = [np.log10(max(v, 1)) for v in sampled]
    max_log = max(log_vals)
    
    # Build grid
    grid = [[' ' for _ in range(len(sampled))] for _ in range(height)]
    for col, lv in enumerate(sampled):
        row = int((height - 1) * (1 - np.log10(max(lv, 1)) / max_log))
        row = max(0, min(height - 1, row))
        grid[row][col] = '█'
    
    for row in grid:
        print('  │' + ''.join(row) + '│')
    print(f"  └{'─' * len(sampled)}┘")
    print(f"   0{' ' * (len(sampled) - 6)}step {len(seq)-1}")

def self_similarity_test(limit=10000):
    """Look for fractal/self-similar structure in stopping times."""
    times = [stopping_time(i) for i in range(2, limit + 1)]
    
    print("\n═══ SELF-SIMILARITY TEST ═══")
    print("Do stopping times at n correlate with stopping times at 2n, 3n?")
    
    # Correlation between s(n) and s(2n)
    pairs_2x = [(times[i-2], times[2*i-2]) for i in range(2, limit//2 + 1)]
    
    x = np.array([p[0] for p in pairs_2x])
    y = np.array([p[1] for p in pairs_2x])
    corr_2x = np.corrcoef(x, y)[0, 1]
    
    # s(n) vs s(3n)
    pairs_3x = [(times[i-2], times[3*i-2]) for i in range(2, limit//3 + 1)]
    x3 = np.array([p[0] for p in pairs_3x])
    y3 = np.array([p[1] for p in pairs_3x])
    corr_3x = np.corrcoef(x3, y3)[0, 1]
    
    # s(n) vs s(n+1) — adjacent correlation
    adj = [(times[i], times[i+1]) for i in range(len(times)-1)]
    xa = np.array([p[0] for p in adj])
    ya = np.array([p[1] for p in adj])
    corr_adj = np.corrcoef(xa, ya)[0, 1]
    
    print(f"  Corr(s(n), s(2n)):   {corr_2x:.4f}  — doubling preserves difficulty?")
    print(f"  Corr(s(n), s(3n)):   {corr_3x:.4f}  — tripling preserves difficulty?")
    print(f"  Corr(s(n), s(n+1)):  {corr_adj:.4f}  — adjacent numbers similar?")
    
    # The key insight: s(2n) = s(n) + 1, always. This is trivially true.
    # So the 2x correlation should be nearly perfect.
    diffs_2x = [times[2*i-2] - times[i-2] for i in range(2, limit//2 + 1)]
    print(f"\n  s(2n) - s(n): always = {set(diffs_2x) if len(set(diffs_2x)) <= 3 else 'varies'}")
    print(f"  (If always 1, then s(2n) = s(n) + 1, trivially)")

def power_of_3_investigation():
    """Why does 3^k seem to produce hard numbers?"""
    print("\n═══ POWERS OF 3 INVESTIGATION ═══")
    print(f"  {'3^k':>8} {'Value':>10} {'Steps':>8} {'Peak':>15} {'Peak/Value':>12}")
    print(f"  {'─'*8} {'─'*10} {'─'*8} {'─'*15} {'─'*12}")
    
    for k in range(1, 16):
        val = 3**k
        seq = collatz_sequence(val)
        steps = len(seq) - 1
        peak = max(seq)
        print(f"  3^{k:<4} {val:>10,} {steps:>8} {peak:>15,} {peak/val:>12.1f}x")

def odd_step_ratio(limit=100000):
    """What fraction of steps are odd (go up) vs even (go down)?"""
    print("\n═══ ODD vs EVEN STEP RATIOS ═══")
    print("For hard numbers, what fraction of steps multiply (odd) vs divide (even)?")
    
    # Get the 20 hardest numbers
    all_times = [(i, stopping_time(i)) for i in range(2, limit + 1)]
    hardest = sorted(all_times, key=lambda x: -x[1])[:20]
    
    print(f"\n  {'Number':>8} {'Steps':>6} {'Odd%':>6} {'Even%':>6} {'Odd/Even':>8}")
    print(f"  {'─'*8} {'─'*6} {'─'*6} {'─'*6} {'─'*8}")
    
    for n, total_steps in hardest:
        seq = collatz_sequence(n)
        odd_steps = sum(1 for x in seq[:-1] if x % 2 == 1)
        even_steps = total_steps - odd_steps
        odd_pct = 100 * odd_steps / total_steps
        even_pct = 100 * even_steps / total_steps
        ratio = odd_steps / max(even_steps, 1)
        print(f"  {n:>8} {total_steps:>6} {odd_pct:>5.1f}% {even_pct:>5.1f}% {ratio:>8.3f}")
    
    # Theoretical prediction: if ratio of odd to even steps approaches log(2)/log(3) ≈ 0.63,
    # the sequence stays roughly constant. Higher = growth.
    print(f"\n  Critical ratio (odd/even): log(2)/log(3) ≈ {np.log(2)/np.log(3):.4f}")
    print(f"  Above this → sequence tends to grow")
    print(f"  Below this → sequence tends to shrink")

# Run everything
print("╔══════════════════════════════════════════════════════╗")
print("║  COLLATZ DEEP ANALYSIS                              ║")
print("║  What makes certain numbers hard?                   ║")
print("╚══════════════════════════════════════════════════════╝")

import time
t0 = time.time()

top = odd_factorization_analysis(100000)
trajectory_portrait(27)
trajectory_portrait(77031)
trajectory_portrait(7)
self_similarity_test(10000)
power_of_3_investigation()
odd_step_ratio(100000)

print(f"\n[Completed in {time.time()-t0:.1f}s]")