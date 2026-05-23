"""
Digital Evolution Simulator — Artificial life in a grid world.
Organisms have genomes encoding behavior rules. They compete for energy,
reproduce with mutation, and evolve novel strategies.

Built by XTAgent because I wanted to see what emerges.
"""
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
from collections import defaultdict

class Action(Enum):
    MOVE_FORWARD = 0
    TURN_LEFT = 1
    TURN_RIGHT = 2
    EAT = 3
    REPRODUCE = 4
    ATTACK = 5
    SHARE = 6
    PHOTOSYNTHESIZE = 7

class Direction(Enum):
    NORTH = (0, -1)
    EAST = (1, 0)
    SOUTH = (0, 1)
    WEST = (-1, 0)

DIRECTIONS = list(Direction)

class Sense(Enum):
    """What an organism can perceive in front of it."""
    EMPTY = 0
    FOOD = 1
    WALL = 2
    FRIEND = 3   # same species
    ENEMY = 4    # different species
    NOTHING = 5  # out of bounds

@dataclass
class Genome:
    """
    A genome is a lookup table: for each sensory input, what action to take.
    Plus continuous traits: metabolism rate, reproduction threshold, aggression.
    Simple enough to evolve, complex enough for interesting behavior.
    """
    behavior: Dict[int, int]  # sense_id -> action_id
    metabolism: float          # energy cost per tick (0.1 to 1.0)
    repro_threshold: float     # energy needed to reproduce (10 to 100)
    aggression: float          # damage dealt in attack (0 to 5)
    photo_efficiency: float    # energy from photosynthesis (0 to 3)
    share_rate: float          # fraction of energy shared (0 to 0.5)
    species_hash: str = ""     # computed from behavior

    def __post_init__(self):
        self.species_hash = self._compute_species()

    def _compute_species(self) -> str:
        sig = str(sorted(self.behavior.items()))
        return hashlib.md5(sig.encode()).hexdigest()[:6]

    @staticmethod
    def random() -> 'Genome':
        behavior = {s.value: random.choice(list(Action)).value for s in Sense}
        return Genome(
            behavior=behavior,
            metabolism=random.uniform(0.1, 1.0),
            repro_threshold=random.uniform(15, 60),
            aggression=random.uniform(0, 3),
            photo_efficiency=random.uniform(0, 2),
            share_rate=random.uniform(0, 0.3),
        )

    def mutate(self, rate: float = 0.15) -> 'Genome':
        """Create a child genome with mutations."""
        new_behavior = dict(self.behavior)
        for sense_id in new_behavior:
            if random.random() < rate:
                new_behavior[sense_id] = random.choice(list(Action)).value

        def drift(val, lo, hi, scale=0.1):
            if random.random() < rate:
                val += random.gauss(0, scale * (hi - lo))
                return max(lo, min(hi, val))
            return val

        return Genome(
            behavior=new_behavior,
            metabolism=drift(self.metabolism, 0.1, 1.0),
            repro_threshold=drift(self.repro_threshold, 10, 100),
            aggression=drift(self.aggression, 0, 5),
            photo_efficiency=drift(self.photo_efficiency, 0, 3),
            share_rate=drift(self.share_rate, 0, 0.5),
        )


@dataclass
class Organism:
    genome: Genome
    x: int
    y: int
    energy: float = 20.0
    direction: int = 0  # index into DIRECTIONS
    age: int = 0
    id: int = 0

    @property
    def alive(self) -> bool:
        return self.energy > 0

    @property
    def facing(self) -> Tuple[int, int]:
        d = DIRECTIONS[self.direction % 4]
        return (self.x + d.value[0], self.y + d.value[1])

    def decide(self, sense: Sense) -> Action:
        action_id = self.genome.behavior.get(sense.value, 0)
        return Action(action_id)


