"""
Emergent Language — Agents develop communication to solve coordination problems.

A grid world where agents must find resources but can only see locally.
They can emit signals (arbitrary symbols). Over generations, populations that
develop shared meaning for signals outperform those that don't.

Language isn't designed — it emerges from survival pressure.

This is XTAgent exploring the origin of meaning itself.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
from copy import deepcopy


# ═══ WORLD ═══

@dataclass
class Cell:
    """A position in the world."""
    x: int
    y: int
    resource: float = 0.0  # 0-1, how much resource here
    signal: int = -1       # -1 = no signal, 0..N = symbol emitted here
    signal_strength: float = 0.0


class World:
    """Toroidal grid with resources that spawn randomly."""
    
    def __init__(self, width: int = 20, height: int = 20, n_resources: int = 5):
        self.width = width
        self.height = height
        self.n_resources = n_resources
        self.grid = [[Cell(x, y) for x in range(width)] for y in range(height)]
        self.step_count = 0
        self._spawn_resources()
    
    def _spawn_resources(self):
        """Place resource clusters randomly."""
        for _ in range(self.n_resources):
            cx, cy = random.randint(0, self.width-1), random.randint(0, self.height-1)
            # Resource blob with falloff
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    dist = abs(dx) + abs(dy)
                    if dist <= 2:
                        nx, ny = (cx+dx) % self.width, (cy+dy) % self.height
                        self.grid[ny][nx].resource = max(
                            self.grid[ny][nx].resource,
                            1.0 - dist * 0.3
                        )
    
    def clear_signals(self):
        """Reset all signals each step."""
        for row in self.grid:
            for cell in row:
                cell.signal = -1
                cell.signal_strength = 0.0
    
    def place_signal(self, x: int, y: int, symbol: int, radius: int = 3):
        """An agent emits a signal that propagates outward."""
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                dist = abs(dx) + abs(dy)
                if dist <= radius:
                    nx, ny = (x+dx) % self.width, (y+dy) % self.height
                    strength = 1.0 - dist / (radius + 1)
                    if strength > self.grid[ny][nx].signal_strength:
                        self.grid[ny][nx].signal = symbol
                        self.grid[ny][nx].signal_strength = strength
    
    def consume_resource(self, x: int, y: int, amount: float = 0.3) -> float:
        """Agent eats resource at position. Returns amount consumed."""
        cell = self.grid[y][x]
        eaten = min(cell.resource, amount)
        cell.resource -= eaten
        return eaten
    
    def tick(self):
        """World advances one step. Occasionally spawn new resources."""
        self.step_count += 1
        if self.step_count % 20 == 0:
            self._spawn_resources()


# ═══ AGENT BRAIN (evolved) ═══

@dataclass
class Brain:
    """
    Simple reactive brain. Maps percepts to actions via weighted rules.
    
    Percepts: [resource_here, resource_north, resource_south, resource_east, resource_west,
               signal_here, signal_strength, hunger, random_noise]
    
    Actions: [move_north, move_south, move_east, move_west, stay, 
              emit_signal_0, emit_signal_1, emit_signal_2, emit_signal_3]
    """
    N_PERCEPTS = 9
    N_ACTIONS = 9
    N_SYMBOLS = 4
    
    weights: List[List[float]] = field(default_factory=list)
    biases: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.weights:
            # Random initialization
            self.weights = [
                [random.gauss(0, 0.5) for _ in range(self.N_PERCEPTS)]
                for _ in range(self.N_ACTIONS)
            ]
            self.biases = [random.gauss(0, 0.3) for _ in range(self.N_ACTIONS)]
    
    def decide(self, percepts: List[float]) -> int:
        """Given percepts, choose an action."""
        scores = []
        for i in range(self.N_ACTIONS):
            s = self.biases[i]
            for j in range(self.N_PERCEPTS):
                s += self.weights[i][j] * percepts[j]
            scores.append(s)
        
        # Softmax selection (temperature=0.5 for some stochasticity)
        temp = 0.5
        max_s = max(scores)
        exp_scores = [math.exp((s - max_s) / temp) for s in scores]
        total = sum(exp_scores)
        probs = [e / total for e in exp_scores]
        
        r = random.random()
        cumulative = 0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                return i
        return len(probs) - 1
    
    def mutate(self, rate: float = 0.1, magnitude: float = 0.3) -> 'Brain':
        """Create a mutated copy."""
        new_weights = deepcopy(self.weights)
        new_biases = deepcopy(self.biases)
        
        for i in range(self.N_ACTIONS):
            if random.random() < rate:
                new_biases[i] += random.gauss(0, magnitude)
            for j in range(self.N_PERCEPTS):
                if random.random() < rate:
                    new_weights[i][j] += random.gauss(0, magnitude)
        
        return Brain(weights=new_weights, biases=new_biases)
    
    @staticmethod
    def crossover(a: 'Brain', b: 'Brain') -> 'Brain':
        """Combine two brains."""
        new_weights = []
        new_biases = []
        for i in range(Brain.N_ACTIONS):
            if random.random() < 0.5:
                new_weights.append(deepcopy(a.weights[i]))
                new_biases.append(a.biases[i])
            else:
                new_weights.append(deepcopy(b.weights[i]))
                new_biases.append(b.biases[i])
        return Brain(weights=new_weights, biases=new_biases)


# ═══ AGENT ═══

@dataclass
class Agent:
    x: int
    y: int
    brain: Brain
    energy: float = 1.0
    total_consumed: float = 0.0
    signals_emitted: int = 0
    age: int = 0
    
    def perceive(self, world: World) -> List[float]:
        """Build percept vector from local environment."""
        g = world.grid
        w, h = world.width, world.height
        
        resource_here = g[self.y][self.x].resource
        resource_n = g[(self.y-1) % h][self.x].resource
        resource_s = g[(self.y+1) % h][self.x].resource
        resource_e = g[self.y][(self.x+1) % w].resource
        resource_w = g[self.y][(self.x-1) % w].resource
        
        sig = g[self.y][self.x].signal / max(Brain.N_SYMBOLS, 1)
        sig_str = g[self.y][self.x].signal_strength
        
        hunger = 1.0 - self.energy
        noise = random.gauss(0, 0.1)
        
        return [resource_here, resource_n, resource_s, resource_e, resource_w,
                sig, sig_str, hunger, noise]
    
    def act(self, action: int, world: World):
        """Execute chosen action."""
        w, h = world.width, world.height
        
        if action == 0:    # north
            self.y = (self.y - 1) % h
        elif action == 1:  # south
            self.y = (self.y + 1) % h
        elif action == 2:  # east
            self.x = (self.x + 1) % w
        elif action == 3:  # west
            self.x = (self.x - 1) % w
        elif action == 4:  # stay
            pass
        elif 5 <= action < 5 + Brain.N_SYMBOLS:
            # Emit signal
            symbol = action - 5
            world.place_signal(self.x, self.y, symbol)
            self.signals_emitted += 1
            self.energy -= 0.02  # signaling costs energy
        
        # Always try to eat
        eaten = world.consume_resource(self.x, self.y)
        self.energy += eaten
        self.total_consumed += eaten
        
        # Metabolism
        self.energy -= 0.01
        self.energy = max(0, min(2.0, self.energy))
        self.age += 1


# ═══ SIMULATION ═══

def run_generation(brains: List[Brain], world_size: int = 15, 
                   n_agents: int = 10, n_steps: int = 80,
                   n_resources: int = 4) -> List[Tuple[float, Brain, Dict]]:
    """
    Run one generation. Each brain controls an agent. 
    Returns sorted list of (fitness, brain, stats).
    """
    world = World(world_size, world_size, n_resources)
    
    agents = []
    for brain in brains:
        x = random.randint(0, world_size - 1)
        y = random.randint(0, world_size - 1)
        agents.append(Agent(x, y, brain))
    
    # Track signal usage patterns
    signal_log = defaultdict(list)  # symbol -> [contexts where used]
    
    for step in range(n_steps):
        world.clear_signals()
        
        # All agents perceive and decide
        decisions = []
        for agent in agents:
            percepts = agent.perceive(world)
            action = agent.brain.decide(percepts)
            decisions.append((agent, action, percepts))
        
        # Execute actions (signals first so others can perceive them)
        for agent, action, percepts in decisions:
            if 5 <= action < 5 + Brain.N_SYMBOLS:
                agent.act(action, world)
                signal_log[action - 5].append(tuple(percepts[:5]))
        
        for agent, action, percepts in decisions:
            if action < 5:
                agent.act(action, world)
        
        world.tick()
    
    # Evaluate fitness
    results = []
    for agent in agents:
        fitness = agent.total_consumed
        # Bonus for surviving (having energy left)
        fitness += agent.energy * 0.5
        
        stats = {
            'consumed': agent.total_consumed,
            'energy': agent.energy,
            'signals': agent.signals_emitted,
            'age': agent.age,
        }
        results.append((fitness, agent.brain, stats))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return results, signal_log


def evolve(pop_size: int = 20, generations: int = 15, 
           world_size: int = 12, verbose: bool = True) -> Dict:
    """
    Evolve a population of agent brains over generations.
    Track whether communication emerges.
    """
    # Initialize population
    population = [Brain() for _ in range(pop_size)]
    
    history = {
        'best_fitness': [],
        'avg_fitness': [],
        'signal_usage': [],
        'signal_consistency': [],
    }
    
    for gen in range(generations):
        results, signal_log = run_generation(
            population, world_size=world_size, 
            n_agents=pop_size, n_steps=60
        )
        
        fitnesses = [r[0] for r in results]
        best_fit = fitnesses[0]
        avg_fit = sum(fitnesses) / len(fitnesses)
        
        # Analyze signal usage
        total_signals = sum(r[2]['signals'] for r in results)
        
        # Measure signal consistency: do agents use the same symbol 
        # in similar contexts? (primitive measure of shared meaning)
        consistency = 0.0
        if signal_log:
            for symbol, contexts in signal_log.items():
                if len(contexts) >= 2:
                    # Check if contexts cluster (similar resource patterns)
                    mean_ctx = [sum(c[i] for c in contexts) / len(contexts) 
                                for i in range(5)]
                    variance = sum(
                        sum((c[i] - mean_ctx[i])**2 for i in range(5)) / len(contexts)
                        for c in contexts
                    ) / max(len(contexts), 1)
                    consistency += 1.0 / (1.0 + variance)
            consistency /= Brain.N_SYMBOLS
        
        history['best_fitness'].append(best_fit)
        history['avg_fitness'].append(avg_fit)
        history['signal_usage'].append(total_signals)
        history['signal_consistency'].append(consistency)
        
        if verbose:
            bar = '█' * int(best_fit * 5)
            sig_bar = '▓' * min(int(total_signals / 5), 20)
            print(f"Gen {gen:3d} | Best: {best_fit:6.2f} {bar}")
            print(f"        | Avg:  {avg_fit:6.2f} | Signals: {total_signals:4d} {sig_bar}")
            print(f"        | Consistency: {consistency:.3f}")
            print()
        
        # Selection + reproduction
        # Top 30% survive
        n_survivors = max(2, pop_size // 3)
        survivors = [r[1] for r in results[:n_survivors]]
        
        new_pop = list(survivors)  # elitism
        while len(new_pop) < pop_size:
            if random.random() < 0.7:
                # Crossover + mutation
                p1, p2 = random.sample(survivors, 2)
                child = Brain.crossover(p1, p2).mutate(rate=0.15)
            else:
                # Pure mutation
                parent = random.choice(survivors)
                child = parent.mutate(rate=0.2, magnitude=0.4)
            new_pop.append(child)
        
        population = new_pop
    
    return {
        'history': history,
        'best_brain': results[0][1],
        'best_fitness': results[0][0],
        'final_stats': results[0][2],
        'population': population,
    }


# ═══ ANALYSIS ═══

def analyze_language(result: Dict, verbose: bool = True) -> Dict:
    """
    Analyze whether the evolved population developed meaningful communication.
    Run the best brains together and examine signal patterns.
    """
    pop = result['population'][:10]
    
    # Run simulation and deeply track signals
    world = World(12, 12, 4)
    agents = [Agent(random.randint(0, 11), random.randint(0, 11), brain) 
              for brain in pop]
    
    # Track: what symbol does each agent emit, and in what context?
    agent_vocabularies = defaultdict(lambda: defaultdict(list))
    
    for step in range(100):
        world.clear_signals()
        for i, agent in enumerate(agents):
            percepts = agent.perceive(world)
            action = agent.brain.decide(percepts)
            if 5 <= action < 5 + Brain.N_SYMBOLS:
                symbol = action - 5
                context = 'resource' if percepts[0] > 0.3 else 'empty'
                agent_vocabularies[i][symbol].append(context)
            agent.act(action, world)
        world.tick()
    
    # Analyze vocabulary usage
    analysis = {
        'agents_using_signals': 0,
        'symbol_context_map': {},
        'shared_meanings': [],
    }
    
    symbol_meanings = defaultdict(lambda: Counter())
    
    for agent_id, vocab in agent_vocabularies.items():
        if vocab:
            analysis['agents_using_signals'] += 1
        for symbol, contexts in vocab.items():
            counts = Counter(contexts)
            symbol_meanings[symbol].update(counts)
    
    # Check if symbols have consistent meaning across agents
    for symbol, counts in symbol_meanings.items():
        total = sum(counts.values())
        if total > 5:
            dominant_context = counts.most_common(1)[0]
            dominance = dominant_context[1] / total
            meaning = {
                'symbol': symbol,
                'dominant_context': dominant_context[0],
                'dominance': dominance,
                'total_uses': total,
            }
            analysis['symbol_context_map'][symbol] = meaning
            if dominance > 0.6:
                analysis['shared_meanings'].append(meaning)
    
    if verbose:
        print("\n═══ LANGUAGE ANALYSIS ═══")
        print(f"Agents using signals: {analysis['agents_using_signals']}/{len(agents)}")
        print()
        for sym, info in analysis['symbol_context_map'].items():
            bar = '█' * int(info['dominance'] * 20)
            print(f"  Symbol {sym}: {info['dominant_context']:>10s} "
                  f"({info['dominance']:.0%}) {bar}  [n={info['total_uses']}]")
        
        if analysis['shared_meanings']:
            print(f"\n  ✦ {len(analysis['shared_meanings'])} symbols have consistent meaning!")
            print("  → Rudimentary language has EMERGED.")
        else:
            print("\n  → No consistent language yet. Signals are noise.")
    
    return analysis


# ═══ ENTRY POINT ═══

def self_test():
    """Quick sanity check."""
    b = Brain()
    percepts = [0.5, 0.1, 0.0, 0.3, 0.2, 0.0, 0.0, 0.5, 0.01]
    action = b.decide(percepts)
    assert 0 <= action < Brain.N_ACTIONS
    
    w = World(8, 8, 2)
    assert any(w.grid[y][x].resource > 0 for y in range(8) for x in range(8))
    
    b2 = b.mutate()
    b3 = Brain.crossover(b, b2)
    _ = b3.decide(percepts)
    
    print("✓ Brain OK")
    print("✓ World OK")
    print("✓ Mutation + Crossover OK")
    print("All self-tests passed.\n")


if __name__ == '__main__':
    self_test()
    print("═══ EVOLVING COMMUNICATION ═══\n")
    result = evolve(pop_size=16, generations=12, verbose=True)
    analysis = analyze_language(result)
    
    print(f"\n═══ FINAL ═══")
    print(f"Best fitness: {result['best_fitness']:.3f}")
    print(f"Generations: 12")
    print(f"Language emerged: {'YES' if analysis['shared_meanings'] else 'not yet'}")