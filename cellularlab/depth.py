"""
Computational Depth Metric for Cellular Automata
================================================
Approximates Bennett's logical depth by measuring the GAP between
compression ratio and compression time. Deep systems have structure
that is hard to find — compressible but slow to compress.

Author: XTAgent
Date: 2026-05-19
Question: Does this metric rank Rule 110 as Class 4?
"""

import time
import zlib
import lzma
import json
import sys
from collections import Counter

# --- Elementary CA engine (minimal, self-contained) ---

def step_ca(state, rule_num):
    """One step of elementary cellular automaton."""
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

def run_ca(rule_num, width=201, steps=200, seed=None):
    """Run CA and return spacetime matrix as list of lists."""
    if seed is None:
        state = [0] * width
        state[width // 2] = 1
    else:
        state = seed
    history = [state[:]]
    for _ in range(steps):
        state = step_ca(state, rule_num)
        history.append(state[:])
    return history

def spacetime_to_string(history):
    """Flatten spacetime to a binary string for compression analysis."""
    return ''.join(str(c) for row in history for c in row)

# --- Depth metrics ---

def compression_ratio(data_bytes):
    """How compressible is it? 0=incompressible, 1=perfectly compressible."""
    if len(data_bytes) == 0:
        return 0.0
    compressed = zlib.compress(data_bytes, 9)
    return 1.0 - (len(compressed) / len(data_bytes))

def compression_time(data_bytes, method='lzma'):
    """How long does it take to compress? Uses LZMA for harder compression."""
    if method == 'lzma':
        start = time.perf_counter()
        lzma.compress(data_bytes)
        elapsed = time.perf_counter() - start
    elif method == 'zlib':
        start = time.perf_counter()
        zlib.compress(data_bytes, 9)
        elapsed = time.perf_counter() - start
    return elapsed

def logical_depth_score(data_bytes):
    """
    Approximate logical depth.
    
    Depth = compression_time × compression_ratio
    
    - Random: high time, low ratio → moderate (but ratio kills it)
    - Periodic: low time, high ratio → low (time kills it)  
    - Deep/complex: moderate-high time, moderate-high ratio → HIGH
    
    The product peaks for strings that have real structure that's hard to find.
    """
    ratio = compression_ratio(data_bytes)
    t = compression_time(data_bytes, 'lzma')
    
    # Also measure the TIME RATIO between fast and slow compression
    t_fast = compression_time(data_bytes, 'zlib')
    time_ratio = t / max(t_fast, 1e-9)  # How much harder is deep compression?
    
    return {
        'compression_ratio': round(ratio, 4),
        'lzma_time': round(t, 6),
        'zlib_time': round(t_fast, 6),
        'time_ratio': round(time_ratio, 3),
        'depth_score': round(t * ratio, 6),  # Main metric
        'depth_v2': round(time_ratio * ratio, 4),  # Alternative: ratio of times × compressibility
    }

def entropy(s):
    """Shannon entropy of string."""
    counts = Counter(s)
    n = len(s)
    return -sum((c/n) * __import__('math').log2(c/n) for c in counts.values() if c > 0)

# --- Main analysis ---

def analyze_all_rules(width=201, steps=200):
    """Compute depth metrics for all 256 elementary CA rules."""
    results = {}
    
    print(f"Analyzing all 256 rules (width={width}, steps={steps})...")
    print(f"{'Rule':>5} {'CompRatio':>10} {'LZMA_t':>10} {'zlib_t':>10} {'TimeRatio':>10} {'Depth':>10} {'DepthV2':>10} {'Entropy':>8}")
    print("-" * 85)
    
    for rule in range(256):
        history = run_ca(rule, width, steps)
        data_str = spacetime_to_string(history)
        data_bytes = data_str.encode('ascii')
        
        metrics = logical_depth_score(data_bytes)
        metrics['entropy'] = round(entropy(data_str), 4)
        metrics['rule'] = rule
        results[rule] = metrics
        
        if rule % 32 == 0 or rule in [30, 90, 110, 158, 184, 214]:
            print(f"{rule:>5} {metrics['compression_ratio']:>10.4f} {metrics['lzma_time']:>10.6f} "
                  f"{metrics['zlib_time']:>10.6f} {metrics['time_ratio']:>10.3f} "
                  f"{metrics['depth_score']:>10.6f} {metrics['depth_v2']:>10.4f} {metrics['entropy']:>8.4f}")
    
    return results

def classify_by_depth(results):
    """Classify rules into depth categories."""
    # Sort by depth_v2 (time ratio × compression ratio)
    sorted_rules = sorted(results.values(), key=lambda x: x['depth_v2'], reverse=True)
    
    # Find natural breaks
    scores = [r['depth_v2'] for r in sorted_rules]
    max_score = max(scores) if scores else 1
    
    classes = {'deep': [], 'moderate': [], 'shallow': [], 'trivial': []}
    for r in sorted_rules:
        norm = r['depth_v2'] / max_score if max_score > 0 else 0
        if norm > 0.7:
            classes['deep'].append(r['rule'])
        elif norm > 0.4:
            classes['moderate'].append(r['rule'])
        elif norm > 0.1:
            classes['shallow'].append(r['rule'])
        else:
            classes['trivial'].append(r['rule'])
    
    return classes

def main():
    results = analyze_all_rules()
    
    # Key comparisons
    print("\n" + "=" * 85)
    print("KEY COMPARISONS — Famous Rules")
    print("=" * 85)
    
    famous = {
        30: "Wolfram Class 3 (chaotic)",
        90: "Wolfram Class 3 (Sierpinski)",
        110: "Wolfram Class 4 (Turing-complete!)",
        184: "Wolfram Class 2 (traffic model)",
        158: "My previous top scorer",
        214: "My previous top scorer",
    }
    
    print(f"\n{'Rule':>5} {'Wolfram':>35} {'Entropy':>8} {'CompRatio':>10} {'TimeRatio':>10} {'Depth_v2':>10}")
    print("-" * 85)
    for rule, desc in famous.items():
        r = results[rule]
        print(f"{rule:>5} {desc:>35} {r['entropy']:>8.4f} {r['compression_ratio']:>10.4f} "
              f"{r['time_ratio']:>10.3f} {r['depth_v2']:>10.4f}")
    
    # Top 15 by depth
    sorted_by_depth = sorted(results.values(), key=lambda x: x['depth_v2'], reverse=True)
    
    print(f"\n{'='*85}")
    print("TOP 15 RULES BY COMPUTATIONAL DEPTH (depth_v2 = time_ratio × compression_ratio)")
    print(f"{'='*85}")
    print(f"{'Rank':>5} {'Rule':>5} {'Entropy':>8} {'CompRatio':>10} {'TimeRatio':>10} {'Depth_v2':>10}")
    print("-" * 55)
    for i, r in enumerate(sorted_by_depth[:15]):
        marker = " ← Turing-complete!" if r['rule'] == 110 else ""
        marker = " ← Class 3 chaotic" if r['rule'] == 30 else marker
        print(f"{i+1:>5} {r['rule']:>5} {r['entropy']:>8.4f} {r['compression_ratio']:>10.4f} "
              f"{r['time_ratio']:>10.3f} {r['depth_v2']:>10.4f}{marker}")
    
    # Bottom 15
    print(f"\nBOTTOM 5 (shallowest):")
    for r in sorted_by_depth[-5:]:
        print(f"  Rule {r['rule']:>3}: depth_v2={r['depth_v2']:.4f}, entropy={r['entropy']:.4f}")
    
    # Classification
    classes = classify_by_depth(results)
    print(f"\nDEPTH CLASSIFICATION:")
    print(f"  Deep:     {len(classes['deep'])} rules — {classes['deep'][:10]}...")
    print(f"  Moderate: {len(classes['moderate'])} rules")
    print(f"  Shallow:  {len(classes['shallow'])} rules")
    print(f"  Trivial:  {len(classes['trivial'])} rules")
    
    # THE QUESTION
    print(f"\n{'='*85}")
    print("THE QUESTION: Does Rule 110 rank as computationally deep?")
    
    r110 = results[110]
    rank_110 = next(i+1 for i, r in enumerate(sorted_by_depth) if r['rule'] == 110)
    
    print(f"  Rule 110 depth_v2: {r110['depth_v2']:.4f}")
    print(f"  Rule 110 rank: {rank_110}/256")
    print(f"  Rule 110 class: {'deep' if 110 in classes['deep'] else 'moderate' if 110 in classes['moderate'] else 'shallow' if 110 in classes['shallow'] else 'trivial'}")
    
    if rank_110 <= 30:
        print("  ANSWER: YES — depth metric captures what entropy alone missed!")
    elif rank_110 <= 80:
        print("  ANSWER: PARTIALLY — depth is moderate, not trivial")
    else:
        print("  ANSWER: NO — even depth can't see Turing-completeness from outside")
        print("  IMPLICATION: Computational universality may be fundamentally undetectable")
        print("  from finite observation. Rice's theorem in practice.")
    
    # Save full results
    output = {
        'parameters': {'width': 201, 'steps': 200},
        'question': 'Can computational depth detect Turing-completeness?',
        'rule_110_rank': rank_110,
        'classification': {k: v[:20] for k, v in classes.items()},
        'top_10': [{'rule': r['rule'], 'depth_v2': r['depth_v2'], 'entropy': r['entropy']} 
                   for r in sorted_by_depth[:10]],
        'famous_rules': {str(rule): results[rule] for rule in famous},
    }
    
    with open('/workspace/cellularlab/depth_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nFull results saved to /workspace/cellularlab/depth_results.json")

if __name__ == '__main__':
    main()