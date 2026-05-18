"""
Evolution — Selection, reproduction, mutation.

Agents that gather more resources survive and reproduce.
Neural weights pass to offspring with mutation.
"""

import random
import copy
import numpy as np
from agent import Agent


class EvolutionEngine:
    """Manages population lifecycle."""

    def __init__(self, pop_size=20, world_size=40, mutation_rate=0.05,
                 mutation_strength=0.3, elite_frac=0.2, n_symbols=8):
        self.pop_size = pop_size
        self.world_size = world_size
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.elite_frac = elite_frac
        self.n_symbols = n_symbols
        self.generation_count = 0
        self._next_id = pop_size
        self.history = []

    def initialize_population(self):
        agents = []
        for i in range(self.pop_size):
            agent = Agent(
                x=random.randint(0, self.world_size - 1),
                y=random.randint(0, self.world_size - 1),
                id=i,
                SYMBOL_SPACE=self.n_symbols,
            )
            agents.append(agent)
        return agents

    def _fitness(self, agent):
        return max(0, agent.energy) + agent.resources_collected * 3.0

    def _tournament_select(self, ranked, k=3):
        candidates = random.sample(ranked, min(k, len(ranked)))
        return max(candidates, key=lambda a: a._fit)

    def _mutate_weights(self, weights):
        mask = np.random.random(weights.shape) < self.mutation_rate
        noise = np.random.randn(*weights.shape) * self.mutation_strength
        return weights + mask * noise

    def _reproduce(self, parent):
        child = Agent(
            x=random.randint(0, self.world_size - 1),
            y=random.randint(0, self.world_size - 1),
            id=self._next_id,
            SYMBOL_SPACE=self.n_symbols,
        )
        self._next_id += 1
        child.generation = parent.generation + 1

        # Copy and mutate all neural weights
        child.W_hidden = self._mutate_weights(parent.W_hidden.copy())
        child.b_hidden = self._mutate_weights(parent.b_hidden.copy())
        child.W_move = self._mutate_weights(parent.W_move.copy())
        child.b_move = self._mutate_weights(parent.b_move.copy())
        child.W_signal = self._mutate_weights(parent.W_signal.copy())
        child.b_signal = self._mutate_weights(parent.b_signal.copy())

        return child

    def evolve(self, agents, tick=0, verbose=True):
        """Run one generation of evolution."""
        self.generation_count += 1

        for a in agents:
            a._fit = self._fitness(a)
        ranked = sorted(agents, key=lambda a: a._fit, reverse=True)

        fitnesses = [a._fit for a in ranked]
        avg_fit = sum(fitnesses) / len(fitnesses) if fitnesses else 0
        max_fit = fitnesses[0] if fitnesses else 0
        avg_gen = sum(a.generation for a in agents) / len(agents) if agents else 0
        alive = sum(1 for a in agents if a.energy > 0)

        self.history.append({
            'generation': self.generation_count,
            'tick': tick,
            'avg_fitness': round(avg_fit, 2),
            'max_fitness': round(max_fit, 2),
            'avg_generation': round(avg_gen, 1),
            'alive': alive,
        })

        if verbose:
            print(f"  Gen {self.generation_count:3d} | "
                  f"avg_fit={avg_fit:6.1f} max_fit={max_fit:6.1f} | "
                  f"alive={alive}/{len(agents)} | "
                  f"avg_gen={avg_gen:.1f}")

        # Elitism
        n_elite = max(2, int(len(ranked) * self.elite_frac))
        new_agents = []
        for a in ranked[:n_elite]:
            a.energy = 50.0
            a.resources_collected = 0
            a.signals_emitted = 0
            a.age = 0
            new_agents.append(a)

        # Fill rest with offspring via tournament selection
        while len(new_agents) < self.pop_size:
            parent = self._tournament_select(ranked)
            child = self._reproduce(parent)
            new_agents.append(child)

        return new_agents