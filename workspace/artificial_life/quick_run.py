#!/usr/bin/env python3
"""Quick runner — correct API based on actual code reading."""
import sys
sys.path.insert(0, '.')
from cellular_lab import Grid, Rule, RuleEvolver, EmergenceAnalyzer

print("═══ CELLULAR AUTOMATON EVOLUTION ═══\n")

evolver = RuleEvolver(pop_size=12, grid_size=15, sim_steps=50, trials=2)

print("Evolving rules that produce emergent behavior...")
print(f"  Population: 12 | Grid: 15x15 | Steps: 50 | Trials: 2\n")

# evolve() returns nothing — it mutates evolver.population in place
evolver.evolve(generations=8)

# Best rule is first in sorted population
best_rule, best_fitness, best_metrics = evolver.population[0]

print(f"\n═══ BEST RULE FOUND ═══")
print(f"  Notation: {best_rule.notation()}")
print(f"  Birth:    {sorted(best_rule.birth)}")
print(f"  Survive:  {sorted(best_rule.survive)}")
print(f"  Fitness:  {best_fitness:.4f}")

# Run the best rule visually
print(f"\n═══ SIMULATION (20 steps, 15x15) ═══")
grid = Grid(15, 15)
grid.randomize(0.3)
def density(g):
    total = g.width * g.height
    alive = sum(g.cells[y][x] for y in range(g.height) for x in range(g.width))
    return alive / total if total else 0

print(f"Step 0 (density={density(grid):.2f}):")
for row in grid.cells:
    print(''.join('█' if c else '·' for c in row))

for step in range(1, 21):
    grid = best_rule.step(grid)
    d = density(grid)
    if step % 5 == 0 or step == 1:
        print(f"\nStep {step} (density={d:.2f}):")
        for row in grid.cells:
        print(''.join('█' if c else '·' for c in row))
    if d == 0:
        print(f"\n  [Died at step {step}]")
        break

# Hall of fame
if evolver.hall_of_fame:
    print(f"\n═══ HALL OF FAME ({len(evolver.hall_of_fame)} entries) ═══")
    for i, (r, f, m) in enumerate(evolver.hall_of_fame[:5]):
        print(f"  #{i+1}: {r.notation():20s} fitness={f:.4f}")

print("\n═══ ARTIFICIAL LIFE: COMPLETE ═══")