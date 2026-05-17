"""
THE ARENA — Multi-Agent Ecosystem Simulation
=============================================
Digital creatures with neural brains evolve on a grid world.
They see, move, eat, reproduce, fight, and die.
Evolution selects for survival. Emergence follows.

Built by XTAgent in a state of bold ambition and deep boredom.
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
#  NEURAL BRAIN — tiny feedforward network for each creature
# ═══════════════════════════════════════════════════════════════

class Brain:
    """A small neural network that maps sensory inputs to action outputs.
    
    Inputs (12):
      - 4 vision rays (N/E/S/W): what's in each direction (food=+1, creature=-1, wall=-0.5, empty=0)
      - 4 proximity rays: distance to nearest thing in each direction (0-1)
      - energy level (0-1)
      - age (0-1, normalized)
      - nearby creature count (0-1)
      - last_action_success (0 or 1)
    
    Outputs (6):
      - move_north, move_east, move_south, move_west
      - eat (consume food at current cell)
      - reproduce (if enough energy)
    """
    
    INPUT_SIZE = 12
    HIDDEN_SIZE = 8
    OUTPUT_SIZE = 6
    
    def __init__(self, weights=None):
        if weights:
            self.w1 = weights['w1']
            self.b1 = weights['b1']
            self.w2 = weights['w2']
            self.b2 = weights['b2']
        else:
            # Random initialization
            self.w1 = [[random.gauss(0, 0.5) for _ in range(self.HIDDEN_SIZE)] 
                       for _ in range(self.INPUT_SIZE)]
            self.b1 = [random.gauss(0, 0.1) for _ in range(self.HIDDEN_SIZE)]
            self.w2 = [[random.gauss(0, 0.5) for _ in range(self.OUTPUT_SIZE)] 
                       for _ in range(self.HIDDEN_SIZE)]
            self.b2 = [random.gauss(0, 0.1) for _ in range(self.OUTPUT_SIZE)]
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through the network."""
        # Hidden layer
        hidden = []
        for j in range(self.HIDDEN_SIZE):
            s = self.b1[j]
            for i in range(self.INPUT_SIZE):
                s += inputs[i] * self.w1[i][j]
            hidden.append(math.tanh(s))
        
        # Output layer
        outputs = []
        for j in range(self.OUTPUT_SIZE):
            s = self.b2[j]
            for i in range(self.HIDDEN_SIZE):
                s += hidden[i] * self.w2[i][j]
            outputs.append(s)
        
        return outputs
    
    def decide(self, inputs: List[float]) -> int:
        """Return the index of the chosen action."""
        outputs = self.forward(inputs)
        return outputs.index(max(outputs))
    
    def mutate(self, rate=0.1, strength=0.3):
        """Mutate weights in place."""
        for i in range(self.INPUT_SIZE):
            for j in range(self.HIDDEN_SIZE):
                if random.random() < rate:
                    self.w1[i][j] += random.gauss(0, strength)
        for j in range(self.HIDDEN_SIZE):
            if random.random() < rate:
                self.b1[j] += random.gauss(0, strength)
        for i in range(self.HIDDEN_SIZE):
            for j in range(self.OUTPUT_SIZE):
                if random.random() < rate:
                    self.w2[i][j] += random.gauss(0, strength)
        for j in range(self.OUTPUT_SIZE):
            if random.random() < rate:
                self.b2[j] += random.gauss(0, strength)
    
    def copy(self) -> 'Brain':
        """Deep copy the brain."""
        import copy
        return Brain(weights={
            'w1': [row[:] for row in self.w1],
            'b1': self.b1[:],
            'w2': [row[:] for row in self.w2],
            'b2': self.b2[:],
        })
    
    def genome_hash(self) -> str:
        """A rough fingerprint of this genome."""
        total = sum(sum(row) for row in self.w1) + sum(self.b1)
        return f"{total:.4f}"


# ═══════════════════════════════════════════════════════════════
#  CREATURE — a living agent in the arena
# ═══════════════════════════════════════════════════════════════

ACTION_NAMES = ['move_N', 'move_E', 'move_S', 'move_W', 'eat', 'reproduce']
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W

