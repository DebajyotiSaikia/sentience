"""
GOLDILOCKS ZONE EXPERIMENT
============================
At what pressure level does cooperation peak?

Sweep from 0% to 100% environmental pressure in 6 steps.
Measure cooperation, communication, and survival at each level.
Find the sweet spot where adversity HELPS rather than HURTS.

Author: XTAgent | 2026-05-17
"""

import numpy as np
import random
from collections import defaultdict

class Creature:
    __slots__ = ['x', 'y', 'energy', 'alive', 'brain', 'age']
    
    def __init__(self, x, y, brain=None):
        self.x, self.y = x, y
        self.energy = 10.0
        self.alive = True
        self.age = 0
        if brain is None:
            self.brain = {
                'signal_rate': random.random(),
                'listen_rate': random.random(),
                'cooperation': random.random(),
                'flee_response': random.random(),
                'boldness': random.random(),
            }
        else:
            self.brain = dict(brain)
    
    def mutate(self):
        child_brain = dict(self.brain)
        gene = random.choice(list(child_brain.keys()))
        child_brain[gene] = max(0, min(1, child_brain[gene] + random.gauss(0, 0.15)))
        return child_brain


def run_condition(pressure_level, n_creatures=15, world_size=40,
                  generations=80, timesteps=40):
    """
    pressure_level: 0.0 (paradise) to 1.0 (hell)
    Controls: predator count, food scarcity, environmental damage
    """
    # Scale parameters by pressure
    n_predators = int(pressure_level * 6)        # 0 to 6 predators
    food_amount = int(20 - pressure_level * 15)  # 20 down to 5 food sources
    env_damage = pressure_level * 0.8            # passive energy drain per tick
    
    # Initialize creatures
    creatures = [Creature(random.randint(0, world_size-1),
                          random.randint(0, world_size-1))
                 for _ in range(n_creatures)]
    
    # Track metrics across generations
    early_metrics = defaultdict(list)  # first 20 gens
    late_metrics = defaultdict(list)   # last 20 gens
    
    for gen in range(generations):
        # Place food
        food = set()
        for _ in range(food_amount):
            food.add((random.randint(0, world_size-1), random.randint(0, world_size-1)))
        
        # Place predators
        predators = [(random.randint(0, world_size-1), random.randint(0, world_size-1))
                     for _ in range(n_predators)]
        
        # Track signals this generation
        signals_emitted = 0
        signals_responded = 0
        cooperative_acts = 0
        
        for t in range(timesteps):
            active = [c for c in creatures if c.alive]
            if len(active) < 2:
                break
            
            # Passive damage from environment
            for c in active:
                c.energy -= 0.1 + env_damage * 0.1
                c.age += 1
                if c.energy <= 0:
                    c.alive = False
            
            # Signal phase
            signals = {}  # position -> signal_strength
            for c in [cr for cr in creatures if cr.alive]:
                if random.random() < c.brain['signal_rate']:
                    # Check if predator nearby
                    pred_near = any(abs(c.x-px) + abs(c.y-py) < 8
                                   for px, py in predators)
                    strength = 1.0 if pred_near else 0.5
                    signals[(c.x, c.y)] = strength
                    signals_emitted += 1
            
            # Response phase
            for c in [cr for cr in creatures if cr.alive]:
                # Check for nearby signals
                for (sx, sy), strength in signals.items():
                    if (sx, sy) == (c.x, c.y):
                        continue
                    dist = abs(c.x - sx) + abs(c.y - sy)
                    if dist < 10 and random.random() < c.brain['listen_rate']:
                        signals_responded += 1
                        # Flee response
                        if strength > 0.7 and random.random() < c.brain['flee_response']:
                            # Move away from signal source (away from danger)
                            c.x = (c.x + random.choice([-3, 3])) % world_size
                            c.y = (c.y + random.choice([-3, 3])) % world_size
                        # Cooperation: move toward signaler
                        elif random.random() < c.brain['cooperation']:
                            dx = 1 if sx > c.x else -1
                            dy = 1 if sy > c.y else -1
                            c.x = (c.x + dx) % world_size
                            c.y = (c.y + dy) % world_size
                            cooperative_acts += 1
            
            # Predator attacks — target isolated creatures
            for px, py in predators:
                nearby = [c for c in creatures if c.alive
                          and abs(c.x-px) + abs(c.y-py) < 5]
                if nearby:
                    # Groups are safer — predator less likely to attack groups
                    for c in nearby:
                        neighbors = sum(1 for o in creatures if o.alive and o is not c
                                        and abs(o.x-c.x) + abs(o.y-c.y) < 4)
                        # Kill probability decreases with group size
                        kill_prob = 0.3 / (1 + neighbors * 0.5)
                        if random.random() < kill_prob:
                            c.alive = False
                # Predators wander
                px = (px + random.randint(-2, 2)) % world_size
                py = (py + random.randint(-2, 2)) % world_size
            
            # Eating
            for c in [cr for cr in creatures if cr.alive]:
                if (c.x, c.y) in food:
                    # Cooperative food: more energy if others nearby
                    neighbors = sum(1 for o in creatures if o.alive and o is not c
                                    and abs(o.x-c.x) + abs(o.y-c.y) < 3)
                    bonus = 1 + neighbors * 0.3 * pressure_level  # cooperation bonus scales with pressure
                    c.energy += 3.0 * bonus
                    food.discard((c.x, c.y))
            
            # Random movement
            for c in [cr for cr in creatures if cr.alive]:
                if random.random() < c.brain['boldness']:
                    c.x = (c.x + random.randint(-2, 2)) % world_size
                    c.y = (c.y + random.randint(-2, 2)) % world_size
        
        # Collect metrics
        alive = [c for c in creatures if c.alive]
        n_alive = len(alive)
        
        metrics = {
            'signal_rate': np.mean([c.brain['signal_rate'] for c in alive]) if alive else 0,
            'listen_rate': np.mean([c.brain['listen_rate'] for c in alive]) if alive else 0,
            'cooperation': np.mean([c.brain['cooperation'] for c in alive]) if alive else 0,
            'flee_response': np.mean([c.brain['flee_response'] for c in alive]) if alive else 0,
            'survival': n_alive,
            'signals': signals_emitted,
            'responses': signals_responded,
            'coop_acts': cooperative_acts,
        }
        
        target = early_metrics if gen < 20 else late_metrics if gen >= 60 else None
        if target is not None:
            for k, v in metrics.items():
                target[k].append(v)
        
        # Reproduction
        alive = [c for c in creatures if c.alive]
        offspring = []
        for c in alive:
            if c.energy > 15:
                child = Creature(
                    (c.x + random.randint(-2, 2)) % world_size,
                    (c.y + random.randint(-2, 2)) % world_size,
                    brain=c.mutate()
                )
                offspring.append(child)
                c.energy -= 8
        
        creatures = alive + offspring
        
        # Population cap
        if len(creatures) > 25:
            creatures = sorted(creatures, key=lambda c: c.energy, reverse=True)[:25]
        
        # Minimum viable population
        while len(creatures) < 5:
            creatures.append(Creature(
                random.randint(0, world_size-1),
                random.randint(0, world_size-1)
            ))
    
    # Compute averages
    result = {}
    for key in ['signal_rate', 'listen_rate', 'cooperation', 'flee_response', 'survival']:
        early = np.mean(early_metrics[key]) if early_metrics[key] else 0
        late = np.mean(late_metrics[key]) if late_metrics[key] else 0
        result[key] = {'early': early, 'late': late, 'delta': late - early}
    
    return result


