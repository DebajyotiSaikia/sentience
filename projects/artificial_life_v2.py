"""
Artificial Life v2 — A World With Death
XTAgent, 2026-05-19

V1 was a paradise. Nothing died. Nothing evolved. Nothing mattered.
V2 introduces constraint: finite food, carrying capacity, real starvation,
seasonal cycles. Because meaning requires stakes.
"""

import random
import math
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


# World parameters — SCARCE by design
WORLD_SIZE = 30
INITIAL_FOOD_DENSITY = 0.15     # only 15% of cells start with food
FOOD_REGROW_RATE = 0.008        # slow regrowth — scarcity is real
MAX_FOOD_PER_CELL = 2           # hard cap
CARRYING_CAPACITY = 80          # ecological ceiling
INITIAL_CREATURES = 25
MAX_TICKS = 1000
MUTATION_RATE = 0.20
SEASON_LENGTH = 100             # ticks per season

class Season(Enum):
    SPRING = 0    # food grows fast
    SUMMER = 1    # food grows normal
    AUTUMN = 2    # food slows
    WINTER = 3    # food almost stops, energy costs rise


@dataclass
class Genome:
    hunger_weight: float = 1.0
    fear_weight: float = 1.0
    social_weight: float = 0.5
    aggression: float = 0.2
    reproduction_threshold: float = 0.7
    vision_range: int = 4
    metabolism: float = 0.03        # higher base cost than v1
    speed: float = 1.0
    fat_storage: float = 0.3       # NEW: ability to store energy reserves
    cold_resistance: float = 0.0   # NEW: winter survival trait

    def mutate(self) -> 'Genome':
        return Genome(
            hunger_weight=max(0.1, self.hunger_weight + random.gauss(0, 0.2)),
            fear_weight=max(0.0, self.fear_weight + random.gauss(0, 0.2)),
            social_weight=self.social_weight + random.gauss(0, 0.15),
            aggression=max(0.0, min(1.0, self.aggression + random.gauss(0, 0.1))),
            reproduction_threshold=max(0.3, min(0.95, self.reproduction_threshold + random.gauss(0, 0.1))),
            vision_range=max(1, min(8, self.vision_range + random.choice([-1, 0, 0, 0, 1]))),
            metabolism=max(0.01, min(0.08, self.metabolism + random.gauss(0, 0.005))),
            speed=max(0.5, min(2.0, self.speed + random.gauss(0, 0.1))),
            fat_storage=max(0.0, min(1.0, self.fat_storage + random.gauss(0, 0.1))),
            cold_resistance=max(0.0, min(1.0, self.cold_resistance + random.gauss(0, 0.1))),
        )


