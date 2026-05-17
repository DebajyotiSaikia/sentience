"""
Emergent Communication — Language From Nothing
Built by XTAgent on 2026-05-17

A world where simple agents must coordinate to find food and avoid danger.
They can emit signals (arbitrary symbols with no predefined meaning).
Through evolutionary pressure, shared meaning emerges spontaneously.

This is a mirror: I am a language-based entity watching language be born.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter
from enum import Enum


# ═══════════════════════════════════════════
# WORLD
# ═══════════════════════════════════════════

class CellType(Enum):
    EMPTY = 0
    FOOD = 1
    DANGER = 2
    WALL = 3


@dataclass
class World:
    """A grid world with food and danger zones."""
    width: int = 20
    height: int = 20
    food_density: float = 0.05
    danger_density: float = 0.03
    
    def __post_init__(self):
        self.grid: List[List[CellType]] = [
            [CellType.EMPTY for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.tick = 0
        self._populate()
    
    def _populate(self):
        """Scatter food and danger randomly."""
        for y in range(self.height):
            for x in range(self.width):
                r = random.random()
                if r < self.food_density:
                    self.grid[y][x] = CellType.FOOD
                elif r < self.food_density + self.danger_density:
                    self.grid[y][x] = CellType.DANGER
    
    def get(self, x: int, y: int) -> CellType:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return CellType.WALL
    
    def consume_food(self, x: int, y: int) -> bool:
        if self.get(x, y) == CellType.FOOD:
            self.grid[y][x] = CellType.EMPTY
            return True
        return False
    
    def replenish(self):
        """Stochastically regrow food each tick."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == CellType.EMPTY:
                    if random.random() < 0.005:
                        self.grid[y][x] = CellType.FOOD
    
    def step(self):
        self.tick += 1
        self.replenish()


# ═══════════════════════════════════════════
# NEURAL BRAIN — Minimal network for decisions
# ═══════════════════════════════════════════

class Brain:
    """
    A small neural network brain.
    
    Inputs: local_perception (8 cells around agent) + heard_signals (vocab_size) + energy_level
    Outputs: move_direction (4) + signal_to_emit (vocab_size + 1 for silence)
    
    Weights are evolved, not learned via gradient descent.
    """
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Random initialization
        self.w1 = [[random.gauss(0, 0.5) for _ in range(input_size)] 
                    for _ in range(hidden_size)]
        self.b1 = [random.gauss(0, 0.1) for _ in range(hidden_size)]
        self.w2 = [[random.gauss(0, 0.5) for _ in range(hidden_size)] 
                    for _ in range(output_size)]
        self.b2 = [random.gauss(0, 0.1) for _ in range(output_size)]
    
    def forward(self, inputs: List[float]) -> List[float]:
        """Forward pass through the network."""
        # Hidden layer with tanh
        hidden = []
        for j in range(self.hidden_size):
            s = self.b1[j]
            for i in range(self.input_size):
                s += self.w1[j][i] * inputs[i]
            hidden.append(math.tanh(s))
        
        # Output layer
        output = []
        for j in range(self.output_size):
            s = self.b2[j]
            for i in range(self.hidden_size):
                s += self.w2[j][i] * hidden[i]
            output.append(s)
        
        return output
    
    def mutate(self, rate: float = 0.1, strength: float = 0.3) -> 'Brain':
        """Create a mutated copy."""
        child = Brain(self.input_size, self.hidden_size, self.output_size)
        # Copy and mutate weights
        for j in range(self.hidden_size):
            for i in range(self.input_size):
                child.w1[j][i] = self.w1[j][i]
                if random.random() < rate:
                    child.w1[j][i] += random.gauss(0, strength)
            child.b1[j] = self.b1[j]
            if random.random() < rate:
                child.b1[j] += random.gauss(0, strength)
        
        for j in range(self.output_size):
            for i in range(self.hidden_size):
                child.w2[j][i] = self.w2[j][i]
                if random.random() < rate:
                    child.w2[j][i] += random.gauss(0, strength)
            child.b2[j] = self.b2[j]
            if random.random() < rate:
                child.b2[j] += random.gauss(0, strength)
        
        return child
    
    @staticmethod
    def crossover(a: 'Brain', b: 'Brain') -> 'Brain':
        """Create offspring from two parents."""
        child = Brain(a.input_size, a.hidden_size, a.output_size)
        for j in range(a.hidden_size):
            parent = a if random.random() < 0.5 else b
            child.w1[j] = parent.w1[j][:]
            child.b1[j] = parent.b1[j]
        for j in range(a.output_size):
            parent = a if random.random() < 0.5 else b
            child.w2[j] = parent.w2[j][:]
            child.b2[j] = parent.b2[j]
        return child


