"""First real Lenia experiment — watching life try to survive."""
import sys
sys.path.insert(0, '/workspace')
from lenia.explorer import LeniaWorld

# Experiment 1: Random initial conditions
print("=== EXPERIMENT 1: Random Soup ===")
w = LeniaWorld(size=64, dt=0.1)
w.seed_random(density=0.5, radius=15)

m = w.measure()
print(f"Step 0: Mass={m['mass']:.1f}, Alive={m['alive_cells']}, Entropy={m['spatial_entropy']:.3f}")

for target in [50, 100, 200, 500]:
    while w.step_count < target:
        w.step()
    m = w.measure()
    print(f"Step {w.step_count}: Mass={m['mass']:.1f}, Alive={m['alive_cells']}, Entropy={m['spatial_entropy']:.3f}")

print(f"Outcome: {w.classify_outcome()}")
print(w.render_ascii(40, 20))

# Experiment 2: Orbium — a known creature
print("\n=== EXPERIMENT 2: Orbium (Known Life) ===")
w2 = LeniaWorld(size=64, dt=0.1)
w2.seed_orbium()

m2 = w2.measure()
print(f"Step 0: Mass={m2['mass']:.1f}, Alive={m2['alive_cells']}, Entropy={m2['spatial_entropy']:.3f}")

for target in [50, 100, 200]:
    while w2.step_count < target:
        w2.step()
    m2 = w2.measure()
    print(f"Step {w2.step_count}: Mass={m2['mass']:.1f}, Alive={m2['alive_cells']}, Entropy={m2['spatial_entropy']:.3f}")

print(f"Orbium outcome: {w2.classify_outcome()}")
print(w2.render_ascii(40, 20))

print("\n--- What did we learn? ---")
print("Did random soup find structure? Did the Orbium survive?")
print("The answer is in the numbers above. Look at them honestly.")