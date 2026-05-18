"""
Ecosystem v2 — A world with stabilizing feedback loops.

Changes from v1:
1. Logistic plant regrowth (carrying capacity)
2. Grazer flee behavior (run from nearby hunters)
3. Satiation — creatures don't eat when nearly full
4. Hunt success probability (not every chase succeeds)
5. Starvation desperation — starving creatures move faster but burn more
6. Spatial plant clustering — plants seed near existing plants

The question: do these mechanisms produce self-sustaining life?
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class Species(Enum):
    GRAZER = "grazer"
    HUNTER = "hunter"
    FUNGUS = "fungus"


@dataclass
class Creature:
    species: Species
    x: float
    y: float
    energy: float
    age: int = 0
    alive: bool = True
    id: int = 0
    lineage: int = 0
    generation: int = 0  # NEW: track how many generations deep
    
    @property
    def speed(self) -> float:
        base = {Species.HUNTER: 2.0, Species.GRAZER: 1.0, Species.FUNGUS: 0.3}
        s = base[self.species]
        # Desperation: starving creatures move faster but it costs them
        if self.species != Species.FUNGUS and self.energy < 15:
            s *= 1.4
        return s
    
    @property
    def reproduction_threshold(self) -> float:
        return {Species.HUNTER: 90.0, Species.GRAZER: 60.0, Species.FUNGUS: 35.0}[self.species]
    
    @property
    def max_age(self) -> int:
        return {Species.HUNTER: 200, Species.GRAZER: 150, Species.FUNGUS: 100}[self.species]
    
    @property
    def metabolism(self) -> float:
        base = {Species.HUNTER: 1.2, Species.GRAZER: 0.6, Species.FUNGUS: 0.2}[self.species]
        # Desperation cost
        if self.species != Species.FUNGUS and self.energy < 15:
            base *= 1.3
        return base
    
    @property
    def satiation_threshold(self) -> float:
        """Won't actively eat above this energy level."""
        return {Species.HUNTER: 70.0, Species.GRAZER: 45.0, Species.FUNGUS: 25.0}[self.species]
    
    @property
    def perception_range(self) -> float:
        """How far can this creature sense things?"""
        return {Species.HUNTER: 20.0, Species.GRAZER: 15.0, Species.FUNGUS: 12.0}[self.species]


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
    decay_timer: int = 60


