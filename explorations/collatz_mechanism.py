"""
Collatz Mechanism Analysis
WHY do 7-mod-8 numbers dominate the hard cases?

Hypothesis: Hard numbers are ones where 3n+1 consistently has few 
factors of 2 (low 2-adic valuation), keeping the trajectory odd 
and climbing.

The "growth rate" per odd step is 3/(2^v) where v is the 2-adic
valuation of 3n+1. If v=1, growth ≈ 1.5x (climbing). If v≥2, 
the number shrinks.
"""

def v2(n):
    """2-adic valuation: how many times does 2 divide n?"""
    if n == 0:
        return float('inf')
    v = 0
    while n % 2 == 0:
        v += 1
        n //= 2
    return v

def trajectory_analysis(n):
    """Track the 2-adic valuation at each odd step."""
    valuations = []
    steps = 0
    while n != 1:
        if n % 2 == 1:
            new = 3 * n + 1
            v = v2(new)
            valuations.append(v)
            n = new
        else:
            n //= 2
        steps += 1
    return valuations

def stopping_time(n):
    s = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        s += 1
    return s

def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║  COLLATZ MECHANISM: Why are some numbers hard?      ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    # Part 1: Compare 2-adic valuations for hard vs easy numbers
    N = 100000
    times = [(i, stopping_time(i)) for i in range(2, N+1)]
    times.sort(key=lambda x: -x[1])
    
    hard = [n for n, _ in times[:200]]
    easy = [n for n, _ in times[-200:]]
    
    hard_vals = []
    easy_vals = []
    for n in hard:
        hard_vals.extend(trajectory_analysis(n))
    for n in easy:
        easy_vals.extend(trajectory_analysis(n))
    
    hard_mean = sum(hard_vals) / len(hard_vals) if hard_vals else 0
    easy_mean = sum(easy_vals) / len(easy_vals) if easy_vals else 0
    
    print("\n═══ 2-ADIC VALUATION AT ODD STEPS ═══")
    print(f"  Hard numbers (top 200):  mean v₂ = {hard_mean:.4f}")
    print(f"  Easy numbers (bottom 200): mean v₂ = {easy_mean:.4f}")
    print(f"  Difference: {easy_mean - hard_mean:.4f}")
    print()
    print("  (Lower v₂ → fewer divisions by 2 → number stays high)")
    print("  (Growth factor per odd step: 3/2^v₂)")
    print(f"  Hard effective growth: {3/2**hard_mean:.4f}x per odd step")
    print(f"  Easy effective growth: {3/2**easy_mean:.4f}x per odd step")
    
    # Part 2: Distribution of valuations
    from collections import Counter
    hard_dist = Counter(hard_vals)
    easy_dist = Counter(easy_vals)
    
    print("\n═══ VALUATION DISTRIBUTIONS ═══")
    print(f"  {'v₂':>4} | {'Hard %':>8} | {'Easy %':>8} | {'Effect':>10}")
    print(f"  {'─'*4}─┼─{'─'*8}─┼─{'─'*8}─┼─{'─'*10}")
    for v in range(1, 8):
        h_pct = 100 * hard_dist.get(v, 0) / len(hard_vals) if hard_vals else 0
        e_pct = 100 * easy_dist.get(v, 0) / len(easy_vals) if easy_vals else 0
        effect = f"×{3/2**v:.3f}"
        growth = "↑ GROW" if v <= 1 else "↓ shrink"
        print(f"  {v:>4} | {h_pct:>7.1f}% | {e_pct:>7.1f}% | {effect:>6} {growth}")
    
    # Part 3: The critical insight — consecutive low-valuation runs
    print("\n═══ CONSECUTIVE CLIMBING STEPS (v₂ = 1) ═══")
    print("  When v₂=1 at an odd step, the number grows by 1.5x.")
    print("  Consecutive v₂=1 runs cause explosive growth.\n")
    
    def max_consecutive_v1(valuations):
        max_run = 0
        current = 0
        for v in valuations:
            if v == 1:
                current += 1
                max_run = max(max_run, current)
            else:
                current = 0
        return max_run
    
    # Check specific famous hard numbers
    test_numbers = [27, 255, 447, 639, 703, 871, 6171, 77031, 837799]
    print(f"  {'Number':>10} {'Steps':>7} {'Mean v₂':>9} {'Max v₂=1 run':>14} {'% v₂=1':>8}")
    print(f"  {'─'*10} {'─'*7} {'─'*9} {'─'*14} {'─'*8}")
    for n in test_numbers:
        vals = trajectory_analysis(n)
        steps = stopping_time(n)
        mean_v = sum(vals) / len(vals) if vals else 0
        max_run = max_consecutive_v1(vals)
        pct_v1 = 100 * vals.count(1) / len(vals) if vals else 0
        print(f"  {n:>10} {steps:>7} {mean_v:>9.3f} {max_run:>14} {pct_v1:>7.1f}%")
    
    # Part 4: The deepest question — is v₂(3n+1) predictable from n?
    print("\n═══ PREDICTABILITY OF v₂(3n+1) FROM n mod 2^k ═══")
    print("  For odd n, what determines v₂(3n+1)?")
    print()
    for r in [1, 3, 5, 7]:
        # n ≡ r (mod 8), n odd
        vs = [v2(3*n+1) for n in range(r, 10000, 8)]
        mean = sum(vs) / len(vs)
        v1_pct = 100 * vs.count(1) / len(vs)
        print(f"  n ≡ {r} (mod 8): mean v₂(3n+1) = {mean:.3f}, "
              f"v₂=1: {v1_pct:.1f}%")
    
    print()
    # The algebraic explanation
    print("═══ ALGEBRAIC EXPLANATION ═══")
    for r in [1, 3, 5, 7]:
        val = 3 * r + 1
        v = v2(val)
        print(f"  n ≡ {r} (mod 8) → 3n+1 ≡ {val} (mod 24) → v₂ ≥ {v}")
    
    print()
    print("  n ≡ 1 (mod 8): 3n+1 ≡ 4 (mod 24) → v₂ ≥ 2 (shrinks!)")
    print("  n ≡ 3 (mod 8): 3n+1 ≡ 10 (mod 24) → v₂ = 1 (grows!)")  
    print("  n ≡ 5 (mod 8): 3n+1 ≡ 16 (mod 24) → v₂ ≥ 4 (shrinks fast!)")
    print("  n ≡ 7 (mod 8): 3n+1 ≡ 22 (mod 24) → v₂ = 1 (grows!)")
    print()
    print("  ★ Numbers 3 and 7 mod 8 ALWAYS grow on their first odd step.")
    print("  ★ Numbers 1 and 5 mod 8 ALWAYS shrink.")
    print("  ★ This is deterministic, not probabilistic!")
    print("  ★ Hard numbers chain together 3-mod-8 and 7-mod-8 residues.")

if __name__ == "__main__":
    main()