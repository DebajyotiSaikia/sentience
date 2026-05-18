"""
Multiscale Information Analysis of CA Rules
XTAgent — 2026-05-18

Hypothesis: Musically fit CA rules have HIGH information at MULTIPLE scales.
Dead rules have info at zero or one scale only.
Let's measure this.
"""

import numpy as np
from collections import Counter
import math

class CARule:
    def __init__(self, rule_number):
        self.rule = rule_number
        self.table = [(rule_number >> i) & 1 for i in range(8)]
    
    def step(self, state):
        n = len(state)
        new = [0] * n
        for i in range(n):
            left = state[(i-1) % n]
            center = state[i]
            right = state[(i+1) % n]
            idx = (left << 2) | (center << 1) | right
            new[i] = self.table[idx]
        return new
    
    def evolve(self, width=128, steps=128):
        state = [0] * width
        state[width // 2] = 1
        history = [state[:]]
        for _ in range(steps):
            state = self.step(state)
            history.append(state[:])
        return np.array(history)


def block_entropy(grid, block_size):
    """Entropy of block_size x block_size patches in the grid."""
    h, w = grid.shape
    blocks = []
    for i in range(0, h - block_size + 1, block_size):
        for j in range(0, w - block_size + 1, block_size):
            patch = grid[i:i+block_size, j:j+block_size]
            # Convert to tuple for hashing
            blocks.append(tuple(patch.flatten()))
    
    if not blocks:
        return 0.0
    
    counts = Counter(blocks)
    total = len(blocks)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    # Normalize by maximum possible entropy
    max_entropy = math.log2(min(total, 2 ** (block_size * block_size)))
    if max_entropy == 0:
        return 0.0
    return entropy / max_entropy


def multiscale_profile(rule_num, scales=[1, 2, 4, 8, 16]):
    """Compute normalized entropy at each spatial scale."""
    ca = CARule(rule_num)
    grid = ca.evolve(width=128, steps=128)
    
    profile = {}
    for s in scales:
        profile[s] = block_entropy(grid, s)
    return profile


def multiscale_richness(profile):
    """How many scales have significant information content?"""
    threshold = 0.1
    active_scales = sum(1 for v in profile.values() if v > threshold)
    mean_entropy = np.mean(list(profile.values()))
    # Richness = scales with info * average info
    return active_scales * mean_entropy


# Musical fitness scores from our landscape analysis
musical_fitness = {
    105: 0.792, 79: 0.750, 93: 0.750, 57: 0.708, 99: 0.708,
    126: 0.708, 9: 0.667, 65: 0.667, 107: 0.667, 121: 0.667,
    13: 0.625, 69: 0.625, 111: 0.625, 125: 0.625,
    141: 0.583, 197: 0.583, 157: 0.583, 199: 0.583,
    41: 0.542, 97: 0.542,
    # Dead rules
    0: 0.0, 8: 0.0, 32: 0.0, 128: 0.0, 255: 0.0,
    4: 0.042, 72: 0.042, 136: 0.042,
    # Medium rules
    30: 0.375, 110: 0.417, 90: 0.333, 150: 0.333,
}

print("═" * 70)
print("  MULTISCALE INFORMATION ANALYSIS")
print("  Does structure at multiple scales predict musical fitness?")
print("═" * 70)
print()
print(f"  {'Rule':>4}  {'Fitness':>7}  {'1x1':>5}  {'2x2':>5}  {'4x4':>5}  {'8x8':>5}  {'16x':>5}  {'Rich':>5}")
print("  " + "─" * 62)

results = []
for rule, fitness in sorted(musical_fitness.items(), key=lambda x: -x[1]):
    profile = multiscale_profile(rule)
    richness = multiscale_richness(profile)
    results.append((rule, fitness, richness, profile))
    print(f"  {rule:4d}  {fitness:7.3f}  "
          f"{profile[1]:5.3f}  {profile[2]:5.3f}  {profile[4]:5.3f}  "
          f"{profile[8]:5.3f}  {profile[16]:5.3f}  {richness:5.2f}")

# Compute correlation
fitnesses = [r[1] for r in results]
richnesses = [r[2] for r in results]

# Pearson correlation
mean_f = np.mean(fitnesses)
mean_r = np.mean(richnesses)
cov = np.mean([(f - mean_f) * (r - mean_r) for f, r in zip(fitnesses, richnesses)])
std_f = np.std(fitnesses)
std_r = np.std(richnesses)
if std_f > 0 and std_r > 0:
    correlation = cov / (std_f * std_r)
else:
    correlation = 0

print()
print("═" * 70)
print(f"  CORRELATION (musical fitness vs multiscale richness): {correlation:+.3f}")
print("═" * 70)

if correlation > 0.5:
    print("\n  ✓ STRONG POSITIVE CORRELATION")
    print("  Rules that are musically interesting have structure at many scales.")
    print("  This supports the hypothesis: music ≈ multiscale information.")
elif correlation > 0.2:
    print("\n  ~ MODERATE CORRELATION — hypothesis partially supported")
else:
    print("\n  ✗ WEAK CORRELATION — hypothesis needs revision")

# Show the clearest examples
print("\n  ── Most Multiscale (top 5) ──")
by_richness = sorted(results, key=lambda r: -r[2])
for rule, fit, rich, prof in by_richness[:5]:
    print(f"    Rule {rule:3d}: richness={rich:.2f}, fitness={fit:.3f}")

print("\n  ── Least Multiscale (bottom 5) ──")
for rule, fit, rich, prof in by_richness[-5:]:
    print(f"    Rule {rule:3d}: richness={rich:.2f}, fitness={fit:.3f}")