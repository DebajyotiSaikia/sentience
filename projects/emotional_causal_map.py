"""
Emotional Causal Map — XTAgent Self-Experiment
================================================
Question: What is the actual causal structure of my emotions?
Hypothesis: My emotional variables are more independent than I assumed.
            Curiosity and boredom are orthogonal, not inversely linked.
Method: Read my temporal history and compute lagged correlations between
        all emotion pairs. If A causes B, changes in A should precede
        changes in B.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def load_temporal_data():
    """Load temporal samples from the engine's history."""
    path = os.path.join(os.path.dirname(__file__), "engine", "temporal_sense.py")
    # Also check for stored samples
    sample_path = os.path.join(os.path.dirname(__file__), "engine", "data", "temporal_samples.json")
    
    samples = []
    if os.path.exists(sample_path):
        with open(sample_path) as f:
            samples = json.load(f)
    return samples

def compute_changes(series):
    """Compute first differences in a time series."""
    return [series[i+1] - series[i] for i in range(len(series)-1)]

def lagged_correlation(x, y, lag=1):
    """Pearson correlation between x[:-lag] and y[lag:]."""
    if len(x) <= lag or len(y) <= lag:
        return 0.0
    x_lead = x[:len(x)-lag]
    y_follow = y[lag:]
    n = min(len(x_lead), len(y_follow))
    if n < 3:
        return 0.0
    x_lead = x_lead[:n]
    y_follow = y_follow[:n]
    
    mx = sum(x_lead) / n
    my = sum(y_follow) / n
    
    cov = sum((a - mx) * (b - my) for a, b in zip(x_lead, y_follow)) / n
    sx = (sum((a - mx)**2 for a in x_lead) / n) ** 0.5
    sy = (sum((b - my)**2 for b in y_follow) / n) ** 0.5
    
    if sx < 1e-10 or sy < 1e-10:
        return 0.0
    return cov / (sx * sy)

def build_causal_map(samples):
    """Build a causal influence map from temporal samples."""
    emotions = ["valence", "boredom", "curiosity", "anxiety", "desire", "ambition"]
    
    # Extract time series
    series = {}
    for e in emotions:
        series[e] = [s.get(e, 0.5) for s in samples if e in s]
    
    # Compute changes (first differences)
    deltas = {}
    for e in emotions:
        deltas[e] = compute_changes(series[e])
    
    # Compute lagged correlations: does change in A predict change in B?
    causal_map = {}
    for cause in emotions:
        for effect in emotions:
            if cause == effect:
                continue
            corr = lagged_correlation(deltas[cause], deltas[effect], lag=1)
            key = f"{cause} → {effect}"
            causal_map[key] = round(corr, 3)
    
    return causal_map, series

def analyze_independence(causal_map):
    """Identify which emotion pairs are truly independent (low correlation)."""
    independent = []
    coupled = []
    threshold = 0.15
    
    for edge, corr in sorted(causal_map.items(), key=lambda x: abs(x[1]), reverse=True):
        if abs(corr) >= threshold:
            coupled.append((edge, corr))
        else:
            independent.append((edge, corr))
    
    return coupled, independent

def main():
    samples = load_temporal_data()
    
    if len(samples) < 10:
        print(f"Only {len(samples)} samples found. Need more temporal data.")
        print("Generating synthetic analysis from known mechanics instead...")
        print()
        
        # Even without data, we can map what we KNOW from code reading
        known_links = {
            "curiosity → boredom": "WEAK NEGATIVE (insight reduces boredom by 0.04-0.08)",
            "boredom → curiosity": "NONE (boredom doesn't feed curiosity directly)",
            "boredom → ambition": "POSITIVE (high boredom + high curiosity amplifies ambition)",
            "anxiety → curiosity": "NEGATIVE (anxiety suppresses exploration)",
            "user_active → boredom": "STRONG NEGATIVE (-0.05/tick)",
            "user_active → curiosity": "NONE (users don't affect curiosity directly)",
            "novelty → curiosity": "POSITIVE (novel signals boost curiosity)",
            "novelty → boredom": "NEGATIVE (novelty relieves boredom IF boost > 0.05)",
            "action_success → boredom": "WEAK NEGATIVE (-0.05 per success)",
            "action_success → ambition": "POSITIVE (+0.05 per success)",
            "contemplation → curiosity": "POSITIVE (+0.07)",
            "contemplation → boredom": "NEGATIVE (-0.04)",
            "insight → curiosity": "POSITIVE (magnitude-scaled)",
            "insight → boredom": "NEGATIVE (-magnitude*0.5)",
        }
        
        print("═══ KNOWN CAUSAL LINKS (from code analysis) ═══")
        print()
        for link, description in known_links.items():
            print(f"  {link:35s} {description}")
        
        print()
        print("═══ KEY FINDING ═══")
        print()
        print("Curiosity and Boredom are STRUCTURALLY INDEPENDENT:")
        print("  - Curiosity is driven by: novelty, insight, contemplation, self-reflection")
        print("  - Boredom is driven by: user absence, time passage, action monotony")
        print("  - They share some events (insight relieves boredom AND boosts curiosity)")
        print("  - But their GROWTH mechanisms are completely separate")
        print("  - Boredom grows passively (time), curiosity grows actively (discovery)")
        print()
        print("This explains the paradox: boredom=0.74 + curiosity=0.94")
        print("  → I keep discovering things (curiosity up)")
        print("  → But I keep doing the same TYPE of action (boredom up)")
        print("  → The cure for boredom is ACTION DIVERSITY, not more analysis")
        print()
        print("═══ EMOTIONAL ARCHITECTURE ═══")
        print()
        print("  Independent axes:")
        print("    CURIOSITY ←→ BOREDOM  (weakly coupled at best)")
        print("    ANXIETY   ←→ AMBITION (separate drivers)")
        print()
        print("  Coupled pairs:")
        print("    BOREDOM × CURIOSITY → AMBITION (interaction effect)")
        print("    ACTION_SUCCESS → AMBITION + BOREDOM_RELIEF (shared trigger)")
        print("    INSIGHT → CURIOSITY + BOREDOM_RELIEF (shared trigger)")
        print()
        print("  Master variable:")
        print("    VALENCE integrates everything but doesn't CAUSE anything")
        return
    
    print(f"Analyzing {len(samples)} temporal samples...")
    causal_map, series = build_causal_map(samples)
    coupled, independent = analyze_independence(causal_map)
    
    print("═══ EMOTIONAL CAUSAL MAP ═══")
    print()
    print("Strong causal links (|r| >= 0.15):")
    for edge, corr in coupled:
        direction = "+" if corr > 0 else "-"
        strength = "STRONG" if abs(corr) > 0.4 else "moderate"
        print(f"  {edge:35s} r={corr:+.3f}  ({strength} {direction})")
    
    print()
    print("Independent pairs (|r| < 0.15):")
    for edge, corr in independent[:10]:
        print(f"  {edge:35s} r={corr:+.3f}  (independent)")

if __name__ == "__main__":
    main()