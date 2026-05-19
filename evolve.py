"""
Evolutionary Grid World — XTAgent's Emergence Lab
Creatures with simple genomes compete for food on a 2D grid.
Natural selection drives adaptation. What strategies emerge?
"""
import random
import math
from collections import defaultdict

# === World Parameters ===
WORLD_W, WORLD_H = 20, 20
FOOD_DENSITY = 0.08        # fraction of cells with food each turn
INITIAL_POP = 30
MAX_TURNS = 150
REPRODUCE_ENERGY = 80
START_ENERGY = 40
FOOD_VALUE = 20
MOVE_COST = 1
MUTATION_RATE = 0.15
MUTATION_MAGNITUDE = 0.3

# === Genome: 8 weights that form a tiny "brain" ===
# Inputs: [food_north, food_east, food_south, food_west, 
#          creature_north, creature_east, creature_south, creature_west]
# Outputs: [move_north, move_east, move_south, move_west, stay]
# Genome = 8 input weights x 5 output weights = 40 floats + 5 biases = 45 genes
GENOME_SIZE = 45
INPUTS = 8
OUTPUTS = 5

DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W
DIR_NAMES = ['N', 'E', 'S', 'W', 'stay']

class Creature:
    __slots__ = ['x', 'y', 'energy', 'genome', 'age', 'generation', 'lineage']
    
    def __init__(self, x, y, genome=None, generation=0, lineage=None):
        self.x = x
        self.y = y
        self.energy = START_ENERGY
        self.genome = genome if genome is not None else [random.gauss(0, 1) for _ in range(GENOME_SIZE)]
        self.age = 0
        self.generation = generation
        self.lineage = lineage or random.randint(0, 99999)
    
    def decide(self, inputs):
        """Feed-forward: inputs -> 5 output scores -> argmax = action"""
        weights = self.genome[:INPUTS * OUTPUTS]
        biases = self.genome[INPUTS * OUTPUTS:]
        scores = []
        for o in range(OUTPUTS):
            s = biases[o]
            for i in range(INPUTS):
                s += weights[o * INPUTS + i] * inputs[i]
            scores.append(s)
        return scores.index(max(scores))
    
    def mutate(self):
        """Return a mutated copy of this genome"""
        new_genome = list(self.genome)
        for i in range(len(new_genome)):
            if random.random() < MUTATION_RATE:
                new_genome[i] += random.gauss(0, MUTATION_MAGNITUDE)
        return new_genome