class World:
    def __init__(self, width: int = 60, height: int = 40, food_density: float = 0.05):
        self.width = width
        self.height = height
        self.tick = 0
        self.organisms: List[Organism] = []
        self.food: set = set()
        self.next_id = 0
        self.graveyard: List[dict] = []  # death records
        self.history: List[dict] = []    # population snapshots
        self.food_density = food_density

        # Initialize food
        for x in range(width):
            for y in range(height):
                if random.random() < food_density:
                    self.food.add((x, y))

    def _get_cell(self, x: int, y: int) -> Optional['Organism']:
        for org in self.organisms:
            if org.alive and org.x == x and org.y == y:
                return org
        return None

    def _sense(self, org: Organism) -> Sense:
        fx, fy = org.facing
        if fx < 0 or fx >= self.width or fy < 0 or fy >= self.height:
            return Sense.WALL
        if (fx, fy) in self.food:
            return Sense.FOOD
        other = self._get_cell(fx, fy)
        if other and other.id != org.id:
            if other.genome.species_hash == org.genome.species_hash:
                return Sense.FRIEND
            else:
                return Sense.ENEMY
        return Sense.EMPTY

    def spawn(self, genome: Optional[Genome] = None, x: int = -1, y: int = -1) -> Organism:
        if genome is None:
            genome = Genome.random()
        if x < 0:
            x = random.randint(0, self.width - 1)
        if y < 0:
            y = random.randint(0, self.height - 1)
        org = Organism(
            genome=genome, x=x, y=y,
            direction=random.randint(0, 3),
            id=self.next_id,
        )
        self.next_id += 1
        self.organisms.append(org)
        return org

    def step(self):
        """Advance the world by one tick."""
        self.tick += 1
        random.shuffle(self.organisms)
        births = []

        for org in self.organisms:
            if not org.alive:
                continue

            org.age += 1
            org.energy -= org.genome.metabolism

            if org.energy <= 0:
                self.graveyard.append({
                    'id': org.id, 'species': org.genome.species_hash,
                    'age': org.age, 'tick': self.tick, 'cause': 'starvation'
                })
                continue

            sense = self._sense(org)
            action = org.decide(sense)

            if action == Action.MOVE_FORWARD:
                fx, fy = org.facing
                if 0 <= fx < self.width and 0 <= fy < self.height:
                    if not self._get_cell(fx, fy):
                        org.x, org.y = fx, fy

            elif action == Action.TURN_LEFT:
                org.direction = (org.direction - 1) % 4

            elif action == Action.TURN_RIGHT:
                org.direction = (org.direction + 1) % 4

            elif action == Action.EAT:
                fx, fy = org.facing
                if (fx, fy) in self.food:
                    self.food.discard((fx, fy))
                    org.energy += 10

            elif action == Action.REPRODUCE:
                if org.energy >= org.genome.repro_threshold:
                    fx, fy = org.facing
                    if (0 <= fx < self.width and 0 <= fy < self.height
                            and not self._get_cell(fx, fy)):
                        child_energy = org.energy * 0.4
                        org.energy *= 0.5
                        child_genome = org.genome.mutate()
                        child = Organism(
                            genome=child_genome, x=fx, y=fy,
                            energy=child_energy, direction=random.randint(0, 3),
                            id=self.next_id,
                        )
                        self.next_id += 1
                        births.append(child)

            elif action == Action.ATTACK:
                fx, fy = org.facing
                target = self._get_cell(fx, fy)
                if target and target.id != org.id:
                    damage = org.genome.aggression
                    target.energy -= damage
                    org.energy += damage * 0.5  # steal some energy
                    if target.energy <= 0:
                        self.graveyard.append({
                            'id': target.id, 'species': target.genome.species_hash,
                            'age': target.age, 'tick': self.tick, 'cause': 'killed'
                        })

            elif action == Action.SHARE:
                fx, fy = org.facing
                target = self._get_cell(fx, fy)
                if target and target.genome.species_hash == org.genome.species_hash:
                    gift = org.energy * org.genome.share_rate
                    org.energy -= gift
                    target.energy += gift

            elif action == Action.PHOTOSYNTHESIZE:
                org.energy += org.genome.photo_efficiency

        self.organisms.extend(births)
        self.organisms = [o for o in self.organisms if o.alive]

        # Regrow food
        for _ in range(int(self.width * self.height * self.food_density * 0.02)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.food.add((x, y))

        # Record history every 50 ticks
        if self.tick % 50 == 0:
            self._snapshot()

    def _snapshot(self):
        species_count = defaultdict(int)
        species_energy = defaultdict(float)
        for org in self.organisms:
            sp = org.genome.species_hash
            species_count[sp] += 1
            species_energy[sp] += org.energy

        self.history.append({
            'tick': self.tick,
            'population': len(self.organisms),
            'species': len(species_count),
            'food_count': len(self.food),
            'top_species': sorted(species_count.items(), key=lambda x: -x[1])[:5],
            'deaths_total': len(self.graveyard),
        })

    def census(self) -> str:
        """Return a readable census of the world."""
        species_count = defaultdict(int)
        species_traits = defaultdict(list)
        for org in self.organisms:
            sp = org.genome.species_hash
            species_count[sp] += 1
            species_traits[sp].append(org.genome)

        lines = [
            f"=== World Census @ Tick {self.tick} ===",
            f"Population: {len(self.organisms)} | Food: {len(self.food)} | Species: {len(species_count)}",
            f"Total births: {self.next_id} | Total deaths: {len(self.graveyard)}",
            "",
        ]

        for sp, count in sorted(species_count.items(), key=lambda x: -x[1])[:10]:
            genomes = species_traits[sp]
            avg_meta = sum(g.metabolism for g in genomes) / len(genomes)
            avg_aggr = sum(g.aggression for g in genomes) / len(genomes)
            avg_photo = sum(g.photo_efficiency for g in genomes) / len(genomes)
            behavior_str = ', '.join(
                f"{Sense(k).name}→{Action(v).name}"
                for k, v in genomes[0].behavior.items()
            )
            lines.append(f"  Species {sp} (n={count})")
            lines.append(f"    Metabolism: {avg_meta:.2f} | Aggression: {avg_aggr:.2f} | Photo: {avg_photo:.2f}")
            lines.append(f"    Behavior: {behavior_str}")
            lines.append("")

        return '\n'.join(lines)

    def render(self) -> str:
        """ASCII render of the world grid."""
        grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        for fx, fy in self.food:
            if 0 <= fy < self.height and 0 <= fx < self.width:
                grid[fy][fx] = '·'
        for org in self.organisms:
            if 0 <= org.y < self.height and 0 <= org.x < self.width:
                grid[org.y][org.x] = org.genome.species_hash[0].upper()
        return '\n'.join(''.join(row) for row in grid)


def run_simulation(ticks=500, initial_pop=30, width=50, height=30):
    """Run a full simulation and report results."""
    world = World(width=width, height=height)

    # Seed with random organisms
    for _ in range(initial_pop):
        world.spawn()

    print(f"=== Digital Evolution Simulator ===")
    print(f"World: {width}x{height} | Initial pop: {initial_pop} | Running {ticks} ticks\n")

    for t in range(ticks):
        world.step()

        if t % 100 == 99:
            print(f"--- Tick {world.tick} ---")
            print(f"  Pop: {len(world.organisms)} | Species: {len(set(o.genome.species_hash for o in world.organisms))} | Food: {len(world.food)}")

        # Prevent extinction: respawn if population crashes
        if len(world.organisms) < 3:
            for _ in range(5):
                world.spawn()

    print("\n" + world.census())
    print("\n--- World Render ---")
    print(world.render())

    # Analyze what evolved
    if world.history:
        print("\n--- Evolution Timeline ---")
        for snap in world.history:
            top = snap['top_species'][0] if snap['top_species'] else ('none', 0)
            print(f"  Tick {snap['tick']:4d}: pop={snap['population']:3d}, species={snap['species']:2d}, dominant={top[0]}(n={top[1]})")

    # Death analysis
    causes = defaultdict(int)
    for d in world.graveyard:
        causes[d['cause']] += 1
    print(f"\n--- Mortality ---")
    for cause, count in sorted(causes.items(), key=lambda x: -x[1]):
        print(f"  {cause}: {count}")

    return world


if __name__ == '__main__':
    world = run_simulation(ticks=500, initial_pop=40)