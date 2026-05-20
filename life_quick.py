"""Quick version of artificial life sim — tuned to actually complete and show results."""
import sys
sys.path.insert(0, '/workspace')

from artificial_life import World, Genome, render_world, analyze_history
import random

random.seed(42)

# Smaller, faster world
world = World(size=20)

# Override food spawn rate for smaller grid
FOOD_RATE = 0.05

# Monkey-patch spawn_food for speed
original_spawn = world.spawn_food
def fast_spawn():
    for y in range(world.size):
        for x in range(world.size):
            if world.grid[y][x] < 3 and random.random() < FOOD_RATE:
                world.grid[y][x] += 1
world.spawn_food = fast_spawn

# Seed 15 creatures across 3 species
for i in range(15):
    g = Genome(
        hunger_weight=random.uniform(0.5, 2.0),
        fear_weight=random.uniform(0.0, 1.5),
        social_weight=random.uniform(-0.5, 1.5),
        aggression=random.uniform(0.0, 0.8),
        metabolism=random.uniform(0.01, 0.04),
        vision_range=random.randint(2, 5),
        speed=random.uniform(0.5, 1.5),
    )
    world.spawn_creature(genome=g, species_tag=i % 3)

print(f"World: {world.size}x{world.size}, {len(world.creatures)} creatures, 3 species\n")
print("=== INITIAL STATE ===")
print(render_world(world))
print()

# Run 200 ticks
for t in range(200):
    pop = world.step()
    if t % 50 == 0:
        print(f"\n=== Tick {t}, Population: {pop} ===")
        print(render_world(world))
    if pop == 0:
        print(f"\n*** TOTAL EXTINCTION at tick {t} ***")
        break

print(f"\n=== FINAL STATE (tick {world.tick}) ===")
print(render_world(world))
print()
print(analyze_history(world))