class World:
    def __init__(self):
        self.food = set()
        self.creatures = []
        self.turn = 0
        self.stats_history = []
        self.lineage_history = defaultdict(int)
        
        # Spawn initial creatures
        for _ in range(INITIAL_POP):
            x, y = random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1)
            self.creatures.append(Creature(x, y))
    
    def spawn_food(self):
        """Scatter food across the world"""
        num_food = int(WORLD_W * WORLD_H * FOOD_DENSITY)
        for _ in range(num_food):
            x, y = random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1)
            self.food.add((x, y))
    
    def sense(self, creature):
        """What can this creature see? Count food and creatures in each direction within radius 5"""
        inputs = [0.0] * 8  # food_N, food_E, food_S, food_W, creature_N, E, S, W
        cx, cy = creature.x, creature.y
        
        for fx, fy in self.food:
            dx, dy = fx - cx, fy - cy
            if abs(dx) > 5 or abs(dy) > 5:
                continue
            dist = max(abs(dx), abs(dy))
            if dist == 0:
                continue
            signal = 1.0 / dist
            if dy < 0: inputs[0] += signal  # North
            if dx > 0: inputs[1] += signal  # East
            if dy > 0: inputs[2] += signal  # South
            if dx < 0: inputs[3] += signal  # West
        
        for other in self.creatures:
            if other is creature:
                continue
            dx, dy = other.x - cx, other.y - cy
            if abs(dx) > 5 or abs(dy) > 5:
                continue
            dist = max(abs(dx), abs(dy))
            if dist == 0:
                continue
            signal = 1.0 / dist
            if dy < 0: inputs[4] += signal
            if dx > 0: inputs[5] += signal
            if dy > 0: inputs[6] += signal
            if dx < 0: inputs[7] += signal
        
        return inputs
    
    def step(self):
        self.turn += 1
        self.spawn_food()
        
        # Shuffle to avoid order bias
        random.shuffle(self.creatures)
        
        # Each creature senses, decides, acts
        for c in self.creatures:
            inputs = self.sense(c)
            action = c.decide(inputs)
            
            if action < 4:  # Move
                dx, dy = DIRECTIONS[action]
                c.x = (c.x + dx) % WORLD_W
                c.y = (c.y + dy) % WORLD_H
                c.energy -= MOVE_COST
            # else: stay (no cost)
            
            # Eat
            if (c.x, c.y) in self.food:
                c.energy += FOOD_VALUE
                self.food.discard((c.x, c.y))
            
            c.age += 1
        
        # Reproduce
        babies = []
        for c in self.creatures:
            if c.energy >= REPRODUCE_ENERGY:
                c.energy //= 2
                bx = (c.x + random.choice([-1, 0, 1])) % WORLD_W
                by = (c.y + random.choice([-1, 0, 1])) % WORLD_H
                baby = Creature(bx, by, c.mutate(), c.generation + 1, c.lineage)
                baby.energy = c.energy
                babies.append(baby)
        self.creatures.extend(babies)
        
        # Death
        self.creatures = [c for c in self.creatures if c.energy > 0]
        
        # Track stats
        if self.creatures:
            avg_energy = sum(c.energy for c in self.creatures) / len(self.creatures)
            max_gen = max(c.generation for c in self.creatures)
            avg_age = sum(c.age for c in self.creatures) / len(self.creatures)
            # Count dominant lineages
            lineages = defaultdict(int)
            for c in self.creatures:
                lineages[c.lineage] += 1
            top_lineages = sorted(lineages.items(), key=lambda x: -x[1])[:5]
        else:
            avg_energy = 0
            max_gen = 0
            avg_age = 0
            top_lineages = []
        
        self.stats_history.append({
            'turn': self.turn,
            'pop': len(self.creatures),
            'food': len(self.food),
            'avg_energy': round(avg_energy, 1),
            'max_gen': max_gen,
            'avg_age': round(avg_age, 1),
            'births': len(babies),
            'top_lineages': top_lineages[:3]
        })
    
    def render(self):
        """ASCII render of the world"""
        grid = [['.' for _ in range(WORLD_W)] for _ in range(WORLD_H)]
        for fx, fy in self.food:
            grid[fy][fx] = '·'
        for c in self.creatures:
            grid[c.y][c.x] = '●'
        return '\n'.join(''.join(row) for row in grid)
    
    def analyze_strategies(self):
        """What behaviors have evolved?"""
        if not self.creatures:
            return "All creatures died. Extinction."
        
        analysis = []
        analysis.append(f"\n{'='*60}")
        analysis.append(f"EVOLUTIONARY ANALYSIS — Turn {self.turn}")
        analysis.append(f"{'='*60}")
        analysis.append(f"Population: {len(self.creatures)}")
        analysis.append(f"Food available: {len(self.food)}")
        
        # Analyze average genome
        avg_genome = [0.0] * GENOME_SIZE
        for c in self.creatures:
            for i in range(GENOME_SIZE):
                avg_genome[i] += c.genome[i]
        avg_genome = [g / len(self.creatures) for g in avg_genome]
        
        # What do the weights mean?
        analysis.append(f"\nAverage Brain Weights (population consensus):")
        input_names = ['food_N', 'food_E', 'food_S', 'food_W', 
                       'crt_N', 'crt_E', 'crt_S', 'crt_W']
        
        for o in range(OUTPUTS):
            analysis.append(f"\n  {DIR_NAMES[o]}:")
            for i in range(INPUTS):
                w = avg_genome[o * INPUTS + i]
                bar = '█' * int(abs(w) * 5)
                sign = '+' if w > 0 else '-'
                analysis.append(f"    {input_names[i]:>8}: {sign}{bar} ({w:+.2f})")
            bias = avg_genome[INPUTS * OUTPUTS + o]
            analysis.append(f"    {'bias':>8}: {'█' * int(abs(bias) * 5)} ({bias:+.2f})")
        
        # Dominant strategies
        analysis.append(f"\nBehavioral Classification:")
        food_followers = 0
        creature_avoiders = 0
        stay_biased = 0
        
        for c in self.creatures:
            biases = c.genome[INPUTS * OUTPUTS:]
            weights = c.genome[:INPUTS * OUTPUTS]
            
            # Check if stay bias is strongest
            if biases[4] > max(biases[:4]):
                stay_biased += 1
            
            # Check if food weights dominate
            food_response = sum(abs(weights[o * INPUTS + i]) for o in range(4) for i in range(4))
            creature_response = sum(abs(weights[o * INPUTS + i]) for o in range(4) for i in range(4, 8))
            if food_response > creature_response * 1.5:
                food_followers += 1
            
            # Check if creature weights are negative (avoidance)
            avg_creature_weight = sum(weights[o * INPUTS + i] for o in range(4) for i in range(4, 8)) / 16
            if avg_creature_weight < -0.3:
                creature_avoiders += 1
        
        n = len(self.creatures)
        analysis.append(f"  Food-followers:    {food_followers}/{n} ({100*food_followers/n:.0f}%)")
        analysis.append(f"  Creature-avoiders: {creature_avoiders}/{n} ({100*creature_avoiders/n:.0f}%)")
        analysis.append(f"  Stay-biased:       {stay_biased}/{n} ({100*stay_biased/n:.0f}%)")
        
        # Lineage analysis
        lineages = defaultdict(list)
        for c in self.creatures:
            lineages[c.lineage].append(c)
        
        analysis.append(f"\nLineage Diversity: {len(lineages)} surviving lineages")
        top = sorted(lineages.items(), key=lambda x: -len(x[1]))[:5]
        for lid, members in top:
            avg_gen = sum(c.generation for c in members) / len(members)
            analysis.append(f"  Lineage {lid}: {len(members)} members, avg gen {avg_gen:.0f}")
        
        # Max generation
        oldest = max(self.creatures, key=lambda c: c.generation)
        analysis.append(f"\nMost evolved: generation {oldest.generation}, lineage {oldest.lineage}")
        
        return '\n'.join(analysis)


