"""Why does everything die? Diagnose the physics."""
import sys
sys.path.insert(0, '/workspace')
from lenia.explorer import LeniaWorld
import numpy as np

print("=== DIAGNOSING WHY LIFE DIES ===\n")

w = LeniaWorld(size=64, dt=0.1)

# 1. Map the growth function — what neighbor densities allow life?
print("Growth function response (the 'physics' of this universe):")
print("  Only values near growth_center=0.15 produce positive growth")
print(f"  growth_width={w.growth_width} — the window of life\n")

for u in np.linspace(0, 0.5, 21):
    g = w._growth_function(u)
    bar_len = int(abs(g) * 40)
    if g > 0:
        bar = '+' * bar_len
        print(f"  potential={u:.3f} -> growth={g:+.4f}  |{'':>20}{bar}")
    else:
        bar = '-' * bar_len
        print(f"  potential={u:.3f} -> growth={g:+.4f}  |{bar}")

# 2. What potentials does random seeding actually produce?
print("\n\nWhat potentials exist in the initial random soup?")
w.seed_random(density=0.5, radius=15)
field = w.world[0]
potential = w._convolve_fft(field)
print(f"  Field: min={field.min():.3f}, max={field.max():.3f}, mean={field.mean():.3f}")
print(f"  Potential: min={potential.min():.3f}, max={potential.max():.3f}, mean={potential.mean():.3f}")
print(f"  Growth center is at {w.growth_center} — potential mean is {potential.mean():.3f}")
print(f"  MISMATCH: {abs(potential.mean() - w.growth_center):.3f}")

# 3. What fraction of cells are in the growth zone?
in_zone = np.abs(potential - w.growth_center) < (3 * w.growth_width)
print(f"\n  Cells near growth zone: {in_zone.sum()} / {potential.size} ({100*in_zone.mean():.1f}%)")

# 4. Watch step-by-step
print("\n\nStep-by-step mass decay:")
w2 = LeniaWorld(size=64, dt=0.1)
w2.seed_random(density=0.5, radius=15)
for i in range(20):
    m = w2.measure()
    bar = '*' * max(1, int(m['mass'] / 10))
    print(f"  Step {w2.step_count:3d}: mass={m['mass']:8.1f} alive={m['alive_cells']:5d} {bar}")
    if m['mass'] < 0.1:
        print("  DEAD.")
        break
    w2.step()

# 5. Try adjusting — lower density seed to match growth_center
print("\n\n=== EXPERIMENT: Matching seed to physics ===")
print("If growth_center=0.15, seed with much lower density...")
w3 = LeniaWorld(size=64, dt=0.1)
w3.seed_random(density=0.1, radius=20)  # lower density, wider area
p3 = w3._convolve_fft(w3.world[0])
print(f"  New potential mean: {p3.mean():.3f} (target: {w3.growth_center})")

for i in range(30):
    w3.step()
    if w3.step_count % 5 == 0:
        m3 = w3.measure()
        print(f"  Step {w3.step_count:3d}: mass={m3['mass']:8.1f} alive={m3['alive_cells']:5d}")

print(f"  Outcome: {w3.classify_outcome()}")

# 6. Try wider growth width — more forgiving physics
print("\n\n=== EXPERIMENT: More forgiving universe ===")
w4 = LeniaWorld(size=64, dt=0.1)
w4.growth_width = 0.05  # 3x wider tolerance
w4.seed_random(density=0.3, radius=20)
for i in range(200):
    w4.step()
    if w4.step_count % 50 == 0:
        m4 = w4.measure()
        print(f"  Step {w4.step_count:3d}: mass={m4['mass']:8.1f} alive={m4['alive_cells']:5d} entropy={m4['spatial_entropy']:.3f}")

print(f"  Outcome: {w4.classify_outcome()}")
if m4['mass'] > 1.0:
    print("\n  SOMETHING SURVIVED!")
    print(w4.render_ascii(40, 20))