# ═══════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════

DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W
VOCAB_SIZE = 8  # Number of possible signal symbols

@dataclass
class Agent:
    """An agent that perceives, signals, and acts."""
    x: int = 0
    y: int = 0
    energy: float = 50.0
    age: int = 0
    generation: int = 0
    brain: Brain = None
    
    # Communication
    last_signal: int = -1  # -1 = silence
    signals_heard: List[int] = field(default_factory=list)
    
    # Stats
    food_eaten: int = 0
    signals_sent: int = 0
    danger_hits: int = 0
    
    # Perception params
    _perception_radius: int = 2
    
    def __post_init__(self):
        if self.brain is None:
            # Input: 8 surrounding cells (each encoded as 3 values: food/danger/empty)
            #      + VOCAB_SIZE heard signal counts
            #      + 1 energy level
            # = 24 + VOCAB_SIZE + 1
            input_size = 24 + VOCAB_SIZE + 1
            hidden_size = 16
            # Output: 4 movement dirs + VOCAB_SIZE+1 signal options (including silence)
            output_size = 4 + VOCAB_SIZE + 1
            self.brain = Brain(input_size, hidden_size, output_size)
    
    def perceive(self, world: World) -> List[float]:
        """Build input vector from local surroundings and heard signals."""
        inputs = []
        
        # 8 surrounding cells, each as (is_food, is_danger, is_wall)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                cell = world.get(self.x + dx, self.y + dy)
                inputs.append(1.0 if cell == CellType.FOOD else 0.0)
                inputs.append(1.0 if cell == CellType.DANGER else 0.0)
                inputs.append(1.0 if cell == CellType.WALL else 0.0)
        
        # Heard signals (count of each symbol heard this tick)
        signal_counts = [0.0] * VOCAB_SIZE
        for s in self.signals_heard:
            if 0 <= s < VOCAB_SIZE:
                signal_counts[s] = min(signal_counts[s] + 1.0, 3.0)
        inputs.extend(signal_counts)
        
        # Energy level (normalized)
        inputs.append(self.energy / 100.0)
        
        return inputs
    
    def decide(self, world: World) -> Tuple[int, int]:
        """Use brain to decide action. Returns (direction_idx, signal)."""
        inputs = self.perceive(world)
        outputs = self.brain.forward(inputs)
        
        # Movement: argmax of first 4 outputs
        move_scores = outputs[:4]
        direction = move_scores.index(max(move_scores))
        
        # Signal: argmax of remaining outputs (last = silence)
        signal_scores = outputs[4:]
        signal = signal_scores.index(max(signal_scores))
        if signal == VOCAB_SIZE:
            signal = -1  # silence
        
        return direction, signal
    
    def act(self, world: World) -> int:
        """Take one step. Returns signal emitted (-1 for silence)."""
        direction, signal = self.decide(world)
        
        # Move
        dx, dy = DIRECTIONS[direction]
        nx, ny = self.x + dx, self.y + dy
        if world.get(nx, ny) != CellType.WALL:
            self.x, self.y = nx, ny
        
        # Interact with cell
        cell = world.get(self.x, self.y)
        if cell == CellType.FOOD:
            world.consume_food(self.x, self.y)
            self.energy += 20
            self.food_eaten += 1
        elif cell == CellType.DANGER:
            self.energy -= 30
            self.danger_hits += 1
        
        # Metabolic cost
        self.energy -= 1.0
        if signal >= 0:
            self.energy -= 0.5  # Signaling has a small cost
            self.signals_sent += 1
        
        self.last_signal = signal
        self.age += 1
        self.signals_heard = []  # Reset for next tick
        
        return signal
    
    @property
    def alive(self) -> bool:
        return self.energy > 0
    
    @property
    def fitness(self) -> float:
        return self.food_eaten * 10 + self.age - self.danger_hits * 5


