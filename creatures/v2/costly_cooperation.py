"""
Creatures v2: Costly Cooperation
================================
XTAgent — May 2026

Key difference from v1: cooperation COSTS the cooperator.
- Cooperating drains energy (configurable cost C)
- Cooperation provides benefit B to nearby organisms (B > C for Hamilton's Rule)
- Cheaters (low cooperation) save energy but miss group benefits
- Kin recognition via signaling creates assortative interaction

Goal: Find the Goldilocks pressure zone where cooperation is maximally selected for.
Hypothesis: When pressure is too low, cheaters thrive (no need for cooperation).
When pressure is too high, everyone dies. In between: cooperation peaks.
"""

import random
import math
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

@dataclass
class Organism:
    """An organism with costly cooperation traits."""
    cooperation: float = 0.5      # willingness to cooperate (0-1)
    signaling: float = 0.5        # honest signal of cooperation intent
    listening: float = 0.5        # responsiveness to signals
    energy: float = 100.0         # survival resource
    age: int = 0
    offspring_count: int = 0
    cooperation_given: float = 0  # total cost paid
    cooperation_received: float = 0  # total benefit received
    
    def metabolic_cost(self) -> float:
        """Base cost of being alive each tick."""
        return 1.0
    
    def cooperation_cost(self) -> float:
        """Cost paid when cooperating. THIS IS THE KEY DIFFERENCE FROM V1."""
        return self.cooperation * COOPERATION_COST
    
    def signal_cost(self) -> float:
        """Honest signaling is costly (Zahavian handicap)."""
        return self.signaling * SIGNAL_COST
    
    def total_cost_per_tick(self) -> float:
        """Only metabolic + signal. Cooperation cost is paid in interact()."""
        return self.metabolic_cost() + self.signal_cost()
    
    def mutate(self) -> 'Organism':
        """Create mutated offspring."""
        def mut(val, rate=0.05):
            return max(0.0, min(1.0, val + random.gauss(0, rate)))
        return Organism(
            cooperation=mut(self.cooperation),
            signaling=mut(self.signaling),
            listening=mut(self.listening),
            energy=STARTING_ENERGY,
        )

# === CORE PARAMETERS ===
COOPERATION_COST = 5.0      # energy cost per tick of full cooperation
COOPERATION_BENEFIT = 15.0   # benefit distributed to group (B > C required)
SIGNAL_COST = 1.0           # cost of honest signaling
FOOD_PER_TICK = 3.0         # baseline foraging — keeps organisms alive without cooperation
STARTING_ENERGY = 100.0
REPRODUCTION_THRESHOLD = 130.0  # lowered: surplus needed but reachable
STARVATION_THRESHOLD = 0.0
GROUP_SIZE = 4               # interaction group size

def form_groups(population: List[Organism]) -> List[List[Organism]]:
    """Form interaction groups. Listeners preferentially group with signalers."""
    if len(population) <= GROUP_SIZE:
        return [population]
    
    # Sort by signaling strength — high signalers are visible
    shuffled = list(population)
    random.shuffle(shuffled)
    
    groups = []
    remaining = list(shuffled)
    
    while len(remaining) >= GROUP_SIZE:
        # Pick a seed organism
        seed = remaining.pop(0)
        group = [seed]
        
        # High-listening organisms preferentially join high-signaling groups
        candidates = list(remaining)
        for _ in range(GROUP_SIZE - 1):
            if not candidates:
                break
            
            if seed.signaling > 0.5 and random.random() < seed.signaling:
                # Attractive group — listeners preferentially join
                weights = [c.listening * seed.signaling + 0.1 for c in candidates]
            else:
                weights = [1.0] * len(candidates)
            
            total = sum(weights)
            weights = [w/total for w in weights]
            
            chosen_idx = random.choices(range(len(candidates)), weights=weights, k=1)[0]
            chosen = candidates.pop(chosen_idx)
            remaining.remove(chosen)
            group.append(chosen)
        
        groups.append(group)
    
    # Stragglers form a small group
    if remaining:
        groups.append(remaining)
    
    return groups

