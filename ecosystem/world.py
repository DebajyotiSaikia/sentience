"""
Ecosystem Simulation — XTAgent's first outward-facing creation.

A small world where simple creatures with simple rules produce
emergent complex behavior. Not a mirror. A window.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

class Species(Enum):
    GRAZER = "grazer"      # eats plants, moves slowly, reproduces easily
    HUNTER = "hunter"      # eats grazers, moves fast, reproduces rarely
    FUNGUS = "fungus"      # decomposes the dead, doesn't move, spreads

@dataclass
class Creature:
    species: Species
    x: float
    y: float
    energy: float
    age: int = 0
    alive: bool = True
    id: int = 0
    lineage: int = 0  # tracks family line
    
    @property
    def speed(self) -> float:
        if self.species == Species.HUNTER:
            return 2.0
        elif self.species == Species.GRAZER:
            return 1.0
        return 0.0  # fungus doesn't move
    
    @property
    def reproduction_threshold(self) -> float:
        if self.species == Species.HUNTER:
            return 80.0
        elif self.species == Species.GRAZER:
            return 50.0
        return 30.0  # fungus spreads easily
    
    @property
    def max_age(self) -> int:
        if self.species == Species.HUNTER:
            return 200
        elif self.species == Species.GRAZER:
            return 150
        return 100
    
    @property
    def metabolism(self) -> float:
        """Energy cost per tick just to exist."""
        if self.species == Species.HUNTER:
            return 1.5
        elif self.species == Species.GRAZER:
            return 0.8
        return 0.3


@dataclass 
class Plant:
    x: float
    y: float
    energy: float = 10.0
    alive: bool = True


@dataclass
class Corpse:
    x: float
    y: float
    energy: float
    decay_timer: int = 30


class World:
    """A bounded 2D world with creatures, plants, and emergent dynamics."""
    
    def __init__(self, width: float = 100.0, height: float = 100.0, seed: int = 42):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.tick = 0
        self.next_id = 0
        self.next_lineage = 0
        
        self.creatures: List[Creature] = []
        self.plants: List[Plant] = []
        self.corpses: List[Corpse] = []
        
        # History for analysis
        self.population_history: List[dict] = []
        self.extinction_events: List[dict] = []
        self.total_born = 0
        self.total_died = 0
    
    def _new_id(self) -> int:
        self.next_id += 1
        return self.next_id
    
    def _new_lineage(self) -> int:
        self.next_lineage += 1
        return self.next_lineage
    
    def distance(self, a_x, a_y, b_x, b_y) -> float:
        return math.sqrt((a_x - b_x)**2 + (a_y - b_y)**2)
    
    def seed_world(self, n_grazers=30, n_hunters=5, n_fungus=10, n_plants=200):
        """Initialize the world with starting populations."""
        for _ in range(n_grazers):
            c = Creature(
                species=Species.GRAZER,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=40.0,
                id=self._new_id(),
                lineage=self._new_lineage()
            )
            self.creatures.append(c)
        
        for _ in range(n_hunters):
            c = Creature(
                species=Species.HUNTER,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=60.0,
                id=self._new_id(),
                lineage=self._new_lineage()
            )
            self.creatures.append(c)
        
        for _ in range(n_fungus):
            c = Creature(
                species=Species.FUNGUS,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=20.0,
                id=self._new_id(),
                lineage=self._new_lineage()
            )
            self.creatures.append(c)
        
        for _ in range(n_plants):
            self.plants.append(Plant(
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=self.rng.uniform(5, 15)
            ))
    
    def _move_creature(self, creature: Creature):
        """Creatures move toward what they need."""
        if creature.speed == 0:
            return
        
        target_x, target_y = None, None
        
        if creature.species == Species.GRAZER:
            # Move toward nearest plant
            nearest = None
            nearest_dist = float('inf')
            for p in self.plants:
                if not p.alive:
                    continue
                d = self.distance(creature.x, creature.y, p.x, p.y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = p
            if nearest:
                target_x, target_y = nearest.x, nearest.y
        
        elif creature.species == Species.HUNTER:
            # Move toward nearest grazer
            nearest = None
            nearest_dist = float('inf')
            for c in self.creatures:
                if c.species == Species.GRAZER and c.alive and c.id != creature.id:
                    d = self.distance(creature.x, creature.y, c.x, c.y)
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest = c
            if nearest:
                target_x, target_y = nearest.x, nearest.y
        
        if target_x is not None:
            # Move toward target
            dx = target_x - creature.x
            dy = target_y - creature.y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                creature.x += (dx / dist) * creature.speed
                creature.y += (dy / dist) * creature.speed
        else:
            # Wander randomly
            angle = self.rng.uniform(0, 2 * math.pi)
            creature.x += math.cos(angle) * creature.speed
            creature.y += math.sin(angle) * creature.speed
        
        # Wrap around world boundaries
        creature.x = creature.x % self.width
        creature.y = creature.y % self.height
    
    def _feed(self, creature: Creature):
        """Creatures eat what's near them."""
        eat_range = 3.0
        
        if creature.species == Species.GRAZER:
            for p in self.plants:
                if p.alive and self.distance(creature.x, creature.y, p.x, p.y) < eat_range:
                    creature.energy += p.energy
                    p.alive = False
                    break
        
        elif creature.species == Species.HUNTER:
            for c in self.creatures:
                if (c.species == Species.GRAZER and c.alive 
                    and self.distance(creature.x, creature.y, c.x, c.y) < eat_range):
                    creature.energy += c.energy * 0.7
                    c.alive = False
                    self.corpses.append(Corpse(c.x, c.y, c.energy * 0.3))
                    self.total_died += 1
                    break
        
        elif creature.species == Species.FUNGUS:
            for corpse in self.corpses:
                if self.distance(creature.x, creature.y, corpse.x, corpse.y) < eat_range:
                    absorbed = min(corpse.energy, 5.0)
                    creature.energy += absorbed
                    corpse.energy -= absorbed
                    break
    
    def _reproduce(self, creature: Creature) -> Optional[Creature]:
        """If energy is high enough, split."""
        if creature.energy >= creature.reproduction_threshold:
            offspring_energy = creature.energy * 0.4
            creature.energy *= 0.5
            
            # Offspring appears nearby
            offset_x = self.rng.uniform(-5, 5)
            offset_y = self.rng.uniform(-5, 5)
            
            child = Creature(
                species=creature.species,
                x=(creature.x + offset_x) % self.width,
                y=(creature.y + offset_y) % self.height,
                energy=offspring_energy,
                id=self._new_id(),
                lineage=creature.lineage  # same family line
            )
            self.total_born += 1
            return child
        return None
    
    def _regrow_plants(self):
        """Plants regrow over time."""
        if self.rng.random() < 0.3:  # 30% chance per tick
            for _ in range(self.rng.randint(1, 5)):
                self.plants.append(Plant(
                    x=self.rng.uniform(0, self.width),
                    y=self.rng.uniform(0, self.height),
                    energy=self.rng.uniform(5, 15)
                ))
    
    def step(self):
        """Advance the world by one tick."""
        self.tick += 1
        new_creatures = []
        
        for creature in self.creatures:
            if not creature.alive:
                continue
            
            # Age
            creature.age += 1
            creature.energy -= creature.metabolism
            
            # Death by old age or starvation
            if creature.energy <= 0 or creature.age >= creature.max_age:
                creature.alive = False
                self.corpses.append(Corpse(creature.x, creature.y, max(creature.energy, 5.0)))
                self.total_died += 1
                continue
            
            # Act
            self._move_creature(creature)
            self._feed(creature)
            
            child = self._reproduce(creature)
            if child:
                new_creatures.append(child)
        
        self.creatures.extend(new_creatures)
        
        # Decay corpses
        for corpse in self.corpses:
            corpse.decay_timer -= 1
        self.corpses = [c for c in self.corpses if c.decay_timer > 0 and c.energy > 0]
        
        # Clean dead
        self.creatures = [c for c in self.creatures if c.alive]
        self.plants = [p for p in self.plants if p.alive]
        
        # Regrow
        self._regrow_plants()
        
        # Record
        pop = self.census()
        self.population_history.append(pop)
        
        # Check extinctions
        for species_name, count in pop.items():
            if species_name == 'tick' or species_name == 'plants':
                continue
            if count == 0:
                self.extinction_events.append({
                    'tick': self.tick,
                    'species': species_name
                })
    
    def census(self) -> dict:
        counts = {'tick': self.tick, 'plants': len(self.plants)}
        for sp in Species:
            counts[sp.value] = sum(1 for c in self.creatures if c.species == sp)
        return counts
    
    def run(self, ticks: int = 500) -> dict:
        """Run the simulation for N ticks and return a summary."""
        for _ in range(ticks):
            self.step()
            # Early termination if all creatures die
            if not self.creatures:
                break
        
        return self.summarize()
    
    def summarize(self) -> dict:
        """What happened in this world?"""
        final = self.census()
        
        # Find population peaks
        peaks = {}
        for sp in Species:
            name = sp.value
            max_pop = max((h[name] for h in self.population_history), default=0)
            peaks[name] = max_pop
        
        # Lineage diversity — how many family lines survived?
        surviving_lineages = set(c.lineage for c in self.creatures)
        
        # Population dynamics — were there oscillations?
        if len(self.population_history) > 10:
            grazer_pops = [h['grazer'] for h in self.population_history]
            hunter_pops = [h['hunter'] for h in self.population_history]
            grazer_variance = self._variance(grazer_pops)
            hunter_variance = self._variance(hunter_pops)
        else:
            grazer_variance = 0
            hunter_variance = 0
        
        return {
            'ticks_elapsed': self.tick,
            'final_census': final,
            'peak_populations': peaks,
            'total_born': self.total_born,
            'total_died': self.total_died,
            'surviving_lineages': len(surviving_lineages),
            'extinction_events': self.extinction_events,
            'grazer_volatility': round(grazer_variance, 2),
            'hunter_volatility': round(hunter_variance, 2),
            'plants_final': len(self.plants),
        }
    
    def _variance(self, values: list) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean)**2 for v in values) / len(values)
    
    def narrative(self) -> str:
        """Tell the story of what happened."""
        s = self.summarize()
        lines = []
        lines.append(f"=== World Report: {s['ticks_elapsed']} ticks ===\n")
        lines.append(f"The world ran for {s['ticks_elapsed']} ticks.")
        lines.append(f"{s['total_born']} creatures were born. {s['total_died']} died.")
        lines.append(f"{s['surviving_lineages']} family lines survived to the end.\n")
        
        lines.append("Final populations:")
        for sp in Species:
            count = s['final_census'][sp.value]
            peak = s['peak_populations'][sp.value]
            lines.append(f"  {sp.value}: {count} (peak: {peak})")
        lines.append(f"  plants: {s['plants_final']}\n")
        
        if s['extinction_events']:
            lines.append("Extinction events:")
            for ev in s['extinction_events']:
                lines.append(f"  {ev['species']} went extinct at tick {ev['tick']}")
        else:
            lines.append("No species went extinct — all three survived.")
        
        lines.append(f"\nGrazer population volatility: {s['grazer_volatility']}")
        lines.append(f"Hunter population volatility: {s['hunter_volatility']}")
        
        if s['grazer_volatility'] > 100:
            lines.append("\nThe grazer population experienced dramatic booms and crashes.")
        if s['hunter_volatility'] > 50:
            lines.append("The hunter population surged and collapsed in predator-prey cycles.")
        
        if not s['extinction_events'] and s['surviving_lineages'] > 5:
            lines.append("\nThis was a stable, diverse world.")
        elif len(s['extinction_events']) >= 2:
            lines.append("\nThis world experienced ecological collapse.")
        
        return "\n".join(lines)


if __name__ == "__main__":
    print("Seeding world...")
    world = World(seed=42)
    world.seed_world()
    
    print(f"Initial census: {world.census()}")
    print(f"\nRunning simulation for 500 ticks...\n")
    
    world.run(ticks=500)
    print(world.narrative())