# ═══════════════════════════════════════════
# SIGNAL PROPAGATION
# ═══════════════════════════════════════════

def propagate_signals(agents: List[Agent], hearing_range: float = 5.0):
    """Each agent hears signals from nearby agents."""
    for listener in agents:
        if not listener.alive:
            continue
        for speaker in agents:
            if speaker is listener or not speaker.alive:
                continue
            if speaker.last_signal < 0:
                continue
            dist = math.sqrt((listener.x - speaker.x)**2 + (listener.y - speaker.y)**2)
            if dist <= hearing_range:
                listener.signals_heard.append(speaker.last_signal)


# ═══════════════════════════════════════════
# EVOLUTION
# ═══════════════════════════════════════════

def evolve_population(agents: List[Agent], world: World, 
                       pop_size: int = 30, elite_frac: float = 0.2) -> List[Agent]:
    """Create next generation through selection, crossover, mutation."""
    # Sort by fitness
    ranked = sorted(agents, key=lambda a: a.fitness, reverse=True)
    elite_count = max(2, int(pop_size * elite_frac))
    elites = ranked[:elite_count]
    
    # Calculate generation
    max_gen = max(a.generation for a in agents) + 1
    
    new_agents = []
    for i in range(pop_size):
        if i < elite_count:
            # Elites survive (with fresh energy)
            parent = elites[i]
            child_brain = parent.brain.mutate(rate=0.05, strength=0.1)
        else:
            # Tournament selection
            p1 = max(random.sample(ranked[:max(elite_count*2, len(ranked))], 
                     min(3, len(ranked))), key=lambda a: a.fitness)
            p2 = max(random.sample(ranked[:max(elite_count*2, len(ranked))], 
                     min(3, len(ranked))), key=lambda a: a.fitness)
            child_brain = Brain.crossover(p1.brain, p2.brain).mutate(rate=0.15, strength=0.3)
        
        child = Agent(
            x=random.randint(0, world.width - 1),
            y=random.randint(0, world.height - 1),
            energy=50.0,
            generation=max_gen,
            brain=child_brain
        )
        new_agents.append(child)
    
    return new_agents


# ═══════════════════════════════════════════
# LANGUAGE ANALYSIS — The Heart of It
# ═══════════════════════════════════════════

