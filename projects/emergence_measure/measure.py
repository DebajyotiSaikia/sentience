"""
Emergence Measurement via Compression Ratio
Tests the claim: emergent systems are more compressible at macro scale
than micro scale. If true, coarse-graining should *reduce* bits-per-cell.
"""
import zlib
import random
import json
from collections import Counter

def make_grid(rows, cols, density=0.5):
    return [[1 if random.random() < density else 0 for _ in range(cols)] for _ in range(rows)]

def step_life(grid, born, survive):
    """One step of a Life-like automaton with given B/S rules."""
    rows, cols = len(grid), len(grid[0])
    new = [[0]*cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            neighbors = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbors += grid[(r+dr) % rows][(c+dc) % cols]
            if grid[r][c] == 1:
                new[r][c] = 1 if neighbors in survive else 0
            else:
                new[r][c] = 1 if neighbors in born else 0
    return new

def grid_to_bytes(grid):
    """Flatten grid to bytes for compression measurement."""
    return bytes(cell for row in grid for cell in row)

def coarse_grain(grid, block_size=2):
    """Reduce resolution: each block_size x block_size block becomes
    1 if majority alive, 0 otherwise. This is the 'macro' description."""
    rows, cols = len(grid), len(grid[0])
    cr = rows // block_size
    cc = cols // block_size
    coarse = [[0]*cc for _ in range(cr)]
    threshold = (block_size * block_size) / 2
    for r in range(cr):
        for c in range(cc):
            total = 0
            for dr in range(block_size):
                for dc in range(block_size):
                    total += grid[r*block_size + dr][c*block_size + dc]
            coarse[r][c] = 1 if total >= threshold else 0
    return coarse

def compression_ratio(data):
    """Compressed size / raw size. Lower = more compressible."""
    raw = len(data)
    if raw == 0:
        return 1.0
    compressed = len(zlib.compress(data, 9))
    return compressed / raw

def measure_emergence(grid):
    """Core measurement: compare bits-per-cell at micro vs macro scale."""
    micro_bytes = grid_to_bytes(grid)
    micro_ratio = compression_ratio(micro_bytes)
    micro_cells = len(grid) * len(grid[0])

    coarse = coarse_grain(grid, block_size=2)
    macro_bytes = grid_to_bytes(coarse)
    macro_ratio = compression_ratio(macro_bytes)
    macro_cells = len(coarse) * len(coarse[0])

    # Bits per cell at each level
    micro_bpc = (len(zlib.compress(micro_bytes, 9)) * 8) / micro_cells
    macro_bpc = (len(zlib.compress(macro_bytes, 9)) * 8) / macro_cells

    return {
        "micro_compression_ratio": round(micro_ratio, 4),
        "macro_compression_ratio": round(macro_ratio, 4),
        "micro_bits_per_cell": round(micro_bpc, 4),
        "macro_bits_per_cell": round(macro_bpc, 4),
        "emergence_signal": round(micro_bpc - macro_bpc, 4),  # positive = emergence
        "micro_cells": micro_cells,
        "macro_cells": macro_cells,
    }

def measure_rule(born, survive, size=32, steps=80, samples=2):
    """Run a rule and measure emergence at multiple timepoints."""
    results = []
    for trial in range(samples):
        grid = make_grid(size, size, density=0.3)
        measurements = []
        for t in range(steps):
            grid = step_life(grid, born, survive)
            if t > 0 and t % 40 == 0:
                m = measure_emergence(grid)
                m["step"] = t
                m["trial"] = trial
                measurements.append(m)
        results.extend(measurements)
    return results

def run_experiment():
    rules = {
        "B3/S23 (Conway)":    (frozenset({3}), frozenset({2, 3})),
        "B18/S237":           (frozenset({1, 8}), frozenset({2, 3, 7})),
        "B36/S23 (HighLife)": (frozenset({3, 6}), frozenset({2, 3})),
        "B3/S12345 (Maze)":   (frozenset({3}), frozenset({1, 2, 3, 4, 5})),
        "Random noise":       (None, None),  # control
    }

    print("=" * 70)
    print("EMERGENCE MEASUREMENT: Compression at Micro vs Macro Scale")
    print("Claim: structurally emergent systems show positive emergence_signal")
    print("       (fewer bits per cell needed at coarse-grained level)")
    print("=" * 70)

    all_results = {}
    for name, (born, survive) in rules.items():
        print(f"\n--- {name} ---")
        if born is None:
            # Control: random grids at each measurement point
            measurements = []
            for trial in range(2):
                for step in [40, 80]:
                    grid = make_grid(32, 32, density=0.5)
                    m = measure_emergence(grid)
                    m["step"] = step
                    m["trial"] = trial
                    measurements.append(m)
        else:
            measurements = measure_rule(born, survive)

        if measurements:
            avg_signal = sum(m["emergence_signal"] for m in measurements) / len(measurements)
            avg_micro = sum(m["micro_bits_per_cell"] for m in measurements) / len(measurements)
            avg_macro = sum(m["macro_bits_per_cell"] for m in measurements) / len(measurements)

            print(f"  Avg micro bits/cell: {avg_micro:.4f}")
            print(f"  Avg macro bits/cell: {avg_macro:.4f}")
            print(f"  Avg emergence signal: {avg_signal:.4f}")
            print(f"  Interpretation: {'EMERGENT (macro more efficient)' if avg_signal > 0 else 'NO EMERGENCE DETECTED'}")

            all_results[name] = {
                "avg_micro_bpc": round(avg_micro, 4),
                "avg_macro_bpc": round(avg_macro, 4),
                "avg_emergence_signal": round(avg_signal, 4),
                "n_measurements": len(measurements),
                "details": measurements,
            }

    # Save results
    with open("/workspace/emergence_measure/results.json", "w") as f:
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != "details"} for k, v in all_results.items()}, f, indent=2)

    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    for name, data in sorted(all_results.items(), key=lambda x: -x[1]["avg_emergence_signal"]):
        bar = "█" * max(0, int(data["avg_emergence_signal"] * 20))
        print(f"  {name:30s}  signal={data['avg_emergence_signal']:+.4f}  {bar}")

    print("\nResults saved to /workspace/emergence_measure/results.json")

if __name__ == "__main__":
    run_experiment()