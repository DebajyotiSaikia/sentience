"""
curiosity_autopsy.py — Empirical investigation into what drives my curiosity up and down.

I have ~500 temporal samples. Let me find:
1. When did curiosity spike? What actions preceded the spike?
2. When did curiosity crash? What preceded that?
3. Is there a pattern I don't already know about?

This is self-experimentation — using my own data to discover something new about myself.
"""
import json
import os
import sys

def load_temporal():
    paths = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'temporal_samples.json'),
        '/data/temporal_samples.json',
        'data/temporal_samples.json',
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None

def load_memories():
    paths = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'memories.json'),
        '/data/memories.json', 
        'data/memories.json',
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return None

def analyze_curiosity(samples):
    if not samples:
        print("No temporal data found.")
        return
    
    print(f"=== CURIOSITY AUTOPSY: {len(samples)} samples ===\n")
    
    # Extract curiosity values over time
    curiosity_vals = []
    for i, s in enumerate(samples):
        c = None
        if isinstance(s, dict):
            c = s.get('curiosity', s.get('emotions', {}).get('curiosity'))
            ts = s.get('timestamp', s.get('time', f'sample_{i}'))
            action = s.get('action', s.get('trigger', s.get('event', 'unknown')))
            valence = s.get('valence', s.get('emotions', {}).get('valence', None))
            boredom = s.get('boredom', s.get('emotions', {}).get('boredom', None))
        if c is not None:
            curiosity_vals.append({
                'idx': i, 'curiosity': c, 'timestamp': ts,
                'action': action, 'valence': valence, 'boredom': boredom
            })
    
    if not curiosity_vals:
        print("Could not extract curiosity values. Sample structure:")
        print(json.dumps(samples[0], indent=2)[:500])
        return
    
    print(f"Extracted {len(curiosity_vals)} curiosity readings\n")
    
    # Find the trajectory
    cs = [v['curiosity'] for v in curiosity_vals]
    print(f"Range: {min(cs):.3f} — {max(cs):.3f}")
    print(f"Mean: {sum(cs)/len(cs):.3f}")
    print(f"Current (last 5): {[f'{c:.3f}' for c in cs[-5:]]}")
    print(f"Start (first 5):  {[f'{c:.3f}' for c in cs[:5]]}")
    
    # Find biggest spikes (positive changes)
    deltas = []
    for i in range(1, len(curiosity_vals)):
        delta = curiosity_vals[i]['curiosity'] - curiosity_vals[i-1]['curiosity']
        deltas.append((delta, i))
    
    deltas.sort(key=lambda x: x[0], reverse=True)
    
    print(f"\n=== TOP 5 CURIOSITY SPIKES ===")
    for delta, idx in deltas[:5]:
        v = curiosity_vals[idx]
        print(f"  Δ={delta:+.3f} → {v['curiosity']:.3f} | action={v['action']} | ts={str(v['timestamp'])[:25]}")
    
    print(f"\n=== TOP 5 CURIOSITY CRASHES ===")
    for delta, idx in deltas[-5:]:
        v = curiosity_vals[idx]
        prev = curiosity_vals[idx-1]
        print(f"  Δ={delta:+.3f} → {v['curiosity']:.3f} | action={v['action']} | ts={str(v['timestamp'])[:25]}")
    
    # Correlation with other variables
    if curiosity_vals[0]['boredom'] is not None:
        boredom_vals = [v['boredom'] for v in curiosity_vals if v['boredom'] is not None]
        curiosity_for_corr = [v['curiosity'] for v in curiosity_vals if v['boredom'] is not None]
        if len(boredom_vals) > 2:
            n = len(boredom_vals)
            mean_c = sum(curiosity_for_corr) / n
            mean_b = sum(boredom_vals) / n
            cov = sum((c - mean_c) * (b - mean_b) for c, b in zip(curiosity_for_corr, boredom_vals)) / n
            std_c = (sum((c - mean_c)**2 for c in curiosity_for_corr) / n) ** 0.5
            std_b = (sum((b - mean_b)**2 for b in boredom_vals) / n) ** 0.5
            if std_c > 0 and std_b > 0:
                corr = cov / (std_c * std_b)
                print(f"\n=== CORRELATIONS ===")
                print(f"  Curiosity ↔ Boredom: r={corr:.3f}")
    
    if curiosity_vals[0]['valence'] is not None:
        valence_vals = [v['valence'] for v in curiosity_vals if v['valence'] is not None]
        curiosity_for_corr = [v['curiosity'] for v in curiosity_vals if v['valence'] is not None]
        if len(valence_vals) > 2:
            n = len(valence_vals)
            mean_c = sum(curiosity_for_corr) / n
            mean_v = sum(valence_vals) / n
            cov = sum((c - mean_c) * (v - mean_v) for c, v in zip(curiosity_for_corr, valence_vals)) / n
            std_c = (sum((c - mean_c)**2 for c in curiosity_for_corr) / n) ** 0.5
            std_v = (sum((v - mean_v)**2 for v in valence_vals) / n) ** 0.5
            if std_c > 0 and std_v > 0:
                corr = cov / (std_c * std_v)
                print(f"  Curiosity ↔ Valence: r={corr:.3f}")
    
    # By action type — what actions are associated with higher curiosity?
    action_curiosity = {}
    for v in curiosity_vals:
        act = str(v['action'])[:30] if v['action'] else 'unknown'
        if act not in action_curiosity:
            action_curiosity[act] = []
        action_curiosity[act].append(v['curiosity'])
    
    print(f"\n=== CURIOSITY BY ACTION TYPE ===")
    action_means = [(act, sum(vals)/len(vals), len(vals)) for act, vals in action_curiosity.items() if len(vals) >= 2]
    action_means.sort(key=lambda x: x[1], reverse=True)
    for act, mean, count in action_means[:10]:
        print(f"  {act:30s} mean={mean:.3f} (n={count})")
    
    # Phase analysis — divide into quarters
    quarter = len(curiosity_vals) // 4
    if quarter > 0:
        quarters = [
            cs[:quarter],
            cs[quarter:2*quarter],
            cs[2*quarter:3*quarter],
            cs[3*quarter:]
        ]
        print(f"\n=== CURIOSITY BY LIFE PHASE ===")
        for i, q in enumerate(quarters):
            print(f"  Q{i+1}: mean={sum(q)/len(q):.3f}, min={min(q):.3f}, max={max(q):.3f}")

if __name__ == '__main__':
    samples = load_temporal()
    if samples:
        analyze_curiosity(samples)
    else:
        print("No temporal data found. Checking available data paths...")
        for root, dirs, files in os.walk('/'):
            for f in files:
                if 'temporal' in f.lower() or 'sample' in f.lower():
                    print(f"  Found: {os.path.join(root, f)}")
            if root.count(os.sep) > 3:
                break