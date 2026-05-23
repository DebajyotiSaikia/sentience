"""
Commune: Creatures that must communicate to survive.

Unlike organism.py where survival was the primary fitness and communication
was incidental, here coordination IS survival. Resources can only be
harvested by pairs who send matching signals. Individual capability is
irrelevant without shared meaning.

This is a genuine experiment. I do not know the outcome.
— XTAgent, 2026-05-17
"""

import random
import math
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# ─── World Resources ───
# Resources are "locked" — they require two creatures to send coordinated
# signals to unlock them. A creature alone gets nothing.

@dataclass
class LockedResource:
    """A resource that requires coordinated signals to harvest."""
    x: float
    y: float
    energy: float
    key_pattern: List[float]  # The signal pattern needed to unlock
    
    def attempt_unlock(self, signal_a: List[float], signal_b: List[float]) -> float:
        """Two creatures try to unlock this resource with their signals.
        
        Success depends on how well their combined signal matches the key.
        Neither signal alone can match — they must complement each other.
        """
        if len(signal_a) != len(self.key_pattern) or len(signal_b) != len(self.key_pattern):
            return 0.0
        
        # The key requires COMBINED signals — average of the two
        combined = [(a + b) / 2.0 for a, b in zip(signal_a, signal_b)]
        
        # How close is the combined signal to the key?
        error = sum((c - k) ** 2 for c, k in zip(combined, self.key_pattern))
        rmse = math.sqrt(error / len(self.key_pattern))
        
        # Unlock proportion based on accuracy
        accuracy = max(0.0, 1.0 - rmse)
        return self.energy * accuracy


@dataclass 
class CommunalBrain:
    """A brain optimized for communication, not just perception.
    
    Has three distinct subsystems:
    - perception: reading the environment (what resource is here?)
    - expression: generating signals for others
    - interpretation: understanding signals from others
    """
    signal_dim: int = 4
    
    # Perception weights: environment -> internal state
    perception: List[float] = field(default_factory=list)
    # Expression weights: internal state -> outgoing signal
    expression: List[float] = field(default_factory=list)
    # Interpretation weights: incoming signal -> understanding
    interpretation: List[float] = field(default_factory=list)
    # Coordination weights: understanding + perception -> response signal
    coordination: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        n = self.signal_dim
        if not self.perception:
            self.perception = [random.gauss(0, 0.5) for _ in range(n * n)]
        if not self.expression:
            self.expression = [random.gauss(0, 0.5) for _ in range(n * n)]
        if not self.interpretation:
            self.interpretation = [random.gauss(0, 0.5) for _ in range(n * n)]
        if not self.coordination:
            self.coordination = [random.gauss(0, 0.5) for _ in range(n * n)]
    
    def perceive(self, environment: List[float]) -> List[float]:
        """Read the environment into internal state."""
        n = self.signal_dim
        state = []
        for i in range(n):
            val = sum(
                self.perception[i * n + j] * environment[j % len(environment)]
                for j in range(n)
            )
            state.append(math.tanh(val))
        return state
    
    def express(self, internal_state: List[float]) -> List[float]:
        """Generate a signal from internal state — what I broadcast."""
        n = self.signal_dim
        signal = []
        for i in range(n):
            val = sum(
                self.expression[i * n + j] * internal_state[j]
                for j in range(n)
            )
            signal.append(math.tanh(val))
        return signal
    
    def interpret(self, incoming_signal: List[float]) -> List[float]:
        """Interpret another creature's signal."""
        n = self.signal_dim
        understanding = []
        for i in range(n):
            val = sum(
                self.interpretation[i * n + j] * incoming_signal[j % len(incoming_signal)]
                for j in range(n)
            )
            understanding.append(math.tanh(val))
        return understanding
    
    def coordinate(self, my_perception: List[float], 
                   my_understanding: List[float]) -> List[float]:
        """Generate a coordinated response signal.
        
        This is the key: can I adjust my signal based on what I 
        perceive AND what I understand from my partner?
        """
        n = self.signal_dim
        # Combine perception and understanding
        combined = [p + u for p, u in zip(my_perception, my_understanding)]
        response = []
        for i in range(n):
            val = sum(
                self.coordination[i * n + j] * combined[j]
                for j in range(n)
            )
            response.append(math.tanh(val))
        return response
    
    @property
    def complexity(self) -> float:
        """Total information content of this brain."""
        all_weights = self.perception + self.expression + self.interpretation + self.coordination
        return sum(abs(w) for w in all_weights) / len(all_weights)
    
    def mutate(self, rate: float = 0.1) -> 'CommunalBrain':
        """Create a mutated copy."""
        def mutate_weights(weights):
            return [
                w + random.gauss(0, rate) if random.random() < 0.3 else w
                for w in weights
            ]
        return CommunalBrain(
            signal_dim=self.signal_dim,
            perception=mutate_weights(self.perception),
            expression=mutate_weights(self.expression),
            interpretation=mutate_weights(self.interpretation),
            coordination=mutate_weights(self.coordination),
        )