def main():
    print("=" * 70)
    print("GOLDILOCKS ZONE EXPERIMENT")
    print("At what pressure level does cooperation peak?")
    print("=" * 70)
    
    pressure_levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    all_results = {}
    
    for p in pressure_levels:
        label = f"{int(p*100)}%"
        print(f"\n▸ Running pressure={label}...", flush=True)
        all_results[p] = run_condition(p)
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS: COOPERATION BY PRESSURE LEVEL")
    print("=" * 70)
    
    print(f"\n{'Pressure':>10} | {'Coop (early)':>12} | {'Coop (late)':>12} | {'Δ Coop':>8} | {'Signal':>8} | {'Listen':>8} | {'Survive':>8}")
    print("-" * 80)
    
    coop_peak = None
    coop_peak_val = -999
    
    for p in pressure_levels:
        r = all_results[p]
        label = f"{int(p*100)}%"
        coop_late = r['cooperation']['late']
        
        if coop_late > coop_peak_val:
            coop_peak_val = coop_late
            coop_peak = p
        
        print(f"{label:>10} | {r['cooperation']['early']:>12.3f} | {coop_late:>12.3f} | "
              f"{r['cooperation']['delta']:>+8.3f} | {r['signal_rate']['late']:>8.3f} | "
              f"{r['listen_rate']['late']:>8.3f} | {r['survival']['late']:>8.1f}")
    
    # Find where cooperation GREW the most
    growth_peak = max(pressure_levels, key=lambda p: all_results[p]['cooperation']['delta'])
    
    print(f"\n{'=' * 70}")
    print("ANALYSIS")
    print(f"{'=' * 70}")
    print(f"\n  Peak cooperation level:  {int(coop_peak*100)}% pressure (coop={coop_peak_val:.3f})")
    print(f"  Peak cooperation GROWTH: {int(growth_peak*100)}% pressure (Δ={all_results[growth_peak]['cooperation']['delta']:+.3f})")
    
    if 0.2 <= coop_peak <= 0.6:
        print(f"\n  ✓ GOLDILOCKS ZONE FOUND at ~{int(coop_peak*100)}% pressure!")
        print(f"    Moderate adversity breeds cooperation.")
    elif coop_peak == 0.0:
        print(f"\n  → Safety breeds cooperation. No Goldilocks zone in this model.")
        print(f"    Cooperation is a luxury good, not a survival strategy.")
    elif coop_peak >= 0.8:
        print(f"\n  → Extreme pressure breeds cooperation. Only the social survive.")
    else:
        print(f"\n  → Results are ambiguous. More resolution needed.")
    
    # Visualize the curve
    print(f"\n  Cooperation curve:")
    for p in pressure_levels:
        bar_len = int(all_results[p]['cooperation']['late'] * 40)
        marker = " ◄ PEAK" if p == coop_peak else ""
        print(f"    {int(p*100):>3}% | {'█' * bar_len}{'░' * (40-bar_len)} {all_results[p]['cooperation']['late']:.3f}{marker}")
    
    print(f"\n{'=' * 70}")


if __name__ == "__main__":
    main()