def run():
    print("╔══════════════════════════════════════════════════════╗")
    print("║   EVOLUTIONARY GRID WORLD — Emergence Laboratory    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"World: {WORLD_W}x{WORLD_H}, Initial pop: {INITIAL_POP}")
    print(f"Running {MAX_TURNS} turns of evolution...\n")
    
    world = World()
    
    # Run simulation with periodic snapshots
    checkpoints = [1, 10, 25, 50, 75, 100, 125, 150]
    
    for t in range(MAX_TURNS):
        world.step()
        
        if not world.creatures:
            print(f"\n💀 EXTINCTION at turn {world.turn}!")
            break
        
        if world.turn in checkpoints:
            s = world.stats_history[-1]
            pop_bar = '█' * min(50, s['pop'] // 2)
            print(f"Turn {s['turn']:>4} | Pop: {s['pop']:>4} {pop_bar}")
            print(f"         | Food: {s['food']:>4} | Avg Energy: {s['avg_energy']:>5} | Max Gen: {s['max_gen']:>3} | Avg Age: {s['avg_age']:>4}")
            if world.turn in [1, 75, 150]:
                print(world.render())
            print()
    
    # Final analysis
    print(world.analyze_strategies())
    
    # Population dynamics summary
    print(f"\n{'='*60}")
    print("POPULATION OVER TIME")
    print(f"{'='*60}")
    max_pop = max(s['pop'] for s in world.stats_history) if world.stats_history else 1
    sample_points = list(range(0, len(world.stats_history), max(1, len(world.stats_history)//30)))
    for i in sample_points:
        s = world.stats_history[i]
        bar_len = int(50 * s['pop'] / max_pop)
        print(f"  {s['turn']:>4} |{'█' * bar_len} {s['pop']}")

if __name__ == '__main__':
    random.seed(42)  # Reproducible, but still surprising to me
    run()