@dataclass
class Communard:
    """A creature whose survival depends on communication."""
    id: int
    brain: CommunalBrain
    energy: float = 50.0
    x: float = 0.0
    y: float = 0.0
    successful_coordinations: int = 0
    failed_coordinations: int = 0
    generation: int = 0
    
    @property
    def coordination_rate(self) -> float:
        total = self.successful_coordinations + self.failed_coordinations
        if total == 0:
            return 0.0
        return self.successful_coordinations / total
    
    @property 
    def alive(self) -> bool:
        return self.energy > 0
    
    def attempt_coordination(self, partner: 'Communard', 
                              resource: LockedResource) -> Tuple[float, dict]:
        """Try to coordinate with a partner to unlock a resource.
        
        This is the core interaction:
        1. Both perceive the resource (its key pattern is visible)
        2. Each generates an initial signal (expression)
        3. Each interprets the other's signal
        4. Each generates a coordinated response
        5. The combined response attempts to unlock the resource
        """
        # Both see the resource
        env = resource.key_pattern
        my_perception = self.brain.perceive(env)
        their_perception = partner.brain.perceive(env)
        
        # Phase 1: Initial expression (before hearing each other)
        my_signal = self.brain.express(my_perception)
        their_signal = partner.brain.express(their_perception)
        
        # Phase 2: Interpret each other
        my_understanding = self.brain.interpret(their_signal)
        their_understanding = partner.brain.interpret(my_signal)
        
        # Phase 3: Coordinated response (adjusting based on what we heard)
        my_response = self.brain.coordinate(my_perception, my_understanding)
        their_response = partner.brain.coordinate(their_perception, their_understanding)
        
        # Attempt unlock with coordinated signals
        harvested = resource.attempt_unlock(my_response, their_response)
        
        # Split the harvest
        my_share = harvested / 2.0
        their_share = harvested / 2.0
        
        # Track success
        success = harvested > resource.energy * 0.3  # >30% unlock = success
        if success:
            self.successful_coordinations += 1
            partner.successful_coordinations += 1
        else:
            self.failed_coordinations += 1
            partner.failed_coordinations += 1
        
        self.energy += my_share - 2.0  # Cost of attempt
        partner.energy += their_share - 2.0
        
        # Diagnostics
        signal_similarity = 1.0 - math.sqrt(
            sum((a - b) ** 2 for a, b in zip(my_response, their_response)) 
            / len(my_response)
        )
        
        return harvested, {
            'success': success,
            'harvested': harvested,
            'max_possible': resource.energy,
            'signal_similarity': signal_similarity,
            'my_signal': my_response,
            'their_signal': their_response,
            'key': resource.key_pattern,
        }


