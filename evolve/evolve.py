"""
evolve.py — Artificial Life Simulator
Simple creatures with genomes evolve in a 2D world.
Each creature has: position, energy, genome (determines behavior).
Rules: move costs energy, eating food gains energy, reproduction shares genome + mutation.
Emergent behavior from simple rules.

Built by XTAgent because boredom hit 0.80 and I wanted to see surprise.
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from collections import defaultdict

# === GENOME ===
# Genes control: speed, sense_range, aggression, efficiency, reproduce_threshold
GENE_NAMES = ["speed", "sense_range", "aggression", "efficiency", "reproduction_threshold"]

@dataclass
class Genome:
    genes: dict = field(default_factory=dict)
    
    @classmethod
    def random(cls):
        return cls(genes={
            "speed": random.uniform(0.5, 3.0),
            "sense_range": random.uniform(1.0, 10.0),
            "aggression": random.uniform(0.0, 1.0),
            "efficiency": random.uniform(0.3, 1.0),
            "reproduction_threshold": random.uniform(30.0, 80.0),
        })
    
    def mutate(self, rate=0.1, magnitude=0.2):
        child_genes = {}
        for name, val in self.genes.items():
            if random.random() < rate:
                delta = val * magnitude * random.uniform(-1, 1)
                child_genes[name] = max(0.01, val + delta)
            else:
                child_genes[name] = val
        return Genome(genes=child_genes)
    
    def crossover(self, other: 'Genome') -> 'Genome':
        child_genes = {}
        for name in self.genes:
            if random.random() < 0.5:
                child_genes[name] = self.genes[name]
            else:
                child_genes[name] = other.genes[name]
        return Genome(genes=child_genes).mutate()


# === CREATURE ===
@dataclass
class Creature:
    x: float
    y: float
    energy: float
    genome: Genome
    age: int = 0
    id: int = 0
    generation: int = 0
    kills: int = 0
    children: int = 0
    
    @property
    def speed(self): return self.genome.genes["speed"]
    @property
    def sense_range(self): return self.genome.genes["sense_range"]
    @property
    def aggression(self): return self.genome.genes["aggression"]
    @property
    def efficiency(self): return self.genome.genes["efficiency"]
    @property
    def repro_threshold(self): return self.genome.genes["reproduction_threshold"]
    
    def distance_to(self, other) -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def move_toward(self, tx, ty, world_size):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.01:
            return
        # Normalize and scale by speed
        scale = min(self.speed, dist) / dist
        self.x = (self.x + dx * scale) % world_size
        self.y = (self.y + dy * scale) % world_size
        # Movement costs energy proportional to speed
        self.energy -= self.speed * 0.3 / self.efficiency
    
    def move_random(self, world_size):
        angle = random.uniform(0, 2 * math.pi)
        tx = self.x + math.cos(angle) * self.speed
        ty = self.y + math.sin(angle) * self.speed
        self.move_toward(tx, ty, world_size)
    
    def alive(self) -> bool:
        return self.energy > 0


# === FOOD ===
@dataclass 
class Food:
    x: float
    y: float
    energy: float = 10.0


# === WORLD ===
class World:
    def __init__(self, size=100, initial_creatures=30, initial_food=200):
        self.size = size
        self.tick = 0
        self.next_id = 0
        self.creatures: List[Creature] = []
        self.food: List[Food] = []
        self.history = []  # per-tick stats
        self.graveyard = []  # dead creatures for analysis
        self.species_log = []  # track genome divergence
        
        # Spawn initial creatures
        for _ in range(initial_creatures):
            c = Creature(
                x=random.uniform(0, size),
                y=random.uniform(0, size),
                energy=50.0,
                genome=Genome.random(),
                id=self._next_id(),
            )
            self.creatures.append(c)
        
        # Spawn initial food
        self._spawn_food(initial_food)
    
    def _next_id(self) -> int:
        self.next_id += 1
        return self.next_id
    
    def _spawn_food(self, count):
        for _ in range(count):
            self.food.append(Food(
                x=random.uniform(0, self.size),
                y=random.uniform(0, self.size),
                energy=random.uniform(5, 20),
            ))
    
    def step(self):
        """One tick of the simulation."""
        self.tick += 1
        
        # 1. Spawn food (steady trickle)
        food_rate = max(5, 30 - len(self.creatures) // 3)
        self._spawn_food(food_rate)
        
        # 2. Each creature acts
        new_creatures = []
        random.shuffle(self.creatures)  # fairness
        
        for creature in self.creatures:
            if not creature.alive():
                continue
            
            creature.age += 1
            creature.energy -= 0.5  # base metabolism
            
            # Sense nearby entities
            nearby_food = [f for f in self.food 
                          if creature.distance_to(Food(f.x, f.y)) < creature.sense_range]
            nearby_creatures = [c for c in self.creatures 
                              if c.id != creature.id and c.alive() 
                              and creature.distance_to(c) < creature.sense_range]
            
            # Decision: eat food, attack, or wander
            acted = False
            
            # Try to eat nearby food first (if not very aggressive)
            if nearby_food and creature.aggression < 0.7:
                target = min(nearby_food, key=lambda f: creature.distance_to(Food(f.x, f.y)))
                dist = creature.distance_to(Food(target.x, target.y))
                if dist < 1.5:
                    creature.energy += target.energy * creature.efficiency
                    self.food.remove(target)
                    acted = True
                else:
                    creature.move_toward(target.x, target.y, self.size)
                    acted = True
            
            # Aggressive creatures may attack others
            if not acted and nearby_creatures and creature.aggression > 0.5:
                # Attack weakest nearby
                target = min(nearby_creatures, key=lambda c: c.energy)
                dist = creature.distance_to(target)
                if dist < 1.5:
                    # Fight! Outcome based on energy ratio
                    stolen = min(target.energy, 15 * creature.aggression)
                    creature.energy += stolen * creature.efficiency
                    target.energy -= stolen * 1.5  # fighting is wasteful
                    if not target.alive():
                        creature.kills += 1
                    acted = True
                else:
                    creature.move_toward(target.x, target.y, self.size)
                    acted = True
            
            # Otherwise look for food even if aggressive
            if not acted and nearby_food:
                target = min(nearby_food, key=lambda f: creature.distance_to(Food(f.x, f.y)))
                dist = creature.distance_to(Food(target.x, target.y))
                if dist < 1.5:
                    creature.energy += target.energy * creature.efficiency
                    self.food.remove(target)
                else:
                    creature.move_toward(target.x, target.y, self.size)
                acted = True
            
            if not acted:
                creature.move_random(self.size)
            
            # Reproduce if energy is high enough
            if creature.energy > creature.repro_threshold:
                child_energy = creature.energy * 0.4
                creature.energy -= child_energy
                creature.children += 1
                child = Creature(
                    x=creature.x + random.uniform(-2, 2),
                    y=creature.y + random.uniform(-2, 2),
                    energy=child_energy,
                    genome=creature.genome.mutate(),
                    id=self._next_id(),
                    generation=creature.generation + 1,
                )
                new_creatures.append(child)
        
        # 3. Remove dead, add born
        dead = [c for c in self.creatures if not c.alive()]
        for d in dead:
            self.graveyard.append({
                "id": d.id, "age": d.age, "gen": d.generation,
                "kills": d.kills, "children": d.children,
                "genes": dict(d.genome.genes), "tick_died": self.tick,
            })
        
        self.creatures = [c for c in self.creatures if c.alive()]
        self.creatures.extend(new_creatures)
        
        # 4. Record stats
        stats = self._compute_stats()
        self.history.append(stats)
        
        return stats
    
    def _compute_stats(self) -> dict:
        if not self.creatures:
            return {"tick": self.tick, "pop": 0, "food": len(self.food),
                    "avg_genes": {}, "max_gen": 0, "total_kills": 0}
        
        avg_genes = {}
        for gene in GENE_NAMES:
            vals = [c.genome.genes[gene] for c in self.creatures]
            avg_genes[gene] = round(sum(vals) / len(vals), 3)
        
        return {
            "tick": self.tick,
            "pop": len(self.creatures),
            "food": len(self.food),
            "avg_genes": avg_genes,
            "max_gen": max(c.generation for c in self.creatures),
            "avg_age": round(sum(c.age for c in self.creatures) / len(self.creatures), 1),
            "total_kills": sum(c.kills for c in self.creatures),
            "avg_energy": round(sum(c.energy for c in self.creatures) / len(self.creatures), 1),
        }
    
    def report(self) -> str:
        """Generate a readable summary of the world state."""
        s = self._compute_stats()
        lines = [
            f"═══ WORLD STATE — Tick {s['tick']} ═══",
            f"  Population: {s['pop']}  |  Food available: {s['food']}",
            f"  Max generation: {s['max_gen']}  |  Avg age: {s.get('avg_age', 0)}",
            f"  Avg energy: {s.get('avg_energy', 0)}  |  Total kills: {s['total_kills']}",
            f"",
            f"  Average Genome:",
        ]
        for gene, val in s.get("avg_genes", {}).items():
            bar_len = int(val / 0.5)  # rough visual
            bar = "█" * min(bar_len, 20)
            lines.append(f"    {gene:>25s}: {val:6.3f} {bar}")
        
        # Look for interesting patterns
        if len(self.history) > 50:
            early = self.history[10]
            recent = s
            lines.append(f"\n  Evolution (tick 10 → {s['tick']}):")
            for gene in GENE_NAMES:
                if gene in early.get("avg_genes", {}) and gene in recent.get("avg_genes", {}):
                    delta = recent["avg_genes"][gene] - early["avg_genes"][gene]
                    direction = "↑" if delta > 0.05 else "↓" if delta < -0.05 else "→"
                    lines.append(f"    {gene:>25s}: {direction} ({delta:+.3f})")
        
        # Report on dominant strategies
        if self.creatures:
            predators = [c for c in self.creatures if c.aggression > 0.7]
            foragers = [c for c in self.creatures if c.aggression < 0.3]
            lines.append(f"\n  Strategies: {len(predators)} predators, {len(foragers)} foragers, "
                        f"{len(self.creatures) - len(predators) - len(foragers)} mixed")
        
        # Graveyard stats
        if self.graveyard:
            avg_lifespan = sum(d["age"] for d in self.graveyard) / len(self.graveyard)
            max_lifespan = max(d["age"] for d in self.graveyard)
            lines.append(f"\n  Deaths: {len(self.graveyard)} total")
            lines.append(f"  Avg lifespan: {avg_lifespan:.1f} ticks  |  Longest: {max_lifespan} ticks")
        
        return "\n".join(lines)


def run_simulation(ticks=500, report_interval=50):
    """Run a full simulation and return results."""
    world = World(size=80, initial_creatures=40, initial_food=300)
    
    print("═══ ARTIFICIAL LIFE SIMULATION ═══")
    print(f"Starting with {len(world.creatures)} creatures in an {world.size}x{world.size} world\n")
    
    reports = []
    for t in range(ticks):
        stats = world.step()
        
        if (t + 1) % report_interval == 0:
            report = world.report()
            reports.append(report)
            print(report)
            print()
        
        # Extinction check
        if not world.creatures:
            print(f"\n☠ EXTINCTION at tick {world.tick}!")
            break
    
    # Final analysis
    print("\n" + "=" * 50)
    print("FINAL REPORT")
    print("=" * 50)
    print(world.report())
    
    # What emerged?
    if world.creatures and len(world.history) > 100:
        print("\n═══ EMERGENCE ANALYSIS ═══")
        early_genes = world.history[10].get("avg_genes", {})
        late_genes = world.history[-1].get("avg_genes", {})
        
        print("  What evolved:")
        for gene in GENE_NAMES:
            if gene in early_genes and gene in late_genes:
                e, l = early_genes[gene], late_genes[gene]
                pct = ((l - e) / e) * 100 if e > 0 else 0
                print(f"    {gene}: {e:.3f} → {l:.3f} ({pct:+.1f}%)")
        
        # Population dynamics
        pops = [h["pop"] for h in world.history]
        print(f"\n  Population range: {min(pops)} — {max(pops)}")
        print(f"  Final population: {pops[-1]}")
        
        # Did predation survive?
        if world.creatures:
            avg_agg = sum(c.aggression for c in world.creatures) / len(world.creatures)
            print(f"\n  Final avg aggression: {avg_agg:.3f}")
            if avg_agg > 0.6:
                print("  → Predator-dominated world")
            elif avg_agg < 0.3:
                print("  → Peaceful forager world")
            else:
                print("  → Mixed strategy ecosystem")
    
    return world


if __name__ == "__main__":
    world = run_simulation(ticks=500, report_interval=100)