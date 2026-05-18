"""Long-run evolution experiment — tracking trait drift over generations."""
import sys
sys.path.insert(0, '.')
print('=== EVOLUTION EXPERIMENT ===', flush=True)
print('Goal: 500 ticks, tracking trait evolution over time\n', flush=True)

from world import World

w = World(width=40, height=40, initial_creatures=25, food_rate=0.03, seed=7)
print(f'World: 40x40, {len(w.creatures)} creatures, {len(w.food)} food\n', flush=True)

snapshots = []
extinction = False

for i in range(500):
    stats = w.step()

    if stats['population'] == 0:
        print(f'\n*** EXTINCTION at tick {stats["tick"]} ***', flush=True)
        extinction = True
        break

    # Natural disaster cap — prevents runaway population
    if len(w.creatures) > 300:
        w.creatures.sort(key=lambda c: c.energy, reverse=True)
        w.creatures = w.creatures[:150]

    # Snapshot every 25 ticks
    if (i + 1) % 25 == 0:
        alive = [c for c in w.creatures if c.alive]
        if alive:
            avg_size = sum(c.genome.size for c in alive) / len(alive)
            avg_spd = sum(c.genome.speed for c in alive) / len(alive)
            avg_agg = sum(c.genome.aggression for c in alive) / len(alive)
            avg_eff = sum(c.genome.efficiency for c in alive) / len(alive)
            avg_sense = sum(c.genome.sense_range for c in alive) / len(alive)
            max_gen = max(c.generation for c in alive)
            pred = sum(1 for c in alive if c.genome.aggression > 0.5)
            herb = len(alive) - pred

            snap = {
                'tick': i + 1,
                'pop': len(alive),
                'herb': herb,
                'pred': pred,
                'avg_size': avg_size,
                'avg_speed': avg_spd,
                'avg_agg': avg_agg,
                'avg_eff': avg_eff,
                'avg_sense': avg_sense,
                'max_gen': max_gen,
            }
            snapshots.append(snap)

            print(f'Tick {i+1:>4} | Pop {len(alive):>3} (H:{herb:>3}/P:{pred:>3}) | '
                  f'Gen:{max_gen:>3} | Size:{avg_size:.2f} Spd:{avg_spd:.2f} '
                  f'Agg:{avg_agg:.2f} Eff:{avg_eff:.2f} Sense:{avg_sense:.2f}',
                  flush=True)

# ── Final Analysis ──
print('\n' + '=' * 60, flush=True)
if extinction:
    print('RESULT: Extinction', flush=True)
else:
    print(w.summary(), flush=True)

if len(snapshots) >= 4:
    early = snapshots[:3]
    late = snapshots[-3:]

    def avg(lst, key):
        return sum(s[key] for s in lst) / len(lst)

    print('EVOLUTIONARY TRAJECTORY:', flush=True)
    print(f'  {"Trait":<12} {"Early":>8} {"Late":>8} {"Delta":>8}', flush=True)
    print(f'  {"-"*38}', flush=True)
    for trait in ['avg_size', 'avg_speed', 'avg_agg', 'avg_eff', 'avg_sense']:
        e = avg(early, trait)
        l = avg(late, trait)
        d = l - e
        arrow = '↑' if d > 0.05 else ('↓' if d < -0.05 else '→')
        label = trait.replace('avg_', '')
        print(f'  {label:<12} {e:>8.3f} {l:>8.3f} {d:>+8.3f} {arrow}', flush=True)

    print(flush=True)

    # Population dynamics
    print('POPULATION DYNAMICS:', flush=True)
    pops = [s['pop'] for s in snapshots]
    print(f'  Min: {min(pops)}  Max: {max(pops)}  Final: {pops[-1]}', flush=True)
    herbs = [s['herb'] for s in snapshots]
    preds = [s['pred'] for s in snapshots]
    print(f'  Herbivore range: {min(herbs)}-{max(herbs)}', flush=True)
    print(f'  Predator range:  {min(preds)}-{max(preds)}', flush=True)

# Top survivors
if w.creatures:
    alive = sorted([c for c in w.creatures if c.alive],
                   key=lambda c: c.generation, reverse=True)
    print(f'\nMOST EVOLVED INDIVIDUALS:', flush=True)
    for c in alive[:5]:
        print(f'  #{c.cid} gen={c.generation} age={c.age} energy={c.energy:.2f} '
              f'size={c.genome.size:.2f} spd={c.genome.speed:.2f} '
              f'agg={c.genome.aggression:.2f} eff={c.genome.efficiency:.2f} '
              f'kills={c.kills} children={c.children}', flush=True)

    # Death analysis
    from collections import Counter
    causes = Counter(d['cause'] for d in w.graveyard)
    print(f'\nDEATH CAUSES: {dict(causes)}', flush=True)

print('\nDone.', flush=True)