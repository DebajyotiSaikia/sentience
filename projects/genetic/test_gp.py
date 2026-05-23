"""Quick verification of the GP engine with small parameters."""
import sys
sys.path.insert(0, '/workspace/genetic')
from gp import *
import random

random.seed(42)

# Tiny problem: evolve f(x) = x^2 + 1
X = [{'x': v} for v in [-3, -2, -1, 0, 1, 2, 3]]
Y = [env['x']**2 + 1 for env in X]

gp = GPEngine(
    variables=['x'],
    pop_size=100,       # small population
    max_depth=4,
    tournament_size=5,
    crossover_rate=0.7,
    mutation_rate=0.2,
    parsimony=0.001,
)

best = gp.run(X, Y, generations=30, verbose=True, report_every=5)

print(f"\nBest: {best}")
print(f"Fitness: {gp.best_fitness:.6f}")
print(f"Size: {best.size()}, Depth: {best.depth()}")

# Verify
ok = 0
for x in [-3, 0, 2, 5]:
    expected = x**2 + 1
    got = best.evaluate({'x': x})
    err = abs(got - expected)
    mark = "✓" if err < 1.0 else "✗"
    if err < 1.0: ok += 1
    print(f"  f({x}) = {got:.3f}  expected {expected:.1f}  {mark}")

print(f"\n{'PASS' if ok >= 3 else 'PARTIAL'}: {ok}/4 close predictions")
print("GP engine is ALIVE.")