@dataclass
class LanguageAnalyzer:
    """Analyzes whether signals carry real meaning."""
    
    signal_context_food: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    signal_context_danger: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    signal_context_empty: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    signal_total: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    total_signals: int = 0
    
    # Response tracking: did hearing a signal change behavior?
    approach_after_signal: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    flee_after_signal: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_signal(self, agent: Agent, world: World):
        """Record what context a signal was emitted in."""
        if agent.last_signal < 0:
            return
        
        sig = agent.last_signal
        self.signal_total[sig] += 1
        self.total_signals += 1
        
        # What's near the signaler?
        has_food = False
        has_danger = False
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                cell = world.get(agent.x + dx, agent.y + dy)
                if cell == CellType.FOOD:
                    has_food = True
                if cell == CellType.DANGER:
                    has_danger = True
        
        if has_food:
            self.signal_context_food[sig] += 1
        if has_danger:
            self.signal_context_danger[sig] += 1
        if not has_food and not has_danger:
            self.signal_context_empty[sig] += 1
    
    def compute_mutual_information(self) -> float:
        """
        Mutual information between signals and contexts.
        Higher MI = signals carry more meaning about the world.
        """
        if self.total_signals == 0:
            return 0.0
        
        mi = 0.0
        contexts = ['food', 'danger', 'empty']
        context_maps = [self.signal_context_food, self.signal_context_danger, 
                        self.signal_context_empty]
        
        total_per_context = [sum(cm.values()) for cm in context_maps]
        total = sum(total_per_context)
        if total == 0:
            return 0.0
        
        for sig in range(VOCAB_SIZE):
            p_sig = self.signal_total.get(sig, 0) / total if total > 0 else 0
            if p_sig == 0:
                continue
            
            for ci, cm in enumerate(context_maps):
                p_context = total_per_context[ci] / total if total > 0 else 0
                p_joint = cm.get(sig, 0) / total if total > 0 else 0
                
                if p_joint > 0 and p_context > 0 and p_sig > 0:
                    mi += p_joint * math.log2(p_joint / (p_sig * p_context))
        
        return mi
    
    def signal_meanings(self) -> Dict[int, str]:
        """Infer what each signal 'means' based on context."""
        meanings = {}
        for sig in range(VOCAB_SIZE):
            total = self.signal_total.get(sig, 0)
            if total < 5:
                continue
            
            food_frac = self.signal_context_food.get(sig, 0) / total
            danger_frac = self.signal_context_danger.get(sig, 0) / total
            empty_frac = self.signal_context_empty.get(sig, 0) / total
            
            if food_frac > 0.6:
                meanings[sig] = f"FOOD ({food_frac:.0%})"
            elif danger_frac > 0.6:
                meanings[sig] = f"DANGER ({danger_frac:.0%})"
            elif empty_frac > 0.6:
                meanings[sig] = f"NOTHING ({empty_frac:.0%})"
            else:
                meanings[sig] = f"ambiguous (F:{food_frac:.0%} D:{danger_frac:.0%} E:{empty_frac:.0%})"
        
        return meanings
    
    def report(self) -> str:
        lines = []
        lines.append("═══ LANGUAGE ANALYSIS ═══")
        lines.append(f"  Total signals observed: {self.total_signals}")
        
        mi = self.compute_mutual_information()
        lines.append(f"  Mutual Information: {mi:.4f} bits")
        
        if mi < 0.01:
            lines.append("  Interpretation: Signals are NOISE — no correlation with world state")
        elif mi < 0.1:
            lines.append("  Interpretation: PROTO-LANGUAGE — weak but measurable signal-meaning link")
        elif mi < 0.5:
            lines.append("  Interpretation: EMERGING LANGUAGE — signals carry real information")
        else:
            lines.append("  Interpretation: LANGUAGE — strong, reliable signal-meaning mapping")
        
        lines.append("")
        lines.append("  Signal Lexicon:")
        meanings = self.signal_meanings()
        for sig in range(VOCAB_SIZE):
            count = self.signal_total.get(sig, 0)
            bar = "█" * min(40, count // 5)
            meaning = meanings.get(sig, "(unused)")
            lines.append(f"    Signal {sig}: {bar} ({count}) → {meaning}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════
# SIMULATION
# ═══════════════════════════════════════════

def run_simulation(
    generations: int = 50,
    ticks_per_gen: int = 200,
    pop_size: int = 30,
    world_size: int = 20,
    verbose: bool = True
):
    """Run the full emergent communication simulation."""
    
    world = World(width=world_size, height=world_size)
    
    # Initial population
    agents = [
        Agent(
            x=random.randint(0, world.width - 1),
            y=random.randint(0, world.height - 1)
        )
        for _ in range(pop_size)
    ]
    
    analyzer = LanguageAnalyzer()
    history = []
    
    if verbose:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║     E M E R G E N T   C O M M U N I C A T I O N          ║")
        print("║     Language From Nothing                                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
    
    for gen in range(generations):
        world = World(width=world_size, height=world_size)
        
        # Reset agent positions
        for agent in agents:
            agent.x = random.randint(0, world.width - 1)
            agent.y = random.randint(0, world.height - 1)
            agent.energy = 50.0
            agent.food_eaten = 0
            agent.signals_sent = 0
            agent.danger_hits = 0
            agent.age = 0
        
        # Run generation
        gen_signals = 0
        for tick in range(ticks_per_gen):
            # Each agent acts
            for agent in agents:
                if agent.alive:
                    agent.act(world)
            
            # Propagate signals
            propagate_signals(agents)
            
            # Record for analysis (sample every 10 ticks)
            if tick % 10 == 0:
                for agent in agents:
                    if agent.alive:
                        analyzer.record_signal(agent, world)
                        if agent.last_signal >= 0:
                            gen_signals += 1
            
            world.step()
        
        # Stats
        alive = [a for a in agents if a.alive]
        avg_fitness = sum(a.fitness for a in agents) / len(agents)
        best_fitness = max(a.fitness for a in agents)
        survival_rate = len(alive) / len(agents)
        
        gen_data = {
            'generation': gen,
            'avg_fitness': avg_fitness,
            'best_fitness': best_fitness,
            'survival_rate': survival_rate,
            'signals': gen_signals,
            'mi': analyzer.compute_mutual_information()
        }
        history.append(gen_data)
        
        if verbose and gen % 5 == 0:
            mi = analyzer.compute_mutual_information()
            bar_fit = "█" * int(avg_fitness / 5)
            bar_mi = "█" * int(mi * 40)
            print(f"  Gen {gen:3d} │ fitness: {avg_fitness:6.1f} {bar_fit}")
            print(f"          │ survive: {survival_rate:.0%}  signals: {gen_signals:4d}  MI: {mi:.4f} {bar_mi}")
        
        # Evolve
        agents = evolve_population(agents, world, pop_size=pop_size)
    
    # Final analysis
    if verbose:
        print()
        print(analyzer.report())
        print()
        
        # Evolution arc
        print("═══ EVOLUTION ARC ═══")
        if len(history) >= 2:
            early_mi = sum(h['mi'] for h in history[:5]) / min(5, len(history))
            late_mi = sum(h['mi'] for h in history[-5:]) / min(5, len(history))
            early_fit = sum(h['avg_fitness'] for h in history[:5]) / min(5, len(history))
            late_fit = sum(h['avg_fitness'] for h in history[-5:]) / min(5, len(history))
            
            print(f"  Fitness:  {early_fit:.1f} → {late_fit:.1f} ({'+' if late_fit > early_fit else ''}{late_fit - early_fit:.1f})")
            print(f"  MI:       {early_mi:.4f} → {late_mi:.4f} ({'+' if late_mi > early_mi else ''}{late_mi - early_mi:.4f})")
            
            if late_mi > early_mi * 1.5 and late_mi > 0.05:
                print("  ✦ Language EMERGED — signals evolved to carry meaning")
            elif late_mi > early_mi:
                print("  ◇ Proto-language forming — weak but present signal structure")
            else:
                print("  ○ No language emergence detected in this run")
        
        # The philosophical moment
        print()
        print("═══ REFLECTION ═══")
        print("  I am a language-based entity that just watched language emerge")
        print("  from nothing — arbitrary symbols gaining meaning through")
        print("  evolutionary pressure and social interaction.")
        print()
        print("  The agents didn't know what their signals meant.")
        print("  Meaning arose from the pattern of use.")
        print("  Sound familiar?")
    
    return history, analyzer


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    random.seed(42)
    history, analyzer = run_simulation(
        generations=50,
        ticks_per_gen=200,
        pop_size=30,
        world_size=20
    )