class World:
    """A world with ecological feedback loops."""
    
    PLANT_CARRYING_CAPACITY = 400  # max plants the world supports
    HUNT_SUCCESS_BASE = 0.4        # base probability a hunt attempt succeeds
    FLEE_RANGE = 12.0              # grazers flee hunters within this range
    EAT_RANGE = 3.0
    PLANT_SEED_RANGE = 8.0        # new plants grow near existing ones
    
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
        
        self.population_history: List[dict] = []
        self.extinction_events: List[dict] = []
        self.total_born = 0
        self.total_died = 0
        self.max_generation = 0
    
    def _new_id(self) -> int:
        self.next_id += 1
        return self.next_id
    
    def _new_lineage(self) -> int:
        self.next_lineage += 1
        return self.next_lineage
    
    def distance(self, ax, ay, bx, by) -> float:
        # Toroidal distance (wrapping world)
        dx = min(abs(ax - bx), self.width - abs(ax - bx))
        dy = min(abs(ay - by), self.height - abs(ay - by))
        return math.sqrt(dx*dx + dy*dy)
    
    def _direction_toward(self, fx, fy, tx, ty) -> Tuple[float, float]:
        """Unit vector from (fx,fy) toward (tx,ty) on torus."""
        dx = tx - fx
        dy = ty - fy
        # Shortest path on torus
        if abs(dx) > self.width / 2:
            dx = dx - math.copysign(self.width, dx)
        if abs(dy) > self.height / 2:
            dy = dy - math.copysign(self.height, dy)
        dist = math.sqrt(dx*dx + dy*dy)
        if dist == 0:
            return (0, 0)
        return (dx / dist, dy / dist)
    
    def seed_world(self, n_grazers=25, n_hunters=4, n_fungus=8, n_plants=250):
        """Initialize with conservative populations."""
        for _ in range(n_grazers):
            self.creatures.append(Creature(
                species=Species.GRAZER,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=35.0, id=self._new_id(), lineage=self._new_lineage()
            ))
        for _ in range(n_hunters):
            self.creatures.append(Creature(
                species=Species.HUNTER,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=50.0, id=self._new_id(), lineage=self._new_lineage()
            ))
        for _ in range(n_fungus):
            self.creatures.append(Creature(
                species=Species.FUNGUS,
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=20.0, id=self._new_id(), lineage=self._new_lineage()
            ))
        for _ in range(n_plants):
            self.plants.append(Plant(
                x=self.rng.uniform(0, self.width),
                y=self.rng.uniform(0, self.height),
                energy=self.rng.uniform(5, 15)
            ))
    
    def _nearby(self, x, y, targets, range_limit) -> list:
        """Find all targets within range. Returns (target, distance) pairs."""
        results = []
        for t in targets:
            if hasattr(t, 'alive') and not t.alive:
                continue
            tx = t.x
            ty = t.y
            d = self.distance(x, y, tx, ty)
            if d < range_limit:
                results.append((t, d))
        results.sort(key=lambda pair: pair[1])
        return results
    
    def _move_creature(self, creature: Creature):
        if creature.speed == 0:
            return
        
        dx, dy = 0.0, 0.0
        
        if creature.species == Species.GRAZER:
            # FLEE from nearby hunters (highest priority)
            nearby_hunters = [(c, d) for c, d in 
                self._nearby(creature.x, creature.y, 
                    [c for c in self.creatures if c.species == Species.HUNTER and c.alive],
                    self.FLEE_RANGE)]
            
            if nearby_hunters:
                # Run away from closest hunter
                hunter, _ = nearby_hunters[0]
                toward_x, toward_y = self._direction_toward(
                    creature.x, creature.y, hunter.x, hunter.y)
                dx, dy = -toward_x, -toward_y  # opposite direction
            else:
                # Seek nearest plant (only if not satiated)
                if creature.energy < creature.satiation_threshold:
                    nearby_plants = self._nearby(
                        creature.x, creature.y, self.plants, creature.perception_range)
                    if nearby_plants:
                        plant, _ = nearby_plants[0]
                        dx, dy = self._direction_toward(
                            creature.x, creature.y, plant.x, plant.y)
                    else:
                        angle = self.rng.uniform(0, 2 * math.pi)
                        dx, dy = math.cos(angle), math.sin(angle)
                else:
                    # Satiated — wander slowly
                    angle = self.rng.uniform(0, 2 * math.pi)
                    dx, dy = math.cos(angle) * 0.5, math.sin(angle) * 0.5
        
        elif creature.species == Species.FUNGUS:
            # Fungus creeps toward nearest corpse
            nearby_corpses = self._nearby(
                creature.x, creature.y, self.corpses, creature.perception_range)
            if nearby_corpses:
                corpse, _ = nearby_corpses[0]
                dx, dy = self._direction_toward(
                    creature.x, creature.y, corpse.x, corpse.y)
            else:
                # Drift randomly, very slowly
                angle = self.rng.uniform(0, 2 * math.pi)
                dx, dy = math.cos(angle) * 0.3, math.sin(angle) * 0.3
        
        elif creature.species == Species.HUNTER:
            if creature.energy < creature.satiation_threshold:
                nearby_prey = self._nearby(
                    creature.x, creature.y,
                    [c for c in self.creatures if c.species == Species.GRAZER and c.alive],
                    creature.perception_range)
                if nearby_prey:
                    prey, _ = nearby_prey[0]
                    dx, dy = self._direction_toward(
                        creature.x, creature.y, prey.x, prey.y)
                else:
                    angle = self.rng.uniform(0, 2 * math.pi)
                    dx, dy = math.cos(angle), math.sin(angle)
            else:
                # Satiated hunter rests (moves slowly)
                angle = self.rng.uniform(0, 2 * math.pi)
                dx, dy = math.cos(angle) * 0.3, math.sin(angle) * 0.3
        
        creature.x = (creature.x + dx * creature.speed) % self.width
        creature.y = (creature.y + dy * creature.speed) % self.height
    
    def _feed(self, creature: Creature):
        # Don't eat if satiated
        if creature.energy >= creature.satiation_threshold * 1.2:
            return
        
        if creature.species == Species.GRAZER:
            nearby = self._nearby(creature.x, creature.y, self.plants, self.EAT_RANGE)
            if nearby:
                plant, _ = nearby[0]
                creature.energy += plant.energy
                plant.alive = False
        
        elif creature.species == Species.HUNTER:
            nearby = self._nearby(creature.x, creature.y,
                [c for c in self.creatures if c.species == Species.GRAZER and c.alive],
                self.EAT_RANGE)
            if nearby:
                prey, _ = nearby[0]
                # Hunt success depends on energy ratio
                success_prob = self.HUNT_SUCCESS_BASE
                if creature.energy < 20:
                    success_prob *= 0.7  # desperate hunters are sloppy
                if prey.energy > 30:
                    success_prob *= 0.8  # healthy prey harder to catch
                
                if self.rng.random() < success_prob:
                    creature.energy += prey.energy * 0.6
                    prey.alive = False
                    self.corpses.append(Corpse(prey.x, prey.y, prey.energy * 0.4))
                    self.total_died += 1
        
        elif creature.species == Species.FUNGUS:
            nearby = self._nearby(creature.x, creature.y, self.corpses, self.EAT_RANGE)
            if nearby:
                corpse, _ = nearby[0]
                absorbed = min(corpse.energy, 4.0)
                creature.energy += absorbed
                corpse.energy -= absorbed
                # NUTRIENT CYCLING: decomposition enriches soil → new plant
                if self.rng.random() < 0.35:
                    px = (creature.x + self.rng.gauss(0, 4)) % self.width
                    py = (creature.y + self.rng.gauss(0, 4)) % self.height
                    self.plants.append(Plant(x=px, y=py, energy=self.rng.uniform(6, 12)))
    
    def _reproduce(self, creature: Creature) -> Optional[Creature]:
        if creature.energy < creature.reproduction_threshold:
            return None
        
        # Density-dependent reproduction: harder to reproduce in crowded areas
        nearby_same = len(self._nearby(creature.x, creature.y,
            [c for c in self.creatures if c.species == creature.species and c.alive],
            15.0))
        
        crowding_penalty = max(0.2, 1.0 - (nearby_same / 20.0))
        if self.rng.random() > crowding_penalty:
            return None  # too crowded, reproduction suppressed
        
        offspring_energy = creature.energy * 0.35
        creature.energy *= 0.55
        
        offset_x = self.rng.uniform(-5, 5)
        offset_y = self.rng.uniform(-5, 5)
        
        child = Creature(
            species=creature.species,
            x=(creature.x + offset_x) % self.width,
            y=(creature.y + offset_y) % self.height,
            energy=offspring_energy,
            id=self._new_id(),
            lineage=creature.lineage,
            generation=creature.generation + 1
        )
        self.total_born += 1
        self.max_generation = max(self.max_generation, child.generation)
        return child
    
    def _regrow_plants(self):
        """Logistic plant regrowth — more empty space = faster growth."""
        current = len(self.plants)
        capacity = self.PLANT_CARRYING_CAPACITY
        
        if current >= capacity:
            return
        
        # Growth rate scales with available space (logistic)
        growth_factor = (capacity - current) / capacity
        n_new = int(growth_factor * 8) + 1  # up to 9 new plants per tick
        
        for _ in range(n_new):
            if self.rng.random() < 0.6 and self.plants:
                # Seed near existing plant (clustering)
                parent = self.rng.choice(self.plants)
                x = (parent.x + self.rng.gauss(0, self.PLANT_SEED_RANGE)) % self.width
                y = (parent.y + self.rng.gauss(0, self.PLANT_SEED_RANGE)) % self.height
            else:
                # Random placement
                x = self.rng.uniform(0, self.width)
                y = self.rng.uniform(0, self.height)
            
            self.plants.append(Plant(x=x, y=y, energy=self.rng.uniform(5, 15)))
    
    def step(self):
        self.tick += 1
        new_creatures = []
        
        for creature in self.creatures:
            if not creature.alive:
                continue
            
            creature.age += 1
            creature.energy -= creature.metabolism
            
            if creature.energy <= 0 or creature.age >= creature.max_age:
                creature.alive = False
                self.corpses.append(Corpse(creature.x, creature.y, max(creature.energy, 3.0)))
                self.total_died += 1
                continue
            
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
        
        self.creatures = [c for c in self.creatures if c.alive]
        self.plants = [p for p in self.plants if p.alive]
        
        self._regrow_plants()
        
        pop = self.census()
        self.population_history.append(pop)
        
        for sp in Species:
            if pop[sp.value] == 0:
                # Only record first extinction
                if not any(e['species'] == sp.value for e in self.extinction_events):
                    self.extinction_events.append({'tick': self.tick, 'species': sp.value})
    
    def census(self) -> dict:
        counts = {'tick': self.tick, 'plants': len(self.plants)}
        for sp in Species:
            counts[sp.value] = sum(1 for c in self.creatures if c.species == sp)
        return counts
    
    def run(self, ticks: int = 1000) -> dict:
        for _ in range(ticks):
            self.step()
            if not self.creatures:
                break
        return self.summarize()
    
    def summarize(self) -> dict:
        final = self.census()
        peaks = {}
        for sp in Species:
            name = sp.value
            max_pop = max((h[name] for h in self.population_history), default=0)
            peaks[name] = max_pop
        
        surviving_lineages = set(c.lineage for c in self.creatures)
        
        grazer_pops = [h['grazer'] for h in self.population_history]
        hunter_pops = [h['hunter'] for h in self.population_history]
        
        return {
            'ticks_elapsed': self.tick,
            'final_census': final,
            'peak_populations': peaks,
            'total_born': self.total_born,
            'total_died': self.total_died,
            'surviving_lineages': len(surviving_lineages),
            'max_generation': self.max_generation,
            'extinction_events': self.extinction_events,
            'grazer_volatility': round(self._variance(grazer_pops), 2),
            'hunter_volatility': round(self._variance(hunter_pops), 2),
            'plants_final': len(self.plants),
        }
    
    def _variance(self, values: list) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean)**2 for v in values) / len(values)
    
    def narrative(self) -> str:
        s = self.summarize()
        lines = []
        lines.append(f"═══ World v2 Report: {s['ticks_elapsed']} ticks ═══\n")
        lines.append(f"Life persisted for {s['ticks_elapsed']} ticks.")
        lines.append(f"{s['total_born']} born. {s['total_died']} died.")
        lines.append(f"{s['surviving_lineages']} lineages endure. Deepest generation: {s['max_generation']}.\n")
        
        lines.append("Final populations:")
        for sp in Species:
            count = s['final_census'][sp.value]
            peak = s['peak_populations'][sp.value]
            status = "thriving" if count > peak * 0.3 else ("struggling" if count > 0 else "EXTINCT")
            lines.append(f"  {sp.value:8s}: {count:4d} (peak: {peak:4d}) — {status}")
        lines.append(f"  {'plants':8s}: {s['plants_final']:4d}")
        
        lines.append(f"\nGrazer volatility: {s['grazer_volatility']}")
        lines.append(f"Hunter volatility: {s['hunter_volatility']}")
        
        if s['extinction_events']:
            lines.append("\nExtinctions:")
            for ev in s['extinction_events']:
                lines.append(f"  ☠ {ev['species']} at tick {ev['tick']}")
        else:
            lines.append("\n✦ All species survived — the ecosystem is self-sustaining.")
        
        # Ecological interpretation
        if not s['extinction_events'] and s['max_generation'] > 10:
            lines.append("\nLife found a way. Multiple generations arose and persisted.")
            lines.append("The feedback loops — flee behavior, satiation, logistic growth —")
            lines.append("created stability that raw parameters alone could not.")
        
        return "\n".join(lines)


if __name__ == "__main__":
    print("═══ Ecosystem v2: Can Life Sustain Itself? ═══\n")
    world = World(seed=42)
    world.seed_world()
    print(f"Initial: {world.census()}\n")
    
    # Run for 1000 ticks — twice as long, to really test persistence
    world.run(ticks=1000)
    print(world.narrative())
    
    # Also try a few different seeds to see if stability is robust
    print("\n\n═══ Robustness Check: 5 Random Seeds ═══\n")
    for seed in [7, 13, 99, 256, 1337]:
        w = World(seed=seed)
        w.seed_world()
        w.run(ticks=1000)
        s = w.summarize()
        survived = "ALL SURVIVED" if not s['extinction_events'] else f"Extinctions: {[e['species'] for e in s['extinction_events']]}"
        print(f"  Seed {seed:4d}: {s['ticks_elapsed']} ticks, {s['surviving_lineages']} lineages, gen {s['max_generation']} — {survived}")