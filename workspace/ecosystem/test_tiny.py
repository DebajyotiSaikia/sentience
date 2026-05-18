"""Minimal ecosystem test — does it run at all?"""
import sys
print('Starting...', flush=True)

from world import World
print('Import OK', flush=True)

w = World(width=20, height=20, initial_creatures=5, food_rate=0.01, seed=42)
print(f'Created: {len(w.creatures)} creatures, {len(w.food)} food', flush=True)

for i in range(50):
    stats = w.step()
    if (i + 1) % 10 == 0:
        print(f'Tick {stats["tick"]:3d}: pop={stats["population"]:3d} '
              f'food={stats["food_count"]:4d} '
              f'herb={stats["herbivores"]} pred={stats["predators"]} '
              f'gen={stats["avg_gen"]:.1f}', flush=True)
    if stats['population'] == 0:
        print('EXTINCTION', flush=True)
        break
    if stats['population'] > 100:
        print(f'Pop explosion at tick {stats["tick"]}!', flush=True)
        break

print('\nSurvivors:', flush=True)
for c in w.creatures[:5]:
    print(f'  {c.status()}', flush=True)

print('\nDONE', flush=True)