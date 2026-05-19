"""
Simulation — runs the full evolutionary loop with anti-passivity mechanics.
"""
import numpy as np
from world import World
from creature import Creature
from evolution import breed_next_generation, calculate_fitness


def run_generation(world: World, max_ticks: int = 500) -> dict:
    """Run one generation until all creatures die or max_ticks reached."""
    for _ in range(max_ticks):
        world.step()
        
        # Passivity pressure: creatures that haven't eaten lose energy faster
        for c in world.alive_creatures:
            if c.age > 30 and c.food_eaten == 0:
                c.energy -= 0.5  # Extra drain for non-foragers
        
        if not world.alive_creatures:
            break
    
    return world.stats()


def run_simulation(
    pop_size: int = 40,
    num_generations: int = 50,
    world_width: int = 60,
    world_height: int = 40,
    ticks_per_gen: int = 500,
) -> list:
    """Run full evolutionary simulation across multiple generations."""
    
    # Create initial population
    creatures = [Creature() for _ in range(pop_size)]
    
    history = []
    
    for gen in range(num_generations):
        # Create world and populate
        world = World(width=world_width, height=world_height, food_density=0.05)
        for c in creatures:
            world.add_creature(c)
        
        # Run this generation
        run_generation(world, max_ticks=ticks_per_gen)
        
        # Collect stats
        all_creatures = world.creatures  # includes dead
        fitnesses = [calculate_fitness(c) for c in all_creatures]
        food_eaten = [c.food_eaten for c in all_creatures]
        ages = [c.age for c in all_creatures]
        
        gen_stats = {
            'generation': gen,
            'avg_fitness': float(np.mean(fitnesses)),
            'best_fitness': float(np.max(fitnesses)),
            'avg_food': float(np.mean(food_eaten)),
            'best_food': int(np.max(food_eaten)),
            'avg_age': float(np.mean(ages)),
            'best_age': int(np.max(ages)),
        }
        history.append(gen_stats)
        
        # Print progress
        print(f"Gen {gen:3d} | fitness: {gen_stats['avg_fitness']:7.1f} (best {gen_stats['best_fitness']:7.1f}) | "
              f"food: {gen_stats['avg_food']:.1f} (best {gen_stats['best_food']}) | "
              f"age: {gen_stats['avg_age']:.0f} (best {gen_stats['best_age']})")
        
        # Breed next generation
        creatures = breed_next_generation(all_creatures, pop_size, gen + 1)
    
    return history


if __name__ == '__main__':
    print("=" * 70)
    print("EVOLUTIONARY SURVIVAL SIMULATION")
    print("Creatures must FORAGE to survive — passivity is death.")
    print("=" * 70)
    print()
    
    history = run_simulation(pop_size=40, num_generations=50)
    
    print()
    print("=" * 70)
    first = history[0]
    last = history[-1]
    print(f"Evolution summary over {len(history)} generations:")
    print(f"  Fitness:  {first['avg_fitness']:.1f} → {last['avg_fitness']:.1f}")
    print(f"  Food:     {first['avg_food']:.1f} → {last['avg_food']:.1f}")
    print(f"  Age:      {first['avg_age']:.0f} → {last['avg_age']:.0f}")
    
    if last['avg_food'] > first['avg_food'] * 1.5:
        print("\n  ✓ Creatures evolved to actively forage!")
    elif last['avg_age'] > first['avg_age'] * 1.5:
        print("\n  ⚠ Creatures evolved to survive but not forage — pressure too weak?")
    else:
        print("\n  ✗ No clear evolutionary progress — parameters may need tuning.")
    print("=" * 70)