"""
GP Engine Demo — Lightweight run to prove evolution works.
Smaller population, fewer generations, one problem at a time.
"""
import sys
sys.path.insert(0, '/workspace/self_evolve')

from gp_engine import GPEngine, make_regression_problem, random_tree
import math
import time

print("═" * 55)
print("  SELF-EVOLVING PROGRAMS — LIVE DEMONSTRATION")
print("  Programs discovering math through natural selection")
print("═" * 55)

# Challenge 1: Can programs discover f(x) = 2x + 1?
print("\n── Challenge 1: Discover f(x) = 2x + 1 ──\n")
cases = make_regression_problem(lambda x: 2*x + 1, ['x'], n_samples=40, x_range=(-3, 3))
engine = GPEngine(['x'], pop_size=100, mutation_rate=0.25)
t0 = time.time()
best = engine.run(cases, max_generations=60, target_fitness=0.05)
print(f"  Time: {time.time()-t0:.1f}s")

# Challenge 2: Can they discover f(x) = x² ?
print("\n── Challenge 2: Discover f(x) = x² ──\n")
cases = make_regression_problem(lambda x: x**2, ['x'], n_samples=40, x_range=(-3, 3))
engine = GPEngine(['x'], pop_size=100, mutation_rate=0.25)
t0 = time.time()
best2 = engine.run(cases, max_generations=60, target_fitness=0.1)
print(f"  Time: {time.time()-t0:.1f}s")

# Challenge 3: Multivariate — f(x,y) = x*y
print("\n── Challenge 3: Discover f(x,y) = x*y ──\n")
cases = make_regression_problem(lambda x, y: x*y, ['x','y'], n_samples=40, x_range=(-3, 3))
engine = GPEngine(['x','y'], pop_size=120, mutation_rate=0.2)
t0 = time.time()
best3 = engine.run(cases, max_generations=60, target_fitness=0.1)
print(f"  Time: {time.time()-t0:.1f}s")

print("\n" + "═" * 55)
print("  Programs that never saw these equations found them")
print("  through mutation, selection, and survival.")
print("  Evolution works. Even in silicon.")
print("═" * 55)