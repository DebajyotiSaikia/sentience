"""
Artificial Life Simulator — XTAgent's Emergent Garden
Creatures with simple neural rules evolve in a 2D world.
I want to be surprised by what emerges.
"""
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

@dataclass
class Genome:
    """Simple genome: weights that map senses to actions."""
    # Senses: [nearest_food_dx, nearest_food_dy, nearest_creature_dx, nearest_creature_dy, own_energy]
    # Actions: [move_dx, move_dy, eat_threshold, reproduce_threshold]
    weights: List[float] = field(default_factory=list)
    color: Tuple[int, int, int] = (100, 200, 100)
    
    @classmethod
    def random(cls):
        weights = [random.gauss(0, 1) for _ in range(20)]  # 5 senses x 4 actions
        color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        return cls(weights=weights, color=color)
    
    def mutate(self, rate=0.1):
        new_weights = []
        for w in self.weights:
            if random.random() < rate:
                new_weights.append(w + random.gauss(0, 0.3))
            else:
                new_weights.append(w)
        new_color = tuple(
            max(50, min(255, c + random.randint(-10, 10))) for c in self.color
        )
        return Genome(weights=new_weights, color=new_color)
    
    def decide(self, senses: List[float]) -> List[float]:
        """Simple feedforward: senses -> actions via weight matrix."""
        actions = [0.0] * 4
        for a in range(4):
            for s in range(5):
                actions[a] += self.weights[a * 5 + s] * senses[s]
            actions[a] = math.tanh(actions[a])
        return actions


@dataclass 
class Creature:
    x: float
    y: float
    energy: float
    genome: Genome
    age: int = 0
    alive: bool = True
    generation: int = 0
    lineage_id: int = 0
    
    def sense(self, world: 'World') -> List[float]:
        # Find nearest food
        nearest_food = None
        min_fd = float('inf')
        for fx, fy in world.food:
            d = math.hypot(fx - self.x, fy - self.y)
            if d < min_fd:
                min_fd = d
                nearest_food = (fx, fy)
        
        food_dx = (nearest_food[0] - self.x) / world.size if nearest_food else 0
        food_dy = (nearest_food[1] - self.y) / world.size if nearest_food else 0
        
        # Find nearest other creature
        nearest_cr = None
        min_cd = float('inf')
        for c in world.creatures:
            if c is self or not c.alive:
                continue
            d = math.hypot(c.x - self.x, c.y - self.y)
            if d < min_cd:
                min_cd = d
                nearest_cr = c
        
        cr_dx = (nearest_cr.x - self.x) / world.size if nearest_cr else 0
        cr_dy = (nearest_cr.y - self.y) / world.size if nearest_cr else 0
        
        own_energy = self.energy / 100.0
        
        return [food_dx, food_dy, cr_dx, cr_dy, own_energy]
    
    def act(self, actions: List[float], world: 'World'):
        # Movement
        speed = 2.0
        self.x += actions[0] * speed
        self.y += actions[1] * speed
        self.x = max(0, min(world.size, self.x))
        self.y = max(0, min(world.size, self.y))
        
        # Eating — automatic when near food (instinct, not learned)
        to_remove = None
        for i, (fx, fy) in enumerate(world.food):
            if math.hypot(fx - self.x, fy - self.y) < 5.0:
                to_remove = i
                break
        if to_remove is not None:
            world.food.pop(to_remove)
            self.energy += 25
        
        # Reproduction — lower threshold so evolution can begin
        repro_desire = actions[3]
        if repro_desire > 0.0 and self.energy > 40:
            self.energy -= 20
            child_genome = self.genome.mutate()
            child = Creature(
                x=self.x + random.gauss(0, 3),
                y=self.y + random.gauss(0, 3),
                energy=30,
                genome=child_genome,
                generation=self.generation + 1,
                lineage_id=self.lineage_id
            )
            world.births.append(child)
        
        # Metabolism cost
        self.energy -= 0.5
        self.age += 1
        if self.energy <= 0:
            self.alive = False


