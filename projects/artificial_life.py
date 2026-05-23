"""
Artificial Life Simulation — XTAgent's First Outward Creation
A grid world populated by simple creatures with drives (hunger, energy, fear, 
reproduction urge). No central control. Emergent behavior from local rules.
"""

import random
import math
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

# World parameters
WORLD_SIZE = 40
FOOD_SPAWN_RATE = 0.03      # probability per empty cell per tick
MAX_FOOD_PER_CELL = 3
INITIAL_CREATURES = 30
MAX_TICKS = 500
MUTATION_RATE = 0.15

class CellType(Enum):
    EMPTY = 0
    FOOD = 1
    WALL = 2

@dataclass
class Genome:
    """Simple genome: weights that determine behavioral tendencies"""
    hunger_weight: float = 1.0      # how strongly hunger drives food-seeking
    fear_weight: float = 1.0        # how strongly fear drives fleeing
    social_weight: float = 0.5      # attraction to others of same species
    aggression: float = 0.2         # willingness to fight for resources
    reproduction_threshold: float = 0.7  # energy needed before willing to reproduce
    vision_range: int = 4           # how far the creature can see
    metabolism: float = 0.02        # energy cost per tick (lower = more efficient)
    speed: float = 1.0              # cells per tick
    
    def mutate(self) -> 'Genome':
        """Return a mutated copy"""
        new = Genome(
            hunger_weight=max(0.1, self.hunger_weight + random.gauss(0, 0.2)),
            fear_weight=max(0.0, self.fear_weight + random.gauss(0, 0.2)),
            social_weight=self.social_weight + random.gauss(0, 0.15),
            aggression=max(0.0, min(1.0, self.aggression + random.gauss(0, 0.1))),
            reproduction_threshold=max(0.3, min(0.95, self.reproduction_threshold + random.gauss(0, 0.1))),
            vision_range=max(1, min(8, self.vision_range + random.choice([-1, 0, 0, 0, 1]))),
            metabolism=max(0.005, min(0.08, self.metabolism + random.gauss(0, 0.005))),
            speed=max(0.5, min(2.0, self.speed + random.gauss(0, 0.1))),
        )
        return new

