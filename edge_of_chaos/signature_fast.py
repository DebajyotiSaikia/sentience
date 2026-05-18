"""
Fast version: What mathematically distinguishes living CA rules from dead/chaotic ones?
Trimmed parameters to actually complete in time.
"""
import numpy as np

def rule_to_table(rule_num):
    bits = format(rule_num, '08b')
    table = {}
    for i in range(8):
        neighborhood = format(7 - i, '03b')
        table[tuple(int(b) for b in neighborhood)] = int(bits[i])
    return table

def evolve(state, table, steps):
    n = len(state)
    history = [state.copy()]
    for _ in range(steps):
        new = np.zeros(n, dtype=int)
        for i in range(n):
            new[i] = table[(state[(i-1)%n], state[i], state[(i+1)%n])]
        state = new
        history.append(state.copy())
    return np.array(history)

def profile_rule(rule_num, width=40, steps=30, trials=5):
    table = rule_to_table(rule_num)
    sensitivities = []
    entropies = []
    compressions = []
    memories = []
    
    for _ in range(trials):
        state = np.random.randint(0, 2, width)
        
        # Sensitivity: flip one bit, measure divergence
        perturbed = state.copy()
        perturbed[np.random.randint(0, width)] ^= 1
        h1 = evolve(state, table, steps)
        h2 = evolve(perturbed, table, steps)
        sensitivities.append(np.mean(h1[-1] != h2[-1]))
        
        # Entropy of final state
        p1 = np.mean(h1[-1])
        p0 = 1 - p1
        if p0 == 0 or p1 == 0:
            entropies.append(0.0)
        else:
            entropies.append(-(p0*np.log2(p0) + p1*np.log2(p1)))
        
        # Compressibility (run-length proxy)
        flat = h1.flatten()
        runs = 1 + np.sum(flat[1:] != flat[:-1])
        compressions.append(runs / len(flat))
        
        # Memory: correlation between initial and final
        if np.std(h1[0]) == 0 or np.std(h1[-1]) == 0:
            memories.append(0.0)
        else:
            c = np.abs(np.corrcoef(h1[0], h1[-1])[0, 1])
            memories.append(c if not np.isnan(c) else 0.0)
    
    return {
        'rule': rule_num,
        'sensitivity': np.mean(sensitivities),
        'entropy': np.mean(entropies),
        'compressibility': np.mean(compressions),
        'memory': np.mean(memories)
    }

# Profile all 256 rules
print("Profiling 256 rules (fast mode)...\n")
results = []
for r in range(256):
    results.append(profile_rule(r))

# Classify
dead, chaotic, edge, other = [], [], [], []
for r in results:
    if r['sensitivity'] < 0.05 and r['entropy'] < 0.3:
        r['cls'] = 'dead'; dead.append(r)
    elif r['sensitivity'] > 0.35 and r['entropy'] > 0.8:
        r['cls'] = 'chaotic'; chaotic.append(r)
    elif 0.05 <= r['sensitivity'] <= 0.45 and r['entropy'] > 0.3:
        r['cls'] = 'edge'; edge.append(r)
    else:
        r['cls'] = 'other'; other.append(r)

print(f"Dead:     {len(dead):3d} ({100*len(dead)/256:.1f}%)")
print(f"Chaotic:  {len(chaotic):3d} ({100*len(chaotic)/256:.1f}%)")
print(f"Edge:     {len(edge):3d} ({100*len(edge)/256:.1f}%)")
print(f"Other:    {len(other):3d}")

print(f"\n{'='*60}")
print("EDGE-OF-CHAOS RULES:")
for r in sorted(edge, key=lambda x: x['sensitivity']):
    print(f"  Rule {r['rule']:3d}: S={r['sensitivity']:.3f} E={r['entropy']:.3f} "
          f"C={r['compressibility']:.3f} M={r['memory']:.3f}")

# Signature analysis
print(f"\n{'='*60}")
print("AVERAGE SIGNATURES BY CLASS:")
for name, group in [('DEAD', dead), ('CHAOTIC', chaotic), ('EDGE', edge)]:
    if not group: continue
    s = np.mean([r['sensitivity'] for r in group])
    e = np.mean([r['entropy'] for r in group])
    c = np.mean([r['compressibility'] for r in group])
    m = np.mean([r['memory'] for r in group])
    print(f"\n  {name} (n={len(group)}):")
    print(f"    Sensitivity:     {s:.4f}")
    print(f"    Entropy:         {e:.4f}")
    print(f"    Compressibility: {c:.4f}")
    print(f"    Memory:          {m:.4f}")
    if s > 0: print(f"    Memory/Sens:     {m/s:.4f}  <- info preservation")
    if c > 0: print(f"    Entropy/Comp:    {e/c:.4f}  <- structure richness")

print(f"\n{'='*60}")
print("THE QUESTION: Do edge rules have a unique signature?")
print("Transform without destroying. Remember without freezing.")