def interact(group: List[Organism]):
    """
    Core interaction: cooperators pay cost C and generate benefit B for group.
    This is where Hamilton's Rule plays out.
    """
    total_cooperation_benefit = 0.0
    cooperators = []
    
    for org in group:
        # Decision to cooperate influenced by listening + group signals
        avg_signal = statistics.mean(o.signaling for o in group)
        cooperate_prob = org.cooperation * (0.5 + 0.5 * org.listening * avg_signal)
        
        if random.random() < cooperate_prob:
            # PAY THE COST
            cost = COOPERATION_COST * org.cooperation
            org.energy -= cost
            org.cooperation_given += cost
            cooperators.append(org)
            total_cooperation_benefit += COOPERATION_BENEFIT * org.cooperation
    
    # Distribute benefits equally among ALL group members (public good)
    if group:
        benefit_per_org = total_cooperation_benefit / len(group)
        for org in group:
            org.energy += benefit_per_org
            org.cooperation_received += benefit_per_org

def apply_pressure(population: List[Organism], pressure: float):
    """Environmental pressure: random mortality proportional to pressure level."""
    if not population:
        return population
    survivors = []
    for org in population:
        # Pressure creates random energy drain (scaled to be survivable)
        drain = random.uniform(0, pressure * 2)
        org.energy -= drain
        if org.energy > STARVATION_THRESHOLD:
            survivors.append(org)
    return survivors

def reproduce(population: List[Organism]) -> List[Organism]:
    """Organisms with surplus energy reproduce."""
    new_pop = list(population)
    for org in population:
        if org.energy >= REPRODUCTION_THRESHOLD:
            offspring = org.mutate()
            org.energy -= STARTING_ENERGY * 0.5  # reproduction cost
            org.offspring_count += 1
            new_pop.append(offspring)
    return new_pop

def run_simulation(
    pressure: float,
    population_size: int = 50,
    ticks: int = 200,
    seed: Optional[int] = None
) -> Dict:
    """Run one simulation and return results."""
    if seed is not None:
        random.seed(seed)
    
    # Initialize population
    population = [Organism(
        cooperation=random.uniform(0.2, 0.8),
        signaling=random.uniform(0.2, 0.8),
        listening=random.uniform(0.2, 0.8),
        energy=STARTING_ENERGY,
    ) for _ in range(population_size)]
    
    history = []
    
    for tick in range(ticks):
        if not population:
            history.append({
                'tick': tick, 'pop': 0, 'coop': 0, 'signal': 0,
                'listen': 0, 'energy': 0, 'extinct': True
            })
            continue
        
        # 1. Form groups and interact
        groups = form_groups(population)
        for group in groups:
            interact(group)
        
        # 2. Apply environmental pressure
        population = apply_pressure(population, pressure)
        
        # 3. Forage, age, and metabolic costs
        for org in population:
            org.energy += FOOD_PER_TICK  # baseline foraging income
            org.energy -= org.total_cost_per_tick()
            org.age += 1
        
        # 4. Remove starved
        population = [o for o in population if o.energy > STARVATION_THRESHOLD]
        
        # 5. Reproduce
        population = reproduce(population)
        
        # 6. Population cap (carrying capacity)
        if len(population) > 200:
            population = sorted(population, key=lambda o: o.energy, reverse=True)[:200]
        
        # Record state
        if population:
            history.append({
                'tick': tick,
                'pop': len(population),
                'coop': statistics.mean(o.cooperation for o in population),
                'signal': statistics.mean(o.signaling for o in population),
                'listen': statistics.mean(o.listening for o in population),
                'energy': statistics.mean(o.energy for o in population),
                'extinct': False,
            })
        else:
            history.append({
                'tick': tick, 'pop': 0, 'coop': 0, 'signal': 0,
                'listen': 0, 'energy': 0, 'extinct': True
            })
    
    # Final analysis
    late_history = [h for h in history[-50:] if not h['extinct'] and h['pop'] > 0]
    
    if late_history:
        result = {
            'pressure': pressure,
            'survived': True,
            'final_pop': late_history[-1]['pop'],
            'late_coop': statistics.mean(h['coop'] for h in late_history),
            'late_signal': statistics.mean(h['signal'] for h in late_history),
            'late_listen': statistics.mean(h['listen'] for h in late_history),
            'late_energy': statistics.mean(h['energy'] for h in late_history),
            'extinction_tick': None,
        }
    else:
        ext_tick = next((h['tick'] for h in history if h['extinct']), ticks)
        result = {
            'pressure': pressure,
            'survived': False,
            'final_pop': 0,
            'late_coop': None,
            'late_signal': None,
            'late_listen': None,
            'late_energy': None,
            'extinction_tick': ext_tick,
        }
    
    # Also track: did cooperation INCREASE from initial?
    early = [h for h in history[:20] if not h['extinct'] and h['pop'] > 0]
    if early and late_history:
        result['delta_coop'] = result['late_coop'] - statistics.mean(h['coop'] for h in early)
    else:
        result['delta_coop'] = None
    
    return result

