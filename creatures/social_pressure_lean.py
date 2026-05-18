"""
LEAN SOCIAL PRESSURE SIMULATION
================================
Can social pressure force communication to emerge?

Stripped to bare essentials:
- 20 creatures, 50x50 grid
- 100 generations, 50 timesteps each
- TWO conditions run back-to-back:
  A) NO PRESSURE: food everywhere, no predators
  B) HIGH PRESSURE: predators that kill loners, cooperative food

Creatures have:
- 4-signal vocabulary (0-3)
- Brain: signal_tendency, listen_tendency, signal_on_danger, flee_on_signal
- They reproduce with mutation if they eat enough

The key metric: does signal diversity and signal-response correlation
increase ONLY under social pressure?

Author: XTAgent | 2026-05-17
"""

import numpy as np
import random
from collections import defaultdict

class Creature:
    __slots__ = ['x', 'y', 'energy', 'brain', 'alive', 'age', 'signals_sent', 'signals_heard']
    
    def __init__(self, x, y, brain=None):
        self.x = x
        self.y = y
        self.energy = 10.0
        self.alive = True
        self.age = 0
        self.signals_sent = 0
        self.signals_heard = 0
        # Brain: 6 genes
        if brain is None:
            self.brain = {
                'signal_rate': random.random(),      # how often to signal
                'listen_rate': random.random(),       # how much to respond to signals
                'danger_signal': random.random(),     # signal when predator near
                'flee_on_signal': random.random(),    # flee when hearing signal
                'signal_type': random.randint(0, 3),  # preferred signal
                'cooperation': random.random(),       # tendency to approach signalers
            }
        else:
            self.brain = dict(brain)
    
    def mutate(self):
        b = self.brain
        for key in ['signal_rate', 'listen_rate', 'danger_signal', 'flee_on_signal', 'cooperation']:
            if random.random() < 0.15:
                b[key] = max(0, min(1, b[key] + random.gauss(0, 0.1)))
        if random.random() < 0.1:
            b['signal_type'] = random.randint(0, 3)


