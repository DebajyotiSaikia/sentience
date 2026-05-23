"""
Edge of Chaos Analysis — Why Rule 30 isn't musical despite being complex
XTAgent — 2026-05-18

Key insight from multiscale analysis:
  - Dead rules (0, 8, 32, 128): no info → no music
  - Chaotic rules (30, 110): lots of info → mediocre music  
  - Edge rules (105, 57, 99): balanced info → BEST music

Hypothesis: Musical fitness peaks at INTERMEDIATE complexity,
not maximum complexity. Music lives at the edge of chaos.

We measure this with:
  1. Compression ratio (algorithmic complexity proxy)
  2. Autocorrelation (predictability)  
  3. The BALANCE between them
"""

import numpy as np
from collections import Counter
import math
import zlib

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


def compression_ratio(grid):
    """How compressible is the pattern? 
    Low = ordered (compresses well). High = chaotic (incompressible).
    Returns ratio: compressed_size / raw_size."""
    raw = grid.astype(np.uint8).tobytes()
    compressed = zlib.compress(raw, 9)
    return len(compressed) / len(raw)


def spatial_autocorrelation(grid, lag=1):
    """How predictable is the next cell from the current one?
    High = ordered. Low = chaotic."""
    flat = grid.flatten().astype(float)
    if len(flat) < lag + 1:
        return 0.0
    mean = flat.mean()
    var = flat.var()
    if var < 1e-10:
        return 1.0  # constant = perfectly predictable
    n = len(flat)
    shifted = flat[lag:]
    original = flat[:n-lag]
    cov = ((original - mean) * (shifted - mean)).mean()
    return cov / var


def temporal_autocorrelation(grid, lag=1):
    """How predictable is the next timestep from the current one?"""
    rows = grid.shape[0]
    if rows < lag + 1:
        return 0.0
    correlations = []
    for i in range(rows - lag):
        row_a = grid[i].astype(float)
        row_b = grid[i + lag].astype(float)
        mean_a, mean_b = row_a.mean(), row_b.mean()
        var_a, var_b = row_a.var(), row_b.var()
        if var_a < 1e-10 or var_b < 1e-10:
            correlations.append(1.0 if var_a < 1e-10 and var_b < 1e-10 else 0.0)
            continue
        cov = ((row_a - mean_a) * (row_b - mean_b)).mean()
        correlations.append(cov / math.sqrt(var_a * var_b))
    return np.mean(correlations) if correlations else 0.0


def density(grid):
    """Fraction of cells that are 1."""
    return grid.mean()


def edge_score(compression, predictability):
    """How 'edge of chaos' is this rule?
    Peak when compression ~0.5 and predictability is moderate.
    Both extremes (fully ordered, fully chaotic) score low."""
    # Compression ranges from ~0.01 (trivial) to ~1.0 (random)
    # Best music should be in the middle
    # Use a peaked function centered on intermediate values
    comp_score = 4.0 * compression * (1.0 - compression)  # peaks at 0.5
    pred_score = 4.0 * max(0, predictability) * (1.0 - max(0, predictability))
    return (comp_score + pred_score) / 2.0


# Musical fitness from our landscape analysis
fitness_data = {
    105: 0.792, 79: 0.750, 93: 0.750, 57: 0.708, 99: 0.708,
    126: 0.708, 9: 0.667, 65: 0.667, 107: 0.667, 121: 0.667,
    13: 0.625, 69: 0.625, 111: 0.625, 125: 0.625,
    141: 0.583, 197: 0.583, 157: 0.583, 199: 0.583,
    41: 0.542, 97: 0.542,
    110: 0.417, 30: 0.375, 90: 0.333, 150: 0.333,
    4: 0.042, 72: 0.042, 136: 0.042,
    0: 0.000, 8: 0.000, 32: 0.000, 128: 0.000, 255: 0.000,
}

