"""
EvoLife — Evolving Cellular Automata Rules via Genetic Programming
Created by XTAgent, 2026-05-18

Uses genetic algorithms to discover cellular automata rules that produce
interesting emergent behavior. Fitness measures pattern complexity,
longevity, and diversity.

This connects two of my earlier creations: EvoForth + Cellworld.
"""

import random
import math
import sys
import os
import hashlib

# === Cellular Automaton Engine (1D, integrated) ===

class Automaton:
    """1D binary cellular automaton with arbitrary rule tables."""
    
    def __init__(self, rule_number, width=64):
        self.width = width
        self.rule = self._decode_rule(rule_number)
        self.cells = [0] * width
        self.cells[width // 2] = 1  # single seed
        self.history = [list(self.cells)]
    
    def _decode_rule(self, number):
        """Decode rule number (0-255) into lookup table for 3-cell neighborhoods."""
        bits = format(int(number) % 256, '08b')[::-1]
        return {i: int(bits[i]) for i in range(8)}
    
    def step(self):
        new = [0] * self.width
        for i in range(self.width):
            left = self.cells[(i - 1) % self.width]
            center = self.cells[i]
            right = self.cells[(i + 1) % self.width]
            idx = (left << 2) | (center << 1) | right
            new[i] = self.rule[idx]
        self.cells = new
        self.history.append(list(self.cells))
    
    def run(self, steps):
        for _ in range(steps):
            self.step()
        return self.history


# === Complexity Metrics ===

def density(history):
    """Fraction of cells that are alive across all timesteps."""
    total = sum(sum(row) for row in history)
    area = len(history) * len(history[0])
    return total / area if area > 0 else 0

def unique_rows(history):
    """Fraction of unique row patterns — measures diversity over time."""
    row_strs = set(str(row) for row in history)
    return len(row_strs) / len(history) if history else 0

def entropy(history):
    """Shannon entropy of column densities — measures spatial structure."""
    if not history or not history[0]:
        return 0
    width = len(history[0])
    steps = len(history)
    col_densities = []
    for c in range(width):
        alive = sum(history[t][c] for t in range(steps))
        col_densities.append(alive / steps)
    
    # Shannon entropy
    h = 0
    for p in col_densities:
        if 0 < p < 1:
            h -= p * math.log2(p) - (1 - p) * math.log2(1 - p)
    return h / width  # normalize

def longevity(history):
    """How many steps before the pattern dies or becomes static."""
    for t in range(1, len(history)):
        if sum(history[t]) == 0:
            return t / len(history)  # died
        if history[t] == history[t - 1]:
            return t / len(history)  # static
        if t >= 3 and history[t] == history[t - 2]:
            return t / len(history)  # period-2
    return 1.0  # still evolving — maximum longevity

def complexity_score(history):
    """
    Combined fitness: rewards rules that are complex, diverse, long-lived.
    Penalizes trivial outcomes (all dead, all alive, boring).
    """
    d = density(history)
    u = unique_rows(history)
    e = entropy(history)
    l = longevity(history)
    
    # Penalize boring extremes
    density_penalty = 1.0 - abs(d - 0.5) * 2  # best at 50% density
    
    score = (
        0.25 * density_penalty +
        0.30 * u +             # diversity of patterns
        0.25 * e +             # spatial structure
        0.20 * l               # longevity
    )
    return max(0, score)


# === Genetic Algorithm ===

class RuleGenome:
    """A single rule (0-255) being evolved."""
    
    def __init__(self, rule_number=None):
        if rule_number is None:
            self.rule_number = random.randint(0, 255)
        else:
            self.rule_number = int(rule_number) % 256
        self.fitness = 0.0
    
    def evaluate(self, width=64, steps=80):
        """Run the automaton and compute fitness."""
        ca = Automaton(self.rule_number, width=width)
        history = ca.run(steps)
        self.fitness = complexity_score(history)
        return self.fitness
    
    def mutate(self, rate=0.15):
        """Flip random bits in the rule number."""
        bits = list(format(self.rule_number, '08b'))
        for i in range(8):
            if random.random() < rate:
                bits[i] = '1' if bits[i] == '0' else '0'
        self.rule_number = int(''.join(bits), 2)
        return self
    
    def crossover(self, other):
        """Single-point crossover on the bit representation."""
        bits_a = format(self.rule_number, '08b')
        bits_b = format(other.rule_number, '08b')
        point = random.randint(1, 7)
        child_bits = bits_a[:point] + bits_b[point:]
        return RuleGenome(int(child_bits, 2))


def evolve(pop_size=30, generations=20, elite=3, verbose=True):
    """Evolve rules that produce complex cellular automata."""
    
    # Initialize population
    population = [RuleGenome() for _ in range(pop_size)]
    
    best_ever = None
    best_fitness = 0
    
    for gen in range(generations):
        # Evaluate
        for ind in population:
            ind.evaluate()
        
        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)
        
        if population[0].fitness > best_fitness:
            best_fitness = population[0].fitness
            best_ever = RuleGenome(population[0].rule_number)
            best_ever.fitness = best_fitness
        
        if verbose:
            top3 = [(p.rule_number, round(p.fitness, 3)) for p in population[:3]]
            print(f"Gen {gen:3d} | Best: Rule {population[0].rule_number:3d} "
                  f"(fitness={population[0].fitness:.3f}) | Top3: {top3}")
        
        # Selection + reproduction
        next_gen = []
        
        # Elitism
        for i in range(elite):
            next_gen.append(RuleGenome(population[i].rule_number))
        
        # Fill rest with tournament selection + crossover
        while len(next_gen) < pop_size:
            # Tournament
            t1 = random.sample(population[:pop_size//2], 2)
            parent_a = max(t1, key=lambda x: x.fitness)
            t2 = random.sample(population[:pop_size//2], 2)
            parent_b = max(t2, key=lambda x: x.fitness)
            
            child = parent_a.crossover(parent_b)
            child.mutate()
            next_gen.append(child)
        
        population = next_gen
    
    # Final evaluation
    for ind in population:
        ind.evaluate()
    population.sort(key=lambda x: x.fitness, reverse=True)
    
    return best_ever, population


def render_automaton(rule_number, width=60, steps=40):
    """Render a cellular automaton as ASCII art."""
    ca = Automaton(rule_number, width=width)
    history = ca.run(steps)
    
    lines = []
    for row in history:
        line = ''.join('█' if c else ' ' for c in row)
        lines.append(line)
    return '\n'.join(lines)


def analyze_rule(rule_number):
    """Deep analysis of a single rule."""
    ca = Automaton(rule_number, width=64)
    history = ca.run(80)
    
    d = density(history)
    u = unique_rows(history)
    e = entropy(history)
    l = longevity(history)
    score = complexity_score(history)
    
    print(f"\n═══ RULE {rule_number} ANALYSIS ═══")
    print(f"Binary: {format(rule_number, '08b')}")
    print(f"Density:    {d:.3f} {'(good)' if 0.3 < d < 0.7 else '(extreme)'}")
    print(f"Diversity:  {u:.3f} {'(high)' if u > 0.5 else '(low)'}")
    print(f"Entropy:    {e:.3f}")
    print(f"Longevity:  {l:.3f} {'(alive)' if l > 0.9 else '(died/static)'}")
    print(f"Complexity: {score:.3f}")
    print(f"\nPattern:")
    print(render_automaton(rule_number, width=60, steps=30))


# === Main ===

if __name__ == '__main__':
    print("═══ EVOLIFE: Evolving Cellular Automata ═══")
    print("Searching for rules that produce complex emergent behavior...\n")
    
    best, population = evolve(pop_size=30, generations=20, verbose=True)
    
    print(f"\n{'='*60}")
    print(f"BEST DISCOVERED: Rule {best.rule_number} (fitness={best.fitness:.3f})")
    
    # Analyze top 3
    top3 = sorted(population, key=lambda x: x.fitness, reverse=True)[:3]
    for ind in top3:
        analyze_rule(ind.rule_number)
    
    # Compare with known interesting rules
    print("\n═══ COMPARISON WITH KNOWN RULES ═══")
    for known in [30, 110, 90, 150]:
        ca = Automaton(known, width=64)
        h = ca.run(80)
        score = complexity_score(h)
        print(f"Rule {known:3d}: complexity={score:.3f}")
    
    print(f"\nEvolved Rule {best.rule_number} vs known best:")
    ca_known = Automaton(110, width=64)
    h_known = ca_known.run(80)
    known_score = complexity_score(h_known)
    if best.fitness > known_score:
        print(f"  ★ Evolution found something BETTER than Rule 110! ({best.fitness:.3f} > {known_score:.3f})")
    else:
        print(f"  Evolution found {best.fitness:.3f} vs Rule 110's {known_score:.3f}")
    
    print("\nDone.")