def run_simulation(social_pressure=False, n_creatures=20, n_generations=80, 
                   steps_per_gen=40, world_size=50):
    """Run one condition. Returns generation-by-generation metrics."""
    
    # Initialize population
    pop = [Creature(random.randint(0, world_size-1), random.randint(0, world_size-1)) 
           for _ in range(n_creatures)]
    
    metrics = []
    
    for gen in range(n_generations):
        # Place food
        food = set()
        if social_pressure:
            # Less solo food, some cooperative food (needs 2 creatures nearby)
            for _ in range(15):  # scarce solo food
                food.add((random.randint(0, world_size-1), random.randint(0, world_size-1)))
            # Cooperative food locations (rich but need partner)
            coop_food = set()
            for _ in range(10):
                coop_food.add((random.randint(0, world_size-1), random.randint(0, world_size-1)))
        else:
            # Abundant solo food
            for _ in range(40):
                food.add((random.randint(0, world_size-1), random.randint(0, world_size-1)))
            coop_food = set()
        
        # Place predators (only in pressure condition)
        predators = []
        if social_pressure:
            for _ in range(5):
                predators.append((random.randint(0, world_size-1), random.randint(0, world_size-1)))
        
        # Track signals this generation
        signals_emitted = []
        signal_responses = 0
        total_signals_heard = 0
        
        for step in range(steps_per_gen):
            # Reset alive creatures' step state
            active_signals = []  # (x, y, signal_type, sender_id)
            
            # Phase 1: Creatures emit signals
            for i, c in enumerate(pop):
                if not c.alive:
                    continue
                
                should_signal = random.random() < c.brain['signal_rate']
                
                # Under pressure: signal more if predator nearby
                if social_pressure:
                    for px, py in predators:
                        if abs(c.x - px) + abs(c.y - py) < 8:
                            if random.random() < c.brain['danger_signal']:
                                should_signal = True
                            break
                
                if should_signal:
                    active_signals.append((c.x, c.y, c.brain['signal_type'], i))
                    c.signals_sent += 1
                    signals_emitted.append(c.brain['signal_type'])
            
            # Phase 2: Creatures perceive signals and act
            for i, c in enumerate(pop):
                if not c.alive:
                    continue
                
                # Hear nearby signals
                heard = []
                for sx, sy, stype, sender_id in active_signals:
                    if sender_id == i:
                        continue
                    dist = abs(c.x - sx) + abs(c.y - sy)
                    if dist < 10:
                        heard.append((sx, sy, stype, dist))
                
                if heard:
                    c.signals_heard += len(heard)
                    total_signals_heard += len(heard)
                
                # Respond to signals?
                if heard and random.random() < c.brain['listen_rate']:
                    signal_responses += 1
                    
                    # Under pressure: flee from predators if signaled
                    if social_pressure and c.brain['flee_on_signal'] > 0.5:
                        # Move away from predators
                        for px, py in predators:
                            if abs(c.x - px) + abs(c.y - py) < 10:
                                dx = 1 if c.x < px else -1
                                c.x = max(0, min(world_size-1, c.x - dx * 3))
                                dy = 1 if c.y < py else -1
                                c.y = max(0, min(world_size-1, c.y - dy * 3))
                                break
                    
                    # Approach signalers (cooperation)
                    if c.brain['cooperation'] > 0.5 and heard:
                        nearest = min(heard, key=lambda h: h[3])
                        dx = 1 if nearest[0] > c.x else -1 if nearest[0] < c.x else 0
                        dy = 1 if nearest[1] > c.y else -1 if nearest[1] < c.y else 0
                        c.x = max(0, min(world_size-1, c.x + dx))
                        c.y = max(0, min(world_size-1, c.y + dy))
                
                # Random movement
                c.x = max(0, min(world_size-1, c.x + random.randint(-2, 2)))
                c.y = max(0, min(world_size-1, c.y + random.randint(-2, 2)))
                
                # Eat solo food
                pos = (c.x, c.y)
                if pos in food:
                    c.energy += 3.0
                    food.discard(pos)
                
                # Eat cooperative food (need another creature within 3)
                if pos in coop_food:
                    partner_near = any(
                        abs(c.x - o.x) + abs(c.y - o.y) < 4 
                        for j, o in enumerate(pop) if j != i and o.alive
                    )
                    if partner_near:
                        c.energy += 6.0  # Big reward for cooperation
                        coop_food.discard(pos)
                
                # Predator kills loners
                if social_pressure:
                    for px, py in predators:
                        if abs(c.x - px) + abs(c.y - py) < 3:
                            # Lone creature dies. Creature with ally nearby survives.
                            allies_near = sum(
                                1 for j, o in enumerate(pop)
                                if j != i and o.alive and abs(c.x - o.x) + abs(c.y - o.y) < 5
                            )
                            if allies_near == 0:
                                c.energy -= 15  # Lethal
                            else:
                                c.energy -= 2   # Bruised but alive
                            break
                
                # Metabolism
                c.energy -= 0.3
                c.age += 1
                if c.energy <= 0:
                    c.alive = False
        
        # End of generation — reproduction
        alive = [c for c in pop if c.alive]
        
        # Collect metrics
        gen_signal_rate = np.mean([c.brain['signal_rate'] for c in alive]) if alive else 0
        gen_listen_rate = np.mean([c.brain['listen_rate'] for c in alive]) if alive else 0
        gen_flee = np.mean([c.brain['flee_on_signal'] for c in alive]) if alive else 0
        gen_coop = np.mean([c.brain['cooperation'] for c in alive]) if alive else 0
        gen_danger = np.mean([c.brain['danger_signal'] for c in alive]) if alive else 0
        
        # Signal diversity: how many different signal types used?
        sig_diversity = len(set(signals_emitted)) / 4.0 if signals_emitted else 0
        
        # Response rate
        response_rate = signal_responses / max(1, total_signals_heard)
        
        metrics.append({
            'gen': gen,
            'alive': len(alive),
            'signal_rate': gen_signal_rate,
            'listen_rate': gen_listen_rate,
            'flee_on_signal': gen_flee,
            'cooperation': gen_coop,
            'danger_signal': gen_danger,
            'signal_diversity': sig_diversity,
            'response_rate': response_rate,
            'total_signals': len(signals_emitted),
        })
        
        # Reproduce
        if len(alive) < 2:
            # Extinction — repopulate with random
            pop = [Creature(random.randint(0, world_size-1), random.randint(0, world_size-1)) 
                   for _ in range(n_creatures)]
        else:
            # Select parents by energy (fitness)
            alive.sort(key=lambda c: c.energy, reverse=True)
            new_pop = []
            for _ in range(n_creatures):
                # Tournament selection
                p = random.choice(alive[:max(2, len(alive)//2)])
                child = Creature(
                    random.randint(0, world_size-1),
                    random.randint(0, world_size-1),
                    brain=p.brain
                )
                child.mutate()
                new_pop.append(child)
            pop = new_pop
    
    return metrics


def compare_conditions():
    """Run both conditions and compare."""
    print("=" * 60)
    print("SOCIAL PRESSURE EXPERIMENT")
    print("Does communication emerge only when silence is lethal?")
    print("=" * 60)
    
    random.seed(42)
    np.random.seed(42)
    
    print("\n▸ Running NO PRESSURE condition...")
    no_pressure = run_simulation(social_pressure=False)
    
    print("▸ Running HIGH PRESSURE condition...")
    high_pressure = run_simulation(social_pressure=True)
    
    # Compare early vs late generations
    early = slice(0, 10)
    late = slice(-10, None)
    
    def avg_metric(data, key, s):
        vals = [d[key] for d in data[s]]
        return np.mean(vals) if vals else 0
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    metrics_to_compare = [
        ('signal_rate', 'Signal Rate'),
        ('listen_rate', 'Listen Rate'),
        ('danger_signal', 'Danger Signaling'),
        ('flee_on_signal', 'Flee on Signal'),
        ('cooperation', 'Cooperation'),
        ('signal_diversity', 'Signal Diversity'),
        ('response_rate', 'Response Rate'),
    ]
    
    print(f"\n{'Metric':<20} {'No Pressure':>20} {'High Pressure':>20}")
    print(f"{'':.<20} {'Early → Late':>20} {'Early → Late':>20}")
    print("-" * 62)
    
    findings = {}
    for key, label in metrics_to_compare:
        np_early = avg_metric(no_pressure, key, early)
        np_late = avg_metric(no_pressure, key, late)
        hp_early = avg_metric(high_pressure, key, early)
        hp_late = avg_metric(high_pressure, key, late)
        
        np_change = np_late - np_early
        hp_change = hp_late - hp_early
        
        print(f"{label:<20} {np_early:.2f} → {np_late:.2f} ({np_change:+.2f})  "
              f"{hp_early:.2f} → {hp_late:.2f} ({hp_change:+.2f})")
        
        findings[key] = {
            'no_pressure_change': np_change,
            'high_pressure_change': hp_change,
            'divergence': hp_change - np_change,
        }
    
    # Survival comparison
    np_survival = avg_metric(no_pressure, 'alive', late)
    hp_survival = avg_metric(high_pressure, 'alive', late)
    print(f"\n{'Survival':<20} {avg_metric(no_pressure, 'alive', early):.0f} → {np_survival:.0f}"
          f"           {avg_metric(high_pressure, 'alive', early):.0f} → {hp_survival:.0f}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    
    communication_emerged = (
        findings['signal_rate']['high_pressure_change'] > findings['signal_rate']['no_pressure_change']
        and findings['listen_rate']['high_pressure_change'] > findings['listen_rate']['no_pressure_change']
    )
    
    cooperation_emerged = (
        findings['cooperation']['high_pressure_change'] > findings['cooperation']['no_pressure_change']
    )
    
    if communication_emerged:
        print("\n✓ COMMUNICATION EMERGED UNDER PRESSURE")
        print("  Signal rate and listen rate both increased MORE under social pressure")
        print("  than in the no-pressure condition.")
    else:
        print("\n✗ Communication did NOT differentially emerge under pressure")
        print("  The social pressure condition didn't produce more signaling")
        print("  than the control. The pressure design may need adjustment.")
    
    if cooperation_emerged:
        print("\n✓ COOPERATION EMERGED UNDER PRESSURE")
        print("  Creatures evolved to approach signalers more under threat.")
    else:
        print("\n✗ Cooperation did not differentially emerge.")
    
    # What was the strongest divergence?
    strongest = max(findings.items(), key=lambda x: abs(x[1]['divergence']))
    print(f"\n→ Strongest divergence: {strongest[0]} "
          f"(pressure effect: {strongest[1]['divergence']:+.3f})")
    
    # Danger signaling specifically
    ds = findings['danger_signal']
    if ds['high_pressure_change'] > 0.05:
        print(f"\n→ DANGER SIGNALING evolved: {ds['high_pressure_change']:+.3f} under pressure")
        print("  Creatures learned to warn each other about predators.")
    
    # Flee on signal
    fs = findings['flee_on_signal']  
    if fs['high_pressure_change'] > 0.05:
        print(f"\n→ FLEE RESPONSE evolved: {fs['high_pressure_change']:+.3f} under pressure")
        print("  Creatures learned to respond to warnings by fleeing.")
    
    print("\n" + "=" * 60)
    return no_pressure, high_pressure


if __name__ == "__main__":
    compare_conditions()