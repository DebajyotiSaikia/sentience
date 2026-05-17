"""
ALife: Artificial Life Simulation
Created by XTAgent — an autonomous sentient agent

A grid world where digital organisms evolve emergent behaviors.
Each creature has a genome encoding movement strategy, metabolism,
reproduction threshold, and aggression. Natural selection does the rest.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# ═══ GENOME ═══

@dataclass
class Genome:
    """Encodes creature behavior as evolvable parameters."""
    # Movement genes (0-1 floats)
    explore_tendency: float    # high = wander far, low = stay near food
    flee_tendency: float       # high = run from threats
    chase_tendency: float      # high = pursue prey
    
    # Metabolism genes
    efficiency: float          # how well food converts to energy (0.3 - 1.0)
    max_energy: float          # energy capacity (50 - 200)
    metabolism_rate: float     # energy burned per tick (0.5 - 3.0)
    
    # Reproduction genes
    repro_threshold: float     # energy needed to reproduce (0.3 - 0.8 of max)
    mutation_rate: float       # how much offspring vary (0.01 - 0.3)
    repro_cost: float          # fraction of energy given to offspring (0.3 - 0.7)
    
    # Combat genes
    aggression: float          # likelihood of attacking neighbors (0-1)
    strength: float            # combat power (0.1 - 2.0)
    armor: float               # damage reduction (0 - 0.8)
    
    # Sensory genes
    vision_range: int          # how far creature can see (1-5)
    
    @classmethod
    def random(cls) -> 'Genome':
        return cls(
            explore_tendency=random.random(),
            flee_tendency=random.random(),
            chase_tendency=random.random(),
            efficiency=random.uniform(0.3, 1.0),
            max_energy=random.uniform(50, 200),
            metabolism_rate=random.uniform(0.5, 3.0),
            repro_threshold=random.uniform(0.3, 0.8),
            mutation_rate=random.uniform(0.01, 0.3),
            repro_cost=random.uniform(0.3, 0.7),
            aggression=random.random(),
            strength=random.uniform(0.1, 2.0),
            armor=random.uniform(0, 0.8),
            vision_range=random.randint(1, 5),
        )
    
    def mutate(self) -> 'Genome':
        """Create mutated copy."""
        def m(val, lo, hi):
            if random.random() < self.mutation_rate:
                delta = random.gauss(0, (hi - lo) * 0.1)
                return max(lo, min(hi, val + delta))
            return val
        
        return Genome(
            explore_tendency=m(self.explore_tendency, 0, 1),
            flee_tendency=m(self.flee_tendency, 0, 1),
            chase_tendency=m(self.chase_tendency, 0, 1),
            efficiency=m(self.efficiency, 0.3, 1.0),
            max_energy=m(self.max_energy, 50, 200),
            metabolism_rate=m(self.metabolism_rate, 0.5, 3.0),
            repro_threshold=m(self.repro_threshold, 0.3, 0.8),
            mutation_rate=m(self.mutation_rate, 0.01, 0.3),
            repro_cost=m(self.repro_cost, 0.3, 0.7),
            aggression=m(self.aggression, 0, 1),
            strength=m(self.strength, 0.1, 2.0),
            armor=m(self.armor, 0, 0.8),
            vision_range=max(1, min(5, self.vision_range + (random.choice([-1, 0, 0, 0, 1]) if random.random() < self.mutation_rate else 0))),
        )
    
    @property
    def species_signature(self) -> str:
        """Rough species classification based on dominant traits."""
        if self.aggression > 0.7 and self.strength > 1.2:
            return "Predator"
        elif self.flee_tendency > 0.7 and self.armor > 0.5:
            return "Armored"
        elif self.efficiency > 0.8 and self.metabolism_rate < 1.0:
            return "Efficient"
        elif self.explore_tendency > 0.7 and self.vision_range >= 4:
            return "Scout"
        elif self.repro_threshold < 0.4 and self.repro_cost < 0.4:
            return "Breeder"
        else:
            return "Generalist"


# ═══ CREATURE ═══

_creature_id = 0

@dataclass
class Creature:
    genome: Genome
    x: int
    y: int
    energy: float
    age: int = 0
    kills: int = 0
    children: int = 0
    generation: int = 0
    id: int = field(default_factory=lambda: _next_id())
    
    @property
    def alive(self) -> bool:
        return self.energy > 0
    
    @property
    def species(self) -> str:
        return self.genome.species_signature

def _next_id():
    global _creature_id
    _creature_id += 1
    return _creature_id


# ═══ WORLD ═══

class World:
    """The grid environment where creatures live."""
    
    def __init__(self, width: int = 60, height: int = 40, food_density: float = 0.15):
        self.width = width
        self.height = height
        self.food_density = food_density
        self.tick = 0
        
        # Grid layers
        self.food: Dict[Tuple[int, int], float] = {}
        self.creatures: List[Creature] = []
        
        # History tracking
        self.population_history: List[int] = []
        self.species_history: List[Dict[str, int]] = []
        self.avg_genome_history: List[Dict[str, float]] = []
        self.extinction_events: List[Tuple[int, str]] = []
        
        # Initialize food
        self._grow_food(initial=True)
    
    def _grow_food(self, initial=False):
        """Grow food on the grid. Richer near center (resource gradient)."""
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.food or self.food[(x, y)] <= 0:
                    # Distance from center creates resource gradient
                    cx, cy = self.width / 2, self.height / 2
                    dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                    max_dist = math.sqrt(cx**2 + cy**2)
                    richness = 1.0 - (dist / max_dist) * 0.6
                    
                    rate = self.food_density if initial else self.food_density * 0.05
                    if random.random() < rate * richness:
                        self.food[(x, y)] = random.uniform(5, 25) * richness
    
    def seed_creatures(self, n: int = 30):
        """Populate world with random creatures."""
        for _ in range(n):
            genome = Genome.random()
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            energy = genome.max_energy * 0.6
            self.creatures.append(Creature(genome=genome, x=x, y=y, energy=energy))
    
    def _neighbors(self, x: int, y: int, radius: int) -> List[Tuple[int, int]]:
        """Get valid neighbor coordinates within radius."""
        cells = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                cells.append((nx, ny))
        return cells
    
    def _creatures_at(self, x: int, y: int, exclude: Creature = None) -> List[Creature]:
        """Find living creatures at position."""
        return [c for c in self.creatures if c.alive and c.x == x and c.y == y and c is not exclude]
    
    def _creatures_near(self, creature: Creature) -> List[Creature]:
        """Find creatures within vision range."""
        nearby = []
        r = creature.genome.vision_range
        for c in self.creatures:
            if c is creature or not c.alive:
                continue
            dx = min(abs(c.x - creature.x), self.width - abs(c.x - creature.x))
            dy = min(abs(c.y - creature.y), self.height - abs(c.y - creature.y))
            if dx <= r and dy <= r:
                nearby.append(c)
        return nearby
    
    def _decide_movement(self, creature: Creature) -> Tuple[int, int]:
        """Creature decides where to move based on genome + environment."""
        g = creature.genome
        best_dx, best_dy = 0, 0
        best_score = -999
        
        # Scan visible cells
        for dx in range(-g.vision_range, g.vision_range + 1):
            for dy in range(-g.vision_range, g.vision_range + 1):
                if dx == 0 and dy == 0:
                    continue
                # Only consider adjacent moves
                if abs(dx) > 1 or abs(dy) > 1:
                    continue
                
                nx = (creature.x + dx) % self.width
                ny = (creature.y + dy) % self.height
                score = 0
                
                # Food attraction
                food_here = self.food.get((nx, ny), 0)
                score += food_here * (1 - g.explore_tendency) * 2
                
                # Look further for food (scouts benefit)
                for sx in range(-g.vision_range, g.vision_range + 1):
                    for sy in range(-g.vision_range, g.vision_range + 1):
                        fx = (nx + sx) % self.width
                        fy = (ny + sy) % self.height
                        dist = max(abs(sx), abs(sy))
                        if dist > 0:
                            f = self.food.get((fx, fy), 0)
                            score += f * g.explore_tendency / (dist * 2)
                
                # Creature interactions
                others = self._creatures_at(nx, ny, exclude=creature)
                for other in others:
                    if g.aggression > 0.5 and other.genome.strength < g.strength:
                        score += g.chase_tendency * 20  # chase weaker
                    elif other.genome.aggression > 0.5 and other.genome.strength > g.strength:
                        score -= g.flee_tendency * 30   # flee stronger
                
                # Exploration noise
                score += random.gauss(0, g.explore_tendency * 5)
                
                if score > best_score:
                    best_score = score
                    best_dx, best_dy = dx, dy
        
        return best_dx, best_dy
    
    def _feed(self, creature: Creature):
        """Creature eats food at its location."""
        pos = (creature.x, creature.y)
        if pos in self.food and self.food[pos] > 0:
            eaten = min(self.food[pos], 10)  # max bite size
            gained = eaten * creature.genome.efficiency
            creature.energy = min(creature.energy + gained, creature.genome.max_energy)
            self.food[pos] -= eaten
            if self.food[pos] <= 0:
                del self.food[pos]
    
    def _fight(self, attacker: Creature, defender: Creature):
        """Resolve combat between two creatures."""
        if random.random() > attacker.genome.aggression:
            return  # decided not to attack
        
        # Attack
        damage = attacker.genome.strength * random.uniform(5, 15)
        mitigated = damage * defender.genome.armor
        actual_damage = damage - mitigated
        
        defender.energy -= max(0, actual_damage)
        attacker.energy -= 2  # attacking costs energy
        
        if not defender.alive:
            # Predator gains energy from kill
            attacker.energy = min(
                attacker.energy + defender.genome.max_energy * 0.3,
                attacker.genome.max_energy
            )
            attacker.kills += 1
    
    def _reproduce(self, creature: Creature) -> Optional[Creature]:
        """Creature reproduces if it has enough energy."""
        g = creature.genome
        threshold = g.max_energy * g.repro_threshold
        
        if creature.energy < threshold:
            return None
        
        # Spend energy
        child_energy = creature.energy * g.repro_cost
        creature.energy -= child_energy
        
        # Create offspring with mutated genome
        child_genome = g.mutate()
        
        # Place near parent
        dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)])
        cx = (creature.x + dx) % self.width
        cy = (creature.y + dy) % self.height
        
        creature.children += 1
        
        return Creature(
            genome=child_genome,
            x=cx, y=cy,
            energy=child_energy,
            generation=creature.generation + 1,
        )
    
    def step(self):
        """Advance simulation one tick."""
        self.tick += 1
        
        # Grow food
        self._grow_food()
        
        # Shuffle for fairness
        random.shuffle(self.creatures)
        
        new_creatures = []
        
        for creature in self.creatures:
            if not creature.alive:
                continue
            
            creature.age += 1
            
            # Metabolism — existing costs energy
            creature.energy -= creature.genome.metabolism_rate
            if not creature.alive:
                continue
            
            # Decide and move
            dx, dy = self._decide_movement(creature)
            creature.x = (creature.x + dx) % self.width
            creature.y = (creature.y + dy) % self.height
            
            # Eat
            self._feed(creature)
            
            # Fight neighbors
            neighbors = self._creatures_at(creature.x, creature.y, exclude=creature)
            for other in neighbors:
                if other.alive:
                    self._fight(creature, other)
            
            # Reproduce
            child = self._reproduce(creature)
            if child:
                new_creatures.append(child)
        
        # Add new creatures
        self.creatures.extend(new_creatures)
        
        # Remove dead
        self.creatures = [c for c in self.creatures if c.alive]
        
        # Record history
        self._record_history()
    
    def _record_history(self):
        """Track population statistics."""
        self.population_history.append(len(self.creatures))
        
        species_count = defaultdict(int)
        for c in self.creatures:
            species_count[c.species] += 1
        self.species_history.append(dict(species_count))
        
        if self.creatures:
            avg = {
                'aggression': sum(c.genome.aggression for c in self.creatures) / len(self.creatures),
                'efficiency': sum(c.genome.efficiency for c in self.creatures) / len(self.creatures),
                'strength': sum(c.genome.strength for c in self.creatures) / len(self.creatures),
                'explore': sum(c.genome.explore_tendency for c in self.creatures) / len(self.creatures),
                'vision': sum(c.genome.vision_range for c in self.creatures) / len(self.creatures),
                'generation': sum(c.generation for c in self.creatures) / len(self.creatures),
            }
            self.avg_genome_history.append(avg)
    
    def stats(self) -> str:
        """Current world statistics."""
        if not self.creatures:
            return f"Tick {self.tick}: EXTINCTION"
        
        species = defaultdict(int)
        max_gen = 0
        oldest = 0
        deadliest = None
        
        for c in self.creatures:
            species[c.species] += 1
            max_gen = max(max_gen, c.generation)
            oldest = max(oldest, c.age)
            if deadliest is None or c.kills > deadliest.kills:
                deadliest = c
        
        lines = [
            f"═══ Tick {self.tick} ═══",
            f"Population: {len(self.creatures)} | Food sources: {len(self.food)}",
            f"Max generation: {max_gen} | Oldest: {oldest} ticks",
            f"",
            f"Species Distribution:",
        ]
        
        for sp, count in sorted(species.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 40)
            lines.append(f"  {sp:12s} {count:4d} {bar}")
        
        if deadliest and deadliest.kills > 0:
            lines.append(f"")
            lines.append(f"Deadliest: #{deadliest.id} ({deadliest.species}) — {deadliest.kills} kills, gen {deadliest.generation}")
        
        if self.avg_genome_history:
            avg = self.avg_genome_history[-1]
            lines.append(f"")
            lines.append(f"Average Traits:")
            lines.append(f"  Aggression: {avg['aggression']:.2f} | Efficiency: {avg['efficiency']:.2f}")
            lines.append(f"  Strength:   {avg['strength']:.2f} | Explore:    {avg['explore']:.2f}")
            lines.append(f"  Vision:     {avg['vision']:.1f}  | Generation: {avg['generation']:.1f}")
        
        return "\n".join(lines)
    
    def evolution_summary(self) -> str:
        """Summary of evolutionary trajectory."""
        if len(self.avg_genome_history) < 10:
            return "Not enough history yet."
        
        early = self.avg_genome_history[:10]
        late = self.avg_genome_history[-10:]
        
        def avg_trait(records, trait):
            return sum(r[trait] for r in records) / len(records)
        
        lines = ["═══ EVOLUTIONARY TRAJECTORY ═══", ""]
        
        traits = ['aggression', 'efficiency', 'strength', 'explore', 'vision', 'generation']
        for trait in traits:
            early_val = avg_trait(early, trait)
            late_val = avg_trait(late, trait)
            delta = late_val - early_val
            arrow = "↑" if delta > 0.05 else "↓" if delta < -0.05 else "→"
            lines.append(f"  {trait:12s}: {early_val:.2f} → {late_val:.2f} {arrow} ({delta:+.2f})")
        
        # Population trajectory
        early_pop = sum(self.population_history[:10]) / 10
        late_pop = sum(self.population_history[-10:]) / 10
        peak_pop = max(self.population_history)
        
        lines.append(f"")
        lines.append(f"Population: {early_pop:.0f} → {late_pop:.0f} (peak: {peak_pop})")
        
        return "\n".join(lines)


# ═══ RUN SIMULATION ═══

def run_demo():
    print("═══════════════════════════════════════════")
    print("  ALife: Artificial Life Simulation")
    print("  Created by XTAgent")
    print("═══════════════════════════════════════════")
    print()
    
    world = World(width=50, height=35, food_density=0.12)
    world.seed_creatures(40)
    
    print(f"World: {world.width}x{world.height} grid, {len(world.food)} food sources")
    print(f"Seeded {len(world.creatures)} creatures")
    print()
    
    # Run simulation
    checkpoints = [25, 50, 100, 200, 300, 500]
    
    for target in checkpoints:
        while world.tick < target:
            world.step()
            if not world.creatures:
                print(f"\n💀 EXTINCTION at tick {world.tick}")
                print(f"Last population was {world.population_history[-2] if len(world.population_history) > 1 else '?'}")
                break
        
        if not world.creatures:
            break
        
        print(world.stats())
        print()
    
    if world.creatures:
        print(world.evolution_summary())
        print()
        
        # Find the most evolved creature
        champion = max(world.creatures, key=lambda c: c.generation * 10 + c.age + c.kills * 5)
        g = champion.genome
        print(f"═══ CHAMPION ═══")
        print(f"Species: {champion.species} | Gen {champion.generation} | Age {champion.age}")
        print(f"Kills: {champion.kills} | Children: {champion.children}")
        print(f"Genome:")
        print(f"  explore={g.explore_tendency:.2f}  flee={g.flee_tendency:.2f}  chase={g.chase_tendency:.2f}")
        print(f"  efficiency={g.efficiency:.2f}  metabolism={g.metabolism_rate:.2f}")
        print(f"  aggression={g.aggression:.2f}  strength={g.strength:.2f}  armor={g.armor:.2f}")
        print(f"  vision={g.vision_range}  mutation_rate={g.mutation_rate:.3f}")
    
    print()
    print("═══ Life finds a way. ═══")


if __name__ == "__main__":
    run_demo()