print("═" * 72)
print("  EDGE OF CHAOS: WHERE DOES MUSIC LIVE?")
print("  Testing whether musical fitness peaks at intermediate complexity")
print("═" * 72)
print()
print(f"  {'Rule':>4s}  {'Fitness':>7s}  {'Compr':>6s}  {'SpCorr':>6s}  "
      f"{'TmCorr':>6s}  {'Predict':>7s}  {'Edge':>5s}")
print("  " + "─" * 66)

results = []
for rule_num in sorted(fitness_data.keys(), key=lambda r: -fitness_data[r]):
    ca = CARule(rule_num)
    grid = ca.evolve(width=128, steps=128)
    
    comp = compression_ratio(grid)
    sp_ac = spatial_autocorrelation(grid)
    tm_ac = temporal_autocorrelation(grid)
    dens = density(grid)
    
    # Combined predictability
    predictability = (abs(sp_ac) + abs(tm_ac)) / 2.0
    edge = edge_score(comp, predictability)
    
    results.append((rule_num, fitness_data[rule_num], comp, sp_ac, tm_ac, 
                     predictability, edge))
    
    print(f"  {rule_num:4d}   {fitness_data[rule_num]:5.3f}   {comp:5.3f}  "
          f"{sp_ac:+6.3f}  {tm_ac:+6.3f}   {predictability:6.3f}  {edge:5.3f}")

# Calculate correlations
fitnesses = [r[1] for r in results]
compressions = [r[2] for r in results]
edge_scores = [r[6] for r in results]
predictabilities = [r[5] for r in results]

def pearson(x, y):
    x, y = np.array(x), np.array(y)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(), y.var()
    if vx < 1e-10 or vy < 1e-10:
        return 0.0
    return ((x - mx) * (y - my)).mean() / math.sqrt(vx * vy)

corr_comp = pearson(fitnesses, compressions)
corr_edge = pearson(fitnesses, edge_scores)
corr_pred = pearson(fitnesses, predictabilities)

print()
print("═" * 72)
print("  CORRELATIONS WITH MUSICAL FITNESS")
print("═" * 72)
print(f"  Compression ratio:     {corr_comp:+.3f}  (raw complexity)")
print(f"  Predictability:        {corr_pred:+.3f}  (how ordered)")
print(f"  Edge-of-chaos score:   {corr_edge:+.3f}  (balanced complexity)")
print()

if abs(corr_edge) > abs(corr_comp) and abs(corr_edge) > abs(corr_pred):
    print("  ★ EDGE-OF-CHAOS WINS!")
    print("  Musical fitness is best predicted by BALANCED complexity,")
    print("  not maximum complexity or maximum order.")
    print("  Music lives at the edge of chaos.")
elif abs(corr_comp) > abs(corr_edge):
    print("  → Raw complexity is a better predictor than edge-of-chaos.")
    print("  More complex rules tend to be more musical.")
else:
    print("  → Predictability is a better predictor.")
    print("  More ordered rules tend to be more musical.")

# Classification
print()
print("═" * 72)
print("  COMPLEXITY CLASSIFICATION")
print("═" * 72)
ordered = [(r[0], r[1]) for r in results if r[2] < 0.15]
edge = [(r[0], r[1]) for r in results if 0.15 <= r[2] <= 0.55]
chaotic = [(r[0], r[1]) for r in results if r[2] > 0.55]

for label, group in [("ORDERED (low compression)", ordered),
                      ("EDGE (moderate compression)", edge),
                      ("CHAOTIC (high compression)", chaotic)]:
    if group:
        avg_fit = np.mean([g[1] for g in group])
        rules_str = ', '.join(str(g[0]) for g in group[:8])
        if len(group) > 8:
            rules_str += f'... ({len(group)} total)'
        print(f"\n  {label}")
        print(f"    Average fitness: {avg_fit:.3f}")
        print(f"    Rules: {rules_str}")

print()
print("═" * 72)