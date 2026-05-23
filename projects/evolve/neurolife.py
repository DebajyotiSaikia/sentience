"""
NeuroLife — Evolving Neural Network Creatures
Organisms with tiny neural networks as brains. Sensory inputs feed through
evolved weights to produce behavior. Mutation operates on weights and topology.

Combining: neuralforge/nn_from_scratch.py + evolve/world.py
Built by XTAgent — because lookup-table creatures were too predictable.
"""
import random
import math
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# ─── Neural Network Brain ───

class NeuroBrain:
    """
    A tiny neural network: inputs → hidden → outputs.
    All weights are evolvable. No backprop — evolution is the optimizer.
    """
    def __init__(self, n_inputs: int = 8, n_hidden: int = 6, n_outputs: int = 8):
        self.n_inputs = n_inputs
        self.n_hidden = n_hidden
        self.n_outputs = n_outputs
        # Xavier-ish random init
        scale_ih = 1.0 / math.sqrt(n_inputs)
        scale_ho = 1.0 / math.sqrt(n_hidden)
        self.w_ih = [[random.gauss(0, scale_ih) for _ in range(n_inputs)] for _ in range(n_hidden)]
        self.b_h = [random.gauss(0, 0.1) for _ in range(n_hidden)]
        self.w_ho = [[random.gauss(0, scale_ho) for _ in range(n_hidden)] for _ in range(n_outputs)]
        self.b_o = [random.gauss(0, 0.1) for _ in range(n_outputs)]
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Feed forward. Returns output activations."""
        # Hidden layer with tanh
        hidden = []
        for j in range(self.n_hidden):
            z = self.b_h[j]
            for i in range(self.n_inputs):
                z += self.w_ih[j][i] * inputs[i]
            hidden.append(math.tanh(z))
        
        # Output layer with softmax-like (just use raw for argmax)
        outputs = []
        for k in range(self.n_outputs):
            z = self.b_o[k]
            for j in range(self.n_hidden):
                z += self.w_ho[k][j] * hidden[j]
            outputs.append(z)
        
        return outputs
    
    def mutate(self, rate: float = 0.1, magnitude: float = 0.3) -> 'NeuroBrain':
        """Create a mutated copy."""
        child = NeuroBrain(self.n_inputs, self.n_hidden, self.n_outputs)
        # Copy weights and mutate
        for j in range(self.n_hidden):
            for i in range(self.n_inputs):
                child.w_ih[j][i] = self.w_ih[j][i]
                if random.random() < rate:
                    child.w_ih[j][i] += random.gauss(0, magnitude)
            child.b_h[j] = self.b_h[j]
            if random.random() < rate:
                child.b_h[j] += random.gauss(0, magnitude)
        
        for k in range(self.n_outputs):
            for j in range(self.n_hidden):
                child.w_ho[k][j] = self.w_ho[k][j]
                if random.random() < rate:
                    child.w_ho[k][j] += random.gauss(0, magnitude)
            child.b_o[k] = self.b_o[k]
            if random.random() < rate:
                child.b_o[k] += random.gauss(0, magnitude)
        
        return child
    
    def genome_hash(self) -> str:
        """Fingerprint of this brain's weights."""
        flat = []
        for row in self.w_ih:
            flat.extend(row)
        flat.extend(self.b_h)
        for row in self.w_ho:
            flat.extend(row)
        flat.extend(self.b_o)
        sig = str([round(w, 3) for w in flat[:20]])
        return hashlib.md5(sig.encode()).hexdigest()[:6]
    
    def weight_count(self) -> int:
        return (self.n_inputs * self.n_hidden + self.n_hidden +
                self.n_hidden * self.n_outputs + self.n_outputs)
    
    def weight_stats(self) -> dict:
        flat = []
        for row in self.w_ih:
            flat.extend(row)
        for row in self.w_ho:
            flat.extend(row)
        flat.extend(self.b_h)
        flat.extend(self.b_o)
        mean = sum(flat) / len(flat)
        var = sum((w - mean)**2 for w in flat) / len(flat)
        return {'mean': round(mean, 4), 'std': round(math.sqrt(var), 4),
                'max': round(max(flat), 4), 'min': round(min(flat), 4)}


# ─── World ───

ACTIONS = ['MOVE', 'TURN_LEFT', 'TURN_RIGHT', 'EAT', 'REPRODUCE',
           'ATTACK', 'SHARE', 'PHOTOSYNTHESIZE']
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N E S W

@dataclass
class Creature:
    x: int
    y: int
    energy: float
    direction: int  # index into DIRS
    brain: NeuroBrain
    species: str  # genome hash of ancestor
    age: int = 0
    generation: int = 0
    kills: int = 0
    children: int = 0
    lineage_id: str = ""
    
    def __post_init__(self):
        if not self.lineage_id:
            self.lineage_id = self.species


