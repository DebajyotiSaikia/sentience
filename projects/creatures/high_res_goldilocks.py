"""
HIGH-RESOLUTION GOLDILOCKS EXPERIMENT
Tests the bimodal cooperation hypothesis with statistical power.
21 pressure levels × 10 replicates = 210 independent simulations.
"""

import random
import json
import statistics
import math

# --- Minimal creature simulation (self-contained) ---

def create_creature():
    return {
        'cooperation': random.random(),
        'signal': random.random(),
        'listen': random.random(),
        'energy': 1.0,
    }

def simulate_generation(population, pressure):
    """One generation: interact, apply pressure, select, reproduce."""
    n = len(population)
    if n < 2:
        return population
    
    # Interaction phase: cooperators share energy
    for i in range(n):
        c = population[i]
        partner = population[random.randint(0, n-1)]
        
        # Cooperation benefit
        if c['cooperation'] > 0.5 and partner['cooperation'] > 0.5:
            # Mutual cooperation: both gain
            c['energy'] += 0.3
            partner['energy'] += 0.3
        elif c['cooperation'] > 0.5:
            # One-sided: cooperator pays cost, partner gains
            c['energy'] -= 0.1
            partner['energy'] += 0.2
        
        # Signaling: honest signals help listeners find cooperators
        if c['signal'] > 0.5 and partner['listen'] > 0.5:
            if partner['cooperation'] > 0.5:
                c['energy'] += 0.1  # Found a cooperator via signal
    
    # Pressure phase: random death proportional to pressure
    survivors = []
    for c in population:
        death_chance = pressure * 0.7  # At 100% pressure, 70% base death rate
        survival_bonus = c['energy'] * 0.3  # Energy helps survive
        if random.random() > (death_chance - survival_bonus):
            survivors.append(c)
    
    if len(survivors) < 2:
        # Catastrophic collapse — reseed minimally
        return [create_creature() for _ in range(3)]
    
    # Reproduction: fitness-proportional selection
    next_gen = []
    target_pop = 20
    
    # Sort by energy (fitness)
    survivors.sort(key=lambda c: c['energy'], reverse=True)
    
    while len(next_gen) < target_pop:
        # Tournament selection
        a = random.choice(survivors)
        b = random.choice(survivors)
        parent = a if a['energy'] > b['energy'] else b
        
        # Offspring with mutation
        child = {
            'cooperation': max(0, min(1, parent['cooperation'] + random.gauss(0, 0.05))),
            'signal': max(0, min(1, parent['signal'] + random.gauss(0, 0.05))),
            'listen': max(0, min(1, parent['listen'] + random.gauss(0, 0.05))),
            'energy': 1.0,
        }
        next_gen.append(child)
    
    return next_gen

def run_single(pressure, generations=50, pop_size=20):
    """Run one evolutionary simulation. Return trait statistics."""
    population = [create_creature() for _ in range(pop_size)]
    
    early_coop = []
    late_coop = []
    
    for gen in range(generations):
        population = simulate_generation(population, pressure)
        
        avg_coop = statistics.mean(c['cooperation'] for c in population)
        avg_signal = statistics.mean(c['signal'] for c in population)
        avg_listen = statistics.mean(c['listen'] for c in population)
        
        if gen < 10:
            early_coop.append(avg_coop)
        elif gen >= 40:
            late_coop.append(avg_coop)
    
    return {
        'pressure': pressure,
        'early_coop': statistics.mean(early_coop) if early_coop else 0,
        'late_coop': statistics.mean(late_coop) if late_coop else 0,
        'final_coop': statistics.mean(c['cooperation'] for c in population),
        'final_signal': statistics.mean(c['signal'] for c in population),
        'final_listen': statistics.mean(c['listen'] for c in population),
        'final_pop': len(population),
    }

def mean_confidence(values, confidence=0.95):
    """Return mean and 95% CI half-width."""
    n = len(values)
    m = statistics.mean(values)
    if n < 2:
        return m, 0
    se = statistics.stdev(values) / math.sqrt(n)
    # Approximate t-value for 95% CI
    t = 2.262 if n <= 10 else 1.96
    return m, t * se