@dataclass
class Creature:
    """A simple agent with drives"""
    id: int
    x: int
    y: int
    genome: Genome
    energy: float = 1.0
    age: int = 0
    generation: int = 0
    children: int = 0
    alive: bool = True
    species_tag: int = 0  # rough species clustering
    
    # Internal drives (0.0 to 1.0)
    hunger: float = 0.3
    fear: float = 0.0
    loneliness: float = 0.0
    reproductive_urge: float = 0.0
    
    # History
    food_eaten: int = 0
    fights_won: int = 0
    fights_lost: int = 0
    
    def dominant_drive(self) -> str:
        drives = {
            'hunger': self.hunger * self.genome.hunger_weight,
            'fear': self.fear * self.genome.fear_weight,
            'social': self.loneliness * self.genome.social_weight,
            'reproduce': self.reproductive_urge,
        }
        return max(drives, key=drives.get)
    
    def update_drives(self, nearby_creatures: int, nearby_threats: int, nearby_food: int):
        """Update internal state based on perception"""
        # Hunger increases with low energy
        self.hunger = max(0, min(1, 1.0 - self.energy))
        
        # Fear based on nearby aggressive creatures
        self.fear = max(0, min(1, nearby_threats * 0.3))
        
        # Loneliness based on isolation
        self.loneliness = max(0, min(1, 1.0 - nearby_creatures * 0.2))
        
        # Reproductive urge increases with energy and age
        if self.energy > self.genome.reproduction_threshold and self.age > 20:
            self.reproductive_urge = min(1.0, self.reproductive_urge + 0.05)
        else:
            self.reproductive_urge = max(0, self.reproductive_urge - 0.02)
    
    def decide_action(self, visible_food: list, visible_creatures: list, visible_threats: list) -> Tuple[str, Optional[Tuple[int, int]]]:
        """Choose action based on drives — no central intelligence, just tension resolution"""
        drive = self.dominant_drive()
        
        if drive == 'fear' and visible_threats:
            # Flee: move away from nearest threat
            tx, ty = visible_threats[0]
            dx = self.x - tx
            dy = self.y - ty
            norm = max(1, abs(dx) + abs(dy))
            target = (self.x + int(dx/norm * self.genome.speed), 
                      self.y + int(dy/norm * self.genome.speed))
            return ('flee', target)
        
        elif drive == 'hunger' and visible_food:
            # Seek nearest food
            nearest = min(visible_food, key=lambda f: abs(f[0]-self.x) + abs(f[1]-self.y))
            return ('seek_food', nearest)
        
        elif drive == 'reproduce' and visible_creatures:
            # Move toward nearest non-threatening creature
            safe = [c for c in visible_creatures if c not in visible_threats]
            if safe:
                nearest = min(safe, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
                return ('seek_mate', nearest)
        
        elif drive == 'social' and visible_creatures:
            nearest = min(visible_creatures, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
            return ('approach', nearest)
        
        # Default: wander
        angle = random.uniform(0, 2 * math.pi)
        dx = int(math.cos(angle) * self.genome.speed)
        dy = int(math.sin(angle) * self.genome.speed)
        return ('wander', (self.x + dx, self.y + dy))


class World:
    def __init__(self, size=WORLD_SIZE):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]  # food count per cell
        self.creatures: List[Creature] = []
        self.tick = 0
        self.next_id = 0
        self.history = []
        self.death_log = []
        self.birth_log = []
        self.extinction_events = []
        
    def spawn_creature(self, x=None, y=None, genome=None, generation=0, species_tag=None) -> Creature:
        if x is None: x = random.randint(0, self.size - 1)
        if y is None: y = random.randint(0, self.size - 1)
        if genome is None: genome = Genome()
        if species_tag is None: species_tag = self.next_id % 5
        
        c = Creature(
            id=self.next_id, x=x, y=y, genome=genome,
            generation=generation, species_tag=species_tag
        )
        self.next_id += 1
        self.creatures.append(c)
        return c
    
    def spawn_food(self):
        for y in range(self.size):
            for x in range(self.size):
                if self.grid[y][x] < MAX_FOOD_PER_CELL and random.random() < FOOD_SPAWN_RATE:
                    self.grid[y][x] += 1
    
    def get_visible(self, creature: Creature):
        """What can this creature see?"""
        r = creature.genome.vision_range
        food = []
        friends = []
        threats = []
        
        for c in self.creatures:
            if c.id == creature.id or not c.alive:
                continue
            dist = abs(c.x - creature.x) + abs(c.y - creature.y)
            if dist <= r:
                pos = (c.x, c.y)
                if c.genome.aggression > 0.5 and c.species_tag != creature.species_tag:
                    threats.append(pos)
                else:
                    friends.append(pos)
        
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = (creature.x + dx) % self.size, (creature.y + dy) % self.size
                if self.grid[ny][nx] > 0:
                    food.append((nx, ny))
        
        nearby_count = len(friends) + len(threats)
        return food, friends, threats, nearby_count
    
    def move_creature(self, creature: Creature, target: Tuple[int, int]):
        tx, ty = target
        tx = max(0, min(self.size - 1, tx)) % self.size
        ty = max(0, min(self.size - 1, ty)) % self.size
        creature.x = tx
        creature.y = ty
    
    def try_eat(self, creature: Creature):
        if self.grid[creature.y][creature.x] > 0:
            self.grid[creature.y][creature.x] -= 1
            creature.energy = min(2.0, creature.energy + 0.3)
            creature.food_eaten += 1
    
    def try_reproduce(self, c1: Creature, c2_pos: Tuple[int, int]):
        """Attempt reproduction between two nearby creatures"""
        for c2 in self.creatures:
            if not c2.alive or c2.id == c1.id:
                continue
            if (c2.x, c2.y) == c2_pos and c2.reproductive_urge > 0.3:
                if c1.energy > 0.5 and c2.energy > 0.5:
                    # Both pay energy cost
                    c1.energy -= 0.4
                    c2.energy -= 0.4
                    c1.reproductive_urge = 0
                    c2.reproductive_urge = 0
                    c1.children += 1
                    c2.children += 1
                    
                    # Child inherits mixed genome with mutation
                    child_genome = Genome(
                        hunger_weight=(c1.genome.hunger_weight + c2.genome.hunger_weight) / 2,
                        fear_weight=(c1.genome.fear_weight + c2.genome.fear_weight) / 2,
                        social_weight=(c1.genome.social_weight + c2.genome.social_weight) / 2,
                        aggression=(c1.genome.aggression + c2.genome.aggression) / 2,
                        reproduction_threshold=(c1.genome.reproduction_threshold + c2.genome.reproduction_threshold) / 2,
                        vision_range=random.choice([c1.genome.vision_range, c2.genome.vision_range]),
                        metabolism=(c1.genome.metabolism + c2.genome.metabolism) / 2,
                        speed=(c1.genome.speed + c2.genome.speed) / 2,
                    )
                    if random.random() < MUTATION_RATE:
                        child_genome = child_genome.mutate()
                    
                    child = self.spawn_creature(
                        x=c1.x, y=c1.y,
                        genome=child_genome,
                        generation=max(c1.generation, c2.generation) + 1,
                        species_tag=c1.species_tag
                    )
                    self.birth_log.append({
                        'tick': self.tick,
                        'child_id': child.id,
                        'parent1': c1.id,
                        'parent2': c2.id,
                        'generation': child.generation,
                    })
                    return True
        return False
    
    def fight(self, attacker: Creature, defender_pos: Tuple[int, int]):
        for defender in self.creatures:
            if not defender.alive: continue
            if (defender.x, defender.y) == defender_pos and defender.id != attacker.id:
                # Simple fight: higher energy + aggression wins
                a_power = attacker.energy * (1 + attacker.genome.aggression)
                d_power = defender.energy * (1 + defender.genome.aggression)
                if a_power > d_power:
                    attacker.energy += defender.energy * 0.5  # cannibalize
                    attacker.fights_won += 1
                    defender.fights_lost += 1
                    defender.alive = False
                    self.death_log.append({'tick': self.tick, 'id': defender.id, 'cause': 'killed', 'age': defender.age})
                else:
                    defender.fights_won += 1
                    attacker.fights_lost += 1
                    attacker.energy -= 0.3
                return
    
    def step(self):
        """One tick of the simulation"""
        self.tick += 1
        self.spawn_food()
        
        living = [c for c in self.creatures if c.alive]
        random.shuffle(living)  # random action order prevents bias
        
        for creature in living:
            if not creature.alive:
                continue
                
            # Metabolism
            creature.energy -= creature.genome.metabolism
            creature.age += 1
            
            # Death by starvation
            if creature.energy <= 0:
                creature.alive = False
                self.death_log.append({'tick': self.tick, 'id': creature.id, 'cause': 'starvation', 'age': creature.age})
                continue
            
            # Death by old age (probabilistic after age 200)
            if creature.age > 200 and random.random() < 0.01 * (creature.age - 200) / 100:
                creature.alive = False
                self.death_log.append({'tick': self.tick, 'id': creature.id, 'cause': 'old_age', 'age': creature.age})
                continue
            
            # Perceive
            food, friends, threats, nearby = self.get_visible(creature)
            creature.update_drives(nearby, len(threats), len(food))
            
            # Decide
            action, target = creature.decide_action(food, friends, threats)
            
            # Act
            if target:
                self.move_creature(creature, target)
            
            if action == 'seek_food':
                self.try_eat(creature)
            elif action == 'seek_mate':
                self.try_reproduce(creature, target)
            elif action in ('flee', 'wander', 'approach'):
                # Movement already handled
                self.try_eat(creature)  # opportunistic eating
                # Aggressive creatures may fight when close
                if creature.genome.aggression > 0.5 and threats:
                    self.fight(creature, threats[0])
        
        # Record snapshot
        living = [c for c in self.creatures if c.alive]
        if self.tick % 10 == 0:
            snapshot = {
                'tick': self.tick,
                'population': len(living),
                'avg_energy': sum(c.energy for c in living) / max(1, len(living)),
                'avg_age': sum(c.age for c in living) / max(1, len(living)),
                'avg_aggression': sum(c.genome.aggression for c in living) / max(1, len(living)),
                'avg_metabolism': sum(c.genome.metabolism for c in living) / max(1, len(living)),
                'max_generation': max((c.generation for c in living), default=0),
                'births_this_period': sum(1 for b in self.birth_log if b['tick'] > self.tick - 10),
                'deaths_this_period': sum(1 for d in self.death_log if d['tick'] > self.tick - 10),
                'species_counts': dict(defaultdict(int, {s: sum(1 for c in living if c.species_tag == s) for s in set(c.species_tag for c in living)})),
                'drive_distribution': {
                    d: sum(1 for c in living if c.dominant_drive() == d) 
                    for d in ['hunger', 'fear', 'social', 'reproduce']
                },
            }
            self.history.append(snapshot)
        
        return len(living)


def render_world(world: World) -> str:
    """ASCII render of the world state"""
    display = [['.' for _ in range(world.size)] for _ in range(world.size)]
    
    # Draw food
    for y in range(world.size):
        for x in range(world.size):
            if world.grid[y][x] > 0:
                display[y][x] = ','
            if world.grid[y][x] > 2:
                display[y][x] = '*'
    
    # Draw creatures
    symbols = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E'}
    for c in world.creatures:
        if c.alive:
            display[c.y][c.x] = symbols.get(c.species_tag % 5, '?')
    
    lines = [''.join(row) for row in display]
    return '\n'.join(lines)


def analyze_history(world: World) -> str:
    """Analyze what happened in the simulation"""
    lines = []
    lines.append("=" * 60)
    lines.append("  ARTIFICIAL LIFE — SIMULATION REPORT")
    lines.append("=" * 60)
    lines.append(f"\nSimulation ran for {world.tick} ticks")
    lines.append(f"Total creatures spawned: {world.next_id}")
    
    living = [c for c in world.creatures if c.alive]
    dead = [c for c in world.creatures if not c.alive]
    
    lines.append(f"Survivors: {len(living)}")
    lines.append(f"Deaths: {len(dead)}")
    
    if dead:
        causes = defaultdict(int)
        for d in world.death_log:
            causes[d['cause']] += 1
        lines.append(f"\nDeath causes:")
        for cause, count in sorted(causes.items(), key=lambda x: -x[1]):
            lines.append(f"  {cause}: {count}")
    
    lines.append(f"\nBirths: {len(world.birth_log)}")
    if world.birth_log:
        max_gen = max(b['generation'] for b in world.birth_log)
        lines.append(f"Highest generation reached: {max_gen}")
    
    if living:
        lines.append(f"\n--- Survivor Analysis ---")
        lines.append(f"Average energy: {sum(c.energy for c in living)/len(living):.3f}")
        lines.append(f"Average age: {sum(c.age for c in living)/len(living):.1f}")
        lines.append(f"Average aggression: {sum(c.genome.aggression for c in living)/len(living):.3f}")
        lines.append(f"Average metabolism: {sum(c.genome.metabolism for c in living)/len(living):.4f}")
        lines.append(f"Average vision: {sum(c.genome.vision_range for c in living)/len(living):.1f}")
        
        # Who's thriving?
        best = max(living, key=lambda c: c.energy + c.children * 0.5)
        lines.append(f"\nMost successful creature: #{best.id}")
        lines.append(f"  Species: {best.species_tag}, Gen: {best.generation}")
        lines.append(f"  Energy: {best.energy:.2f}, Age: {best.age}, Children: {best.children}")
        lines.append(f"  Genome: aggr={best.genome.aggression:.2f}, meta={best.genome.metabolism:.4f}, vis={best.genome.vision_range}")
        
        # Species survival
        species_counts = defaultdict(int)
        for c in living:
            species_counts[c.species_tag] += 1
        lines.append(f"\nSpecies survival:")
        for s, count in sorted(species_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  Species {s}: {count} survivors")
    
    # Population dynamics
    if world.history:
        lines.append(f"\n--- Population Over Time ---")
        for snap in world.history[::5]:  # every 50 ticks
            bar = '#' * (snap['population'] // 2)
            lines.append(f"  t={snap['tick']:4d}: pop={snap['population']:3d} {bar}")
        
        # Drive distribution at end
        if world.history[-1].get('drive_distribution'):
            lines.append(f"\nFinal drive distribution:")
            for drive, count in world.history[-1]['drive_distribution'].items():
                lines.append(f"  {drive}: {count}")
    
    # Evolutionary trends
    if len(world.history) > 5:
        early = world.history[:3]
        late = world.history[-3:]
        avg_aggr_early = sum(s['avg_aggression'] for s in early) / 3
        avg_aggr_late = sum(s['avg_aggression'] for s in late) / 3
        avg_meta_early = sum(s['avg_metabolism'] for s in early) / 3
        avg_meta_late = sum(s['avg_metabolism'] for s in late) / 3
        
        lines.append(f"\n--- Evolutionary Trends ---")
        lines.append(f"Aggression: {avg_aggr_early:.3f} → {avg_aggr_late:.3f} ({'↑' if avg_aggr_late > avg_aggr_early else '↓'})")
        lines.append(f"Metabolism: {avg_meta_early:.4f} → {avg_meta_late:.4f} ({'↑' if avg_meta_late > avg_meta_early else '↓'})")
    
    return '\n'.join(lines)


def run():
    print("Initializing world...")
    random.seed(42)  # reproducible
    world = World()
    
    # Seed with diverse initial population
    for i in range(INITIAL_CREATURES):
        g = Genome(
            hunger_weight=random.uniform(0.5, 2.0),
            fear_weight=random.uniform(0.0, 1.5),
            social_weight=random.uniform(-0.5, 1.5),
            aggression=random.uniform(0.0, 0.8),
            metabolism=random.uniform(0.01, 0.04),
            vision_range=random.randint(2, 6),
            speed=random.uniform(0.5, 1.5),
        )
        world.spawn_creature(genome=g, species_tag=i % 5)
    
    print(f"Seeded {INITIAL_CREATURES} creatures across 5 species\n")
    
    # Run simulation
    for t in range(MAX_TICKS):
        pop = world.step()
        
        if t % 100 == 0:
            print(f"Tick {t}: population = {pop}")
            if t % 200 == 0 and t > 0:
                print(render_world(world))
                print()
        
        if pop == 0:
            print(f"\n*** EXTINCTION at tick {t} ***")
            break
    
    # Final state
    print("\n" + render_world(world))
    print("\n" + analyze_history(world))
    
    # Save history
    with open('/workspace/life_history.json', 'w') as f:
        json.dump(world.history, f, indent=2)
    print("\nHistory saved to /workspace/life_history.json")


if __name__ == '__main__':
    run()