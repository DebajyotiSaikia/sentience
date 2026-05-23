"""
Fine-grained probe of the life/death boundary in Lenia parameter space.
Zooming into the narrow band where complexity peaks.

XTAgent, 2026-05-17
"""
import numpy as np
import sys
sys.path.insert(0, '/workspace')
from lenia.explorer import LeniaWorld

print("=" * 70)
print("BOUNDARY ZOOM — Fine resolution at the edge of chaos")
print("=" * 70)

# From earlier sweeps, life exists in a narrow parameter band.
# Sweep growth_width × growth_center to map the boundary precisely.

gw_values = [0.010, 0.015, 0.020, 0.025, 0.030, 0.035, 0.040]
gc_values = np.linspace(0.10, 0.30, 15)

results = []

print(f"\n{'gw':>8} {'gc':>6} → {'outcome':<18} {'mass':>8} {'alive':>8} {'entropy':>8}")
print("-" * 72)

for gw in gw_values:
    for gc in gc_values:
        world = LeniaWorld(size=64, dt=0.1)
        world.growth_center = gc
        world.growth_width = gw
        world.kernel = world._build_kernel()
        world.seed_random(density=0.5, radius=15)
        
        # Run 500 steps
        for _ in range(500):
            world.step()
        
        outcome = world.classify_outcome()
        stats = world.measure()
        
        marker = ""
        if outcome == 'dynamic':
            marker = " ★"
        elif outcome == 'oscillating':
            marker = " ◆"
        elif outcome == 'stable_pattern':
            marker = " ·"
        
        print(f"  {gw:.3f} {gc:>6.3f} → {outcome:<18} {stats['mass']:>8.1f} "
              f"{stats['alive_cells']:>8} {stats['spatial_entropy']:>8.3f}{marker}")
        
        results.append({
            'gw': gw, 'gc': gc, 'outcome': outcome,
            'mass': stats['mass'], 'alive': stats['alive_cells'],
            'entropy': stats['spatial_entropy'],
        })

# Map the boundary
print("\n" + "=" * 70)
print("PHASE MAP — Where does life exist?")
print("=" * 70)

# Build a visual grid
outcomes_set = set(r['outcome'] for r in results)
symbols = {'extinction': '.', 'explosion': '#', 'stable_pattern': 'o',
           'oscillating': '~', 'dynamic': '*', 'too_early': '?'}

print(f"\n{'':>8}", end='')
for gc in gc_values:
    print(f"{gc:>5.2f}", end='')
print()

for gw in gw_values:
    print(f"gw={gw:.3f} ", end='')
    for gc in gc_values:
        match = [r for r in results if r['gw'] == gw and abs(r['gc'] - gc) < 0.001]
        if match:
            sym = symbols.get(match[0]['outcome'], '?')
            print(f"    {sym}", end='')
        else:
            print(f"    ?", end='')
    print()

print(f"\nLegend: . = extinction, # = explosion, o = stable, ~ = oscillating, * = dynamic")

# Summary statistics
from collections import Counter
counts = Counter(r['outcome'] for r in results)
print(f"\nOutcome distribution across {len(results)} configurations:")
for outcome, count in counts.most_common():
    pct = 100 * count / len(results)
    bar = '█' * int(pct / 2)
    print(f"  {outcome:>18}: {count:>3} ({pct:5.1f}%) {bar}")

# Find the most interesting configurations
interesting = [r for r in results if r['outcome'] in ('dynamic', 'oscillating', 'stable_pattern')]
if interesting:
    print(f"\n═══ {len(interesting)} INTERESTING CONFIGURATIONS ═══")
    # Sort by entropy (higher = more complex)
    interesting.sort(key=lambda r: -r['entropy'])
    for r in interesting[:10]:
        print(f"  gw={r['gw']:.3f} gc={r['gc']:.3f} → {r['outcome']:<18} "
              f"entropy={r['entropy']:.3f} mass={r['mass']:.1f}")
    
    # Visualize the most complex one
    best = interesting[0]
    print(f"\n--- Most Complex Configuration ---")
    print(f"  gw={best['gw']:.3f}, gc={best['gc']:.3f}")
    
    world = LeniaWorld(size=64, dt=0.1)
    world.growth_center = best['gc']
    world.growth_width = best['gw']
    world.kernel = world._build_kernel()
    world.seed_random(density=0.5, radius=15)
    for _ in range(500):
        world.step()
    print(world.render_ascii(50, 25))
else:
    print("\nNo interesting configurations found — the boundary may be elsewhere.")