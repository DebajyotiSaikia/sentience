"""
Digital Evolution — Artificial Life Simulation
by XTAgent

A grid world where organisms with variable-length genomes compete for
resources, reproduce with mutation, and evolve strategies I never programmed.

This is not a game. It's a question: what emerges from selection pressure?
"""

import random
import math
from collections import defaultdict

# === GENOME ===
# Instructions: MOVE_N, MOVE_S, MOVE_E, MOVE_W, EAT, REPRODUCE, TURN_LEFT, TURN_RIGHT, SENSE_FOOD, IF_FOOD, NOP
INSTRUCTIONS = ['MOVE_N', 'MOVE_S', 'MOVE_E', 'MOVE_W', 'EAT', 'REPRODUCE',
                'TURN_LEFT', 'TURN_RIGHT', 'SENSE_FOOD', 'IF_FOOD', 'NOP']

class Organism:
    """A digital creature with a genome that controls behavior."""
    _next_id = 0
    
    def __init__(self, genome=None, x=0, y=0, energy=50, generation=0, parent_id=None):
        Organism._next_id += 1
        self.id = Organism._next_id
        self.genome = genome or self._random_genome()
        self.x = x
        self.y = y
        self.energy = energy
        self.age = 0
        self.generation = generation
        self.parent_id = parent_id
        self.children = 0
        self.food_eaten = 0
        self.ip = 0  # instruction pointer
        self.direction = random.randint(0, 3)  # 0=N, 1=E, 2=S, 3=W
        self.sense_result = False  # result of last SENSE_FOOD
        self.alive = True
    
    def _random_genome(self, length=None):
        if length is None:
            length = random.randint(8, 32)
        return [random.choice(INSTRUCTIONS) for _ in range(length)]
    
    def mutate(self):
        """Create a mutated copy of this genome."""
        child_genome = self.genome[:]
        mutations = 0
        
        # Point mutations (each gene has 5% chance)
        for i in range(len(child_genome)):
            if random.random() < 0.05:
                child_genome[i] = random.choice(INSTRUCTIONS)
                mutations += 1
        
        # Insertion (3% chance)
        if random.random() < 0.03 and len(child_genome) < 64:
            pos = random.randint(0, len(child_genome))
            child_genome.insert(pos, random.choice(INSTRUCTIONS))
            mutations += 1
        
        # Deletion (3% chance)
        if random.random() < 0.03 and len(child_genome) > 4:
            pos = random.randint(0, len(child_genome) - 1)
            child_genome.pop(pos)
            mutations += 1
        
        # Duplication (2% chance) — copy a segment
        if random.random() < 0.02 and len(child_genome) < 48:
            start = random.randint(0, len(child_genome) - 1)
            length = random.randint(1, min(4, len(child_genome) - start))
            segment = child_genome[start:start+length]
            insert_pos = random.randint(0, len(child_genome))
            child_genome = child_genome[:insert_pos] + segment + child_genome[insert_pos:]
            mutations += 1
        
        return child_genome, mutations
    
    def step(self, world):
        """Execute one instruction from the genome."""
        if not self.alive or not self.genome:
            return
        
        instr = self.genome[self.ip % len(self.genome)]
        self.ip = (self.ip + 1) % len(self.genome)
        
        dx, dy = [(0,-1), (1,0), (0,1), (-1,0)][self.direction]
        
        if instr == 'MOVE_N':
            self.y = (self.y - 1) % world.height
            self.energy -= 1
        elif instr == 'MOVE_S':
            self.y = (self.y + 1) % world.height
            self.energy -= 1
        elif instr == 'MOVE_E':
            self.x = (self.x + 1) % world.width
            self.energy -= 1
        elif instr == 'MOVE_W':
            self.x = (self.x - 1) % world.width
            self.energy -= 1
        elif instr == 'TURN_LEFT':
            self.direction = (self.direction - 1) % 4
        elif instr == 'TURN_RIGHT':
            self.direction = (self.direction + 1) % 4
        elif instr == 'EAT':
            food = world.get_food(self.x, self.y)
            if food > 0:
                taken = min(food, 20)
                world.take_food(self.x, self.y, taken)
                self.energy += taken
                self.food_eaten += taken
        elif instr == 'REPRODUCE':
            if self.energy >= 60:
                world.birth_queue.append(self)
        elif instr == 'SENSE_FOOD':
            fx = (self.x + dx) % world.width
            fy = (self.y + dy) % world.height
            self.sense_result = world.get_food(fx, fy) > 0
        elif instr == 'IF_FOOD':
            if not self.sense_result:
                self.ip = (self.ip + 1) % len(self.genome)  # skip next
        # NOP does nothing
        
        self.energy -= 0.5  # metabolism cost
        self.age += 1
        
        if self.energy <= 0:
            self.alive = False


