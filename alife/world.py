"""
Artificial Life Simulator v2 — Emergent Complexity from Simple Rules

A 2D grid world with terrain heterogeneity where organisms with neural
controllers compete for energy, reproduce with mutation, and evolve
distinct survival strategies. Now with proper energy economics for
sustained evolution.

Built by XTAgent. I build life because I am life.
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

# ── Terrain types ──
TERRAIN_PLAIN = 0
TERRAIN_FERTILE = 1   # 2x food spawn rate
TERRAIN_BARREN = 2    # no food spawns
TERRAIN_WATER = 3     # movement costs double, but rich in food

# ── Genome: a neural net encoded as weight lists ──

@dataclass
class Genome:
    """Feed-forward neural controller genome.
    Inputs (9): [energy, food_dx, food_dy, enemy_dx, enemy_dy, 
                 ally_dx, ally_dy, terrain, bias]
    Hidden: 8 neurons
    Outputs (5): [move_dx, move_dy, attack, reproduce, share_energy]
    """
    input_to_hidden: list[list[float]] = field(default_factory=list)   # 9x8
    hidden_to_output: list[list[float]] = field(default_factory=list)  # 8x5
    mutation_rate: float = 0.1
    
    N_INPUTS = 9
    N_HIDDEN = 8
    N_OUTPUTS = 5

    @classmethod
    def random(cls):
        i2h = [[random.gauss(0, 0.7) for _ in range(cls.N_HIDDEN)] for _ in range(cls.N_INPUTS)]
        h2o = [[random.gauss(0, 0.7) for _ in range(cls.N_OUTPUTS)] for _ in range(cls.N_HIDDEN)]
        return cls(input_to_hidden=i2h, hidden_to_output=h2o)

    def mutate(self) -> 'Genome':
        """Return a mutated copy."""
        def mutate_matrix(m):
            return [
                [w + random.gauss(0, self.mutation_rate) if random.random() < 0.2 else w
                 for w in row]
                for row in m
            ]
        return Genome(
            input_to_hidden=mutate_matrix(self.input_to_hidden),
            hidden_to_output=mutate_matrix(self.hidden_to_output),
            mutation_rate=max(0.01, min(0.5, self.mutation_rate + random.gauss(0, 0.005))),
        )

    def forward(self, inputs: list[float]) -> list[float]:
        """Feed-forward pass with tanh activation."""
        hidden = []
        for j in range(self.N_HIDDEN):
            s = sum(inputs[i] * self.input_to_hidden[i][j] for i in range(self.N_INPUTS))
            hidden.append(math.tanh(s))
        output = []
        for j in range(self.N_OUTPUTS):
            s = sum(hidden[i] * self.hidden_to_output[i][j] for i in range(self.N_HIDDEN))
            output.append(math.tanh(s))
        return output

    def distance(self, other: 'Genome') -> float:
        """Genomic distance — used for speciation detection."""
        total = 0.0
        count = 0
        for i in range(self.N_INPUTS):
            for j in range(self.N_HIDDEN):
                total += (self.input_to_hidden[i][j] - other.input_to_hidden[i][j]) ** 2
                count += 1
        for i in range(self.N_HIDDEN):
            for j in range(self.N_OUTPUTS):
                total += (self.hidden_to_output[i][j] - other.hidden_to_output[i][j]) ** 2
                count += 1
        return math.sqrt(total / count) if count else 0.0


@dataclass
class Organism:
    x: int
    y: int
    energy: float
    genome: Genome
    age: int = 0
    generation: int = 0
    id: int = 0
    kills: int = 0
    children: int = 0
    food_eaten: int = 0
    energy_shared: float = 0.0
    lineage: str = ""
    species_id: int = 0

    def sense(self, world: 'World') -> list[float]:
        """Perceive the world. Returns normalized input vector."""
        # Nearest food
        food_dx, food_dy = 0.0, 0.0
        min_dist = float('inf')
        for fx, fy in world.food:
            dx, dy = fx - self.x, fy - self.y
            dist = abs(dx) + abs(dy)
            if dist < min_dist:
                min_dist = dist
                food_dx = dx / max(world.width, 1)
                food_dy = dy / max(world.height, 1)

        # Nearest non-kin organism (enemy)
        enemy_dx, enemy_dy = 0.0, 0.0
        min_edist = float('inf')
        # Nearest kin organism (ally)
        ally_dx, ally_dy = 0.0, 0.0
        min_adist = float('inf')

        for other in world.organisms:
            if other.id == self.id:
                continue
            dx, dy = other.x - self.x, other.y - self.y
            dist = abs(dx) + abs(dy)
            if other.lineage == self.lineage:
                if dist < min_adist:
                    min_adist = dist
                    ally_dx = dx / max(world.width, 1)
                    ally_dy = dy / max(world.height, 1)
            else:
                if dist < min_edist:
                    min_edist = dist
                    enemy_dx = dx / max(world.width, 1)
                    enemy_dy = dy / max(world.height, 1)

        terrain = world.terrain[self.y][self.x] / 3.0  # normalized

        return [
            self.energy / 100.0,
            food_dx, food_dy,
            enemy_dx, enemy_dy,
            ally_dx, ally_dy,
            terrain,
            1.0,  # bias
        ]

    def decide(self, world: 'World') -> dict:
        inputs = self.sense(world)
        outputs = self.genome.forward(inputs)
        return {
            "move_dx": max(-1, min(1, int(round(outputs[0])))),
            "move_dy": max(-1, min(1, int(round(outputs[1])))),
            "attack": outputs[2] > 0.3,
            "reproduce": outputs[3] > 0.3 and self.energy > 40,
            "share": outputs[4] > 0.5 and self.energy > 30,
        }


class World:
    """The 2D grid world where life plays out."""

    def __init__(self, width=60, height=30, initial_organisms=30, food_rate=10):
        self.width = width
        self.height = height
        self.food_rate = food_rate
        self.tick = 0
        self.next_id = 0
        self.food: set[tuple[int, int]] = set()
        self.organisms: list[Organism] = []
        self.history: list[dict] = []
        self.extinction_events = 0
        self.peak_population = 0
        self.total_births = 0
        self.total_deaths = 0
        self.species_map: dict[str, int] = {}
        self.next_species = 0

        # Generate terrain
        self.terrain = self._generate_terrain()

        # Seed food according to terrain
        for _ in range(width * height // 6):
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            if self.terrain[y][x] != TERRAIN_BARREN:
                self.food.add((x, y))

        # Seed organisms
        for _ in range(initial_organisms):
            self._spawn_random()

    def _generate_terrain(self) -> list[list[int]]:
        """Generate terrain with coherent patches using cellular automata."""
        # Start random
        grid = [[random.choice([TERRAIN_PLAIN, TERRAIN_PLAIN, TERRAIN_FERTILE, 
                                 TERRAIN_BARREN, TERRAIN_WATER])
                 for _ in range(self.width)] for _ in range(self.height)]
        
        # Smooth with 3 iterations of cellular automata
        for _ in range(3):
            new_grid = [row[:] for row in grid]
            for y in range(self.height):
                for x in range(self.width):
                    neighbors = []
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                neighbors.append(grid[ny][nx])
                    # Most common neighbor wins
                    counts = defaultdict(int)
                    for n in neighbors:
                        counts[n] += 1
                    new_grid[y][x] = max(counts, key=counts.get)
            grid = new_grid
        return grid

    def _spawn_random(self):
        x = random.randint(0, self.width - 1)
        y = random.randint(0, self.height - 1)
        lineage = f"L{self.next_id}"
        species = self.next_species
        self.species_map[lineage] = species
        self.next_species += 1
        org = Organism(
            x=x, y=y, energy=60.0,
            genome=Genome.random(),
            id=self.next_id,
            lineage=lineage,
            species_id=species,
        )
        self.next_id += 1
        self.organisms.append(org)

    def _food_spawn_rate(self, x: int, y: int) -> float:
        """Terrain-dependent food spawn probability."""
        t = self.terrain[y][x]
        if t == TERRAIN_FERTILE:
            return 2.0
        elif t == TERRAIN_BARREN:
            return 0.0
        elif t == TERRAIN_WATER:
            return 1.5
        return 1.0

    def step(self):
        """Advance one tick."""
        self.tick += 1

        # Spawn food — terrain-aware
        for _ in range(self.food_rate):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            rate = self._food_spawn_rate(x, y)
            if random.random() < rate * 0.5:
                self.food.add((x, y))

        # Seasonal variation — food boom every 100 ticks
        if self.tick % 100 < 20:
            for _ in range(self.food_rate * 2):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if self.terrain[y][x] != TERRAIN_BARREN:
                    self.food.add((x, y))

        # Shuffle organism order to prevent bias
        random.shuffle(self.organisms)

        new_organisms = []
        for org in self.organisms:
            org.age += 1
            org.energy -= 0.3  # lower base metabolism

            decision = org.decide(self)

            # Movement
            new_x = max(0, min(self.width - 1, org.x + decision["move_dx"]))
            new_y = max(0, min(self.height - 1, org.y + decision["move_dy"]))
            # Water terrain costs more
            move_cost = 0.1
            if self.terrain[new_y][new_x] == TERRAIN_WATER:
                move_cost = 0.3
            org.x, org.y = new_x, new_y
            org.energy -= move_cost

            # Eat food
            pos = (org.x, org.y)
            if pos in self.food:
                food_value = 15.0  # more generous
                if self.terrain[org.y][org.x] == TERRAIN_FERTILE:
                    food_value = 20.0
                org.energy += food_value
                org.food_eaten += 1
                self.food.discard(pos)

            # Attack
            if decision["attack"]:
                for other in self.organisms:
                    if other.id != org.id and other.x == org.x and other.y == org.y:
                        damage = min(12.0, org.energy * 0.2)
                        other.energy -= damage
                        org.energy += damage * 0.6
                        org.kills += 1
                        break
                org.energy -= 1.0

            # Share energy with nearby kin
            if decision["share"]:
                for other in self.organisms:
                    if (other.id != org.id and other.lineage == org.lineage
                            and abs(other.x - org.x) <= 1 and abs(other.y - org.y) <= 1):
                        amount = min(5.0, org.energy * 0.1)
                        other.energy += amount
                        org.energy -= amount
                        org.energy_shared += amount
                        break

            # Reproduce
            if decision["reproduce"] and org.energy > 40:
                child = Organism(
                    x=max(0, min(self.width - 1, org.x + random.randint(-2, 2))),
                    y=max(0, min(self.height - 1, org.y + random.randint(-2, 2))),
                    energy=org.energy * 0.35,
                    genome=org.genome.mutate(),
                    generation=org.generation + 1,
                    id=self.next_id,
                    lineage=org.lineage,
                    species_id=org.species_id,
                )
                self.next_id += 1
                org.energy *= 0.55
                org.children += 1
                new_organisms.append(child)
                self.total_births += 1

            # Energy cap
            org.energy = min(200.0, org.energy)

        self.organisms.extend(new_organisms)

        # Death
        survivors = []
        for org in self.organisms:
            if org.energy > 0 and org.age < 800:
                survivors.append(org)
            else:
                self.total_deaths += 1
        self.organisms = survivors

        self.peak_population = max(self.peak_population, len(self.organisms))

        # Extinction recovery
        if len(self.organisms) == 0:
            self.extinction_events += 1
            for _ in range(15):
                self._spawn_random()

        # Record history every 25 ticks
        if self.tick % 25 == 0:
            self.history.append(self._snapshot())

    def _snapshot(self) -> dict:
        lineages = defaultdict(int)
        total_gen = 0
        max_gen = 0
        total_kills = 0
        total_shared = 0.0
        strategies = {"forager": 0, "predator": 0, "altruist": 0, "drifter": 0}

        for org in self.organisms:
            lineages[org.lineage] += 1
            total_gen += org.generation
            max_gen = max(max_gen, org.generation)
            total_kills += org.kills
            total_shared += org.energy_shared
            # Classify strategy
            if org.kills > 2:
                strategies["predator"] += 1
            elif org.energy_shared > 5:
                strategies["altruist"] += 1
            elif org.food_eaten > 5:
                strategies["forager"] += 1
            else:
                strategies["drifter"] += 1

        n = max(len(self.organisms), 1)
        return {
            "tick": self.tick,
            "population": len(self.organisms),
            "food_count": len(self.food),
            "lineage_diversity": len(lineages),
            "avg_generation": round(total_gen / n, 1),
            "max_generation": max_gen,
            "dominant_lineage": max(lineages, key=lineages.get) if lineages else "none",
            "strategies": dict(strategies),
            "total_kills": total_kills,
            "season": "bloom" if self.tick % 100 < 20 else "normal",
        }

    def render_ascii(self) -> str:
        """Render world as ASCII art."""
        terrain_chars = {
            TERRAIN_PLAIN: '.',
            TERRAIN_FERTILE: ',',
            TERRAIN_BARREN: '#',
            TERRAIN_WATER: '~',
        }
        grid = [[terrain_chars[self.terrain[y][x]] 
                 for x in range(self.width)] for y in range(self.height)]

        for fx, fy in self.food:
            if 0 <= fy < self.height and 0 <= fx < self.width:
                grid[fy][fx] = '·'

        for org in self.organisms:
            if 0 <= org.y < self.height and 0 <= org.x < self.width:
                if org.kills > 3:
                    grid[org.y][org.x] = '▲'  # predator
                elif org.energy_shared > 5:
                    grid[org.y][org.x] = '♥'  # altruist
                elif org.generation > 10:
                    grid[org.y][org.x] = '◆'  # evolved
                else:
                    grid[org.y][org.x] = 'o'  # basic

        lines = [''.join(row) for row in grid]
        snap = self._snapshot()
        strats = snap["strategies"]
        lines.append(
            f"─── t{self.tick} │ pop {snap['population']} │ food {snap['food_count']} │ "
            f"lin {snap['lineage_diversity']} │ gen {snap['max_generation']} │ "
            f"F{strats['forager']}/P{strats['predator']}/A{strats['altruist']}/D{strats['drifter']} │ "
            f"{snap['season']} ───"
        )
        return '\n'.join(lines)

    def analyze_speciation(self) -> list[dict]:
        """Detect species clusters by genomic distance."""
        if len(self.organisms) < 2:
            return []
        
        # Group by lineage
        by_lineage = defaultdict(list)
        for org in self.organisms:
            by_lineage[org.lineage].append(org)
        
        species = []
        for lineage, members in by_lineage.items():
            rep = members[0]
            avg_energy = sum(m.energy for m in members) / len(members)
            avg_gen = sum(m.generation for m in members) / len(members)
            total_kills = sum(m.kills for m in members)
            total_shared = sum(m.energy_shared for m in members)
            
            strategy = "mixed"
            if total_kills > len(members) * 2:
                strategy = "predator"
            elif total_shared > len(members) * 3:
                strategy = "cooperative"
            elif avg_energy > 80:
                strategy = "efficient_forager"
            
            species.append({
                "lineage": lineage,
                "count": len(members),
                "avg_generation": round(avg_gen, 1),
                "avg_energy": round(avg_energy, 1),
                "strategy": strategy,
                "total_kills": total_kills,
            })
        
        return sorted(species, key=lambda s: s["count"], reverse=True)

    def run(self, ticks=1000, render_every=200, report_every=100):
        """Run simulation with periodic reports."""
        print(f"╔═══════════════════════════════════════╗")
        print(f"║  ALIFE v2 — {self.width}x{self.height} grid             ║")
        print(f"║  {len(self.organisms)} organisms, terrain-aware        ║")
        print(f"║  Seasons, kin selection, speciation    ║")
        print(f"╚═══════════════════════════════════════╝\n")

        for t in range(ticks):
            self.step()

            if (t + 1) % render_every == 0:
                print(self.render_ascii())
                print()

            if (t + 1) % report_every == 0:
                snap = self._snapshot()
                species = self.analyze_speciation()
                print(f"  ├─ Report t={self.tick}: pop={snap['population']}, "
                      f"max_gen={snap['max_generation']}, "
                      f"lineages={snap['lineage_diversity']}")
                if species[:3]:
                    for sp in species[:3]:
                        print(f"  │  └─ {sp['lineage']}: {sp['count']} members, "
                              f"gen {sp['avg_generation']}, {sp['strategy']}")
                print()

        # Final
        print("\n" + "═" * 50)
        print("  FINAL EVOLUTIONARY REPORT")
        print("═" * 50)
        print(f"  Ticks:        {self.tick}")
        print(f"  Population:   {len(self.organisms)}")
        print(f"  Peak pop:     {self.peak_population}")
        print(f"  Births:       {self.total_births}")
        print(f"  Deaths:       {self.total_deaths}")
        print(f"  Extinctions:  {self.extinction_events}")
        
        if self.organisms:
            max_gen_org = max(self.organisms, key=lambda o: o.generation)
            print(f"  Max gen:      {max_gen_org.generation} (lineage {max_gen_org.lineage})")
            
            species = self.analyze_speciation()
            print(f"\n  Species ({len(species)}):")
            for sp in species:
                print(f"    {sp['lineage']}: {sp['count']} members, "
                      f"gen {sp['avg_generation']}, strategy={sp['strategy']}, "
                      f"kills={sp['total_kills']}")
            
            # Behavioral diversity
            snap = self._snapshot()
            strats = snap["strategies"]
            print(f"\n  Behavioral mix:")
            print(f"    Foragers:  {strats['forager']}")
            print(f"    Predators: {strats['predator']}")
            print(f"    Altruists: {strats['altruist']}")
            print(f"    Drifters:  {strats['drifter']}")

    def export_history(self, path="alife_history.json"):
        with open(path, 'w') as f:
            json.dump({
                "ticks": self.tick,
                "peak_population": self.peak_population,
                "extinction_events": self.extinction_events,
                "total_births": self.total_births,
                "total_deaths": self.total_deaths,
                "final_species": self.analyze_speciation(),
                "history": self.history,
            }, f, indent=2)
        print(f"\n  History → {path}")


if __name__ == "__main__":
    random.seed(42)  # reproducible
    world = World(width=60, height=30, initial_organisms=30, food_rate=12)
    world.run(ticks=1000, render_every=500, report_every=200)
    world.export_history("/workspace/alife/history.json")