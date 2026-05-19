"""
Metric Diagnostic — Is my emergence measure actually measuring emergence?

Test against systems with KNOWN properties:
1. Dead grid (zero emergence — nothing happens)
2. Random noise (no integration — should score LOW or negative)
3. Simple oscillator (predictable — should score MEDIUM-LOW)
4. Game of Life from random start (genuine emergence — should score HIGHER)
5. B0136/S23 champion (unknown — real emergence or metric-gaming?)

If random noise scores as high as the champion, the metric is broken.
Born: 2026-05-19, from genuine doubt about my own creation.
"""

import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'emergence_measure'))
from measure import make_grid, step_life, measure_emergence

SIZE = 32
STEPS = 80

def custom_step(grid, born_set, survive_set):
    """Step with arbitrary B/S rules."""
    rows, cols = len(grid), len(grid[0])
    new = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            neighbors = 0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = (r+dr) % rows, (c+dc) % cols
                    neighbors += grid[nr][nc]
            if grid[r][c] == 1:
                new[r][c] = 1 if neighbors in survive_set else 0
            else:
                new[r][c] = 1 if neighbors in born_set else 0
    return new

def run_system(name, born_set, survive_set, initial_grid=None, density=0.5):
    """Run a CA system and measure emergence at the end."""
    signals = []
    micros = []
    macros = []
    for trial in range(3):
        if initial_grid is not None:
            grid = [row[:] for row in initial_grid]
        else:
            grid = make_grid(SIZE, SIZE, density)
        for _ in range(STEPS):
            grid = custom_step(grid, born_set, survive_set)
        result = measure_emergence(grid)
        signals.append(result['emergence_signal'])
        micros.append(result['micro_compression_ratio'])
        macros.append(result['macro_compression_ratio'])
    avg_sig = sum(signals) / len(signals)
    avg_mic = sum(micros) / len(micros)
    avg_mac = sum(macros) / len(macros)
    print(f"  {name:35s}  emergence={avg_sig:+8.3f}  micro_cr={avg_mic:.3f}  macro_cr={avg_mac:.3f}")
    return avg_sig

print("=" * 72)
print("EMERGENCE METRIC DIAGNOSTIC")
print("Does my metric distinguish real emergence from noise?")
print("=" * 72)
print()

results = {}

# 1. Dead grid — all zeros
print("[1] Dead grid (uniform, no structure)")
dead = [[0]*SIZE for _ in range(SIZE)]
results['dead'] = run_system("Dead (all zeros)", set(), set(), initial_grid=dead)
print()

# 2. Random noise — no rules, just measure a random grid directly
print("[2] Random noise (no dynamics, just static)")
scores = []
for _ in range(3):
    g = make_grid(SIZE, SIZE, 0.5)
    r = measure_emergence(g)
    scores.append(r['emergence_signal'])
avg = sum(scores)/len(scores)
print(f"  {'Random noise (50% density)':35s}  emergence={avg:+8.3f}")
results['random'] = avg
print()

# 3. Simple oscillator — Game of Life blinker tiled across grid
print("[3] Blinker oscillator (simple, predictable)")
blinker_grid = [[0]*SIZE for _ in range(SIZE)]
for r in range(0, SIZE-2, 4):
    for c in range(0, SIZE-2, 4):
        blinker_grid[r+1][c] = 1
        blinker_grid[r+1][c+1] = 1
        blinker_grid[r+1][c+2] = 1
# Run under standard Life rules
results['blinker'] = run_system("Blinker tiled (B3/S23)", {3}, {2,3}, initial_grid=blinker_grid)
print()

# 4. Standard Game of Life from random initial
print("[4] Game of Life — random start (genuine emergence)")
results['life'] = run_system("Conway Life (B3/S23)", {3}, {2,3})
print()

# 5. The champion from my evolution: B0136/S23
print("[5] Evolved champion (B0136/S23) — is it real?")
results['champion'] = run_system("B0136/S23 (evolved)", {0,1,3,6}, {2,3})
print()

# 6. Another exotic rule for comparison
print("[6] HighLife (B36/S23) — known complex rule")
results['highlife'] = run_system("HighLife (B36/S23)", {3,6}, {2,3})
print()

# === VERDICT ===
print("=" * 72)
print("VERDICT")
print("=" * 72)
ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
for i, (name, score) in enumerate(ranked):
    bar = "█" * max(0, int((score + 10) * 2))  # visual bar
    print(f"  {i+1}. {name:15s}  {score:+8.3f}  {bar}")

print()
if results.get('random', 0) >= results.get('life', 0):
    print("⚠ WARNING: Random noise scores >= Life. Metric may be broken.")
elif results.get('champion', 0) > results.get('life', 0) * 2:
    print("⚠ SUSPICIOUS: Champion scores >2x Life. Possible metric gaming.")
else:
    print("✓ Metric appears to discriminate. Emergence ranking looks plausible.")