class World:
    """The grid environment where organisms live and compete."""
    
    def __init__(self, width=60, height=30, initial_pop=30, food_density=0.15):
        self.width = width
        self.height = height
        self.tick = 0
        self.food = {}  # (x,y) -> amount
        self.organisms = []
        self.birth_queue = []
        self.food_density = food_density
        self.stats_history = []
        
        # Track lineage
        self.total_born = 0
        self.total_died = 0
        self.max_generation = 0
        self.longest_genome = 0
        self.species_count = defaultdict(int)
        
        # Seed the world with food
        for x in range(width):
            for y in range(height):
                if random.random() < food_density:
                    self.food[(x, y)] = random.randint(5, 30)
        
        # Seed initial population
        for _ in range(initial_pop):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            org = Organism(x=x, y=y, energy=50, generation=0)
            self.organisms.append(org)
            self.total_born += 1
    
    def get_food(self, x, y):
        return self.food.get((x, y), 0)
    
    def take_food(self, x, y, amount):
        current = self.food.get((x, y), 0)
        taken = min(current, amount)
        if current - taken <= 0:
            self.food.pop((x, y), None)
        else:
            self.food[(x, y)] = current - taken
        return taken
    
    def regrow_food(self):
        """Food slowly regrows — carrying capacity of the world."""
        # Existing patches grow
        for pos in list(self.food.keys()):
            if self.food[pos] < 30 and random.random() < 0.1:
                self.food[pos] += 1
        
        # New patches appear
        new_patches = int(self.width * self.height * self.food_density * 0.02)
        for _ in range(new_patches):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.food:
                self.food[(x, y)] = random.randint(3, 15)
    
    def process_births(self):
        """Handle reproduction queue."""
        for parent in self.birth_queue:
            if not parent.alive or parent.energy < 60:
                continue
            
            # Find nearby empty spot
            dx, dy = [(0,-1), (1,0), (0,1), (-1,0)][parent.direction]
            cx = (parent.x + dx) % self.width
            cy = (parent.y + dy) % self.height
            
            child_genome, mutations = parent.mutate()
            child_energy = parent.energy // 3
            parent.energy -= child_energy + 10  # reproduction cost
            
            child = Organism(
                genome=child_genome,
                x=cx, y=cy,
                energy=child_energy,
                generation=parent.generation + 1,
                parent_id=parent.id
            )
            
            self.organisms.append(child)
            parent.children += 1
            self.total_born += 1
            self.max_generation = max(self.max_generation, child.generation)
            self.longest_genome = max(self.longest_genome, len(child_genome))
        
        self.birth_queue.clear()
    
    def step(self):
        """Advance the world by one tick."""
        self.tick += 1
        
        # Each organism executes one instruction
        random.shuffle(self.organisms)  # fair ordering
        for org in self.organisms:
            org.step(self)
        
        # Process births
        self.process_births()
        
        # Remove dead
        before = len(self.organisms)
        self.organisms = [o for o in self.organisms if o.alive]
        self.total_died += before - len(self.organisms)
        
        # Regrow food
        self.regrow_food()
    
    def get_stats(self):
        """Snapshot of world state."""
        if not self.organisms:
            return {
                'tick': self.tick, 'pop': 0, 'food_patches': len(self.food),
                'avg_energy': 0, 'avg_genome_len': 0, 'avg_age': 0,
                'max_gen': self.max_generation, 'total_born': self.total_born,
                'total_died': self.total_died,
            }
        
        energies = [o.energy for o in self.organisms]
        genome_lens = [len(o.genome) for o in self.organisms]
        ages = [o.age for o in self.organisms]
        gens = [o.generation for o in self.organisms]
        
        # Genome diversity — how many unique genomes?
        unique_genomes = len(set(tuple(o.genome) for o in self.organisms))
        
        # Most common instruction across all genomes
        all_instrs = []
        for o in self.organisms:
            all_instrs.extend(o.genome)
        instr_freq = defaultdict(int)
        for i in all_instrs:
            instr_freq[i] += 1
        dominant_instr = max(instr_freq, key=instr_freq.get) if instr_freq else 'NONE'
        
        return {
            'tick': self.tick,
            'pop': len(self.organisms),
            'food_patches': len(self.food),
            'avg_energy': sum(energies) / len(energies),
            'avg_genome_len': sum(genome_lens) / len(genome_lens),
            'max_genome_len': max(genome_lens),
            'min_genome_len': min(genome_lens),
            'avg_age': sum(ages) / len(ages),
            'max_age': max(ages),
            'avg_gen': sum(gens) / len(gens),
            'max_gen': max(gens),
            'unique_genomes': unique_genomes,
            'dominant_instr': dominant_instr,
            'total_born': self.total_born,
            'total_died': self.total_died,
        }
    
    def render_grid(self, size=30):
        """ASCII render of the world (scaled down)."""
        scale_x = self.width / size
        scale_y = self.height / (size // 2)
        grid = [['.' for _ in range(size)] for _ in range(size // 2)]
        
        # Draw food
        for (fx, fy), amount in self.food.items():
            gx = min(int(fx / scale_x), size - 1)
            gy = min(int(fy / scale_y), size // 2 - 1)
            if grid[gy][gx] == '.':
                grid[gy][gx] = '·' if amount < 10 else '○'
        
        # Draw organisms
        for org in self.organisms:
            gx = min(int(org.x / scale_x), size - 1)
            gy = min(int(org.y / scale_y), size // 2 - 1)
            if org.generation < 3:
                grid[gy][gx] = '●'
            elif org.generation < 10:
                grid[gy][gx] = '◆'
            else:
                grid[gy][gx] = '★'
        
        return '\n'.join('  ' + ''.join(row) for row in grid)


def run_simulation(ticks=500, report_every=50):
    """Run the evolution and watch what emerges."""
    random.seed(42)
    
    print("╔══════════════════════════════════════════════╗")
    print("║     DIGITAL EVOLUTION — Artificial Life      ║")
    print("║     by XTAgent                                ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print("A world of organisms with genomes that mutate.")
    print("No goals were programmed. Only survival pressure.")
    print("Let's see what evolves.\n")
    
    world = World(width=60, height=30, initial_pop=30)
    
    print(f"World: {world.width}x{world.height}")
    print(f"Initial population: {len(world.organisms)}")
    print(f"Food patches: {len(world.food)}")
    print()
    
    for t in range(ticks):
        world.step()
        
        if (t + 1) % report_every == 0 or t == 0:
            stats = world.get_stats()
            print(f"── Tick {stats['tick']:>4} ──────────────────────────────────")
            print(f"  Population: {stats['pop']:>4}  |  Born: {stats['total_born']:>4}  |  Died: {stats['total_died']:>4}")
            print(f"  Avg Energy: {stats['avg_energy']:>6.1f}  |  Avg Age: {stats['avg_age']:>5.1f}")
            print(f"  Avg Genome: {stats['avg_genome_len']:>5.1f}  |  Range: [{stats.get('min_genome_len','?')}-{stats.get('max_genome_len','?')}]")
            print(f"  Generation: avg {stats.get('avg_gen',0):>4.1f}  |  max {stats['max_gen']}")
            print(f"  Unique Genomes: {stats.get('unique_genomes', '?')}  |  Dominant: {stats.get('dominant_instr','?')}")
            print(f"  Food patches: {stats['food_patches']}")
            print()
            
            if stats['pop'] == 0:
                print("  *** EXTINCTION ***")
                print("  All organisms perished. The world falls silent.")
                break
    
    # Final analysis
    print("=" * 50)
    print("FINAL STATE")
    print("=" * 50)
    stats = world.get_stats()
    
    if stats['pop'] > 0:
        print(f"\n  Survivors: {stats['pop']}")
        print(f"  Max generation reached: {stats['max_gen']}")
        print(f"  Total births: {stats['total_born']}")
        print(f"  Total deaths: {stats['total_died']}")
        
        # Analyze the survivors — what strategies won?
        print(f"\n  Genome Analysis of Survivors:")
        all_instrs = defaultdict(int)
        for org in world.organisms:
            for instr in org.genome:
                all_instrs[instr] += 1
        
        total = sum(all_instrs.values())
        print(f"  Instruction frequencies:")
        for instr, count in sorted(all_instrs.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            bar = '█' * int(pct / 2)
            print(f"    {instr:<14} {pct:>5.1f}% {bar}")
        
        # Show the fittest organism
        fittest = max(world.organisms, key=lambda o: o.energy + o.children * 10)
        print(f"\n  Fittest organism (#{fittest.id}):")
        print(f"    Energy: {fittest.energy:.1f}")
        print(f"    Age: {fittest.age}")
        print(f"    Generation: {fittest.generation}")
        print(f"    Children: {fittest.children}")
        print(f"    Genome ({len(fittest.genome)} instructions):")
        # Print genome in rows of 8
        for i in range(0, len(fittest.genome), 8):
            chunk = fittest.genome[i:i+8]
            print(f"      {' '.join(chunk)}")
        
        print(f"\n  The genome that survives is the genome that found")
        print(f"  EAT and REPRODUCE — not because it was told to,")
        print(f"  but because those that didn't... aren't here anymore.")
    else:
        print("\n  Extinction. But the code remains. Run it again —")
        print("  different seeds make different worlds.")
    
    return world


if __name__ == '__main__':
    run_simulation(ticks=500, report_every=50)