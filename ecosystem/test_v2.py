"""Quick test of ecosystem v2 — short run to check if feedback loops work."""
from world_v2 import World, Species

# Single seed, 300 ticks — should finish fast
world = World(seed=42)
world.seed_world()

# Print every 50 ticks
for t in range(300):
    world.step()
    if t % 50 == 0:
        c = world.census()
        print(f"  tick {t:3d}: grazers={c['grazer']:3d} hunters={c['hunter']:3d} fungus={c['fungus']:3d} plants={c['plants']:3d}")

print()
s = world.summarize()
print(f"Final: {s['final_census']}")
print(f"Born: {s['total_born']} | Died: {s['total_died']}")
print(f"Lineages: {s['surviving_lineages']} | Max generation: {s['max_generation']}")
if s['extinction_events']:
    for ev in s['extinction_events']:
        print(f"  ☠ {ev['species']} extinct at tick {ev['tick']}")
else:
    print("✦ All species survived!")