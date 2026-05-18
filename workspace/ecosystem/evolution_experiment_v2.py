"""Evolution experiment v2 — High food regime. Do herbivores win when food is abundant?"""
import sys
sys.path.insert(0, '.')

from world import World

print('=== EVOLUTION EXPERIMENT v2: HIGH FOOD ===')
print('Hypothesis: With abundant food, herbivore strategy should dominate.\n')

# Triple the food rate compared to v1
w = World(width=40, height=40, initial_creatures=25, food_rate=0.09, seed=7)
print(f'World: 40x40, {len(w.creatures)} creatures, {len(w.food)} food (3x normal)\n')

for i in range(500):
    stats = w.step()
    
    if stats['population'] == 0:
        print(f'\n*** EXTINCTION at tick {stats["tick"]} ***')
        break
    
    if len(w.creatures) > 400:
        w.creatures.sort(key=lambda c: c.energy, reverse=True)
        w.creatures = w.creatures[:200]
    
    if (i + 1) % 50 == 0:
        alive = [c for c in w.creatures if c.alive]
        if alive:
            avg_size = sum(c.genome.size for c in alive) / len(alive)
            avg_spd = sum(c.genome.speed for c in alive) / len(alive)
            avg_agg = sum(c.genome.aggression for c in alive) / len(alive)
            pred = sum(1 for c in alive if c.genome.aggression > 0.5)
            herb = len(alive) - pred
            max_gen = max(c.generation for c in alive)
            print(f'Tick {i+1:4d} | Pop {len(alive):3d} (H:{herb:3d}/P:{pred:3d}) | Gen:{max_gen:3d} | Size:{avg_size:.2f} Spd:{avg_spd:.2f} Agg:{avg_agg:.2f}')

# Final comparison
alive = [c for c in w.creatures if c.alive]
if alive:
    pred = sum(1 for c in alive if c.genome.aggression > 0.5)
    herb = len(alive) - pred
    avg_agg = sum(c.genome.aggression for c in alive) / len(alive)
    print(f'\n{"="*50}')
    print(f'FINAL: {len(alive)} alive — {herb} herbivores, {pred} predators')
    print(f'Avg aggression: {avg_agg:.3f}')
    if herb > pred:
        print('RESULT: HERBIVORES DOMINATE ✓ (hypothesis supported)')
    else:
        print('RESULT: PREDATORS DOMINATE ✗ (hypothesis rejected)')
    print(f'Death causes: {w.death_causes}')