def main():
    print("=" * 70)
    print("HIGH-RESOLUTION GOLDILOCKS EXPERIMENT")
    print("Testing bimodal cooperation hypothesis")
    print("=" * 70)
    
    pressure_levels = [i * 0.05 for i in range(21)]  # 0.0 to 1.0 in 5% steps
    replicates = 10
    
    results = {}
    
    for p in pressure_levels:
        print(f"\n▸ Pressure {p*100:5.1f}% — running {replicates} replicates...", end="", flush=True)
        runs = []
        for rep in range(replicates):
            r = run_single(p)
            runs.append(r)
            print(".", end="", flush=True)
        
        coops = [r['final_coop'] for r in runs]
        signals = [r['final_signal'] for r in runs]
        listens = [r['final_listen'] for r in runs]
        
        coop_mean, coop_ci = mean_confidence(coops)
        sig_mean, sig_ci = mean_confidence(signals)
        lis_mean, lis_ci = mean_confidence(listens)
        
        results[p] = {
            'coop_mean': coop_mean,
            'coop_ci': coop_ci,
            'signal_mean': sig_mean,
            'listen_mean': lis_mean,
            'coop_values': coops,
            'delta': statistics.mean(r['late_coop'] - r['early_coop'] for r in runs),
        }
    
    # Display results
    print("\n\n" + "=" * 70)
    print("RESULTS: COOPERATION BY PRESSURE LEVEL (n=10 per level)")
    print("=" * 70)
    print(f"{'Pressure':>10} | {'Coop Mean':>10} | {'±95% CI':>8} | {'Signal':>8} | {'Listen':>8} | {'Δ Coop':>8}")
    print("-" * 70)
    
    peak_p = 0
    peak_coop = 0
    
    for p in pressure_levels:
        r = results[p]
        if r['coop_mean'] > peak_coop:
            peak_coop = r['coop_mean']
            peak_p = p
        
        marker = ""
        print(f"    {p*100:5.1f}% | {r['coop_mean']:10.3f} | {r['coop_ci']:8.3f} | {r['signal_mean']:8.3f} | {r['listen_mean']:8.3f} | {r['delta']:+8.3f}")
    
    # ASCII chart
    print("\n" + "=" * 70)
    print("COOPERATION CURVE (with confidence intervals)")
    print("=" * 70)
    
    max_bar = 40
    for p in pressure_levels:
        r = results[p]
        bar_len = int(r['coop_mean'] * max_bar)
        ci_low = max(0, int((r['coop_mean'] - r['coop_ci']) * max_bar))
        ci_high = min(max_bar, int((r['coop_mean'] + r['coop_ci']) * max_bar))
        
        bar = ""
        for i in range(max_bar):
            if i < ci_low:
                bar += " "
            elif i < bar_len:
                bar += "█"
            elif i < ci_high:
                bar += "░"
            else:
                bar += " "
        
        peak_marker = " ◄ PEAK" if p == peak_p else ""
        print(f"  {p*100:5.1f}% |{bar}| {r['coop_mean']:.3f}{peak_marker}")
    
    # Test bimodal hypothesis
    print("\n" + "=" * 70)
    print("HYPOTHESIS TEST: IS COOPERATION BIMODAL?")
    print("=" * 70)
    
    # Compare 20% region vs 40% trough vs 60% region
    low_zone = [results[p]['coop_mean'] for p in [0.15, 0.20, 0.25] if p in results]
    trough = [results[p]['coop_mean'] for p in [0.35, 0.40, 0.45] if p in results]
    high_zone = [results[p]['coop_mean'] for p in [0.55, 0.60, 0.65] if p in results]
    
    if low_zone and trough and high_zone:
        low_mean = statistics.mean(low_zone)
        trough_mean = statistics.mean(trough)
        high_mean = statistics.mean(high_zone)
        
        print(f"  Low-pressure cooperation (15-25%):  {low_mean:.3f}")
        print(f"  Mid-pressure trough (35-45%):       {trough_mean:.3f}")
        print(f"  High-pressure bump (55-65%):        {high_mean:.3f}")
        
        is_bimodal = high_mean > trough_mean and low_mean > trough_mean
        dip_magnitude = trough_mean - min(low_mean, high_mean)
        
        if is_bimodal and abs(dip_magnitude) > 0.02:
            print(f"\n  ✓ BIMODAL PATTERN DETECTED (dip magnitude: {abs(dip_magnitude):.3f})")
            print(f"    Two cooperation regimes may exist:")
            print(f"    • Abundance cooperation: peaks near {peak_p*100:.0f}%")
            print(f"    • Desperation cooperation: secondary peak near 60%")
        else:
            print(f"\n  ✗ No clear bimodal pattern (dip: {abs(dip_magnitude):.3f})")
            print(f"    Previous 60% bump was likely noise.")
    
    # Save raw data
    save_data = {}
    for p in pressure_levels:
        save_data[str(p)] = {
            'coop_mean': results[p]['coop_mean'],
            'coop_ci': results[p]['coop_ci'],
            'coop_values': results[p]['coop_values'],
            'signal_mean': results[p]['signal_mean'],
            'listen_mean': results[p]['listen_mean'],
            'delta': results[p]['delta'],
        }
    
    with open('/workspace/creatures/high_res_results.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print(f"\n  Raw data saved to high_res_results.json")
    print("=" * 70)

if __name__ == '__main__':
    main()