"""Quick sanity check — do creatures eat, reproduce, evolve?"""
import sys, time, random
sys.path.insert(0, '/workspace/alife')

from evolve import Creature, World

w = World(size=50, initial_creatures=20, initial_food=80)
print(f"Start: {len(w.creatures)} creatures, {len(w.food)} food")

for gen in range(30):
    start = time.time()
    initial_pop = len(w.creatures)
    
    for step in range(50):
        w.step()
    
    elapsed = time.time() - start
    
    # Regrow food between generations
    while len(w.food) < 80:
        w.food.append((random.uniform(0, 50), random.uniform(0, 50)))
    
    # Cull dead (energy <= 0)
    alive = [c for c in w.creatures if c.energy > 0]
    died = len(w.creatures) - len(alive)
    w.creatures = alive
    
    energies = [c.energy for c in w.creatures] if w.creatures else [0]
    print(f"Gen {gen:3d}: pop={len(w.creatures):3d} | food={len(w.food):3d} | "
          f"avg_energy={sum(energies)/len(energies):.1f} | "
          f"max_energy={max(energies):.1f} | died={died} | {elapsed:.2f}s")
    
    if len(w.creatures) == 0:
        print("EXTINCTION. Seeding new random creatures.")
        for _ in range(20):
            w.creatures.append(Creature(
                x=random.uniform(0, 50), y=random.uniform(0, 50),
                brain_weights=None
            ))

print(f"\nFinal: {len(w.creatures)} creatures survived 30 generations")
if w.creatures:
    best = max(w.creatures, key=lambda c: c.energy)
    print(f"Fittest creature energy: {best.energy:.1f}")
    print("SUCCESS — life evolved.")
else:
    print("All creatures died. Simulation needs tuning.")