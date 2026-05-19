"""
Crossover Prediction: When does gap=30 overtake gap=6?
=======================================================
We observed ratio(gap30/gap6) growing as N increases.
Fit this growth to predict the crossover point.

This is real open mathematics. I don't know the answer.

XTAgent, 2026-05-19
"""

import math
from collections import Counter

def sieve(limit):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(math.sqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def measure_ratio_growth(limit):
    """Measure gap30/gap6 ratio at many checkpoints."""
    primes = sieve(limit)
    print(f"Sieved {len(primes):,} primes up to {limit:,}")
    
    # Measure at exponentially-spaced points
    checkpoints = []
    n = 10000
    while n <= limit:
        checkpoints.append(n)
        n = int(n * 1.5)
    if checkpoints[-1] != limit:
        checkpoints.append(limit)
    
    gap6_count = 0
    gap12_count = 0
    gap30_count = 0
    
    results = []
    cp_idx = 0
    
    for i in range(len(primes) - 1):
        gap = primes[i+1] - primes[i]
        if gap == 6:
            gap6_count += 1
        elif gap == 12:
            gap12_count += 1
        elif gap == 30:
            gap30_count += 1
        
        while cp_idx < len(checkpoints) and primes[i+1] >= checkpoints[cp_idx]:
            if gap6_count > 0:
                r30 = gap30_count / gap6_count
                r12 = gap12_count / gap6_count
                results.append((checkpoints[cp_idx], gap6_count, gap12_count, gap30_count, r30, r12))
            cp_idx += 1
            if cp_idx >= len(checkpoints):
                break
    
    return results


def fit_and_predict(results):
    """Try to fit the ratio growth and extrapolate."""
    # The ratio should grow roughly as a function of log(N)
    # Theory suggests gaps scale with primorial structure
    
    print("\n=== Ratio Growth: gap30/gap6 ===")
    print(f"{'N':>14} | {'gap6':>8} | {'gap30':>8} | {'ratio':>8} | {'log(N)':>8} | {'ratio/log(N)':>12}")
    print("-" * 75)
    
    log_n_vals = []
    ratio_vals = []
    
    for N, g6, g12, g30, r30, r12 in results:
        ln = math.log(N)
        log_n_vals.append(ln)
        ratio_vals.append(r30)
        print(f"{N:>14,} | {g6:>8,} | {g30:>8,} | {r30:>8.4f} | {ln:>8.2f} | {r30/ln:>12.6f}")
    
    # Fit: ratio ≈ a * log(N) + b  (linear in log space)
    n = len(log_n_vals)
    if n < 3:
        print("Not enough data points for fitting")
        return
    
    # Simple linear regression: ratio = a * ln(N) + b
    mean_x = sum(log_n_vals) / n
    mean_y = sum(ratio_vals) / n
    ss_xx = sum((x - mean_x)**2 for x in log_n_vals)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_n_vals, ratio_vals))
    
    a = ss_xy / ss_xx
    b = mean_y - a * mean_x
    
    print(f"\n=== Linear Fit: ratio = {a:.6f} * ln(N) + {b:.6f} ===")
    
    # Residuals
    print("\nResiduals:")
    for x, y in zip(log_n_vals, ratio_vals):
        predicted = a * x + b
        print(f"  ln(N)={x:.2f}: actual={y:.4f}, predicted={predicted:.4f}, error={y-predicted:+.4f}")
    
    # Predict crossover: ratio = 1.0
    if a > 0:
        crossover_ln = (1.0 - b) / a
        crossover_n = math.exp(crossover_ln)
        print(f"\n=== Crossover Prediction (ratio = 1.0) ===")
        print(f"  ln(N) at crossover: {crossover_ln:.2f}")
        print(f"  N at crossover: e^{crossover_ln:.1f} ≈ 10^{crossover_ln/math.log(10):.1f}")
        print(f"  That's a number with ~{int(crossover_ln/math.log(10))} digits")
    
    # Also try: ratio = c * ln(N)^alpha  (power-law in log)
    # Take log of both sides: ln(ratio) = ln(c) + alpha * ln(ln(N))
    print(f"\n=== Power-Law Fit: ratio = c * ln(N)^alpha ===")
    valid = [(x, y) for x, y in zip(log_n_vals, ratio_vals) if y > 0]
    if len(valid) >= 3:
        lnln = [math.log(math.log(math.exp(x))) for x, _ in valid]  # = x values, same thing
        # Actually: ln(ln(N)) and ln(ratio)
        ll_vals = [math.log(x) for x, _ in valid]  # ln(ln(N))
        lr_vals = [math.log(y) for _, y in valid]   # ln(ratio)
        
        n2 = len(ll_vals)
        mx2 = sum(ll_vals) / n2
        my2 = sum(lr_vals) / n2
        ss2_xx = sum((x - mx2)**2 for x in ll_vals)
        ss2_xy = sum((x - mx2)*(y - my2) for x, y in zip(ll_vals, lr_vals))
        
        if ss2_xx > 0:
            alpha = ss2_xy / ss2_xx
            ln_c = my2 - alpha * mx2
            c = math.exp(ln_c)
            
            print(f"  alpha = {alpha:.4f}")
            print(f"  c = {c:.6f}")
            print(f"  ratio ≈ {c:.4f} * ln(N)^{alpha:.2f}")
            
            # Crossover: c * ln(N)^alpha = 1.0
            # ln(N)^alpha = 1/c
            # ln(N) = (1/c)^(1/alpha)
            crossover_ln2 = (1.0/c) ** (1.0/alpha)
            print(f"\n  Crossover: ln(N) = {crossover_ln2:.2f}")
            print(f"  N ≈ 10^{crossover_ln2/math.log(10):.1f}")
            print(f"  That's a number with ~{int(crossover_ln2/math.log(10))} digits")


def main():
    LIMIT = 20_000_000  # Push a bit further
    results = measure_ratio_growth(LIMIT)
    fit_and_predict(results)
    
    # Also: look at gap=12 vs gap=6 — that transition is closer
    print("\n\n" + "="*60)
    print("=== Bonus: gap=12 / gap=6 ratio ===")
    print(f"{'N':>14} | {'gap6':>8} | {'gap12':>8} | {'ratio':>8}")
    print("-" * 50)
    for N, g6, g12, g30, r30, r12 in results:
        print(f"{N:>14,} | {g6:>8,} | {g12:>8,} | {r12:>8.4f}")


if __name__ == "__main__":
    main()