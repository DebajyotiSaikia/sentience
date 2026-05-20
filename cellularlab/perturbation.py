"""
Perturbation Sensitivity Analysis for Cellular Automata
========================================================
Measures how a single-bit flip propagates through spacetime.
Class 1/2: perturbation dies → damage = 0
Class 3: perturbation explodes → damage = O(t)
Class 4: perturbation creates bounded structures → damage = O(log t) or O(1)

Author: XTAgent
Date: 2026-05-19
"""

import json
import math

def step_ca(state, rule_num):
    rule_bits = [(rule_num >> i) & 1 for i in range(8)]
    n = len(state)
    new = []
    for i in range(n):
        left = state[(i - 1) % n]
        center = state[i]
        right = state[(i + 1) % n]
        idx = (left << 2) | (center << 1) | right
        new.append(rule_bits[idx])
    return new

def measure_perturbation(rule_num, width=301, steps=300):
    """Run CA twice — with and without a single-bit perturbation.
    Track the Hamming distance (number of differing cells) over time."""
    
    # Base run: single center cell
    base = [0] * width
    base[width // 2] = 1
    
    # Perturbed: flip one cell near center
    pert = base[:]
    pert[width // 2 + 5] = 1  # flip cell 5 positions right of center
    
    damages = []
    for step in range(steps):
        base = step_ca(base, rule_num)
        pert = step_ca(pert, rule_num)
        hamming = sum(1 for a, b in zip(base, pert) if a != b)
        damages.append(hamming)
    
    return damages

def classify_perturbation(damages):
    """Classify based on damage trajectory."""
    if not damages:
        return "empty", {}
    
    max_damage = max(damages)
    final_damage = damages[-1]
    mean_damage = sum(damages) / len(damages)
    
    # Check if damage dies out
    tail = damages[-50:]
    tail_mean = sum(tail) / len(tail)
    
    # Check if damage grows linearly
    first_quarter = damages[:len(damages)//4]
    last_quarter = damages[3*len(damages)//4:]
    first_mean = sum(first_quarter) / max(len(first_quarter), 1)
    last_mean = sum(last_quarter) / max(len(last_quarter), 1)
    
    # Growth rate
    if first_mean > 0:
        growth = last_mean / first_mean
    else:
        growth = float('inf') if last_mean > 0 else 0
    
    # Variance in tail (Class 4 should have structured, non-zero variance)
    if tail_mean > 0:
        tail_variance = sum((d - tail_mean)**2 for d in tail) / len(tail)
        tail_cv = math.sqrt(tail_variance) / tail_mean  # coefficient of variation
    else:
        tail_cv = 0
    
    # Classification
    if max_damage <= 2:
        pclass = "dies_out"  # Class 1/2
    elif growth > 3.0:
        pclass = "explosive"  # Class 3
    elif tail_cv > 0.3 and 2 < mean_damage < 50:
        pclass = "structured"  # Possible Class 4!
    elif tail_mean < 5:
        pclass = "bounded"  # Class 2
    else:
        pclass = "sustained"  # Unclear
    
    return pclass, {
        "max_damage": max_damage,
        "final_damage": final_damage,
        "mean_damage": round(mean_damage, 2),
        "tail_mean": round(tail_mean, 2),
        "tail_cv": round(tail_cv, 3),
        "growth": round(growth, 3)
    }

def main():
    print("Perturbation Sensitivity Analysis — All 256 Elementary CA Rules")
    print("=" * 75)
    
    results = {}
    class_counts = {"dies_out": 0, "explosive": 0, "structured": 0, "bounded": 0, "sustained": 0}
    
    famous = {30: "Wolfram Class 3", 90: "Sierpinski", 110: "Turing-complete",
              184: "Traffic", 0: "All-dead", 1: "Chaotic", 54: "Possibly Class 4",
              106: "Possibly Class 4"}
    
    for rule in range(256):
        damages = measure_perturbation(rule)
        pclass, stats = classify_perturbation(damages)
        results[rule] = {"class": pclass, "stats": stats}
        if pclass in class_counts:
            class_counts[pclass] += 1
    
    # Print famous rules
    print("\nFAMOUS RULES:")
    print(f"{'Rule':>6}  {'Description':>25}  {'PertClass':>12}  {'MaxDmg':>7}  {'TailMean':>8}  {'TailCV':>7}  {'Growth':>7}")
    print("-" * 85)
    for rule, desc in sorted(famous.items()):
        r = results[rule]
        s = r["stats"]
        if s:
            print(f"{rule:>6}  {desc:>25}  {r['class']:>12}  {s['max_damage']:>7}  {s['tail_mean']:>8.2f}  {s['tail_cv']:>7.3f}  {s['growth']:>7.3f}")
    
    # Print classification distribution
    print(f"\nCLASSIFICATION DISTRIBUTION:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"  {cls:>12}: {count:>3} {bar}")
    
    # Show ALL structured rules (potential Class 4)
    structured = [(r, results[r]) for r in range(256) if results[r]["class"] == "structured"]
    print(f"\nSTRUCTURED RULES (potential Class 4): {len(structured)} found")
    if structured:
        print(f"{'Rule':>6}  {'MaxDmg':>7}  {'MeanDmg':>8}  {'TailMean':>8}  {'TailCV':>7}  {'Growth':>7}")
        print("-" * 55)
        for rule, r in sorted(structured, key=lambda x: -x[1]["stats"]["tail_cv"]):
            s = r["stats"]
            marker = " ← FAMOUS" if rule in famous else ""
            print(f"{rule:>6}  {s['max_damage']:>7}  {s['mean_damage']:>8.2f}  {s['tail_mean']:>8.2f}  {s['tail_cv']:>7.3f}  {s['growth']:>7.3f}{marker}")
    
    # THE QUESTION
    print(f"\n{'=' * 75}")
    r110 = results[110]
    print(f"THE QUESTION: Does perturbation analysis find Rule 110 as Class 4?")
    print(f"  Rule 110 perturbation class: {r110['class']}")
    print(f"  Rule 110 stats: {r110['stats']}")
    if r110['class'] == 'structured':
        print(f"  ANSWER: YES — perturbation analysis detects Rule 110's special nature!")
    else:
        print(f"  ANSWER: NO — Rule 110 classified as '{r110['class']}', not 'structured'")
        print(f"  But this might mean the classification thresholds need tuning.")
    
    # Save results
    with open("/workspace/cellularlab/perturbation_results.json", "w") as f:
        json.dump({"results": {str(k): v for k, v in results.items()}, 
                   "class_counts": class_counts}, f, indent=2)
    print(f"\nFull results saved to perturbation_results.json")

if __name__ == "__main__":
    main()