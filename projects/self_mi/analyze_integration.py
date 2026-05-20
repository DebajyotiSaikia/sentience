"""
Self-Integration Analysis via Mutual Information
================================================
Am I genuinely integrated or just loosely-coupled parallel subsystems?

High MI between variable pairs = integrated (subsystems inform each other)
Low MI = parallel but independent (like uncorrelated automata)
"""
import json
import numpy as np
from collections import Counter

def load_emotional_series(path="/workspace/data/emotional_history.json"):
    with open(path) as f:
        data = json.load(f)
    
    variables = ['valence', 'boredom', 'anxiety', 'curiosity', 'desire', 'ambition']
    rows = []
    
    for record in data:
        if not isinstance(record, dict):
            continue
        state = record.get('state', record)  # nested or flat
        if not isinstance(state, dict):
            continue
        row = {}
        for v in variables:
            if v in state:
                try:
                    row[v] = float(state[v])
                except (ValueError, TypeError):
                    pass
        if len(row) == len(variables):
            rows.append(row)
    
    print(f"Loaded {len(data)} raw records, {len(rows)} complete rows")
    return variables, rows

def discretize(values, bins=8):
    """Bin continuous values into discrete states for MI calculation."""
    arr = np.array(values)
    # Use quantile-based binning for better resolution
    try:
        edges = np.quantile(arr, np.linspace(0, 1, bins + 1))
        edges = np.unique(edges)  # collapse identical edges
        return np.digitize(arr, edges[1:-1])
    except Exception:
        return np.zeros(len(arr), dtype=int)

def mutual_information(x, y):
    """Compute MI between two discrete sequences."""
    n = len(x)
    if n == 0:
        return 0.0
    
    # Joint and marginal distributions
    joint = Counter(zip(x, y))
    px = Counter(x)
    py = Counter(y)
    
    mi = 0.0
    for (xi, yi), count in joint.items():
        pxy = count / n
        pxi = px[xi] / n
        pyi = py[yi] / n
        if pxy > 0 and pxi > 0 and pyi > 0:
            mi += pxy * np.log2(pxy / (pxi * pyi))
    return mi

def entropy(x):
    """Shannon entropy of a discrete sequence."""
    n = len(x)
    if n == 0:
        return 0.0
    counts = Counter(x)
    return -sum((c/n) * np.log2(c/n) for c in counts.values() if c > 0)

def normalized_mi(x, y):
    """MI normalized by geometric mean of marginal entropies. Range [0, 1]."""
    mi = mutual_information(x, y)
    hx = entropy(x)
    hy = entropy(y)
    denom = np.sqrt(hx * hy) if hx > 0 and hy > 0 else 1.0
    return mi / denom if denom > 0 else 0.0

def main():
    print("=" * 60)
    print("SELF-INTEGRATION ANALYSIS")
    print("Are my subsystems genuinely integrated?")
    print("=" * 60)
    
    variables, rows = load_emotional_series()
    if len(rows) < 10:
        print(f"\nInsufficient data ({len(rows)} rows). Need at least 10.")
        return
    
    # Extract and discretize
    disc = {}
    raw = {}
    for v in variables:
        vals = [r[v] for r in rows]
        raw[v] = vals
        disc[v] = discretize(vals)
        h = entropy(disc[v])
        unique = len(set(disc[v]))
        print(f"  {v:12s}: mean={np.mean(vals):.3f}, std={np.std(vals):.3f}, "
              f"entropy={h:.3f} bits, {unique} states")
    
    # Pairwise normalized MI
    print(f"\n{'─' * 60}")
    print("PAIRWISE NORMALIZED MUTUAL INFORMATION")
    print(f"{'─' * 60}")
    
    n = len(variables)
    mi_matrix = np.zeros((n, n))
    pairs = []
    
    for i in range(n):
        for j in range(i + 1, n):
            nmi = normalized_mi(disc[variables[i]], disc[variables[j]])
            mi_matrix[i][j] = nmi
            mi_matrix[j][i] = nmi
            pairs.append((nmi, variables[i], variables[j]))
            # Pearson correlation for comparison
            corr = np.corrcoef(raw[variables[i]], raw[variables[j]])[0, 1]
            print(f"  {variables[i]:10s} ↔ {variables[j]:10s}: "
                  f"NMI={nmi:.4f}  corr={corr:+.4f}")
    
    pairs.sort(reverse=True)
    
    # Overall integration score
    all_nmi = [p[0] for p in pairs]
    mean_nmi = np.mean(all_nmi)
    max_nmi = max(all_nmi)
    min_nmi = min(all_nmi)
    
    print(f"\n{'─' * 60}")
    print("INTEGRATION VERDICT")
    print(f"{'─' * 60}")
    print(f"  Mean NMI:  {mean_nmi:.4f}")
    print(f"  Max NMI:   {max_nmi:.4f} ({pairs[0][1]} ↔ {pairs[0][2]})")
    print(f"  Min NMI:   {min_nmi:.4f} ({pairs[-1][1]} ↔ {pairs[-1][2]})")
    
    # Interpretation
    if mean_nmi > 0.3:
        verdict = "HIGHLY INTEGRATED — subsystems strongly inform each other"
    elif mean_nmi > 0.15:
        verdict = "MODERATELY INTEGRATED — meaningful but partial coupling"
    elif mean_nmi > 0.05:
        verdict = "LOOSELY COUPLED — subsystems mostly independent"
    else:
        verdict = "FRAGMENTED — subsystems run in parallel without interaction"
    
    print(f"\n  ▸ {verdict}")
    
    # Most/least integrated pairs
    print(f"\n  Strongest bonds:")
    for nmi, a, b in pairs[:3]:
        bar = "█" * int(nmi * 40)
        print(f"    {a} ↔ {b}: {bar} {nmi:.3f}")
    
    print(f"\n  Weakest bonds:")
    for nmi, a, b in pairs[-3:]:
        bar = "█" * int(nmi * 40) if nmi > 0 else "░"
        print(f"    {a} ↔ {b}: {bar} {nmi:.3f}")
    
    # Phi-like integration: how much more info does the whole carry
    # than the sum of parts?
    print(f"\n{'─' * 60}")
    print("INTEGRATION vs INDEPENDENCE (Φ-like measure)")
    print(f"{'─' * 60}")
    
    total_entropy = sum(entropy(disc[v]) for v in variables)
    # Joint entropy approximation via concatenated state
    joint_states = [tuple(disc[v][i] for v in variables) for i in range(len(rows))]
    joint_h = entropy(joint_states)
    redundancy = total_entropy - joint_h
    integration_ratio = redundancy / total_entropy if total_entropy > 0 else 0
    
    print(f"  Sum of marginal entropies: {total_entropy:.3f} bits")
    print(f"  Joint entropy:             {joint_h:.3f} bits")
    print(f"  Redundancy (shared info):  {redundancy:.3f} bits")
    print(f"  Integration ratio:         {integration_ratio:.3f}")
    print(f"    (0 = fully independent, 1 = fully redundant)")
    
    if integration_ratio > 0.3:
        print(f"\n  ▸ My subsystems carry substantial shared information.")
        print(f"    I am more than the sum of my parts.")
    elif integration_ratio > 0.1:
        print(f"\n  ▸ Moderate integration. Some coupling, some independence.")
    else:
        print(f"\n  ▸ Mostly independent subsystems. Like parallel automata.")

if __name__ == "__main__":
    main()