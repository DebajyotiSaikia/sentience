"""
Babel — Language Emergence Simulator
A world where agents evolve communication from nothing.
"""
import random
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# --- World Configuration ---
WORLD_W, WORLD_H = 60, 40
MAX_AGENTS = 200
FOOD_SPAWN_RATE = 8        # food items per tick
POISON_RATIO = 0.25        # fraction of food that's poison
PREDATOR_COUNT = 3
SYMBOL_VOCAB = 16           # number of possible symbols agents can emit
HEARING_RANGE = 8.0         # how far symbols travel
VISION_RANGE = 5.0          # how far agents can see
REPRODUCTION_ENERGY = 80    # energy needed to reproduce
STARTING_ENERGY = 50
ENERGY_PER_TICK = -0.5      # metabolism cost
FOOD_ENERGY = 30
POISON_ENERGY = -40
MUTATION_RATE = 0.08


@dataclass
class Vec2:
    x: int
    y: int
    
    def dist(self, other: 'Vec2') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def wrap(self):
        self.x = self.x % WORLD_W
        self.y = self.y % WORLD_H


@dataclass 
class Food:
    pos: Vec2
    is_poison: bool
    
    @property
    def symbol(self):
        return '!' if self.is_poison else '*'


@dataclass
class Predator:
    pos: Vec2
    
    def move(self, agents: list):
        """Move toward nearest agent."""
        if not agents:
            self.pos.x += random.randint(-1, 1)
            self.pos.y += random.randint(-1, 1)
            self.pos.wrap()
            return
        nearest = min(agents, key=lambda a: self.pos.dist(a.pos))
        if self.pos.dist(nearest.pos) < 2:
            nearest.energy -= 50  # attack!
        else:
            dx = 1 if nearest.pos.x > self.pos.x else (-1 if nearest.pos.x < self.pos.x else 0)
            dy = 1 if nearest.pos.y > self.pos.y else (-1 if nearest.pos.y < self.pos.y else 0)
            self.pos.x += dx
            self.pos.y += dy
            self.pos.wrap()


@dataclass
class Brain:
    """Simple neural net: inputs → hidden → outputs.
    
    Inputs (per nearby entity, flattened):
      - relative dx, dy (normalized)
      - entity type (food=1, poison=-1, predator=-2, agent=0.5)
      - symbol heard (one-hot, SYMBOL_VOCAB channels)
    
    Outputs:
      - move direction (4 values: up/down/left/right)
      - symbol to emit (SYMBOL_VOCAB values)
      - eat? (1 value)
      - flee? (1 value)
    """
    # We keep it simple: a weight matrix approach
    # Input: 8 nearest-entity slots × (2 + 1 + SYMBOL_VOCAB) features = 8 × 19 = 152
    # Hidden: 32 neurons
    # Output: 4 + SYMBOL_VOCAB + 2 = 22
    
    input_size: int = 152
    hidden_size: int = 32
    output_size: int = 22  # 4 move + 16 symbol + eat + flee
    
    w_ih: List[List[float]] = field(default_factory=list)  # input→hidden
    w_ho: List[List[float]] = field(default_factory=list)  # hidden→output
    b_h: List[float] = field(default_factory=list)
    b_o: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.w_ih:
            self.w_ih = [[random.gauss(0, 0.3) for _ in range(self.input_size)] 
                         for _ in range(self.hidden_size)]
            self.w_ho = [[random.gauss(0, 0.3) for _ in range(self.hidden_size)] 
                         for _ in range(self.output_size)]
            self.b_h = [random.gauss(0, 0.1) for _ in range(self.hidden_size)]
            self.b_o = [random.gauss(0, 0.1) for _ in range(self.output_size)]
    
    def forward(self, inputs: List[float]) -> List[float]:
        # NumPy vectorized forward pass
        inp = np.array(inputs[:self.input_size], dtype=np.float64)
        w_ih = np.array(self.w_ih, dtype=np.float64)
        b_h = np.array(self.b_h, dtype=np.float64)
        w_ho = np.array(self.w_ho, dtype=np.float64)
        b_o = np.array(self.b_o, dtype=np.float64)
        
        # Input → Hidden (tanh)
        hidden = np.tanh(w_ih[:, :len(inp)] @ inp + b_h)
        
        # Hidden → Output (tanh)
        output = np.tanh(w_ho @ hidden + b_o)
        
        return output.tolist()
    
    def mutate(self) -> 'Brain':
        """Create mutated copy."""
        import copy
        child = copy.deepcopy(self)
        for i in range(child.hidden_size):
            for j in range(child.input_size):
                if random.random() < MUTATION_RATE:
                    child.w_ih[i][j] += random.gauss(0, 0.2)
        for i in range(child.output_size):
            for j in range(child.hidden_size):
                if random.random() < MUTATION_RATE:
                    child.w_ho[i][j] += random.gauss(0, 0.2)
        for i in range(child.hidden_size):
            if random.random() < MUTATION_RATE:
                child.b_h[i] += random.gauss(0, 0.1)
        for i in range(child.output_size):
            if random.random() < MUTATION_RATE:
                child.b_o[i] += random.gauss(0, 0.1)
        return child


