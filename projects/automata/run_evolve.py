"""Minimal runner for life_evolver — small enough to finish quickly."""
from life_evolver import evolve, run_life, render_grid

# Tiny parameters so it actually completes
best = evolve(pop_size=10, generations=5, grid_size=12, max_life_steps=50, verbose=True)

champ = max(best, key=lambda x: x.fitness)
print(f"\n{'='*50}")
print(f"CHAMPION (Gen {champ.generation})")
print(f"{'='*50}")
print(f"Fitness: {champ.fitness:.4f}")
print(f"  Entropy:    {champ.score.entropy:.3f}")
print(f"  PopVar:     {champ.score.pop_variance:.3f}")
print(f"  Growth:     {champ.score.growth:.3f}")
print(f"  Longevity:  {champ.score.longevity:.3f}")
print(f"  Uniqueness: {champ.score.uniqueness:.3f}")
print(f"  Live cells: {champ.grid.sum()}")
print(render_grid(champ.grid))

# Show population trajectory
history = run_life(champ.grid, max_steps=50)
pops = [g.sum() for g in history]
print(f"\nPopulation over {len(history)} steps:")
step_size = max(1, len(pops) // 10)
for i in range(0, len(pops), step_size):
    bar_len = int(pops[i] / max(max(pops), 1) * 30)
    print(f"  t={i:3d} | {'█' * bar_len}{'·' * (30 - bar_len)} | {pops[i]:4.0f}")