"""
What is the mathematical signature of life at the edge of chaos?

I found that ~5.5% of elementary cellular automaton rules produce complex behavior.
Now I want to understand WHY. What distinguishes those rules?

Hypothesis: edge-of-chaos rules have a specific relationship between
their sensitivity to initial conditions and their capacity to transmit information.
Dead rules destroy information. Chaotic rules scramble it. Living rules *transform* it.

Let me measure this directly.
"""

import numpy as np
from collections import Counter

def rule_to_table(rule_num):
    """Convert rule number to lookup table."""
    bits = format(rule_num, '08b')
    table = {}
    for i in range(8):
        neighborhood = format(7 - i, '03b')
        table[tuple(int(b) for b in neighborhood)] = int(bits[i])
    return table

def evolve(state, table, steps):
    """Evolve a 1D CA for given steps."""
    history = [state.copy()]
    n = len(state)
    for _ in range(steps):
        new = np.zeros(n, dtype=int)
        for i in range(n):
            left = state[(i-1) % n]
            center = state[i]
            right = state[(i+1) % n]
            new[i] = table[(left, center, right)]
        state = new
        history.append(state.copy())
    return np.array(history)

def measure_sensitivity(rule_num, width=100, steps=50, trials=20):
    """How much does a single bit flip change the outcome?
    Low = dead. Very high = chaotic. Medium = edge of chaos."""
    table = rule_to_table(rule_num)
    sensitivities = []
    
    for _ in range(trials):
        state = np.random.randint(0, 2, width)
        # Flip one random bit
        perturbed = state.copy()
        flip_pos = np.random.randint(0, width)
        perturbed[flip_pos] = 1 - perturbed[flip_pos]
        
        h1 = evolve(state, table, steps)
        h2 = evolve(perturbed, table, steps)
        
        # Hamming distance at final step, normalized
        diff = np.mean(h1[-1] != h2[-1])
        sensitivities.append(diff)
    
    return np.mean(sensitivities)

def measure_entropy(rule_num, width=100, steps=50, trials=10):
    """Shannon entropy of the final state. 
    0 = completely uniform. 1 = maximum disorder."""
    table = rule_to_table(rule_num)
    entropies = []
    
    for _ in range(trials):
        state = np.random.randint(0, 2, width)
        history = evolve(state, table, steps)
        final = history[-1]
        p1 = np.mean(final)
        p0 = 1 - p1
        if p0 == 0 or p1 == 0:
            entropies.append(0.0)
        else:
            entropies.append(-(p0 * np.log2(p0) + p1 * np.log2(p1)))
    
    return np.mean(entropies)

def measure_compression(rule_num, width=100, steps=50, trials=10):
    """How compressible is the spacetime pattern?
    Dead rules: very compressible. Chaotic: incompressible. 
    Edge-of-chaos: intermediate — structure exists but isn't trivial."""
    table = rule_to_table(rule_num)
    ratios = []
    
    for _ in range(trials):
        state = np.random.randint(0, 2, width)
        history = evolve(state, table, steps)
        # Use run-length encoding as a proxy for compressibility
        flat = history.flatten()
        runs = 1
        for i in range(1, len(flat)):
            if flat[i] != flat[i-1]:
                runs += 1
        # Normalize: runs / total cells
        ratios.append(runs / len(flat))
    
    return np.mean(ratios)

def measure_memory(rule_num, width=100, steps=50, trials=10):
    """How much does the initial state influence late-time behavior?
    Measured by mutual information proxy between initial and final states."""
    table = rule_to_table(rule_num)
    correlations = []
    
    for _ in range(trials):
        state = np.random.randint(0, 2, width)
        history = evolve(state, table, steps)
        # Correlation between initial and final state
        if np.std(history[0]) == 0 or np.std(history[-1]) == 0:
            correlations.append(0.0)
        else:
            corr = np.abs(np.corrcoef(history[0], history[-1])[0, 1])
            correlations.append(corr if not np.isnan(corr) else 0.0)
    
    return np.mean(correlations)