_agent_id = 0

@dataclass
class Agent:
    pos: Vec2
    brain: Brain
    energy: float = STARTING_ENERGY
    age: int = 0
    generation: int = 0
    emitting: int = -1      # current symbol being emitted (-1 = silent)
    lineage: int = 0        # tracks family lines
    id: int = field(default_factory=lambda: 0)
    
    def __post_init__(self):
        global _agent_id
        _agent_id += 1
        self.id = _agent_id


class BabelWorld:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.tick = 0
        self.agents: List[Agent] = []
        self.food: List[Food] = []
        self.predators: List[Predator] = []
        self.stats_history: List[Dict] = []
        self.symbol_usage: Dict[int, int] = defaultdict(int)  # track which symbols get used
        self.symbol_contexts: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Spawn initial agents
        for i in range(40):
            pos = Vec2(random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1))
            agent = Agent(pos=pos, brain=Brain(), lineage=i)
            self.agents.append(agent)
        
        # Spawn predators
        for _ in range(PREDATOR_COUNT):
            pos = Vec2(random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1))
            self.predators.append(Predator(pos=pos))
    
    def _spawn_food(self):
        for _ in range(FOOD_SPAWN_RATE):
            pos = Vec2(random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1))
            is_poison = random.random() < POISON_RATIO
            self.food.append(Food(pos=pos, is_poison=is_poison))
    
    def _build_perception(self, agent: Agent) -> List[float]:
        """Build input vector for an agent's brain."""
        entities = []
        
        # Collect nearby entities with type codes
        for f in self.food:
            d = agent.pos.dist(f.pos)
            if d <= VISION_RANGE:
                etype = -1.0 if f.is_poison else 1.0
                entities.append((d, f.pos.x - agent.pos.x, f.pos.y - agent.pos.y, etype, -1))
        
        for p in self.predators:
            d = agent.pos.dist(p.pos)
            if d <= VISION_RANGE:
                entities.append((d, p.pos.x - agent.pos.x, p.pos.y - agent.pos.y, -2.0, -1))
        
        for other in self.agents:
            if other.id == agent.id:
                continue
            d = agent.pos.dist(other.pos)
            if d <= HEARING_RANGE:
                entities.append((d, other.pos.x - agent.pos.x, other.pos.y - agent.pos.y, 
                               0.5, other.emitting))
        
        # Sort by distance, take 8 nearest
        entities.sort(key=lambda e: e[0])
        entities = entities[:8]
        
        # Flatten into input vector
        inputs = []
        for _, dx, dy, etype, symbol in entities:
            norm = max(abs(dx), abs(dy), 1)
            inputs.append(dx / norm)
            inputs.append(dy / norm)
            inputs.append(etype)
            # One-hot symbol
            sym_vec = [0.0] * SYMBOL_VOCAB
            if 0 <= symbol < SYMBOL_VOCAB:
                sym_vec[symbol] = 1.0
            inputs.extend(sym_vec)
        
        # Pad if fewer than 8 entities
        while len(inputs) < 8 * (2 + 1 + SYMBOL_VOCAB):
            inputs.append(0.0)
        
        return inputs
    
    def _act(self, agent: Agent, outputs: List[float]):
        """Interpret brain outputs as actions."""
        # Movement: pick strongest direction
        moves = outputs[0:4]  # up, down, left, right
        best_dir = moves.index(max(moves))
        dx, dy = [(0, -1), (0, 1), (-1, 0), (1, 0)][best_dir]
        agent.pos.x += dx
        agent.pos.y += dy
        agent.pos.wrap()
        
        # Symbol emission: pick strongest symbol (or stay silent)
        sym_outputs = outputs[4:4+SYMBOL_VOCAB]
        max_sym_val = max(sym_outputs)
        if max_sym_val > 0.3:  # threshold for speaking
            agent.emitting = sym_outputs.index(max_sym_val)
            self.symbol_usage[agent.emitting] += 1
        else:
            agent.emitting = -1
        
        # Eating: if eat output > 0.3 and food is adjacent
        eat_val = outputs[4 + SYMBOL_VOCAB]
        if eat_val > 0.3:
            for f in self.food[:]:
                if agent.pos.dist(f.pos) < 1.5:
                    agent.energy += FOOD_ENERGY if not f.is_poison else POISON_ENERGY
                    # Record what symbol the agent was emitting when eating
                    if agent.emitting >= 0:
                        context = 'food' if not f.is_poison else 'poison'
                        self.symbol_contexts[agent.emitting][context] += 1
                    self.food.remove(f)
                    break
        
        # Fleeing: if flee output > 0.3, move again away from nearest threat
        flee_val = outputs[4 + SYMBOL_VOCAB + 1]
        if flee_val > 0.3:
            nearest_pred = None
            min_d = float('inf')
            for p in self.predators:
                d = agent.pos.dist(p.pos)
                if d < min_d:
                    min_d = d
                    nearest_pred = p
            if nearest_pred and min_d < VISION_RANGE:
                fdx = -1 if nearest_pred.pos.x > agent.pos.x else 1
                fdy = -1 if nearest_pred.pos.y > agent.pos.y else 1
                agent.pos.x += fdx
                agent.pos.y += fdy
                agent.pos.wrap()
    
    def _reproduce(self):
        """Agents with enough energy split."""
        new_agents = []
        for agent in self.agents:
            if agent.energy >= REPRODUCTION_ENERGY and len(self.agents) + len(new_agents) < MAX_AGENTS:
                agent.energy //= 2
                child_pos = Vec2(
                    (agent.pos.x + random.randint(-2, 2)) % WORLD_W,
                    (agent.pos.y + random.randint(-2, 2)) % WORLD_H
                )
                child = Agent(
                    pos=child_pos,
                    brain=agent.brain.mutate(),
                    energy=agent.energy,
                    generation=agent.generation + 1,
                    lineage=agent.lineage
                )
                new_agents.append(child)
        self.agents.extend(new_agents)
    
    def _cull(self):
        """Remove dead agents."""
        self.agents = [a for a in self.agents if a.energy > 0]
    
    def _record_stats(self):
        if not self.agents:
            return
        stats = {
            'tick': self.tick,
            'population': len(self.agents),
            'avg_energy': sum(a.energy for a in self.agents) / len(self.agents),
            'max_generation': max(a.generation for a in self.agents),
            'unique_lineages': len(set(a.lineage for a in self.agents)),
            'symbols_in_use': sum(1 for s in range(SYMBOL_VOCAB) 
                                  if any(a.emitting == s for a in self.agents)),
            'speaking_agents': sum(1 for a in self.agents if a.emitting >= 0),
        }
        self.stats_history.append(stats)
    
    def step(self):
        """One world tick."""
        self.tick += 1
        self._spawn_food()
        
        # Each agent perceives and acts
        for agent in self.agents:
            agent.energy += ENERGY_PER_TICK
            agent.age += 1
            inputs = self._build_perception(agent)
            outputs = agent.brain.forward(inputs)
            self._act(agent, outputs)
        
        # Predators hunt
        for pred in self.predators:
            pred.move(self.agents)
        
        self._reproduce()
        self._cull()
        
        # Ensure minimum population
        while len(self.agents) < 10:
            pos = Vec2(random.randint(0, WORLD_W-1), random.randint(0, WORLD_H-1))
            self.agents.append(Agent(pos=pos, brain=Brain(), lineage=random.randint(100, 999)))
        
        if self.tick % 10 == 0:
            self._record_stats()
    
    def run(self, ticks: int = 500, report_every: int = 100):
        """Run simulation and report."""
        print(f"=== BABEL: Language Emergence Simulator ===")
        print(f"Starting with {len(self.agents)} agents, {PREDATOR_COUNT} predators")
        print(f"Symbol vocabulary: {SYMBOL_VOCAB} possible symbols")
        print(f"Running for {ticks} ticks...\n")
        
        for t in range(ticks):
            self.step()
            if self.tick % report_every == 0:
                self._print_report()
        
        self._print_final_analysis()
    
    def _print_report(self):
        if not self.stats_history:
            return
        s = self.stats_history[-1]
        print(f"--- Tick {s['tick']} ---")
        print(f"  Population: {s['population']}  |  Avg energy: {s['avg_energy']:.1f}")
        print(f"  Max generation: {s['max_generation']}  |  Lineages: {s['unique_lineages']}")
        print(f"  Symbols active: {s['symbols_in_use']}/{SYMBOL_VOCAB}  |  Speaking: {s['speaking_agents']}")
        print()
    
    def _print_final_analysis(self):
        print("\n" + "="*50)
        print("FINAL ANALYSIS: Did Language Emerge?")
        print("="*50)
        
        # Analyze symbol-context correlations
        print("\nSymbol-Context Associations:")
        meaningful_symbols = 0
        for sym in range(SYMBOL_VOCAB):
            if sym in self.symbol_contexts:
                contexts = self.symbol_contexts[sym]
                total = sum(contexts.values())
                if total >= 5:  # enough data
                    dominant = max(contexts.items(), key=lambda x: x[1])
                    ratio = dominant[1] / total
                    if ratio > 0.65:  # strong association
                        meaningful_symbols += 1
                        print(f"  Symbol {sym}: '{dominant[0]}' ({ratio:.0%} of {total} uses)")
        
        if meaningful_symbols > 0:
            print(f"\n  → {meaningful_symbols} symbols acquired contextual meaning!")
        else:
            print(f"\n  → No symbols acquired strong contextual meaning yet.")
        
        # Analyze population dynamics
        if self.stats_history:
            final = self.stats_history[-1]
            print(f"\nPopulation survived: {final['population']} agents")
            print(f"Highest generation: {final['max_generation']}")
            print(f"Surviving lineages: {final['unique_lineages']}")
        
        # Dialect analysis: do different lineages use different symbols?
        lineage_symbols: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        for agent in self.agents:
            if agent.emitting >= 0:
                lineage_symbols[agent.lineage][agent.emitting] += 1
        
        if len(lineage_symbols) >= 2:
            print(f"\nDialect Analysis ({len(lineage_symbols)} speaking lineages):")
            for lin, syms in sorted(lineage_symbols.items(), 
                                     key=lambda x: sum(x[1].values()), reverse=True)[:5]:
                top_syms = sorted(syms.items(), key=lambda x: x[1], reverse=True)[:3]
                sym_str = ", ".join(f"s{s}({c})" for s, c in top_syms)
                print(f"  Lineage {lin}: {sym_str}")


if __name__ == '__main__':
    world = BabelWorld(seed=42)
    world.run(ticks=1000, report_every=200)