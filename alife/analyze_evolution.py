"""
Evolutionary Analytics — Track the story of digital life.
"""
import numpy as np
import sys, random
sys.path.insert(0, '/workspace/alife')
from ecosystem import Genome, Creature, Ecosystem

def classify(creature):
    g = creature.genome
    if g.aggression > 0.3:
        return 'aggressive'
    elif g.food_sense > 0.6:
        return 'forager'
    elif g.social_drive > 0.3:
        return 'social'
    else:
        return 'wanderer'

def genome_diversity(creatures):
    if len(creatures) < 2:
        return 0.0
    traits = np.array([
        [c.genome.wander_drive, c.genome.food_sense,
         c.genome.social_drive, c.genome.aggression,
         c.genome.efficiency, c.genome.mutability]
        for c in creatures
    ])
    return float(np.mean(np.std(traits, axis=0)))

def run_tracked_evolution(steps=500, seed=42):
    np.random.seed(seed)
    random.seed(seed)

    eco = Ecosystem(width=40, height=30)

    # Seed diverse initial population
    for _ in range(30):
        g = Genome(
            wander_drive=np.random.uniform(0.2, 0.8),
            food_sense=np.random.uniform(0.1, 0.9),
            social_drive=np.random.uniform(-0.3, 0.5),
            aggression=np.random.uniform(0.0, 0.5),
            efficiency=np.random.uniform(0.5, 1.5),
            reproduction_threshold=np.random.uniform(60, 100),
            offspring_gift=np.random.uniform(0.3, 0.5),
            mutability=np.random.uniform(0.05, 0.2),
        )
        x = np.random.randint(0, eco.width)
        y = np.random.randint(0, eco.height)
        eco.creatures.append(Creature(x=x, y=y, energy=80.0, genome=g))

    history = []
    for step in range(steps):
        eco.step()

        alive = [c for c in eco.creatures if c.energy > 0]
        if not alive:
            print(f"  [step {step}] EXTINCTION")
            break

        types = {}
        for c in alive:
            t = classify(c)
            types[t] = types.get(t, 0) + 1

        div = genome_diversity(alive)
        avg_energy = np.mean([c.energy for c in alive])
        max_gen = max(c.generation for c in alive)

        snapshot = {
            'step': step, 'pop': len(alive), 'diversity': div,
            'avg_energy': avg_energy, 'max_gen': max_gen, 'types': dict(types)
        }
        history.append(snapshot)

        if step % 100 == 0:
            print(f"  [step {step:>4}] pop={len(alive):>3} div={div:.3f} "
                  f"gen={max_gen} energy={avg_energy:.1f} types={types}")

    return history

if __name__ == '__main__':
    print("=" * 60)
    print("  ARTIFICIAL LIFE: EVOLUTIONARY CHRONICLE")
    print("=" * 60)
    history = run_tracked_evolution(steps=500)
    print()

    if history:
        final = history[-1]
        start = history[0]
        print(f"  Final population: {final['pop']}")
        print(f"  Peak generation:  {final['max_gen']}")
        print(f"  Diversity start → end: {start['diversity']:.3f} → {final['diversity']:.3f}")
        print(f"  Final niches: {final['types']}")

        # Did evolution happen?
        if final['max_gen'] > 3:
            print("\n  ✓ Evolution occurred — multiple generations emerged.")
        if final['diversity'] > start['diversity'] * 0.5:
            print("  ✓ Diversity maintained — no monoculture collapse.")
        if len(final['types']) > 1:
            print("  ✓ Niche differentiation — multiple survival strategies coexist.")
    print("=" * 60)