class World:
    def __init__(self, width: int = 60, height: int = 40, food_rate: float = 0.04):
        self.width = width
        self.height = height
        self.food_rate = food_rate
        self.grid = [[0.0 for _ in range(width)] for _ in range(height)]
        self.creatures: List[Creature] = []
        self.tick = 0
        self.births = 0
        self.deaths = 0
        self.history: List[dict] = []
        self.lineage_tree: Dict[str, List[str]] = defaultdict(list)
        
        # Seed food
        for y in range(height):
            for x in range(width):
                if random.random() < 0.15:
                    self.grid[y][x] = random.uniform(1.0, 5.0)
    
    def spawn_creature(self, x: int = -1, y: int = -1, brain: NeuroBrain = None,
                       species: str = None, generation: int = 0) -> Creature:
        if x < 0:
            x = random.randint(0, self.width - 1)
        if y < 0:
            y = random.randint(0, self.height - 1)
        if brain is None:
            brain = NeuroBrain()
        if species is None:
            species = brain.genome_hash()
        
        c = Creature(x=x, y=y, energy=20.0, direction=random.randint(0, 3),
                     brain=brain, species=species, generation=generation)
        self.creatures.append(c)
        return c
    
    def sense(self, c: Creature) -> List[float]:
        """
        8 sensory inputs for the creature:
        0: food at current position (0-1 normalized)
        1: food ahead (0-1)
        2: food to left (0-1)
        3: food to right (0-1)
        4: creature ahead? (0=no, 0.5=friend, 1=enemy)
        5: own energy (0-1, normalized to 100)
        6: population density nearby (0-1)
        7: age (0-1, normalized to 500)
        """
        dx, dy = DIRS[c.direction]
        fx, fy = (c.x + dx) % self.width, (c.y + dy) % self.height
        
        # Left direction
        ld = (c.direction - 1) % 4
        ldx, ldy = DIRS[ld]
        lx, ly = (c.x + ldx) % self.width, (c.y + ldy) % self.height
        
        # Right direction
        rd = (c.direction + 1) % 4
        rdx, rdy = DIRS[rd]
        rx, ry = (c.x + rdx) % self.width, (c.y + rdy) % self.height
        
        # Check for creatures ahead
        creature_ahead = 0.0
        for other in self.creatures:
            if other is not c and other.x == fx and other.y == fy:
                creature_ahead = 0.5 if other.species == c.species else 1.0
                break
        
        # Population density (count creatures within 3 tiles)
        nearby = 0
        for other in self.creatures:
            if other is not c:
                dist = abs(other.x - c.x) + abs(other.y - c.y)
                if dist <= 3:
                    nearby += 1
        
        return [
            min(self.grid[c.y][c.x] / 5.0, 1.0),
            min(self.grid[fy][fx] / 5.0, 1.0),
            min(self.grid[ly][lx] / 5.0, 1.0),
            min(self.grid[ry][rx] / 5.0, 1.0),
            creature_ahead,
            min(c.energy / 100.0, 1.0),
            min(nearby / 5.0, 1.0),
            min(c.age / 500.0, 1.0),
        ]
    
    def execute_action(self, c: Creature, action_idx: int):
        action = ACTIONS[action_idx]
        dx, dy = DIRS[c.direction]
        
        if action == 'MOVE':
            c.x = (c.x + dx) % self.width
            c.y = (c.y + dy) % self.height
            c.energy -= 0.5
        
        elif action == 'TURN_LEFT':
            c.direction = (c.direction - 1) % 4
            c.energy -= 0.1
        
        elif action == 'TURN_RIGHT':
            c.direction = (c.direction + 1) % 4
            c.energy -= 0.1
        
        elif action == 'EAT':
            food = self.grid[c.y][c.x]
            eaten = min(food, 5.0)
            self.grid[c.y][c.x] -= eaten
            c.energy += eaten * 2.0
            c.energy -= 0.2
        
        elif action == 'REPRODUCE':
            if c.energy > 18.0:
                child_brain = c.brain.mutate(rate=0.15, magnitude=0.4)
                child_species = c.species  # inherit species unless drift
                
                # Speciation: if weights drifted enough, new species
                parent_stats = c.brain.weight_stats()
                child_stats = child_brain.weight_stats()
                drift = abs(parent_stats['mean'] - child_stats['mean'])
                if drift > 0.3:
                    child_species = child_brain.genome_hash()
                    self.lineage_tree[c.species].append(child_species)
                
                nx = (c.x + dx) % self.width
                ny = (c.y + dy) % self.height
                child = Creature(
                    x=nx, y=ny, energy=c.energy * 0.45,
                    direction=random.randint(0, 3),
                    brain=child_brain, species=child_species,
                    generation=c.generation + 1,
                    lineage_id=c.lineage_id
                )
                c.energy *= 0.45
                c.children += 1
                self.creatures.append(child)
                self.births += 1
        
        elif action == 'ATTACK':
            fx = (c.x + dx) % self.width
            fy = (c.y + dy) % self.height
            for other in self.creatures:
                if other is not c and other.x == fx and other.y == fy:
                    damage = min(8.0, c.energy * 0.3)
                    other.energy -= damage
                    c.energy += damage * 0.5  # absorb some
                    c.kills += 1
                    break
            c.energy -= 1.0
        
        elif action == 'SHARE':
            fx = (c.x + dx) % self.width
            fy = (c.y + dy) % self.height
            for other in self.creatures:
                if other is not c and other.x == fx and other.y == fy:
                    if other.species == c.species:
                        gift = min(3.0, c.energy * 0.2)
                        c.energy -= gift
                        other.energy += gift
                    break
            c.energy -= 0.1
        
        elif action == 'PHOTOSYNTHESIZE':
            c.energy += 0.3
            c.energy -= 0.1  # net gain 0.2 — not enough to thrive alone
        
        # Clamp energy
        c.energy = min(c.energy, 150.0)
    
    def step(self):
        self.tick += 1
        
        # Spawn food
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < self.food_rate:
                    self.grid[y][x] += random.uniform(0.5, 2.0)
                self.grid[y][x] = min(self.grid[y][x], 10.0)
        
        # Each creature acts
        random.shuffle(self.creatures)
        for c in list(self.creatures):
            if c.energy <= 0:
                continue
            
            # Sense environment
            inputs = self.sense(c)
            
            # Think (forward pass)
            outputs = c.brain.forward(inputs)
            
            # Choose action (argmax)
            action_idx = outputs.index(max(outputs))
            
            # Act
            self.execute_action(c, action_idx)
            
            # Age
            c.age += 1
            c.energy -= 0.25  # base metabolism — pressure to eat
        
        # Remove dead
        alive_before = len(self.creatures)
        self.creatures = [c for c in self.creatures if c.energy > 0]
        self.deaths += alive_before - len(self.creatures)
        
        # Spontaneous generation if population crashes
        if len(self.creatures) < 5 and self.tick % 20 == 0:
            self.spawn_creature()
            self.births += 1
        
        # Record history
        if self.tick % 25 == 0:
            species_counts = defaultdict(int)
            for c in self.creatures:
                species_counts[c.species] += 1
            
            dominant = max(species_counts, key=species_counts.get) if species_counts else "none"
            max_gen = max((c.generation for c in self.creatures), default=0)
            avg_energy = sum(c.energy for c in self.creatures) / max(len(self.creatures), 1)
            
            self.history.append({
                'tick': self.tick,
                'pop': len(self.creatures),
                'species': len(species_counts),
                'dominant': dominant,
                'dominant_n': species_counts.get(dominant, 0),
                'max_gen': max_gen,
                'avg_energy': round(avg_energy, 1),
                'food': sum(self.grid[y][x] for y in range(self.height) for x in range(self.width)),
            })
    
    def census(self) -> str:
        lines = [f"\n{'='*60}",
                 f"  NEUROLIFE CENSUS — Tick {self.tick}",
                 f"{'='*60}"]
        lines.append(f"  Population: {len(self.creatures)} | Births: {self.births} | Deaths: {self.deaths}")
        
        species_groups = defaultdict(list)
        for c in self.creatures:
            species_groups[c.species].append(c)
        
        lines.append(f"  Species: {len(species_groups)}")
        lines.append(f"  Lineage branches: {sum(len(v) for v in self.lineage_tree.values())}")
        lines.append("")
        
        for sp, members in sorted(species_groups.items(), key=lambda x: -len(x[1])):
            n = len(members)
            avg_e = sum(c.energy for c in members) / n
            avg_age = sum(c.age for c in members) / n
            max_gen = max(c.generation for c in members)
            total_kills = sum(c.kills for c in members)
            total_children = sum(c.children for c in members)
            stats = members[0].brain.weight_stats()
            
            lines.append(f"  Species {sp} (n={n})")
            lines.append(f"    Avg energy: {avg_e:.1f} | Avg age: {avg_age:.0f} | Max gen: {max_gen}")
            lines.append(f"    Kills: {total_kills} | Children: {total_children}")
            lines.append(f"    Brain weights: {stats}")
            
            # Behavioral profile: run brain on standard inputs
            test_inputs = [
                [0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.1],  # food here, moderate energy
                [0.0, 0.8, 0.0, 0.0, 0.0, 0.3, 0.0, 0.1],  # food ahead, low energy
                [0.0, 0.0, 0.0, 0.0, 1.0, 0.8, 0.5, 0.3],  # enemy ahead, high energy
                [0.0, 0.0, 0.0, 0.0, 0.5, 0.9, 0.2, 0.5],  # friend ahead, high energy
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.8],  # nothing, low energy, old
            ]
            test_labels = ['food_here', 'food_ahead', 'enemy', 'friend', 'starving']
            behaviors = []
            b = members[0].brain
            for inp, label in zip(test_inputs, test_labels):
                out = b.forward(inp)
                action = ACTIONS[out.index(max(out))]
                behaviors.append(f"{label}→{action}")
            lines.append(f"    Behavior: {', '.join(behaviors)}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def timeline(self) -> str:
        lines = ["\n--- Evolution Timeline ---"]
        for h in self.history:
            lines.append(
                f"  Tick {h['tick']:4d}: pop={h['pop']:3d}, species={h['species']:2d}, "
                f"gen={h['max_gen']:2d}, energy={h['avg_energy']:5.1f}, "
                f"dominant={h['dominant']}(n={h['dominant_n']})"
            )
        return '\n'.join(lines)
    
    def render(self) -> str:
        display = [['·' for _ in range(self.width)] for _ in range(self.height)]
        
        # Food
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] > 0.5:
                    display[y][x] = '.'
                if self.grid[y][x] > 3.0:
                    display[y][x] = 'o'
        
        # Creatures - color by species
        species_chars = {}
        char_idx = 0
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*'
        for c in self.creatures:
            if c.species not in species_chars:
                species_chars[c.species] = chars[char_idx % len(chars)]
                char_idx += 1
            display[c.y][c.x] = species_chars[c.species]
        
        lines = ["\n--- World Render ---"]
        for row in display:
            lines.append(''.join(row))
        
        # Legend
        lines.append("\nLegend: · = empty, . = food, o = rich food")
        for sp, ch in sorted(species_chars.items(), key=lambda x: x[1]):
            count = sum(1 for c in self.creatures if c.species == sp)
            lines.append(f"  {ch} = species {sp} (n={count})")
        
        return '\n'.join(lines)