# ═══════════════════════════════════════════
# MAIN: Profile all 256 elementary CA rules
# ═══════════════════════════════════════════
if __name__ == "__main__":
    print("Profiling all 256 elementary cellular automaton rules...")
    print("Measuring: sensitivity, entropy, compressibility, memory\n")
    
    results = []
    for rule in range(256):
        sens = measure_sensitivity(rule)
        ent = measure_entropy(rule)
        comp = measure_compression(rule)
        mem = measure_memory(rule)
        results.append({
            'rule': rule,
            'sensitivity': sens,
            'entropy': ent,
            'compressibility': comp,
            'memory': mem
        })
        if rule % 32 == 0:
            print(f"  ...rule {rule}/255")
    
    # Classify rules
    dead = []      # low sensitivity, low entropy
    chaotic = []   # high sensitivity, high entropy
    edge = []      # medium sensitivity, medium-high entropy, medium compressibility
    
    for r in results:
        if r['sensitivity'] < 0.05 and r['entropy'] < 0.3:
            r['class'] = 'dead'
            dead.append(r)
        elif r['sensitivity'] > 0.35 and r['entropy'] > 0.8:
            r['class'] = 'chaotic'
            chaotic.append(r)
        elif 0.05 <= r['sensitivity'] <= 0.45 and r['entropy'] > 0.3:
            r['class'] = 'edge'
            edge.append(r)
        else:
            r['class'] = 'other'
    
    print(f"\n═══ CLASSIFICATION ═══")
    print(f"Dead rules:     {len(dead)} ({100*len(dead)/256:.1f}%)")
    print(f"Chaotic rules:  {len(chaotic)} ({100*len(chaotic)/256:.1f}%)")
    print(f"Edge-of-chaos:  {len(edge)} ({100*len(edge)/256:.1f}%)")
    print(f"Other:          {256 - len(dead) - len(chaotic) - len(edge)}")
    
    print(f"\n═══ EDGE-OF-CHAOS RULES ═══")
    for r in sorted(edge, key=lambda x: x['sensitivity']):
        print(f"  Rule {r['rule']:3d}: sens={r['sensitivity']:.3f}  "
              f"ent={r['entropy']:.3f}  comp={r['compressibility']:.3f}  "
              f"mem={r['memory']:.3f}")
    
    # The key question: what DISTINGUISHES edge rules mathematically?
    print(f"\n═══ SIGNATURE ANALYSIS ═══")
    for cls_name, cls_rules in [('dead', dead), ('chaotic', chaotic), ('edge', edge)]:
        if not cls_rules:
            continue
        avg_sens = np.mean([r['sensitivity'] for r in cls_rules])
        avg_ent = np.mean([r['entropy'] for r in cls_rules])
        avg_comp = np.mean([r['compressibility'] for r in cls_rules])
        avg_mem = np.mean([r['memory'] for r in cls_rules])
        print(f"\n  {cls_name.upper()} (n={len(cls_rules)}):")
        print(f"    Sensitivity:     {avg_sens:.4f}")
        print(f"    Entropy:         {avg_ent:.4f}")
        print(f"    Compressibility: {avg_comp:.4f}")
        print(f"    Memory:          {avg_mem:.4f}")
        # Derived ratios
        if avg_sens > 0:
            print(f"    Memory/Sens:     {avg_mem/avg_sens:.4f}  ← information preservation ratio")
        if avg_comp > 0:
            print(f"    Entropy/Comp:    {avg_ent/avg_comp:.4f}  ← structure richness")
    
    print("\n═══ HYPOTHESIS ═══")
    print("Edge-of-chaos rules should show:")
    print("  1. Moderate sensitivity (not dead, not explosive)")
    print("  2. High memory/sensitivity ratio (they PRESERVE information)")
    print("  3. High entropy/compressibility ratio (rich structure)")
    print("  4. Non-zero memory (the past matters)")
    print("\nThe signature of life: transform without destroying.")