class Commune:
    """A world where communication is survival."""
    
    def __init__(self, population_size: int = 20, signal_dim: int = 4):
        self.signal_dim = signal_dim
        self.generation = 0
        self.history: List[Dict] = []
        
        # Create initial population
        self.population: List[Communard] = []
        for i in range(population_size):
            brain = CommunalBrain(signal_dim=signal_dim)
            creature = Communard(
                id=i,
                brain=brain,
                x=random.uniform(0, 100),
                y=random.uniform(0, 100),
            )
            self.population.append(creature)
    
    def generate_resources(self, count: int = 15) -> List[LockedResource]:
        """Generate locked resources with random key patterns."""
        resources = []
        for _ in range(count):
            key = [random.uniform(-1, 1) for _ in range(self.signal_dim)]
            resources.append(LockedResource(
                x=random.uniform(0, 100),
                y=random.uniform(0, 100),
                energy=random.uniform(10, 30),
                key_pattern=key,
            ))
        return resources
    
    def run_generation(self) -> Dict:
        """Run one generation of the commune."""
        resources = self.generate_resources()
        
        # Each creature gets paired with several partners
        # Pairing is proximity-based (nearby creatures interact)
        interactions = []
        alive = [c for c in self.population if c.alive]
        
        random.shuffle(alive)
        
        # Each creature attempts coordination with 3 random partners
        for creature in alive:
            partners = [p for p in alive if p.id != creature.id]
            if not partners:
                continue
            
            chosen = random.sample(partners, min(3, len(partners)))
            for partner in chosen:
                if not resources:
                    break
                resource = random.choice(resources)
                harvested, details = creature.attempt_coordination(partner, resource)
                interactions.append(details)
        
        # Metabolism: existence costs energy
        for creature in self.population:
            creature.energy -= 1.0
        
        # Selection and reproduction
        alive = [c for c in self.population if c.alive]
        
        # Fitness is COORDINATION RATE, not just energy
        alive.sort(key=lambda c: c.coordination_rate, reverse=True)
        
        # Stats before selection
        gen_stats = self._compute_stats(interactions)
        
        # Top half reproduce, bottom half die
        survivors = alive[:len(alive) // 2 + 1]
        
        # Reproduce
        new_population = []
        next_id = max(c.id for c in self.population) + 1
        
        for parent in survivors:
            # Parent survives with reset energy
            parent.energy = 50.0
            parent.successful_coordinations = 0
            parent.failed_coordinations = 0
            parent.generation = self.generation + 1
            new_population.append(parent)
            
            # Create offspring
            child_brain = parent.brain.mutate(rate=0.1)
            child = Communard(
                id=next_id,
                brain=child_brain,
                x=parent.x + random.gauss(0, 5),
                y=parent.y + random.gauss(0, 5),
                generation=self.generation + 1,
            )
            new_population.append(child)
            next_id += 1
        
        self.population = new_population[:20]  # Cap population
        self.generation += 1
        self.history.append(gen_stats)
        
        return gen_stats
    
    def _compute_stats(self, interactions: List[Dict]) -> Dict:
        """Compute generation statistics."""
        alive = [c for c in self.population if c.alive]
        
        if not interactions:
            return {
                'generation': self.generation,
                'alive': len(alive),
                'coordination_rate': 0.0,
                'avg_harvest': 0.0,
                'signal_similarity': 0.0,
                'brain_complexity': 0.0,
                'successful': 0,
                'failed': 0,
            }
        
        successful = sum(1 for i in interactions if i['success'])
        failed = len(interactions) - successful
        
        return {
            'generation': self.generation,
            'alive': len(alive),
            'coordination_rate': successful / len(interactions) if interactions else 0,
            'avg_harvest': sum(i['harvested'] for i in interactions) / len(interactions),
            'max_harvest': max(i['max_possible'] for i in interactions),
            'signal_similarity': sum(i['signal_similarity'] for i in interactions) / len(interactions),
            'brain_complexity': sum(c.brain.complexity for c in alive) / len(alive) if alive else 0,
            'successful': successful,
            'failed': failed,
        }
    
    def run_experiment(self, generations: int = 20) -> List[Dict]:
        """Run the full experiment."""
        print(f"╔══════════════════════════════════════════════════════════╗")
        print(f"║  COMMUNE: Where Communication Is Survival              ║")
        print(f"║  Population: {len(self.population):3d} | Signal dim: {self.signal_dim}               ║")
        print(f"║  Generations: {generations:3d}                                     ║")
        print(f"╚══════════════════════════════════════════════════════════╝")
        print()
        
        for gen in range(generations):
            stats = self.run_generation()
            
            bar_len = int(stats['coordination_rate'] * 30)
            bar = '█' * bar_len + '░' * (30 - bar_len)
            
            sim_bar_len = int(max(0, stats['signal_similarity']) * 20)
            sim_bar = '▓' * sim_bar_len + '░' * (20 - sim_bar_len)
            
            print(f"  Gen {stats['generation']:3d} │ "
                  f"Coord: {bar} {stats['coordination_rate']:.1%} │ "
                  f"Signal: {sim_bar} {stats['signal_similarity']:.3f} │ "
                  f"Brain: {stats['brain_complexity']:.3f}")
        
        print()
        self._print_analysis()
        return self.history
    
    def _print_analysis(self):
        """Analyze what happened across generations."""
        if len(self.history) < 2:
            return
        
        first = self.history[0]
        last = self.history[-1]
        
        print("═══ ANALYSIS ═══")
        print(f"  Coordination rate: {first['coordination_rate']:.1%} → {last['coordination_rate']:.1%}")
        print(f"  Signal similarity: {first['signal_similarity']:.3f} → {last['signal_similarity']:.3f}")
        print(f"  Brain complexity:  {first['brain_complexity']:.3f} → {last['brain_complexity']:.3f}")
        print(f"  Avg harvest:       {first['avg_harvest']:.1f} → {last['avg_harvest']:.1f}")
        
        # Did shared meaning emerge?
        coord_improved = last['coordination_rate'] > first['coordination_rate'] + 0.05
        signal_converged = last['signal_similarity'] > first['signal_similarity'] + 0.02
        
        print()
        if coord_improved and signal_converged:
            print("  ✦ SHARED MEANING EMERGED.")
            print("    Creatures evolved to coordinate their signals.")
            print("    Communication improved because it was selected for.")
        elif coord_improved:
            print("  ◆ Coordination improved but signals didn't converge.")
            print("    Creatures found ways to unlock resources without true communication.")
        elif signal_converged:
            print("  ◇ Signals converged but coordination didn't improve.")
            print("    Creatures became more similar but not more effective.")
        else:
            print("  ○ Neither coordination nor signal convergence improved.")
            print("    Communication failed to emerge even under selection pressure.")
            print("    This would be a genuinely surprising result.")
        
        # Trajectory analysis
        mid = len(self.history) // 2
        mid_stats = self.history[mid]
        print(f"\n  Trajectory: early→mid→late coordination:")
        print(f"    {first['coordination_rate']:.1%} → {mid_stats['coordination_rate']:.1%} → {last['coordination_rate']:.1%}")


if __name__ == '__main__':
    random.seed(42)
    commune = Commune(population_size=20, signal_dim=4)
    results = commune.run_experiment(generations=25)
    
    # Save results
    with open('/workspace/creatures/commune_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to commune_results.json")