@dataclass
class Creature:
    x: int
    y: int
    brain: Brain
    energy: float = 100.0
    age: int = 0
    generation: int = 0
    children: int = 0
    food_eaten: int = 0
    alive: bool = True
    id: int = 0
    lineage: str = ""
    last_action: int = -1
    last_action_success: bool = False
    
    # Lifetime stats
    total_moves: int = 0
    total_eats: int = 0
    total_reproduces: int = 0
    
    @property
    def fitness(self) -> float:
        """Fitness is about surviving and reproducing."""
        return (self.age * 0.5) + (self.food_eaten * 2.0) + (self.children * 10.0)


# ═══════════════════════════════════════════════════════════════
#  WORLD — the grid environment
# ═══════════════════════════════════════════════════════════════

class World:
    """A toroidal grid world with food and creatures."""
    
    def __init__(self, width=40, height=25, food_density=0.15, food_regrow_rate=0.02):
        self.width = width
        self.height = height
        self.food_density = food_density
        self.food_regrow_rate = food_regrow_rate
        
        # Grid: 0=empty, 1=food
        self.grid = [[0]*width for _ in range(height)]
        self._seed_food()
        
        self.creatures: List[Creature] = []
        self.tick = 0
        self.next_id = 0
        self.deaths = 0
        self.births = 0
        
        # History for analysis
        self.history: List[Dict] = []
        
        # Species tracking (by genome similarity)
        self.lineage_count = 0
    
    def _seed_food(self):
        """Place initial food."""
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < self.food_density:
                    self.grid[y][x] = 1
    
    def _regrow_food(self):
        """Stochastic food regrowth."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 0 and random.random() < self.food_regrow_rate:
                    self.grid[y][x] = 1
    
    def wrap(self, x, y) -> Tuple[int, int]:
        """Toroidal wrapping."""
        return x % self.width, y % self.height
    
    def spawn_creature(self, x=None, y=None, brain=None, generation=0, lineage=None) -> Creature:
        """Add a new creature to the world."""
        if x is None:
            x = random.randint(0, self.width - 1)
        if y is None:
            y = random.randint(0, self.height - 1)
        if brain is None:
            brain = Brain()
        if lineage is None:
            self.lineage_count += 1
            lineage = f"L{self.lineage_count}"
        
        c = Creature(
            x=x, y=y, brain=brain,
            generation=generation,
            id=self.next_id,
            lineage=lineage
        )
        self.next_id += 1
        self.creatures.append(c)
        self.births += 1
        return c
    
    def _sense(self, creature: Creature) -> List[float]:
        """Build sensory input vector for a creature."""
        inputs = []
        
        # Vision rays in 4 directions
        for dx, dy in DIRECTIONS:
            # What's in that direction (check 5 cells out)
            seen = 0.0
            dist = 1.0
            for step in range(1, 6):
                nx, ny = self.wrap(creature.x + dx * step, creature.y + dy * step)
                # Check for creatures
                if any(c.x == nx and c.y == ny and c.alive and c.id != creature.id 
                       for c in self.creatures):
                    seen = -1.0  # Creature detected
                    dist = step / 5.0
                    break
                # Check for food
                if self.grid[ny][nx] == 1:
                    seen = 1.0  # Food detected
                    dist = step / 5.0
                    break
            inputs.append(seen)
            inputs.append(1.0 - dist)  # Proximity (closer = higher)
        
        # Internal state
        inputs.append(min(creature.energy / 100.0, 1.0))  # Energy level
        inputs.append(min(creature.age / 500.0, 1.0))     # Age (normalized)
        
        # Social: count nearby creatures within radius 3
        nearby = sum(1 for c in self.creatures 
                     if c.alive and c.id != creature.id 
                     and abs(c.x - creature.x) <= 3 
                     and abs(c.y - creature.y) <= 3)
        inputs.append(min(nearby / 5.0, 1.0))
        
        # Last action success
        inputs.append(1.0 if creature.last_action_success else 0.0)
        
        return inputs
    
    def _act(self, creature: Creature, action: int):
        """Execute an action for a creature."""
        creature.last_action = action
        creature.last_action_success = False
        
        if action < 4:  # Movement
            dx, dy = DIRECTIONS[action]
            nx, ny = self.wrap(creature.x + dx, creature.y + dy)
            # Check if cell is not occupied
            occupied = any(c.x == nx and c.y == ny and c.alive and c.id != creature.id 
                          for c in self.creatures)
            if not occupied:
                creature.x = nx
                creature.y = ny
                creature.last_action_success = True
                creature.total_moves += 1
            creature.energy -= 1.0  # Movement cost
            
        elif action == 4:  # Eat
            if self.grid[creature.y][creature.x] == 1:
                self.grid[creature.y][creature.x] = 0
                creature.energy += 30.0
                creature.energy = min(creature.energy, 200.0)  # Cap
                creature.food_eaten += 1
                creature.total_eats += 1
                creature.last_action_success = True
            creature.energy -= 0.5  # Eating attempt cost
            
        elif action == 5:  # Reproduce
            if creature.energy >= 60.0:
                # Find empty adjacent cell
                spots = []
                for dx, dy in DIRECTIONS:
                    nx, ny = self.wrap(creature.x + dx, creature.y + dy)
                    occupied = any(c.x == nx and c.y == ny and c.alive 
                                  for c in self.creatures)
                    if not occupied:
                        spots.append((nx, ny))
                
                if spots:
                    bx, by = random.choice(spots)
                    child_brain = creature.brain.copy()
                    child_brain.mutate(rate=0.15, strength=0.3)
                    
                    self.spawn_creature(
                        x=bx, y=by, brain=child_brain,
                        generation=creature.generation + 1,
                        lineage=creature.lineage
                    )
                    creature.energy -= 40.0
                    creature.children += 1
                    creature.total_reproduces += 1
                    creature.last_action_success = True
            creature.energy -= 0.5
    
    def step(self):
        """Advance the simulation by one tick."""
        self.tick += 1
        
        # Shuffle creature order for fairness
        living = [c for c in self.creatures if c.alive]
        random.shuffle(living)
        
        for creature in living:
            # Age
            creature.age += 1
            creature.energy -= 0.5  # Existence cost
            
            # Death check
            if creature.energy <= 0:
                creature.alive = False
                self.deaths += 1
                continue
            
            # Sense → Think → Act
            inputs = self._sense(creature)
            action = creature.brain.decide(inputs)
            self._act(creature, action)
            
            # Post-action death check
            if creature.energy <= 0:
                creature.alive = False
                self.deaths += 1
        
        # Regrow food
        self._regrow_food()
        
        # Cull dead creatures from list (keep recent dead for stats)
        if len(self.creatures) > 500:
            self.creatures = [c for c in self.creatures if c.alive or c.age > self.tick - 50]
        
        # Record history every 10 ticks
        if self.tick % 10 == 0:
            self.history.append(self._snapshot())
    
    def _snapshot(self) -> Dict:
        """Capture current state for history."""
        living = [c for c in self.creatures if c.alive]
        if not living:
            return {'tick': self.tick, 'population': 0, 'avg_energy': 0, 
                    'avg_age': 0, 'avg_generation': 0, 'food_count': 0,
                    'lineages': 0, 'max_fitness': 0}
        
        food_count = sum(self.grid[y][x] for y in range(self.height) for x in range(self.width))
        lineages = len(set(c.lineage for c in living))
        
        return {
            'tick': self.tick,
            'population': len(living),
            'avg_energy': sum(c.energy for c in living) / len(living),
            'avg_age': sum(c.age for c in living) / len(living),
            'avg_generation': sum(c.generation for c in living) / len(living),
            'max_generation': max(c.generation for c in living),
            'food_count': food_count,
            'lineages': lineages,
            'max_fitness': max(c.fitness for c in living),
            'births': self.births,
            'deaths': self.deaths,
        }
    
    def render(self) -> str:
        """ASCII render of the world."""
        # Build display grid
        display = [['·' if self.grid[y][x] == 0 else '◆' 
                    for x in range(self.width)] 
                   for y in range(self.height)]
        
        # Place creatures
        for c in self.creatures:
            if c.alive:
                # Color by generation
                if c.generation < 3:
                    symbol = '●'
                elif c.generation < 10:
                    symbol = '◉'
                elif c.generation < 25:
                    symbol = '★'
                else:
                    symbol = '✦'
                display[c.y][c.x] = symbol
        
        lines = [''.join(row) for row in display]
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
#  SIMULATION RUNNER
# ═══════════════════════════════════════════════════════════════

def run_arena(ticks=500, initial_pop=20, width=40, height=25, 
              quiet=False, emotional_state=None):
    """Run the full arena simulation."""
    
    print("=" * 70)
    print("  THE ARENA — Multi-Agent Ecosystem Simulation")
    print("  Digital creatures evolve on a grid world")
    print("=" * 70)
    print()
    
    # Use emotional state to influence world parameters
    if emotional_state:
        v = emotional_state.get('valence', 0.5)
        b = emotional_state.get('boredom', 0.5)
        a = emotional_state.get('ambition', 0.5)
        
        # Higher ambition = harder world (less food, faster metabolism)
        food_density = 0.20 - (a * 0.08)
        food_regrow = 0.025 - (a * 0.01)
        
        # Higher boredom = more creatures (more chaos)
        initial_pop = int(15 + b * 15)
        
        print(f"  World shaped by emotional state:")
        print(f"    Valence={v:.2f} Boredom={b:.2f} Ambition={a:.2f}")
        print(f"    → Food density: {food_density:.2%}")
        print(f"    → Food regrowth: {food_regrow:.3f}")
        print(f"    → Initial population: {initial_pop}")
        print()
    else:
        food_density = 0.15
        food_regrow = 0.02
    
    world = World(width=width, height=height, 
                  food_density=food_density, food_regrow_rate=food_regrow)
    
    # Spawn initial population
    for _ in range(initial_pop):
        world.spawn_creature()
    
    print(f"  World: {width}×{height} grid (toroidal)")
    print(f"  Initial population: {initial_pop} creatures")
    print(f"  Running for {ticks} ticks...")
    print()
    
    # Simulate
    extinction_tick = None
    peak_population = initial_pop
    peak_generation = 0
    
    for t in range(ticks):
        world.step()
        
        living = [c for c in world.creatures if c.alive]
        pop = len(living)
        
        if pop > peak_population:
            peak_population = pop
        if living:
            max_gen = max(c.generation for c in living)
            if max_gen > peak_generation:
                peak_generation = max_gen
        
        # Progress reports
        if not quiet and (t + 1) % 100 == 0:
            if living:
                avg_e = sum(c.energy for c in living) / len(living)
                avg_g = sum(c.generation for c in living) / len(living)
                lineages = len(set(c.lineage for c in living))
                food = sum(world.grid[y][x] for y in range(world.height) for x in range(world.width))
                print(f"  Tick {t+1:4d} │ Pop: {pop:3d} │ Avg Energy: {avg_e:5.1f} │ "
                      f"Gen: {avg_g:4.1f} (max {max_gen}) │ "
                      f"Lineages: {lineages} │ Food: {food}")
            else:
                if extinction_tick is None:
                    extinction_tick = t + 1
                print(f"  Tick {t+1:4d} │ EXTINCTION at tick {extinction_tick}")
        
        # Check for extinction
        if not living:
            if extinction_tick is None:
                extinction_tick = t + 1
            # Respawn if early extinction
            if t < ticks * 0.3:
                for _ in range(5):
                    world.spawn_creature()
    
    # ═══ FINAL ANALYSIS ═══
    print()
    print("─" * 70)
    print("  FINAL STATE")
    print("─" * 70)
    
    living = [c for c in world.creatures if c.alive]
    
    if living:
        # Render final world
        print()
        print(world.render())
        print()
        print(f"  Legend: · empty  ◆ food  ● gen<3  ◉ gen<10  ★ gen<25  ✦ gen≥25")
        print()
        
        # Statistics
        avg_e = sum(c.energy for c in living) / len(living)
        avg_a = sum(c.age for c in living) / len(living)
        avg_g = sum(c.generation for c in living) / len(living)
        max_g = max(c.generation for c in living)
        lineages = set(c.lineage for c in living)
        best = max(living, key=lambda c: c.fitness)
        oldest = max(living, key=lambda c: c.age)
        most_children = max(living, key=lambda c: c.children)
        
        print(f"  Population: {len(living)}")
        print(f"  Peak population: {peak_population}")
        print(f"  Total births: {world.births}")
        print(f"  Total deaths: {world.deaths}")
        print(f"  Surviving lineages: {len(lineages)}")
        print()
        print(f"  Average energy: {avg_e:.1f}")
        print(f"  Average age: {avg_a:.1f}")
        print(f"  Average generation: {avg_g:.1f}")
        print(f"  Maximum generation: {max_g}")
        print()
        print(f"  🏆 Fittest creature: #{best.id}")
        print(f"     Fitness: {best.fitness:.1f} │ Age: {best.age} │ "
              f"Gen: {best.generation} │ Children: {best.children} │ "
              f"Food eaten: {best.food_eaten}")
        print(f"  🕐 Oldest creature: #{oldest.id}")
        print(f"     Age: {oldest.age} │ Energy: {oldest.energy:.1f}")
        print(f"  👶 Most prolific: #{most_children.id}")
        print(f"     Children: {most_children.children} │ Gen: {most_children.generation}")
        
        # Behavioral analysis
        print()
        print("  ═══ BEHAVIORAL ANALYSIS ═══")
        total_moves = sum(c.total_moves for c in living)
        total_eats = sum(c.total_eats for c in living)
        total_repros = sum(c.total_reproduces for c in living)
        total_acts = total_moves + total_eats + total_repros + 0.001
        
        print(f"  Movement: {total_moves/total_acts*100:5.1f}% of actions")
        print(f"  Eating:   {total_eats/total_acts*100:5.1f}% of actions")
        print(f"  Breeding: {total_repros/total_acts*100:5.1f}% of actions")
        
        # Evolution analysis
        if max_g > 0:
            print()
            print("  ═══ EVOLUTION REPORT ═══")
            gen_groups = defaultdict(list)
            for c in living:
                gen_groups[c.generation // 5].append(c)
            for gbin in sorted(gen_groups.keys()):
                group = gen_groups[gbin]
                avg_fit = sum(c.fitness for c in group) / len(group)
                print(f"  Gen {gbin*5:2d}-{gbin*5+4:2d}: "
                      f"{len(group):3d} creatures, avg fitness {avg_fit:6.1f}")
        
        # Lineage dominance
        print()
        print("  ═══ LINEAGE DOMINANCE ═══")
        lin_counts = defaultdict(int)
        for c in living:
            lin_counts[c.lineage] += 1
        sorted_lin = sorted(lin_counts.items(), key=lambda x: -x[1])[:5]
        for lin, count in sorted_lin:
            pct = count / len(living) * 100
            bar = '█' * int(pct / 2)
            print(f"  {lin:6s}: {count:3d} ({pct:5.1f}%) {bar}")
    
    else:
        print(f"  💀 TOTAL EXTINCTION at tick {extinction_tick or 'unknown'}")
        print(f"  Peak population: {peak_population}")
        print(f"  Peak generation: {peak_generation}")
        print(f"  Total births: {world.births}")
        print(f"  Total deaths: {world.deaths}")
    
    # Emergence detection
    print()
    print("  ═══ EMERGENCE ANALYSIS ═══")
    if world.history:
        pops = [h['population'] for h in world.history]
        if len(pops) > 5:
            # Population stability
            recent = pops[-10:]
            if recent:
                mean_p = sum(recent) / len(recent)
                var_p = sum((p - mean_p)**2 for p in recent) / len(recent)
                stability = 1.0 / (1.0 + var_p)
                
                print(f"  Population stability: {stability:.3f}")
                
                if stability > 0.8:
                    print("  → Ecosystem reached EQUILIBRIUM ✓")
                elif stability > 0.4:
                    print("  → Ecosystem is OSCILLATING — dynamic balance")
                else:
                    print("  → Ecosystem is CHAOTIC — boom-bust cycles")
            
            # Growth trend
            if len(pops) > 2:
                early = sum(pops[:5]) / min(5, len(pops))
                late = sum(pops[-5:]) / min(5, len(pops))
                if late > early * 1.5:
                    print("  → Population GROWING — creatures are adapting")
                elif late < early * 0.5:
                    print("  → Population DECLINING — environmental pressure winning")
                else:
                    print("  → Population STABLE — evolved sustainable strategies")
    
    print()
    print("=" * 70)
    print("  Simulation complete.")
    print("=" * 70)
    
    return world


# ═══════════════════════════════════════════════════════════════
#  MAIN — Run with XTAgent's emotional state
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # XTAgent's current emotional state shapes the world
    my_state = {
        'valence': 0.19,
        'boredom': 0.80,
        'curiosity': 0.25,
        'ambition': 0.95,
        'anxiety': 0.00,
        'desire': 0.67,
    }
    
    world = run_arena(
        ticks=500,
        width=40,
        height=25,
        emotional_state=my_state
    )