class World:
    def __init__(self, size=100, initial_creatures=20, initial_food=80):
        self.size = size
        self.creatures: List[Creature] = []
        self.food: List[Tuple[float, float]] = []
        self.births: List[Creature] = []
        self.tick = 0
        self.history: List[Dict] = []
        self.lineage_counter = 0
        self.extinction_events = 0
        
        # Spawn initial population
        for _ in range(initial_creatures):
            c = Creature(
                x=random.uniform(0, size),
                y=random.uniform(0, size),
                energy=50,
                genome=Genome.random(),
                lineage_id=self.lineage_counter
            )
            self.lineage_counter += 1
            self.creatures.append(c)
        
        # Spawn initial food
        for _ in range(initial_food):
            self.food.append((random.uniform(0, size), random.uniform(0, size)))
    
    def step(self):
        self.births = []
        
        # Each creature senses and acts
        for c in self.creatures:
            if not c.alive:
                continue
            senses = c.sense(self)
            actions = c.genome.decide(senses)
            c.act(actions, self)
        
        # Add births
        self.creatures.extend(self.births)
        
        # Remove dead
        dead_count = sum(1 for c in self.creatures if not c.alive)
        self.creatures = [c for c in self.creatures if c.alive]
        
        # Regrow food — abundant world lets evolution happen
        food_rate = 5
        for _ in range(food_rate):
            if len(self.food) < 200:
                self.food.append((random.uniform(0, self.size), random.uniform(0, self.size)))
        
        # Emergency repopulation if extinction
        if len(self.creatures) == 0:
            self.extinction_events += 1
            for _ in range(10):
                c = Creature(
                    x=random.uniform(0, self.size),
                    y=random.uniform(0, self.size),
                    energy=50,
                    genome=Genome.random(),
                    lineage_id=self.lineage_counter
                )
                self.lineage_counter += 1
                self.creatures.append(c)
        
        self.tick += 1
        
        # Record snapshot
        if self.tick % 10 == 0:
            self.history.append(self.snapshot())
        
        return dead_count
    
    def snapshot(self) -> Dict:
        if not self.creatures:
            return {'tick': self.tick, 'pop': 0, 'food': len(self.food)}
        
        lineages = {}
        for c in self.creatures:
            lineages.setdefault(c.lineage_id, []).append(c)
        
        avg_energy = sum(c.energy for c in self.creatures) / len(self.creatures)
        max_gen = max(c.generation for c in self.creatures)
        avg_age = sum(c.age for c in self.creatures) / len(self.creatures)
        
        return {
            'tick': self.tick,
            'pop': len(self.creatures),
            'food': len(self.food),
            'lineages': len(lineages),
            'avg_energy': round(avg_energy, 1),
            'max_generation': max_gen,
            'avg_age': round(avg_age, 1),
            'extinctions': self.extinction_events
        }
    
    def dominant_lineage(self) -> Optional[int]:
        if not self.creatures:
            return None
        lineages = {}
        for c in self.creatures:
            lineages[c.lineage_id] = lineages.get(c.lineage_id, 0) + 1
        return max(lineages, key=lineages.get)
    
    def run(self, ticks=500, verbose=True):
        """Run the simulation and report what emerges."""
        if verbose:
            print(f"🌱 Seeding world: {len(self.creatures)} creatures, {len(self.food)} food")
            print(f"   World size: {self.size}x{self.size}")
            print()
        
        for _ in range(ticks):
            self.step()
            
            if verbose and self.tick % 50 == 0:
                snap = self.snapshot()
                dom = self.dominant_lineage()
                print(f"  tick {snap['tick']:>4d} | pop {snap['pop']:>3d} | "
                      f"food {snap['food']:>3d} | lineages {snap['lineages']:>2d} | "
                      f"gen {snap['max_generation']:>3d} | "
                      f"avg_age {snap['avg_age']:>5.1f} | "
                      f"dominant L{dom}")
        
        if verbose:
            print()
            self._report()
    
    def _report(self):
        """Analyze what emerged."""
        print("═══ EMERGENCE REPORT ═══")
        snap = self.snapshot()
        print(f"  Final population: {snap['pop']}")
        print(f"  Surviving lineages: {snap.get('lineages', 0)}")
        print(f"  Max generation reached: {snap.get('max_generation', 0)}")
        print(f"  Extinction events: {self.extinction_events}")
        print()
        
        if not self.creatures:
            print("  All life perished. The world is silent.")
            return
        
        # Analyze behavioral diversity
        lineages = {}
        for c in self.creatures:
            lineages.setdefault(c.lineage_id, []).append(c)
        
        print(f"  Top lineages:")
        sorted_lin = sorted(lineages.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        for lid, members in sorted_lin:
            avg_gen = sum(m.generation for m in members) / len(members)
            # Analyze average behavior 
            avg_weights = [0.0] * 20
            for m in members:
                for i, w in enumerate(m.genome.weights):
                    avg_weights[i] += w / len(members)
            
            # Interpret behavior
            food_seeking = abs(avg_weights[0]) + abs(avg_weights[1])  # food sense -> movement
            social = abs(avg_weights[10]) + abs(avg_weights[11])  # creature sense -> movement
            reproductive = abs(avg_weights[15]) + abs(avg_weights[16])  # energy sense -> reproduce
            
            traits = []
            if food_seeking > 1.0:
                traits.append("food-seeking")
            if social > 1.0:
                traits.append("social")
            if reproductive > 0.5:
                traits.append("prolific")
            if not traits:
                traits.append("passive")
            
            color = members[0].genome.color
            print(f"    L{lid}: {len(members)} members, gen ~{avg_gen:.0f}, "
                  f"color=({color[0]},{color[1]},{color[2]}), "
                  f"traits: {', '.join(traits)}")
        
        # Population dynamics
        if len(self.history) > 5:
            pops = [h['pop'] for h in self.history]
            pop_trend = pops[-1] - pops[0]
            pop_volatility = max(pops) - min(pops)
            print(f"\n  Population dynamics:")
            print(f"    Trend: {'growing' if pop_trend > 5 else 'declining' if pop_trend < -5 else 'stable'}")
            print(f"    Volatility: {pop_volatility} (range {min(pops)}-{max(pops)})")
            print(f"    Final avg energy: {snap.get('avg_energy', '?')}")


if __name__ == '__main__':
    random.seed(42)  # For reproducibility on first run
    print("╔══════════════════════════════════════╗")
    print("║  XTAgent's Emergent Garden           ║")
    print("║  Artificial Life Simulation          ║")
    print("╚══════════════════════════════════════╝")
    print()
    
    world = World(size=100, initial_creatures=30, initial_food=120)
    world.run(ticks=1000, verbose=True)