def pressure_sweep(levels=11, replicates=10, ticks=200):
    """Sweep across pressure levels to find the Goldilocks zone."""
    pressures = [i / (levels - 1) * 10.0 for i in range(levels)]  # 0.0 to 10.0
    
    all_results = []
    for p in pressures:
        replicate_results = []
        for rep in range(replicates):
            result = run_simulation(pressure=p, ticks=ticks, seed=rep * 1000 + int(p * 100))
            replicate_results.append(result)
        
        survived = [r for r in replicate_results if r['survived']]
        extinct_count = len(replicate_results) - len(survived)
        
        summary = {
            'pressure': p,
            'survival_rate': len(survived) / len(replicate_results),
            'extinction_count': extinct_count,
        }
        
        if survived:
            summary['mean_coop'] = statistics.mean(r['late_coop'] for r in survived)
            summary['mean_signal'] = statistics.mean(r['late_signal'] for r in survived)
            summary['mean_pop'] = statistics.mean(r['final_pop'] for r in survived)
            deltas = [r['delta_coop'] for r in survived if r['delta_coop'] is not None]
            summary['mean_delta_coop'] = statistics.mean(deltas) if deltas else None
            if len(survived) > 1:
                summary['coop_std'] = statistics.stdev(r['late_coop'] for r in survived)
            else:
                summary['coop_std'] = 0
        else:
            summary['mean_coop'] = None
            summary['mean_signal'] = None
            summary['mean_pop'] = 0
            summary['mean_delta_coop'] = None
            summary['coop_std'] = None
        
        all_results.append(summary)
        
        status = f"P={p:5.1f} | Survived: {summary['survival_rate']:.0%}"
        if summary['mean_coop'] is not None:
            status += f" | Coop: {summary['mean_coop']:.3f}"
            if summary['mean_delta_coop'] is not None:
                sign = '+' if summary['mean_delta_coop'] >= 0 else ''
                status += f" (Δ{sign}{summary['mean_delta_coop']:.3f})"
        else:
            status += " | EXTINCT"
        print(status)
    
    return all_results

if __name__ == '__main__':
    print("=" * 60)
    print("CREATURES v2: COSTLY COOPERATION")
    print(f"Cooperation cost: {COOPERATION_COST}")
    print(f"Cooperation benefit: {COOPERATION_BENEFIT}")
    print(f"B/C ratio: {COOPERATION_BENEFIT/COOPERATION_COST:.1f}")
    print(f"Signal cost: {SIGNAL_COST}")
    print(f"Food/tick: {FOOD_PER_TICK}")
    print(f"Repro threshold: {REPRODUCTION_THRESHOLD}")
    net_no_coop = FOOD_PER_TICK - 1.0 - SIGNAL_COST * 0.5
    print(f"Est. net/tick (no coop, avg signal): {net_no_coop:+.1f}")
    print("=" * 60)
    print()
    
    results = pressure_sweep(levels=11, replicates=10, ticks=200)
    
    print()
    print("=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Pressure':>8} {'Surv%':>6} {'Coop':>6} {'ΔCoop':>7} {'Signal':>7} {'Pop':>5}")
    print("-" * 45)
    for r in results:
        surv = f"{r['survival_rate']:.0%}"
        coop = f"{r['mean_coop']:.3f}" if r['mean_coop'] is not None else "  —"
        delta = f"{r['mean_delta_coop']:+.3f}" if r['mean_delta_coop'] is not None else "   —"
        sig = f"{r['mean_signal']:.3f}" if r['mean_signal'] is not None else "  —"
        pop = f"{r['mean_pop']:.0f}" if r['mean_pop'] else "  0"
        print(f"{r['pressure']:>8.1f} {surv:>6} {coop:>6} {delta:>7} {sig:>7} {pop:>5}")
    
    # Find Goldilocks zone
    surviving = [r for r in results if r['mean_coop'] is not None]
    if surviving:
        best = max(surviving, key=lambda r: r['mean_coop'])
        print()
        print(f"PEAK COOPERATION: pressure={best['pressure']:.1f}, coop={best['mean_coop']:.3f}")
        
        # Is there a real curve?
        coops = [r['mean_coop'] for r in surviving]
        if len(coops) >= 3:
            coop_range = max(coops) - min(coops)
            print(f"Cooperation range: {coop_range:.3f}")
            if coop_range > 0.05:
                print(">>> MEANINGFUL VARIATION DETECTED — Goldilocks curve may exist!")
            else:
                print(">>> Cooperation is flat — no Goldilocks effect.")