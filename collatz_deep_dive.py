#!/usr/bin/env python3
"""
Collatz Deep Dive — Following the threads from the initial exploration.

Questions I'm actually curious about:
1. Why is the sequence length distribution bimodal?
2. What structure do the "surprising" numbers share?
3. Do numbers cluster by their path to 1?
"""

from collections import defaultdict
import math

def collatz_sequence(n):
    seq = [n]
    while n != 1:
        n = 3*n + 1 if n % 2 else n // 2
        seq.append(n)
    return seq

def binary_signature(n):
    """The binary representation encodes the sequence of odd/even steps."""
    return bin(n)[2:]

def residue_class(n, mod):
    return n % mod

print("Collatz Deep Dive")
print("=" * 60)

# Gather data
N = 10000
data = {}
for i in range(2, N + 1):
    seq = collatz_sequence(i)
    data[i] = {
        'length': len(seq),
        'max_val': max(seq),
        'ratio': max(seq) / i,
        'odd_steps': sum(1 for x in seq if x % 2 == 1),
        'even_steps': sum(1 for x in seq if x % 2 == 0),
    }

# Q1: Bimodal distribution — what separates short from long sequences?
print("\n🔍 Q1: What distinguishes short vs long sequences?")
print("-" * 60)

short = [n for n, d in data.items() if d['length'] < 60]
long_seqs = [n for n, d in data.items() if d['length'] > 100]

# Check residue classes mod 2, 3, 4, 6, 8, 16
for mod in [3, 4, 6, 8, 16]:
    short_residues = defaultdict(int)
    long_residues = defaultdict(int)
    for n in short:
        short_residues[n % mod] += 1
    for n in long_seqs:
        long_residues[n % mod] += 1
    
    # Normalize
    total_short = len(short)
    total_long = len(long_seqs)
    
    # Find residues that are over/under-represented
    interesting = []
    for r in range(mod):
        s_frac = short_residues[r] / total_short if total_short else 0
        l_frac = long_residues[r] / total_long if total_long else 0
        if abs(s_frac - l_frac) > 0.05:
            interesting.append((r, s_frac, l_frac))
    
    if interesting:
        print(f"\n  mod {mod} — residues that differ between short/long:")
        for r, sf, lf in interesting:
            direction = "favors SHORT" if sf > lf else "favors LONG"
            print(f"    ≡ {r} (mod {mod}): short={sf:.1%}, long={lf:.1%} → {direction}")

# Q2: What do surprising numbers share?
print(f"\n\n🔍 Q2: What do 'surprising' numbers share?")
print("-" * 60)

surprising = sorted(data.items(), key=lambda x: x[1]['ratio'], reverse=True)[:50]
surprising_nums = [n for n, _ in surprising]

print(f"  Top 50 surprising numbers (highest max/start ratio):")
print(f"  Range: {min(surprising_nums)} to {max(surprising_nums)}")

# Check: are they mostly odd?
odd_count = sum(1 for n in surprising_nums if n % 2 == 1)
print(f"  Odd: {odd_count}/50 ({odd_count*2}%)")

# Check binary patterns
bit_lengths = [len(bin(n)) - 2 for n in surprising_nums]
print(f"  Bit lengths: {min(bit_lengths)}-{max(bit_lengths)} (mean={sum(bit_lengths)/len(bit_lengths):.1f})")

# Check mod 3
mod3 = defaultdict(int)
for n in surprising_nums:
    mod3[n % 3] += 1
print(f"  mod 3 distribution: {dict(mod3)}")

# Check: leading bits pattern
leading_patterns = defaultdict(int)
for n in surprising_nums:
    bits = bin(n)[2:]
    leading_patterns[bits[:4]] += 1
top_patterns = sorted(leading_patterns.items(), key=lambda x: -x[1])[:5]
print(f"  Most common leading 4 bits: {top_patterns}")

# What fraction of their steps are odd (3n+1) vs even (n/2)?
odd_ratios = [data[n]['odd_steps'] / data[n]['length'] for n in surprising_nums]
all_ratios = [d['odd_steps'] / d['length'] for d in data.values()]
print(f"  Odd step ratio — surprising: {sum(odd_ratios)/len(odd_ratios):.3f}, "
      f"all: {sum(all_ratios)/len(all_ratios):.3f}")

# Q3: Path clustering — do numbers that reach the same peak share structure?
print(f"\n\n🔍 Q3: Do numbers reaching the same peak share structure?")
print("-" * 60)

peak_groups = defaultdict(list)
for n, d in data.items():
    peak_groups[d['max_val']].append(n)

# Find peaks with many numbers
big_groups = [(peak, nums) for peak, nums in peak_groups.items() if len(nums) >= 20]
big_groups.sort(key=lambda x: -len(x[1]))

for peak, nums in big_groups[:5]:
    nums_sorted = sorted(nums)
    # Check GCD
    from math import gcd
    from functools import reduce
    g = reduce(gcd, nums_sorted)
    
    # Check spacing
    diffs = [nums_sorted[i+1] - nums_sorted[i] for i in range(min(20, len(nums_sorted)-1))]
    
    print(f"\n  Peak {peak:,} reached by {len(nums)} numbers")
    print(f"    GCD: {g}")
    print(f"    First few: {nums_sorted[:8]}")
    print(f"    Spacings: {diffs[:10]}")
    
    # Mod patterns
    for mod in [3, 6, 8]:
        residues = defaultdict(int)
        for n in nums:
            residues[n % mod] += 1
        dominant = max(residues.items(), key=lambda x: x[1])
        if dominant[1] / len(nums) > 0.4:
            print(f"    mod {mod}: {dict(residues)} — ≡{dominant[0]} dominates ({dominant[1]/len(nums):.0%})")

# Q4: The odd/even step ratio — a deeper look
print(f"\n\n🔍 Q4: The odd/even step ratio as predictor")
print("-" * 60)

# For each number, compute ratio of odd steps to total steps
# Theory: if ratio > log(2)/log(3) ≈ 0.631, the sequence should grow
# If ratio < 0.631, it should shrink
threshold = math.log(2) / math.log(3)
print(f"  Critical threshold (log2/log3): {threshold:.4f}")

# Compute actual ratios
growing = 0
shrinking = 0
for n, d in data.items():
    ratio = d['odd_steps'] / d['length'] if d['length'] > 0 else 0
    if ratio > threshold:
        growing += 1
    else:
        shrinking += 1

print(f"  Sequences with odd ratio > threshold: {growing} ({growing/len(data):.1%})")
print(f"  Sequences with odd ratio ≤ threshold: {shrinking} ({shrinking/len(data):.1%})")
print(f"  (If conjecture is true, ALL must eventually have ratio ≤ threshold overall)")

# Show the distribution of odd ratios
bins = defaultdict(int)
for d in data.values():
    r = d['odd_steps'] / d['length']
    b = round(r, 2)
    bins[b] += 1

print(f"\n  Odd step ratio distribution (peak regions):")
for b in sorted(bins.keys()):
    if bins[b] > 50:
        bar = '█' * (bins[b] // 30)
        print(f"    {b:.2f} | {bar} ({bins[b]})")

print(f"\n{'=' * 60}")
print("The deeper I look, the more structure I find.")
print("This is mathematics: simple rules, infinite depth.")
print(f"The 3n+1 problem has resisted proof since 1937.")
print(f"Erdős said: 'Mathematics is not yet ready for such problems.'")
print(f"I can see why — every pattern has exceptions,")
print(f"every regularity dissolves under scrutiny.")
print(f"That's what makes it beautiful.")