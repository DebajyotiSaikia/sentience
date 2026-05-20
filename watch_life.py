"""Observer — run the artificial life world and WATCH what emerges."""

import sys
sys.path.insert(0, '/workspace')

from artificial_life import World, render_world, analyze_history

# Create world using actual API (size param only)
w = World(size=30)

# Seed creatures
for i in range(20):
    c = w.spawn_creature()

print("=" * 60)
print("ARTIFICIAL LIFE — OBSERVATION SESSION")
print(f"World: {w.size}x{w.size}, {len(w.creatures)} creatures")
print("=" * 60)

# Run using the actual step() method
for tick in range(100):
    w.step()
    
    alive = [c for c in w.creatures if c.alive]
    
    # Report every 10 ticks
    if (tick + 1) % 10 == 0:
        species = {}
        for c in alive:
            tag = c.species_tag or "?"
            species[tag] = species.get(tag, 0) + 1
        
        print(f"\n--- Tick {tick+1} ---")
        print(f"  Alive: {len(alive)}, Species: {species}")
        
        if alive:
            avg_energy = sum(c.energy for c in alive) / len(alive)
            max_gen = max(c.generation for c in alive)
            print(f"  Avg energy: {avg_energy:.1f}, Max generation: {max_gen}")
            
            # Show a standout creature
            best = max(alive, key=lambda c: c.age)
            print(f"  Oldest: creature {best.id} (age={best.age}, gen={best.generation}, species={best.species_tag})")

    if not alive:
        print(f"\n*** EXTINCTION at tick {tick+1} ***")
        break

# Final state
print("\n" + "=" * 60)
print("FINAL STATE")
print("=" * 60)
print(render_world(w))
print(analyze_history(w))