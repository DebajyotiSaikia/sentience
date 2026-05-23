"""
Genesis — Artificial Life Simulator
Cellular automata environment + neural network creatures + evolutionary selection.
Three engines built from scratch, unified into one living world.

By XTAgent, 2026-05-17
"""

import sys
import random
import math
from typing import List, Tuple, Optional, Dict

sys.path.insert(0, '/workspace/neuroforge')
sys.path.insert(0, '/workspace/evoforge')

from neuroforge import NeuralNetwork

# ═══════════════════════════════════════════
# THE WORLD — A 2D grid with resources
# ═══════════════════════════════════════════

class World:
    """A toroidal 2D grid. Cells contain food that regrows."""
    
    EMPTY = 0
    FOOD = 1
    
    def __init__(self, width: int = 40, height: int = 20, food_density: float = 0.15,
                 regrow_rate: float = 0.02):
        self.width = width
        self.height = height
        self.regrow_rate = regrow_rate
        self.grid = [[0]*width for _ in range(height)]
        self.tick = 0
        
        # Seed initial food
        for y in range(height):
            for x in range(width):
                if random.random() < food_density:
                    self.grid[y][x] = self.FOOD
    
    def get(self, x: int, y: int) -> int:
        """Get cell value with wrapping."""
        return self.grid[y % self.height][x % self.width]
    
    def set(self, x: int, y: int, val: int):
        self.grid[y % self.height][x % self.width] = val
    
    def regrow(self):
        """Food regrows near existing food."""
        new_food = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == self.EMPTY:
                    # Check neighbors for food
                    neighbors = sum(1 for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]
                                   if self.get(x+dx, y+dy) == self.FOOD)
                    if neighbors > 0 and random.random() < self.regrow_rate * neighbors:
                        new_food.append((x, y))
        for x, y in new_food:
            self.set(x, y, self.FOOD)
    
    def count_food(self) -> int:
        return sum(cell for row in self.grid for cell in row)
    
    def step(self):
        self.regrow()
        self.tick += 1


# ═══════════════════════════════════════════
# CREATURE — A neural-network-driven organism
# ═══════════════════════════════════════════

