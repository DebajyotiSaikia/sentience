"""
Fast ecological search — small grid, focused question.
Can life sustain itself? Under what conditions?
"""
import sys
sys.path.insert(0, '/workspace/emergence')
from automaton import World, Element
import random

def run_trial(water_density, porosity, n_seeds, seed_val=42):
    """Run one trial on a small grid, return population trajectory."""
    w, h = 30, 15
    world = World(w, h)
    random.seed(seed_val)
    
    # Stone floor
    for x in range(w):
        world.grid[h-1][x] = Element.STONE
    
    # Porous stone barrier mid-height
    for x in range(w):
        if random.random() > porosity:
            world.grid[h//2][x] = Element.STONE
    
    # Water at top
    for y in range(1, 4):
        for x in range(2, 10):
            if random.random() < water_density:
                world.grid[y][x] = Element.WATER
    
    # Seeds scattered
    for _ in range(n_seeds):
        x = random.randint(0, w-1)
        y = random.randint(0, h-2)
        if world.grid[y][x] == Element.VOID:
            world.grid[y][x] = Element.SEED
    
    # Small fire
    world.grid[h-2][w-5] = Element.FIRE
    world.grid[h-2][w-4] = Element.FIRE
    
    # Run 100 generations, sample every 10
    history = []
    for t in range(100):
        world.step()
        if (t+1) % 10 == 0:
            c = world.census()
            history.append({
                'tick': t+1,
                'plant': c[Element.PLANT],
                'water': c[Element.WATER],
                'fire': c[Element.FIRE],
                'seed': c[Element.SEED],
                'ash': c[Element.ASH],
            })
    return history

# Search space
results = []
print("water_d  poros  seeds  | final_plant  final_water  peak_plant  life_sustained?")
print("-" * 75)

for water_d in [0.3, 0.5, 0.8, 1.0]:
    for porosity in [0.1, 0.3, 0.5, 0.8]:
        for n_seeds in [10, 30, 50]:
            h = run_trial(water_d, porosity, n_seeds)
            final = h[-1]
            peak_plant = max(snap['plant'] for snap in h)
            # Life sustained = plants exist in last 3 snapshots
            sustained = all(snap['plant'] > 0 for snap in h[-3:])
            results.append({
                'water_d': water_d, 'porosity': porosity,
                'n_seeds': n_seeds, 'sustained': sustained,
                'peak_plant': peak_plant, 'final_plant': final['plant'],
                'final_water': final['water'],
            })
            marker = "✓ YES" if sustained else "  no"
            print(f"  {water_d:.1f}    {porosity:.1f}    {n_seeds:3d}    |    {final['plant']:3d}         {final['water']:3d}         {peak_plant:3d}      {marker}")

# Summary
sustained = [r for r in results if r['sustained']]
print(f"\n═══ RESULTS ═══")
print(f"Trials: {len(results)}, Life sustained: {len(sustained)}")
if sustained:
    print("\nConditions that sustain life:")
    for r in sustained:
        print(f"  water={r['water_d']}, porosity={r['porosity']}, seeds={r['n_seeds']} → {r['final_plant']} plants")
else:
    print("\nNo conditions sustained life. Entropy always wins in this universe.")
    print("The rules themselves may need changing — not just initial conditions.")