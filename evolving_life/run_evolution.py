"""
Watch evolution design the laws of physics.
Written to match the ACTUAL evolver.py API.
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from evolver import (
    evolve_rules, demonstrate_rule, benchmark_known_rules,
    individual_to_rule, simulate_rule, life_rule
)

print("╔══════════════════════════════════════════════╗")
print("║  EVOLVING LIFE                              ║")
print("║  What rules does evolution discover?        ║")
print("╚══════════════════════════════════════════════╝")
print()

# First: how interesting are the known rules?
benchmark_known_rules()

# Now evolve — small enough to finish, big enough to surprise
print("═══ Evolution Begins ═══\n")
random.seed(42)

best, engine = evolve_rules(pop_size=50, generations=25, verbose=True)

print()
print(demonstrate_rule(best, "BEST EVOLVED RULE"))

# Compare evolved vs Conway's Life
print("\n═══ Head to Head: Evolution vs Conway ═══\n")
evolved_rule = individual_to_rule(best)
for seed in [42, 99, 200]:
    em = simulate_rule(evolved_rule, 20, 20, 80, seed=seed)
    lm = simulate_rule(life_rule, 20, 20, 80, seed=seed)
    print(f"  Seed {seed}:")
    print(f"    Evolved:  {em.summary()}")
    print(f"    Conway:   {lm.summary()}")
    print()

print(f"═══ Evolution Complete ═══")
print(f"Best expression: {best.genome}")
print(f"Best fitness: {best.fitness:.4f}")