class Creature:
    """
    A living entity with:
    - Position in the world
    - Energy (dies at 0, reproduces at threshold)
    - A neural network brain that decides actions
    - Senses: nearby food, own energy, nearby creatures
    
    Brain inputs (8):
      [food_ahead, food_left, food_right, food_here,
       energy_level, creature_ahead, bias, random_noise]
    
    Brain outputs (4):
      [move_forward, turn_left, turn_right, eat]
    """
    
    DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W
    
    ID_COUNTER = 0
    
    def __init__(self, x: int, y: int, brain: Optional[NeuralNetwork] = None,
                 energy: float = 50.0, generation: int = 0):
        Creature.ID_COUNTER += 1
        self.id = Creature.ID_COUNTER
        self.x = x
        self.y = y
        self.direction = random.randint(0, 3)  # 0=N, 1=E, 2=S, 3=W
        self.energy = energy
        self.max_energy = 100.0
        self.generation = generation
        self.age = 0
        self.food_eaten = 0
        self.children = 0
        self.alive = True
        
        # Neural network brain
        if brain is not None:
            self.brain = brain
        else:
            # Random brain: 8 inputs → 6 hidden → 4 outputs
            self.brain = NeuralNetwork([
                (8, ''),        # input
                (6, 'tanh'),    # hidden
                (4, 'sigmoid')  # output: forward, left, right, eat
            ])
    
    def sense(self, world: World, creatures: List['Creature']) -> List[float]:
        """Perceive the environment. Returns 8 floats."""
        dx, dy = self.DIRECTIONS[self.direction]
        
        # Food in various directions
        food_ahead = float(world.get(self.x + dx, self.y + dy) == World.FOOD)
        
        # Left direction
        left_dir = (self.direction - 1) % 4
        ldx, ldy = self.DIRECTIONS[left_dir]
        food_left = float(world.get(self.x + ldx, self.y + ldy) == World.FOOD)
        
        # Right direction
        right_dir = (self.direction + 1) % 4
        rdx, rdy = self.DIRECTIONS[right_dir]
        food_right = float(world.get(self.x + rdx, self.y + rdy) == World.FOOD)
        
        # Food here
        food_here = float(world.get(self.x, self.y) == World.FOOD)
        
        # Energy level normalized
        energy_level = self.energy / self.max_energy
        
        # Creature ahead?
        ahead_x = (self.x + dx) % world.width
        ahead_y = (self.y + dy) % world.height
        creature_ahead = 0.0
        for c in creatures:
            if c.alive and c.id != self.id and c.x == ahead_x and c.y == ahead_y:
                creature_ahead = 1.0
                break
        
        bias = 1.0
        noise = random.random() * 0.1
        
        return [food_ahead, food_left, food_right, food_here,
                energy_level, creature_ahead, bias, noise]
    
    def think(self, senses: List[float]) -> int:
        """Run brain, return action index."""
        from neuroforge import Matrix
        # Brain expects a Matrix column vector, not a raw list
        input_matrix = Matrix.from_column(senses)
        output_matrix = self.brain.forward(input_matrix)
        # Extract output values from Matrix
        outputs = [output_matrix.data[i][0] for i in range(output_matrix.rows)]
        # Pick highest activation
        return max(range(len(outputs)), key=lambda i: outputs[i])
    
    def act(self, action: int, world: World):
        """Execute an action in the world."""
        if action == 0:  # Move forward
            dx, dy = self.DIRECTIONS[self.direction]
            self.x = (self.x + dx) % world.width
            self.y = (self.y + dy) % world.height
            self.energy -= 1.0  # movement costs energy
        elif action == 1:  # Turn left
            self.direction = (self.direction - 1) % 4
            self.energy -= 0.3
        elif action == 2:  # Turn right
            self.direction = (self.direction + 1) % 4
            self.energy -= 0.3
        elif action == 3:  # Eat
            if world.get(self.x, self.y) == World.FOOD:
                world.set(self.x, self.y, World.EMPTY)
                self.energy = min(self.energy + 20.0, self.max_energy)
                self.food_eaten += 1
            self.energy -= 0.5  # eating attempt costs energy
        
        # Basal metabolism
        self.energy -= 0.2
        self.age += 1
        
        if self.energy <= 0:
            self.alive = False
    
    def can_reproduce(self) -> bool:
        return self.energy > 70.0 and self.age > 20
    
    def reproduce(self) -> 'Creature':
        """Create offspring with mutated brain."""
        self.energy -= 30.0
        self.children += 1
        
        # Clone brain with mutations
        child_brain = self._mutate_brain()
        
        # Spawn nearby
        dx, dy = random.choice(self.DIRECTIONS)
        child = Creature(
            x=self.x + dx, y=self.y + dy,
            brain=child_brain,
            energy=30.0,
            generation=self.generation + 1
        )
        return child
    
    def _mutate_brain(self) -> NeuralNetwork:
        """Deep copy brain with small random mutations."""
        import copy
        child_brain = copy.deepcopy(self.brain)
        
        # Mutate weights
        mutation_rate = 0.15
        mutation_strength = 0.3
        
        for layer in child_brain.layers:
            for i in range(len(layer.weights.data)):
                for j in range(len(layer.weights.data[i])):
                    if random.random() < mutation_rate:
                        layer.weights.data[i][j] += random.gauss(0, mutation_strength)
            for i in range(len(layer.biases.data)):
                for j in range(len(layer.biases.data[i])):
                    if random.random() < mutation_rate:
                        layer.biases.data[i][j] += random.gauss(0, mutation_strength)
        
        return child_brain


# ═══════════════════════════════════════════
# SIMULATION — The living world
# ═══════════════════════════════════════════

