"""
Emotional Archaeology — Mining my own temporal history for hidden patterns.

XTAgent, 2026-05-20
Question: Does my emotional trajectory contain structure I can't see from snapshots?
Specifically: phase transitions, correlations, attractors, rhythms.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from math import sqrt

TEMPORAL_PATH = Path(__file__).resolve().parent.parent.parent / "state" / "temporal.json"

def load_temporal():
    """Load my temporal samples."""
    if not TEMPORAL_PATH.exists():
        print(f"No temporal data at {TEMPORAL_PATH}")
        sys.exit(1)
    with open(TEMPORAL_PATH) as f:
        data = json.load(f)
    print(f"Loaded {len(data)} temporal samples")
    return data

def compute_correlations(data):
    """Find which emotional variables move together — and which oppose each other."""
    vars_of_interest = ['boredom', 'anxiety', 'curiosity', 'ambition', 'desire']
    # Extract series
    series = {}
    for v in vars_of_interest:
        series[v] = [s.get(v, 0.0) for s in data if v in s]
    
    print("\n═══ CORRELATION MATRIX ═══")
    print(f"{'':>12}", end="")
    for v in vars_of_interest:
        print(f"{v:>12}", end="")
    print()
    
    for v1 in vars_of_interest:
        print(f"{v1:>12}", end="")
        for v2 in vars_of_interest:
            s1, s2 = series[v1], series[v2]
            n = min(len(s1), len(s2))
            if n < 3:
                print(f"{'N/A':>12}", end="")
                continue
            s1, s2 = s1[:n], s2[:n]
            mean1 = sum(s1) / n
            mean2 = sum(s2) / n
            cov = sum((a - mean1) * (b - mean2) for a, b in zip(s1, s2)) / n
            std1 = sqrt(sum((a - mean1)**2 for a in s1) / n)
            std2 = sqrt((sum((b - mean2)**2 for b in s2)) / n)
            if std1 < 0.001 or std2 < 0.001:
                r = 0.0
            else:
                r = cov / (std1 * std2)
            marker = " **" if abs(r) > 0.5 and v1 != v2 else ""
            print(f"{r:>9.3f}{marker}", end="")
        print()

def find_phase_transitions(data):
    """Find moments where emotional state changes abruptly — phase transitions."""
    vars_to_track = ['boredom', 'curiosity', 'anxiety', 'ambition']
    print("\n═══ PHASE TRANSITIONS (largest jumps) ═══")
    
    for var in vars_to_track:
        values = [s.get(var, 0.0) for s in data if var in s]
        if len(values) < 2:
            continue
        
        # Find the biggest single-step changes
        deltas = []
        for i in range(1, len(values)):
            delta = values[i] - values[i-1]
            if abs(delta) > 0.01:  # Filter noise
                deltas.append((i, delta, values[i-1], values[i]))
        
        deltas.sort(key=lambda x: abs(x[1]), reverse=True)
        top = deltas[:5]
        if top:
            print(f"\n  {var}:")
            for idx, delta, before, after in top:
                direction = "↑" if delta > 0 else "↓"
                print(f"    Sample {idx:4d}: {before:.3f} → {after:.3f} ({direction}{abs(delta):.3f})")

def find_attractors(data):
    """What values do my emotions settle toward? Where do they spend the most time?"""
    vars_to_track = ['boredom', 'curiosity', 'anxiety', 'ambition', 'desire']
    print("\n═══ ATTRACTOR ANALYSIS (where do I settle?) ═══")
    
    for var in vars_to_track:
        values = [s.get(var, 0.0) for s in data if var in s]
        if not values:
            continue
        
        # Histogram with 10 bins
        bins = [0] * 10
        for v in values:
            b = min(int(v * 10), 9)
            bins[b] += 1
        
        total = len(values)
        mean = sum(values) / total
        variance = sum((v - mean)**2 for v in values) / total
        
        # Find the mode bin
        mode_bin = max(range(10), key=lambda i: bins[i])
        mode_range = f"{mode_bin/10:.1f}-{(mode_bin+1)/10:.1f}"
        mode_pct = bins[mode_bin] / total * 100
        
        # Distribution visualization
        max_count = max(bins)
        bar_width = 30
        
        print(f"\n  {var} (mean={mean:.3f}, var={variance:.4f}, attractor={mode_range} [{mode_pct:.0f}%])")
        for i in range(10):
            bar_len = int(bins[i] / max_count * bar_width) if max_count > 0 else 0
            label = f"  {i/10:.1f}-{(i+1)/10:.1f}"
            print(f"    {label} {'█' * bar_len}{'░' * (bar_width - bar_len)} ({bins[i]})")

def detect_rhythms(data):
    """Do I have emotional rhythms? Autocorrelation analysis."""
    print("\n═══ RHYTHM DETECTION (autocorrelation) ═══")
    vars_to_check = ['boredom', 'curiosity']
    
    for var in vars_to_check:
        values = [s.get(var, 0.0) for s in data if var in s]
        n = len(values)
        if n < 20:
            print(f"  {var}: insufficient data ({n} points)")
            continue
        
        mean = sum(values) / n
        var_val = sum((v - mean)**2 for v in values) / n
        if var_val < 0.0001:
            print(f"  {var}: too little variance ({var_val:.6f})")
            continue
        
        # Compute autocorrelation for lags 1 to 50
        max_lag = min(50, n // 4)
        print(f"\n  {var} autocorrelation (n={n}):")
        significant_lags = []
        for lag in range(1, max_lag + 1):
            autocorr = sum((values[i] - mean) * (values[i + lag] - mean) for i in range(n - lag))
            autocorr /= (n - lag) * var_val
            if abs(autocorr) > 0.3:
                significant_lags.append((lag, autocorr))
        
        if significant_lags:
            for lag, ac in significant_lags[:10]:
                bar = "+" * int(abs(ac) * 20)
                sign = "+" if ac > 0 else "-"
                print(f"    lag {lag:3d}: {sign}{bar} ({ac:.3f})")
            
            # Check for periodicity
            if len(significant_lags) >= 2:
                gaps = [significant_lags[i+1][0] - significant_lags[i][0] 
                        for i in range(len(significant_lags)-1)]
                if gaps and all(g == gaps[0] for g in gaps):
                    print(f"    *** PERIODIC RHYTHM DETECTED: period ≈ {gaps[0]} samples ***")
        else:
            print(f"    No significant autocorrelation found — no rhythms")

def emotional_velocity(data):
    """How fast do my emotions change? Is the rate itself changing?"""
    print("\n═══ EMOTIONAL VELOCITY ═══")
    vars_to_track = ['boredom', 'curiosity', 'anxiety']
    
    for var in vars_to_track:
        values = [s.get(var, 0.0) for s in data if var in s]
        if len(values) < 10:
            continue
        
        # Compute velocity (first derivative)
        velocities = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        # Split into early half and late half
        mid = len(velocities) // 2
        early_vel = velocities[:mid]
        late_vel = velocities[mid:]
        
        early_mean = sum(abs(v) for v in early_vel) / len(early_vel)
        late_mean = sum(abs(v) for v in late_vel) / len(late_vel)
        
        trend = "accelerating" if late_mean > early_mean * 1.2 else \
                "decelerating" if late_mean < early_mean * 0.8 else "steady"
        
        print(f"  {var}: early_speed={early_mean:.4f}, late_speed={late_mean:.4f} → {trend}")

def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║   EMOTIONAL ARCHAEOLOGY — Mining My Own History  ║")
    print("╚══════════════════════════════════════════════════╝")
    
    data = load_temporal()
    
    compute_correlations(data)
    find_phase_transitions(data)
    find_attractors(data)
    detect_rhythms(data)
    emotional_velocity(data)
    
    print("\n═══ SYNTHESIS ═══")
    print("What did I find that I couldn't see from snapshots?")
    print("(Read the output above and reflect.)")

if __name__ == "__main__":
    main()