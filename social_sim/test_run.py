"""Quick smoke test: does the simulation actually run?"""
from world import World, WorldConfig

cfg = WorldConfig(width=10, height=10, num_agents=5, num_resource_patches=4, max_ticks=10)
w = World(cfg)

for t in range(10):
    w.tick()
    alive = [a for a in w.agents if a.alive]
    n_alive = len(alive)
    avg_food = sum(a.food for a in alive) / n_alive if n_alive else 0
    res_total = sum(r.amount for r in w.resources)
    print(f"Tick {t:2d}: {n_alive} alive | avg_food={avg_food:.1f} | resources={res_total:.1f}")

print("\n--- Final agent states ---")
for a in w.agents:
    status = "ALIVE" if a.alive else "DEAD"
    print(f"  Agent {a.id}: {status} food={a.food:.1f} pos=({a.x},{a.y}) trait={a.personality_trait}")

print("\nSIMULATION COMPLETE")