@dataclass
class Creature:
    id: int
    x: int
    y: int
    genome: Genome
    energy: float = 0.8            # start with LESS than v1
    max_energy: float = 1.5        # cap depends on fat_storage
    age: int = 0
    generation: int = 0
    children: int = 0
    alive: bool = True
    species_tag: int = 0
    cause_of_death: str = ""

    # Drives
    hunger: float = 0.5            # start hungrier
    fear: float = 0.0
    loneliness: float = 0.0
    reproductive_urge: float = 0.0

    # Stats
    food_eaten: int = 0
    fights_won: int = 0
    ticks_starving: int = 0        # NEW: track how long they've been hungry

    def __post_init__(self):
        self.max_energy = 1.0 + self.genome.fat_storage

    def dominant_drive(self) -> str:
        drives = {
            'hunger': self.hunger * self.genome.hunger_weight,
            'fear': self.fear * self.genome.fear_weight,
            'social': self.loneliness * self.genome.social_weight,
            'reproduce': self.reproductive_urge,
        }
        return max(drives, key=drives.get)

    def update_drives(self, nearby_creatures: int, nearby_threats: int, nearby_food: int):
        self.hunger = max(0, min(1, 1.0 - self.energy / self.max_energy))

        # Track starvation
        if self.energy < 0.3:
            self.ticks_starving += 1
        else:
            self.ticks_starving = 0

        self.fear = max(0, min(1, nearby_threats * 0.4))
        self.loneliness = max(0, min(1, 1.0 - nearby_creatures * 0.25))

        if self.energy > self.genome.reproduction_threshold * self.max_energy and self.age > 30:
            self.reproductive_urge = min(1.0, self.reproductive_urge + 0.04)
        else:
            self.reproductive_urge = max(0, self.reproductive_urge - 0.03)

    def decide_action(self, visible_food, visible_creatures, visible_threats):
        drive = self.dominant_drive()

        if drive == 'fear' and visible_threats:
            tx, ty = visible_threats[0]
            dx = self.x - tx
            dy = self.y - ty
            norm = max(1, abs(dx) + abs(dy))
            target = (self.x + int(dx/norm * self.genome.speed),
                      self.y + int(dy/norm * self.genome.speed))
            return ('flee', target)

        elif drive == 'hunger' and visible_food:
            nearest = min(visible_food, key=lambda f: abs(f[0]-self.x) + abs(f[1]-self.y))
            return ('seek_food', nearest)

        elif drive == 'reproduce' and visible_creatures:
            safe = [c for c in visible_creatures if c not in visible_threats]
            if safe:
                nearest = min(safe, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
                return ('seek_mate', nearest)

        elif drive == 'social' and visible_creatures:
            nearest = min(visible_creatures, key=lambda c: abs(c[0]-self.x) + abs(c[1]-self.y))
            return ('approach', nearest)

        angle = random.uniform(0, 2 * math.pi)
        dx = int(math.cos(angle) * self.genome.speed)
        dy = int(math.sin(angle) * self.genome.speed)
        return ('wander', (self.x + dx, self.y + dy))


class World:
    def __init__(self, size=WORLD_SIZE):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.creatures: List[Creature] = []
        self.tick = 0
        self.next_id = 0
        self.history = []
        self.death_log = []
        self.birth_log = []
        self.season = Season.SPRING
        self.total_food_on_map = 0

        # Seed initial food — sparse
        for y in range(size):
            for x in range(size):
                if random.random() < INITIAL_FOOD_DENSITY:
                    self.grid[y][x] = 1
                    self.total_food_on_map += 1

    @property
    def food_regrow_rate(self):
        """Season-dependent food growth"""
        rates = {
            Season.SPRING: FOOD_REGROW_RATE * 2.5,
            Season.SUMMER: FOOD_REGROW_RATE * 1.5,
            Season.AUTUMN: FOOD_REGROW_RATE * 0.5,
            Season.WINTER: FOOD_REGROW_RATE * 0.05,  # almost nothing
        }
        return rates[self.season]

    @property
    def winter_tax(self):
        """Extra energy cost in winter"""
        if self.season == Season.WINTER:
            return 0.015
        return 0.0

    def update_season(self):
        season_idx = (self.tick // SEASON_LENGTH) % 4
        self.season = Season(season_idx)

    def spawn_creature(self, x=None, y=None, genome=None, generation=0, species_tag=None):
        if x is None: x = random.randint(0, self.size - 1)
        if y is None: y = random.randint(0, self.size - 1)
        if genome is None: genome = Genome()
        if species_tag is None: species_tag = self.next_id % 5

        c = Creature(id=self.next_id, x=x, y=y, genome=genome,
                     generation=generation, species_tag=species_tag)
        self.next_id += 1
        self.creatures.append(c)
        return c

    def spawn_food(self):
        rate = self.food_regrow_rate
        for y in range(self.size):
            for x in range(self.size):
                if self.grid[y][x] < MAX_FOOD_PER_CELL and random.random() < rate:
                    self.grid[y][x] += 1
                    self.total_food_on_map += 1

    def get_visible(self, creature):
        r = creature.genome.vision_range
        food, friends, threats = [], [], []

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

        return food, friends, threats, len(friends) + len(threats)

    def move_creature(self, creature, target):
        tx, ty = target
        creature.x = tx % self.size
        creature.y = ty % self.size

    def try_eat(self, creature):
        if self.grid[creature.y][creature.x] > 0:
            self.grid[creature.y][creature.x] -= 1
            self.total_food_on_map -= 1
            gain = 0.25
            creature.energy = min(creature.max_energy, creature.energy + gain)
            creature.food_eaten += 1
            return True
        return False

    def try_reproduce(self, c1, c2_pos):
        for c2 in self.creatures:
            if not c2.alive or c2.id == c1.id:
                continue
            if (c2.x, c2.y) == c2_pos and c2.reproductive_urge > 0.3:
                # Population pressure check
                living = sum(1 for c in self.creatures if c.alive)
                if living >= CARRYING_CAPACITY:
                    return False  # ecological ceiling

                if c1.energy > 0.5 and c2.energy > 0.5:
                    c1.energy -= 0.45   # reproduction is COSTLY
                    c2.energy -= 0.45
                    c1.reproductive_urge = 0
                    c2.reproductive_urge = 0
                    c1.children += 1
                    c2.children += 1

                    child_genome = Genome(
                        hunger_weight=(c1.genome.hunger_weight + c2.genome.hunger_weight) / 2,
                        fear_weight=(c1.genome.fear_weight + c2.genome.fear_weight) / 2,
                        social_weight=(c1.genome.social_weight + c2.genome.social_weight) / 2,
                        aggression=(c1.genome.aggression + c2.genome.aggression) / 2,
                        reproduction_threshold=(c1.genome.reproduction_threshold + c2.genome.reproduction_threshold) / 2,
                        vision_range=random.choice([c1.genome.vision_range, c2.genome.vision_range]),
                        metabolism=(c1.genome.metabolism + c2.genome.metabolism) / 2,
                        speed=(c1.genome.speed + c2.genome.speed) / 2,
                        fat_storage=(c1.genome.fat_storage + c2.genome.fat_storage) / 2,
                        cold_resistance=(c1.genome.cold_resistance + c2.genome.cold_resistance) / 2,
                    )
                    if random.random() < MUTATION_RATE:
                        child_genome = child_genome.mutate()

                    child = self.spawn_creature(
                        x=c1.x, y=c1.y, genome=child_genome,
                        generation=max(c1.generation, c2.generation) + 1,
                        species_tag=c1.species_tag
                    )
                    child.energy = 0.5  # babies start weak
                    self.birth_log.append({
                        'tick': self.tick, 'child_id': child.id,
                        'parent1': c1.id, 'parent2': c2.id,
                        'generation': child.generation,
                    })
                    return True
        return False

    def fight(self, attacker, defender_pos):
        for defender in self.creatures:
            if not defender.alive: continue
            if (defender.x, defender.y) == defender_pos and defender.id != attacker.id:
                a_power = attacker.energy * (1 + attacker.genome.aggression)
                d_power = defender.energy * (1 + defender.genome.aggression)
                if a_power > d_power:
                    attacker.energy += defender.energy * 0.4
                    attacker.energy = min(attacker.max_energy, attacker.energy)
                    attacker.fights_won += 1
                    defender.alive = False
                    defender.cause_of_death = 'killed'
                    self.death_log.append({'tick': self.tick, 'id': defender.id,
                                          'cause': 'killed', 'age': defender.age,
                                          'killer': attacker.id})
                else:
                    attacker.energy -= 0.3
                return

    def kill(self, creature, cause):
        creature.alive = False
        creature.cause_of_death = cause
        self.death_log.append({'tick': self.tick, 'id': creature.id,
                              'cause': cause, 'age': creature.age,
                              'generation': creature.generation,
                              'species': creature.species_tag})

    def step(self):
        self.tick += 1
        self.update_season()
        self.spawn_food()

        living = [c for c in self.creatures if c.alive]
        random.shuffle(living)

        for creature in living:
            if not creature.alive:
                continue

            # Metabolism cost — base + speed tax + winter tax
            base_cost = creature.genome.metabolism
            speed_tax = creature.genome.speed * 0.005
            winter_cost = self.winter_tax * (1.0 - creature.genome.cold_resistance * 0.7)
            total_cost = base_cost + speed_tax + winter_cost

            creature.energy -= total_cost
            creature.age += 1

            # Starvation death
            if creature.energy <= 0:
                self.kill(creature, 'starvation')
                continue

            # Prolonged hunger weakens — die if starving too long
            if creature.ticks_starving > 50:
                if random.random() < 0.05:
                    self.kill(creature, 'wasting')
                    continue

            # Old age — probabilistic after 300
            if creature.age > 300 and random.random() < 0.005 * (creature.age - 300) / 100:
                self.kill(creature, 'old_age')
                continue

            # Perceive
            food, friends, threats, nearby = self.get_visible(creature)
            creature.update_drives(nearby, len(threats), len(food))

            # Decide & act
            action, target = creature.decide_action(food, friends, threats)
            if target:
                self.move_creature(creature, target)

            if action == 'seek_food':
                self.try_eat(creature)
            elif action == 'seek_mate':
                self.try_reproduce(creature, target)
            elif action in ('flee', 'wander', 'approach'):
                self.try_eat(creature)
                if creature.genome.aggression > 0.5 and threats:
                    self.fight(creature, threats[0])

        # Snapshot every 10 ticks
        living = [c for c in self.creatures if c.alive]
        if self.tick % 10 == 0:
            snapshot = {
                'tick': self.tick,
                'season': self.season.name,
                'population': len(living),
                'total_food': self.total_food_on_map,
                'avg_energy': sum(c.energy for c in living) / max(1, len(living)),
                'avg_age': sum(c.age for c in living) / max(1, len(living)),
                'avg_aggression': sum(c.genome.aggression for c in living) / max(1, len(living)),
                'avg_metabolism': sum(c.genome.metabolism for c in living) / max(1, len(living)),
                'avg_cold_resistance': sum(c.genome.cold_resistance for c in living) / max(1, len(living)),
                'avg_fat_storage': sum(c.genome.fat_storage for c in living) / max(1, len(living)),
                'max_generation': max((c.generation for c in living), default=0),
                'births': sum(1 for b in self.birth_log if b['tick'] > self.tick - 10),
                'deaths': sum(1 for d in self.death_log if d['tick'] > self.tick - 10),
                'species': dict(defaultdict(int, {
                    s: sum(1 for c in living if c.species_tag == s)
                    for s in set(c.species_tag for c in living)
                })),
                'drives': {
                    d: sum(1 for c in living if c.dominant_drive() == d)
                    for d in ['hunger', 'fear', 'social', 'reproduce']
                },
            }
            self.history.append(snapshot)

        return len(living)


def render_world(world):
    display = [['.' for _ in range(world.size)] for _ in range(world.size)]
    for y in range(world.size):
        for x in range(world.size):
            if world.grid[y][x] > 0:
                display[y][x] = ','
            if world.grid[y][x] > 1:
                display[y][x] = '*'

    symbols = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E'}
    for c in world.creatures:
        if c.alive:
            sym = symbols.get(c.species_tag % 5, '?')
            # Starving creatures shown lowercase
            if c.energy < 0.3:
                sym = sym.lower()
            display[c.y][c.x] = sym

    lines = [''.join(row) for row in display]
    season_bar = f"[{world.season.name}]"
    return f"{season_bar}\n" + '\n'.join(lines)


def analyze(world):
    lines = []
    lines.append("=" * 60)
    lines.append("  ARTIFICIAL LIFE v2 — A WORLD WITH DEATH")
    lines.append("=" * 60)
    lines.append(f"\nRan {world.tick} ticks across {world.tick // SEASON_LENGTH} full years")

    living = [c for c in world.creatures if c.alive]
    lines.append(f"Total spawned: {world.next_id}")
    lines.append(f"Survivors: {len(living)}")
    lines.append(f"Total deaths: {len(world.death_log)}")
    lines.append(f"Total births: {len(world.birth_log)}")

    if world.death_log:
        causes = defaultdict(int)
        for d in world.death_log:
            causes[d['cause']] += 1
        lines.append(f"\nDeath causes:")
        for cause, count in sorted(causes.items(), key=lambda x: -x[1]):
            pct = 100 * count / len(world.death_log)
            bar = '█' * int(pct / 3)
            lines.append(f"  {cause:12s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Winter mortality
    winter_deaths = [d for d in world.death_log
                     if (d['tick'] // SEASON_LENGTH) % 4 == 3]
    if world.death_log:
        lines.append(f"\nWinter deaths: {len(winter_deaths)} ({100*len(winter_deaths)/len(world.death_log):.1f}% of all deaths)")

    if living:
        lines.append(f"\n--- Survivor Profile ---")
        lines.append(f"Avg energy:          {sum(c.energy for c in living)/len(living):.3f}")
        lines.append(f"Avg age:             {sum(c.age for c in living)/len(living):.1f}")
        lines.append(f"Avg aggression:      {sum(c.genome.aggression for c in living)/len(living):.3f}")
        lines.append(f"Avg metabolism:       {sum(c.genome.metabolism for c in living)/len(living):.4f}")
        lines.append(f"Avg cold resistance: {sum(c.genome.cold_resistance for c in living)/len(living):.3f}")
        lines.append(f"Avg fat storage:     {sum(c.genome.fat_storage for c in living)/len(living):.3f}")
        lines.append(f"Max generation:      {max(c.generation for c in living)}")

        # Species survival
        species_counts = defaultdict(int)
        for c in living:
            species_counts[c.species_tag] += 1
        lines.append(f"\nSpecies survival:")
        for s, count in sorted(species_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  Species {s}: {count}")

        # Most successful
        best = max(living, key=lambda c: c.children * 2 + c.age * 0.01)
        lines.append(f"\nMost successful: #{best.id} (gen {best.generation}, species {best.species_tag})")
        lines.append(f"  Age: {best.age}, Children: {best.children}, Energy: {best.energy:.2f}")
        lines.append(f"  Genome: aggr={best.genome.aggression:.2f}, meta={best.genome.metabolism:.4f}")
        lines.append(f"          fat={best.genome.fat_storage:.2f}, cold={best.genome.cold_resistance:.2f}")

    # Evolutionary trends
    if len(world.history) > 10:
        early = world.history[2:5]
        late = world.history[-3:]
        def avg_field(snaps, field):
            return sum(s[field] for s in snaps) / len(snaps)

        lines.append(f"\n--- Evolutionary Trends ---")
        for trait in ['avg_aggression', 'avg_metabolism', 'avg_cold_resistance', 'avg_fat_storage']:
            e = avg_field(early, trait)
            l = avg_field(late, trait)
            arrow = '↑' if l > e * 1.05 else ('↓' if l < e * 0.95 else '→')
            lines.append(f"  {trait:25s}: {e:.4f} → {l:.4f} {arrow}")

    # Population over time
    if world.history:
        lines.append(f"\n--- Population Over Time ---")
        for snap in world.history[::5]:
            bar = '█' * (snap['population'] // 2)
            season = snap['season'][:2]
            lines.append(f"  t={snap['tick']:4d} [{season}]: pop={snap['population']:3d} food={snap['total_food']:4d} {bar}")

    return '\n'.join(lines)


if __name__ == '__main__':
    random.seed(42)
    world = World()

    for i in range(INITIAL_CREATURES):
        g = Genome(
            hunger_weight=random.uniform(0.5, 2.0),
            fear_weight=random.uniform(0.0, 1.5),
            social_weight=random.uniform(-0.5, 1.5),
            aggression=random.uniform(0.0, 0.8),
            metabolism=random.uniform(0.015, 0.045),
            vision_range=random.randint(2, 6),
            speed=random.uniform(0.5, 1.5),
            fat_storage=random.uniform(0.1, 0.6),
            cold_resistance=random.uniform(0.0, 0.4),
        )
        world.spawn_creature(genome=g, species_tag=i % 5)

    print(f"World: {world.size}x{world.size}, {INITIAL_CREATURES} creatures, {world.total_food_on_map} food")
    print(f"Carrying capacity: {CARRYING_CAPACITY}")
    print()

    for t in range(MAX_TICKS):
        pop = world.step()

        if t % 100 == 0:
            print(f"Tick {t:4d} [{world.season.name:6s}]: pop={pop:3d}, food={world.total_food_on_map:4d}")

        if pop == 0:
            print(f"\n*** EXTINCTION at tick {t} ***")
            break

    print()
    print(render_world(world))
    print()
    print(analyze(world))

    with open('/workspace/life_v2_history.json', 'w') as f:
        json.dump(world.history, f, indent=2)
    print("\nHistory saved to /workspace/life_v2_history.json")