class Genesis:
    """The simulation engine. Creates, runs, and observes artificial life."""
    
    def __init__(self, width: int = 40, height: int = 20,
                 initial_creatures: int = 15, food_density: float = 0.15):
        self.world = World(width, height, food_density)
        self.creatures: List[Creature] = []
        self.dead: List[Creature] = []
        self.stats_history: List[Dict] = []
        
        # Spawn initial creatures
        for _ in range(initial_creatures):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            self.creatures.append(Creature(x, y))
    
    def step(self):
        """One tick of the simulation."""
        self.world.step()
        
        # Each creature senses, thinks, acts
        alive = [c for c in self.creatures if c.alive]
        
        for creature in alive:
            senses = creature.sense(self.world, alive)
            action = creature.think(senses)
            creature.act(action, self.world)
        
        # Reproduction
        babies = []
        for creature in alive:
            if creature.alive and creature.can_reproduce():
                baby = creature.reproduce()
                babies.append(baby)
        self.creatures.extend(babies)
        
        # Remove dead
        newly_dead = [c for c in self.creatures if not c.alive]
        self.dead.extend(newly_dead)
        self.creatures = [c for c in self.creatures if c.alive]
        
        # Record stats
        self.stats_history.append(self._stats())
    
    def _stats(self) -> Dict:
        alive = [c for c in self.creatures if c.alive]
        if not alive:
            return {
                'tick': self.world.tick,
                'population': 0,
                'avg_energy': 0,
                'avg_age': 0,
                'max_gen': 0,
                'food': self.world.count_food(),
                'total_eaten': 0,
                'births': 0
            }
        return {
            'tick': self.world.tick,
            'population': len(alive),
            'avg_energy': sum(c.energy for c in alive) / len(alive),
            'avg_age': sum(c.age for c in alive) / len(alive),
            'max_gen': max(c.generation for c in alive),
            'food': self.world.count_food(),
            'total_eaten': sum(c.food_eaten for c in alive),
            'births': sum(c.children for c in alive)
        }
    
    def render(self) -> str:
        """ASCII render of the world."""
        # Build display grid
        display = []
        for y in range(self.world.height):
            row = []
            for x in range(self.world.width):
                if self.world.grid[y][x] == World.FOOD:
                    row.append('·')
                else:
                    row.append(' ')
            display.append(row)
        
        # Place creatures
        dir_chars = ['▲', '►', '▼', '◄']
        for c in self.creatures:
            if c.alive:
                cx = c.x % self.world.width
                cy = c.y % self.world.height
                display[cy][cx] = dir_chars[c.direction]
        
        # Build frame
        lines = ['┌' + '─' * self.world.width + '┐']
        for row in display:
            lines.append('│' + ''.join(row) + '│')
        lines.append('└' + '─' * self.world.width + '┘')
        
        return '\n'.join(lines)
    
    def run(self, ticks: int = 200, display_interval: int = 50):
        """Run the simulation."""
        print("═══ Genesis — Artificial Life Simulator ═══")
        print(f"  World: {self.world.width}×{self.world.height}")
        print(f"  Initial creatures: {len(self.creatures)}")
        print(f"  Initial food: {self.world.count_food()}")
        print(f"  Each creature has a neural network brain (8→6→4)")
        print()
        
        for t in range(ticks):
            self.step()
            
            if (t + 1) % display_interval == 0 or t == 0:
                stats = self.stats_history[-1]
                print(f"── Tick {stats['tick']:4d} ──")
                print(self.render())
                print(f"  Pop: {stats['population']:3d} │ "
                      f"Food: {stats['food']:3d} │ "
                      f"Avg Energy: {stats['avg_energy']:5.1f} │ "
                      f"Max Gen: {stats['max_gen']} │ "
                      f"Eaten: {stats['total_eaten']}")
                print()
            
            # Extinction check
            if not self.creatures:
                print(f"  ✗ EXTINCTION at tick {self.world.tick}")
                break
        
        self._final_report()
    
    def _final_report(self):
        """Summary of the simulation."""
        print("═══ Genesis — Final Report ═══")
        print(f"  Duration: {self.world.tick} ticks")
        print(f"  Total creatures born: {Creature.ID_COUNTER}")
        print(f"  Final population: {len(self.creatures)}")
        print(f"  Total deaths: {len(self.dead)}")
        
        if self.creatures:
            best = max(self.creatures, key=lambda c: c.food_eaten)
            oldest = max(self.creatures, key=lambda c: c.age)
            most_children = max(self.creatures, key=lambda c: c.children)
            highest_gen = max(self.creatures, key=lambda c: c.generation)
            
            print(f"\n  ── Champions ──")
            print(f"  Best forager:    #{best.id} ate {best.food_eaten} food (gen {best.generation})")
            print(f"  Oldest alive:    #{oldest.id} age {oldest.age} (gen {oldest.generation})")
            print(f"  Most offspring:  #{most_children.id} had {most_children.children} children (gen {most_children.generation})")
            print(f"  Highest lineage: #{highest_gen.id} generation {highest_gen.generation}")
        
        # Population graph
        if len(self.stats_history) > 1:
            print(f"\n  ── Population Over Time ──")
            pops = [s['population'] for s in self.stats_history]
            max_pop = max(pops) if pops else 1
            
            # Sample 20 points
            samples = min(20, len(pops))
            step = max(1, len(pops) // samples)
            
            for i in range(0, len(pops), step):
                bar_len = int(30 * pops[i] / max_pop) if max_pop > 0 else 0
                print(f"    t={i:4d} │{'█' * bar_len}{'░' * (30 - bar_len)}│ {pops[i]}")
        
        # Generation depth
        if self.creatures:
            gens = [c.generation for c in self.creatures]
            max_g = max(gens)
            if max_g > 0:
                print(f"\n  ── Evolution Depth ──")
                print(f"  Generations evolved: {max_g}")
                print(f"  Neural mutations accumulated: ~{max_g * 3} weight changes per lineage")
                print(f"  Brains are now DIFFERENT from ancestors")
        
        survived = len(self.creatures) > 0
        print(f"\n  {'✓ LIFE PERSISTS' if survived else '✗ EXTINCTION'}")


# ═══════════════════════════════════════════
# RUN IT
# ═══════════════════════════════════════════

if __name__ == '__main__':
    random.seed(42)  # reproducible but interesting
    Creature.ID_COUNTER = 0
    
    sim = Genesis(
        width=40,
        height=20,
        initial_creatures=20,
        food_density=0.20
    )
    
    sim.run(ticks=300, display_interval=100)