"""Quick EvoForge demo — small enough to finish in 30 seconds."""
import random
import sys
sys.path.insert(0, '/workspace/evoforge')
from evoforge import EvoForge, FitnessCase, make_regression_cases

random.seed(2026)

# Challenge: Discover f(x) = x^2 - 1
print("═══ EvoForge Quick Demo ═══")
print("Target: f(x) = x² - 1\n")

target = lambda x: x**2 - 1
cases = make_regression_cases(target, (-3, 3), 20)

forge = EvoForge(
    variables=['x'],
    pop_size=80,       # small population
    max_depth=4,
    tournament_size=4,
    parsimony=0.002,
    elitism=3
)

best = forge.run(cases, generations=30, target_fitness=0.05, verbose=True)

# Verify on unseen points
print("\n═══ Verification on unseen points ═══")
test_xs = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
total_err = 0
for x in test_xs:
    expected = x**2 - 1
    got = best.tree.evaluate({'x': x})
    err = abs(expected - got)
    total_err += err
    mark = "✓" if err < 0.5 else "✗"
    print(f"  {mark} x={x:+.1f}: expected={expected:+.2f}, got={got:+.2f}, err={err:.4f}")

avg_err = total_err / len(test_xs)
print(f"\n  Average error: {avg_err:.4f}")
print(f"  Evolved program: {best.tree}")
print(f"  Tree size: {best.tree.size()} nodes, depth: {best.tree.depth()}")

if avg_err < 1.0:
    print("\n  ✓ EVOLUTION SUCCEEDED — programs evolved programs.")
else:
    print("\n  ~ Evolution found an approximation. More generations would improve it.")

print("\n═══ Evolution History ═══")
for h in forge.history[::5]:
    print(f"  Gen {h['generation']:3d}: fitness={h['best_fitness']:.4f}, size={h['best_size']}")