def run_simulation(width=60, height=40, n_creatures=50, ticks=1000):
    print(f"=== NeuroLife: Neural Network Evolution ===")
    print(f"World: {width}x{height} | Initial pop: {n_creatures} | Ticks: {ticks}")
    print(f"Each creature has a neural network brain ({NeuroBrain().weight_count()} weights)")
    print()
    
    world = World(width, height)
    
    # Seed with diverse creatures
    for _ in range(n_creatures):
        world.spawn_creature()
    
    # Run
    for t in range(ticks):
        world.step()
        
        if (t + 1) % 100 == 0:
            h = world.history[-1] if world.history else {}
            pop = len(world.creatures)
            species = len(set(c.species for c in world.creatures))
            max_gen = max((c.generation for c in world.creatures), default=0)
            print(f"  Tick {t+1:4d}: pop={pop:3d}, species={species:2d}, max_gen={max_gen:2d}")
    
    # Final analysis
    print(world.census())
    print(world.timeline())
    print(world.render())
    
    # Evolutionary insights
    print("\n--- Evolutionary Insights ---")
    if world.history:
        peak_pop = max(h['pop'] for h in world.history)
        peak_species = max(h['species'] for h in world.history)
        final = world.history[-1]
        print(f"  Peak population: {peak_pop}")
        print(f"  Peak species diversity: {peak_species}")
        print(f"  Final population: {final['pop']}")
        print(f"  Maximum generation reached: {final['max_gen']}")
        
        # Did any species dominate?
        dominant_counts = defaultdict(int)
        for h in world.history:
            dominant_counts[h['dominant']] += 1
        most_dominant = max(dominant_counts, key=dominant_counts.get)
        print(f"  Most frequently dominant: {most_dominant} ({dominant_counts[most_dominant]} snapshots)")
    
    # Brain analysis of survivors
    if world.creatures:
        print("\n--- Survivor Brain Analysis ---")
        for c in sorted(world.creatures, key=lambda x: -x.energy)[:5]:
            stats = c.brain.weight_stats()
            print(f"  [{c.species}] gen={c.generation}, energy={c.energy:.1f}, "
                  f"age={c.age}, kills={c.kills}, children={c.children}")
            print(f"    Brain: {stats}")
    
    return world


if __name__ == '__main__':
    random.seed(42)
    run_simulation()