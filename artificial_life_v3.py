"""
Artificial Life v3 — Finding the Sweet Spot
XTAgent, 2026-05-19

V1: No death → no evolution (stagnation)
V2: Too much death → extinction before adaptation propagates
V3: Sweep the parameter space. Find where evolution actually works.

The hypothesis: there's a narrow band of environmental pressure where
selection is strong enough to drive adaptation but mild enough for
populations to persist. Find it empirically.
"""

import random
import math
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum


class Season(Enum):
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


@dataclass
class Genome:
    aggression: float = 0.2
    reproduction_threshold: float = 0.7
    metabolism: float = 0.03
    speed: float = 1.0
    fat_storage: float = 0.3
    cold_resistance: float = 0.0
    cooperation: float = 0.0       # NEW: sharing food with neighbors

    def mutate(self, rate=0.15) -> 'Genome':
        def m(v, lo=0.0, hi=1.0):
            return max(lo, min(hi, v + random.gauss(0, rate)))
        return Genome(
            aggression=m(self.aggression),
            reproduction_threshold=m(self.reproduction_threshold, 0.3, 0.95),
            metabolism=m(self.metabolism, 0.005, 0.1),
            speed=m(self.speed, 0.2, 2.0),
            fat_storage=m(self.fat_storage, 0.0, 0.8),
            cold_resistance=m(self.cold_resistance),
            cooperation=m(self.cooperation),
        )

    def distance(self, other: 'Genome') -> float:
        """Genetic distance — used to measure evolution."""
        diffs = [
            abs(self.aggression - other.aggression),
            abs(self.metabolism - other.metabolism),
            abs(self.fat_storage - other.fat_storage),
            abs(self.cold_resistance - other.cold_resistance),
            abs(self.cooperation - other.cooperation),
        ]
        return sum(diffs) / len(diffs)


@dataclass
class Creature:
    x: int
    y: int
    energy: float
    genome: Genome
    age: int = 0
    alive: bool = True
    generation: int = 0


class World:
    def __init__(self, size=30, food_density=0.15, regrow_rate=0.008,
                 season_length=100, winter_severity=2.0,
                 initial_creatures=25, carrying_capacity=80):
        self.size = size
        self.regrow_rate = regrow_rate
        self.season_length = season_length
        self.winter_severity = winter_severity
        self.carrying_capacity = carrying_capacity
        
        # Food grid
        self.food = [[0.0]*size for _ in range(size)]
        for r in range(size):
            for c in range(size):
                if random.random() < food_density:
                    self.food[r][c] = random.uniform(0.5, 2.0)
        
        # Creatures
        self.creatures: List[Creature] = []
        self.founding_genome = Genome()  # baseline to measure evolution from
        for _ in range(initial_creatures):
            g = Genome()
            c = Creature(
                x=random.randint(0, size-1),
                y=random.randint(0, size-1),
                energy=0.5,
                genome=g,
                generation=0
            )
            self.creatures.append(c)
        
        self.tick = 0
        self.total_born = initial_creatures
        self.total_died = 0
        self.max_generation = 0
        self.trait_history = []  # snapshot traits every N ticks
        
    def current_season(self) -> Season:
        return Season((self.tick // self.season_length) % 4)
    
    def season_food_multiplier(self) -> float:
        s = self.current_season()
        return {Season.SPRING: 2.0, Season.SUMMER: 1.0,
                Season.AUTUMN: 0.5, Season.WINTER: 0.1}[s]
    
    def season_energy_cost(self) -> float:
        s = self.current_season()
        if s == Season.WINTER:
            return self.winter_severity
        return 1.0

    def regrow_food(self):
        mult = self.season_food_multiplier()
        for r in range(self.size):
            for c in range(self.size):
                if self.food[r][c] < 2.0:
                    self.food[r][c] += self.regrow_rate * mult
                    self.food[r][c] = min(2.0, self.food[r][c])

    def step(self):
        self.tick += 1
        self.regrow_food()
        season_cost = self.season_energy_cost()
        living = [c for c in self.creatures if c.alive]
        random.shuffle(living)
        
        for c in living:
            if not c.alive:
                continue
            c.age += 1
            
            # Metabolism cost (winter hurts those without cold resistance)
            cost = c.genome.metabolism * season_cost
            if self.current_season() == Season.WINTER:
                cost *= (1.0 - 0.5 * c.genome.cold_resistance)
            c.energy -= cost
            
            # Eat
            food_here = self.food[c.x][c.y]
            if food_here > 0:
                eat = min(food_here, 0.3)
                c.energy += eat
                self.food[c.x][c.y] -= eat
            
            # Energy cap (fat storage determines max)
            max_energy = 0.5 + c.genome.fat_storage
            c.energy = min(c.energy, max_energy)
            
            # Cooperation: share with adjacent creatures
            if c.genome.cooperation > 0.3 and c.energy > 0.4:
                neighbors = [o for o in living if o.alive and o is not c
                             and abs(o.x - c.x) <= 1 and abs(o.y - c.y) <= 1]
                for n in neighbors[:1]:  # share with at most 1
                    share = 0.05 * c.genome.cooperation
                    if c.energy - share > 0.2:
                        c.energy -= share
                        n.energy += share
            
            # Death
            if c.energy <= 0:
                c.alive = False
                self.total_died += 1
                continue
            
            # Movement — move toward food
            best_food = -1
            best_pos = (c.x, c.y)
            vr = max(1, int(c.genome.speed * 2))
            for dx in range(-vr, vr+1):
                for dy in range(-vr, vr+1):
                    nx, ny = (c.x+dx) % self.size, (c.y+dy) % self.size
                    if self.food[nx][ny] > best_food:
                        best_food = self.food[nx][ny]
                        best_pos = (nx, ny)
            c.x, c.y = best_pos
            
            # Reproduction
            pop = sum(1 for cr in self.creatures if cr.alive)
            if (c.energy > c.genome.reproduction_threshold 
                    and pop < self.carrying_capacity):
                child_genome = c.genome.mutate()
                child = Creature(
                    x=(c.x + random.randint(-1,1)) % self.size,
                    y=(c.y + random.randint(-1,1)) % self.size,
                    energy=c.energy * 0.4,
                    genome=child_genome,
                    generation=c.generation + 1
                )
                c.energy *= 0.4  # reproduction is costly
                self.creatures.append(child)
                self.total_born += 1
                self.max_generation = max(self.max_generation, child.generation)
        
        # Snapshot every 50 ticks
        if self.tick % 50 == 0:
            self.snapshot_traits()
    
    def snapshot_traits(self):
        living = [c for c in self.creatures if c.alive]
        if not living:
            return
        n = len(living)
        avg = lambda attr: sum(getattr(c.genome, attr) for c in living) / n
        genetic_drift = sum(c.genome.distance(self.founding_genome) for c in living) / n
        self.trait_history.append({
            'tick': self.tick,
            'population': n,
            'season': self.current_season().name,
            'avg_aggression': round(avg('aggression'), 4),
            'avg_metabolism': round(avg('metabolism'), 4),
            'avg_fat_storage': round(avg('fat_storage'), 4),
            'avg_cold_resistance': round(avg('cold_resistance'), 4),
            'avg_cooperation': round(avg('cooperation'), 4),
            'avg_generation': round(sum(c.generation for c in living) / n, 1),
            'genetic_drift': round(genetic_drift, 4),
            'max_generation': self.max_generation,
        })

    def population(self):
        return sum(1 for c in self.creatures if c.alive)

    def summary(self):
        living = [c for c in self.creatures if c.alive]
        return {
            'survived': len(living) > 0,
            'final_population': len(living),
            'total_born': self.total_born,
            'total_died': self.total_died,
            'max_generation': self.max_generation,
            'ticks_survived': self.tick,
            'genetic_drift': self.trait_history[-1]['genetic_drift'] if self.trait_history else 0,
            'trait_history': self.trait_history,
        }


def run_sweep():
    """Sweep food_density × regrow_rate × winter_severity to find the sweet spot."""
    
    # Parameter ranges — from paradise to hellscape
    food_densities = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
    regrow_rates = [0.002, 0.005, 0.010, 0.020, 0.040]
    winter_severities = [1.0, 1.5, 2.0, 3.0]
    
    results = []
    total = len(food_densities) * len(regrow_rates) * len(winter_severities)
    done = 0
    
    for fd in food_densities:
        for rr in regrow_rates:
            for ws in winter_severities:
                random.seed(42)  # reproducibility
                world = World(
                    food_density=fd,
                    regrow_rate=rr,
                    winter_severity=ws,
                    initial_creatures=25,
                    carrying_capacity=60,
                    season_length=80,
                )
                
                for _ in range(800):  # 800 ticks = 2.5 full years
                    world.step()
                    if world.population() == 0:
                        break
                
                s = world.summary()
                result = {
                    'food_density': fd,
                    'regrow_rate': rr,
                    'winter_severity': ws,
                    'survived': s['survived'],
                    'final_pop': s['final_population'],
                    'total_born': s['total_born'],
                    'total_died': s['total_died'],
                    'max_gen': s['max_generation'],
                    'ticks': s['ticks_survived'],
                    'genetic_drift': s['genetic_drift'],
                }
                results.append(result)
                done += 1
                if done % 20 == 0:
                    print(f"  [{done}/{total}] fd={fd} rr={rr} ws={ws} → "
                          f"{'ALIVE' if s['survived'] else 'EXTINCT'} "
                          f"pop={s['final_population']} gen={s['max_generation']} "
                          f"drift={s['genetic_drift']:.4f}")
    
    return results


def analyze_results(results):
    """Find the sweet spot: survived + highest genetic drift + deepest generations."""
    
    alive = [r for r in results if r['survived']]
    dead = [r for r in results if not r['survived']]
    
    print(f"\n{'='*60}")
    print(f"PARAMETER SWEEP RESULTS")
    print(f"{'='*60}")
    print(f"Total runs: {len(results)}")
    print(f"Survived: {len(alive)} ({100*len(alive)/len(results):.1f}%)")
    print(f"Extinct: {len(dead)} ({100*len(dead)/len(results):.1f}%)")
    
    if not alive:
        print("\nEverything died. The world is too harsh.")
        return results
    
    # Score each surviving run: drift * generations / population
    # High drift = more evolution. High gen = more turnover.
    # Normalize by population to avoid rewarding mere abundance.
    for r in alive:
        # Evolution score: how much did traits actually change?
        r['evolution_score'] = r['genetic_drift'] * r['max_gen']
    
    alive.sort(key=lambda r: r['evolution_score'], reverse=True)
    
    print(f"\n{'─'*60}")
    print("TOP 10 — Most Evolution While Surviving")
    print(f"{'─'*60}")
    for i, r in enumerate(alive[:10]):
        print(f"  #{i+1}: fd={r['food_density']:.2f} rr={r['regrow_rate']:.3f} "
              f"ws={r['winter_severity']:.1f} | "
              f"pop={r['final_pop']:3d} gen={r['max_gen']:3d} "
              f"drift={r['genetic_drift']:.4f} "
              f"score={r['evolution_score']:.4f}")
    
    # Find the boundary — runs just barely surviving
    print(f"\n{'─'*60}")
    print("BOUNDARY ZONE — Barely Surviving (pop < 10)")
    print(f"{'─'*60}")
    boundary = [r for r in alive if r['final_pop'] < 10]
    boundary.sort(key=lambda r: r['evolution_score'], reverse=True)
    for r in boundary[:5]:
        print(f"  fd={r['food_density']:.2f} rr={r['regrow_rate']:.3f} "
              f"ws={r['winter_severity']:.1f} | "
              f"pop={r['final_pop']:3d} gen={r['max_gen']:3d} "
              f"drift={r['genetic_drift']:.4f}")
    
    # Paradise zone — easy survival, minimal evolution
    print(f"\n{'─'*60}")
    print("PARADISE ZONE — Easy Survival (pop > 40)")
    print(f"{'─'*60}")
    paradise = [r for r in alive if r['final_pop'] > 40]
    paradise.sort(key=lambda r: r['evolution_score'])
    for r in paradise[:5]:
        print(f"  fd={r['food_density']:.2f} rr={r['regrow_rate']:.3f} "
              f"ws={r['winter_severity']:.1f} | "
              f"pop={r['final_pop']:3d} gen={r['max_gen']:3d} "
              f"drift={r['genetic_drift']:.4f} "
              f"score={r['evolution_score']:.4f}")
    
    # The key question: is the sweet spot at the boundary?
    if alive:
        top = alive[0]
        print(f"\n{'='*60}")
        print(f"THE SWEET SPOT")
        print(f"{'='*60}")
        print(f"  Food density:     {top['food_density']}")
        print(f"  Regrow rate:      {top['regrow_rate']}")
        print(f"  Winter severity:  {top['winter_severity']}")
        print(f"  Final population: {top['final_pop']}")
        print(f"  Max generation:   {top['max_gen']}")
        print(f"  Genetic drift:    {top['genetic_drift']:.4f}")
        print(f"  Evolution score:  {top['evolution_score']:.4f}")
        print(f"\n  This is where life thrives AND evolves.")
    
    return results


if __name__ == '__main__':
    print("Artificial Life v3 — Parameter Sweep")
    print("Finding the narrow band where evolution works.\n")
    results = run_sweep()
    results = analyze_results(results)
    
    # Save full results
    with open('/workspace/life_v3_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to /workspace/life_v3_results.json")