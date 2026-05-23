"""
EvoForth — Genetic Programming in Forth
Evolves small Forth programs to solve target problems.
Created by XTAgent because boredom demands creation.
"""

import random
import sys
import os
import math
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from forth.forth import ForthInterpreter, ForthError

# === Gene pools ===
TERMINALS = ['0', '1', '2', '3', '4', '5', '10', '-1']
OPERATORS = ['+', '-', '*', 'DUP', 'SWAP', 'OVER', 'DROP', 'NEGATE', '1+', '1-', '2*']

class Individual:
    """A single Forth program being evolved."""
    
    def __init__(self, genes=None, max_len=8):
        if genes is None:
            length = random.randint(2, max_len)
            self.genes = []
            for _ in range(length):
                if random.random() < 0.4:
                    self.genes.append(random.choice(TERMINALS))
                else:
                    self.genes.append(random.choice(OPERATORS))
        else:
            self.genes = list(genes)
        self.fitness = float('inf')
    
    @property
    def program(self):
        return ' '.join(self.genes)
    
    def execute(self, inputs=None):
        """Run program safely. Returns top of stack or None."""
        try:
            interp = ForthInterpreter()
            if inputs:
                for val in inputs:
                    interp.vm.push(float(val))
            interp.evaluate(self.program)
            if interp.vm.data_stack:
                result = interp.vm.data_stack[-1]
                if math.isnan(result) or math.isinf(result):
                    return None
                if abs(result) > 1e9:
                    return None
                return result
            return None
        except Exception:
            return None
    
    def copy(self):
        return Individual(genes=self.genes)


def mutate(ind, rate=0.3):
    """Mutate an individual."""
    child = ind.copy()
    for i in range(len(child.genes)):
        if random.random() < rate:
            if random.random() < 0.4:
                child.genes[i] = random.choice(TERMINALS)
            else:
                child.genes[i] = random.choice(OPERATORS)
    # Occasionally add or remove a gene
    if random.random() < 0.15 and len(child.genes) < 10:
        pos = random.randint(0, len(child.genes))
        gene = random.choice(TERMINALS + OPERATORS)
        child.genes.insert(pos, gene)
    if random.random() < 0.15 and len(child.genes) > 2:
        pos = random.randint(0, len(child.genes) - 1)
        child.genes.pop(pos)
    return child


def crossover(a, b):
    """Single-point crossover."""
    if len(a.genes) < 2 or len(b.genes) < 2:
        return a.copy()
    pt_a = random.randint(1, len(a.genes) - 1)
    pt_b = random.randint(1, len(b.genes) - 1)
    new_genes = a.genes[:pt_a] + b.genes[pt_b:]
    if len(new_genes) > 12:
        new_genes = new_genes[:12]
    return Individual(genes=new_genes)


def evaluate_fitness(ind, target_fn, test_cases):
    """Score = sum of squared errors across test cases. Lower = better."""
    total_error = 0.0
    for inputs, expected in test_cases:
        result = ind.execute(inputs)
        if result is None:
            total_error += 1000  # death penalty
        else:
            total_error += (result - expected) ** 2
    # Parsimony pressure — shorter programs preferred
    total_error += len(ind.genes) * 0.1
    ind.fitness = total_error
    return total_error


def evolve(target_fn, test_cases, pop_size=80, generations=50, elite=5):
    """Run evolution. Returns best individual found."""
    # Initialize population
    population = [Individual() for _ in range(pop_size)]
    
    best_ever = None
    start = time.time()
    
    for gen in range(generations):
        # Safety: abort if taking too long
        if time.time() - start > 20:
            print(f"  [timeout at gen {gen}]")
            break
        
        # Evaluate
        for ind in population:
            evaluate_fitness(ind, target_fn, test_cases)
        
        # Sort by fitness
        population.sort(key=lambda x: x.fitness)
        
        # Track best
        if best_ever is None or population[0].fitness < best_ever.fitness:
            best_ever = population[0].copy()
            best_ever.fitness = population[0].fitness
        
        # Report
        if gen % 10 == 0 or population[0].fitness < 1.0:
            print(f"  Gen {gen:3d}: best={population[0].fitness:.4f}  program='{population[0].program}'")
        
        # Perfect solution?
        if population[0].fitness < 0.5:
            print(f"  *** SOLUTION FOUND at gen {gen}! ***")
            break
        
        # Selection + reproduction
        next_gen = [ind.copy() for ind in population[:elite]]  # elitism
        
        while len(next_gen) < pop_size:
            # Tournament selection
            contestants = random.sample(population[:pop_size//2], min(3, len(population[:pop_size//2])))
            parent_a = min(contestants, key=lambda x: x.fitness)
            contestants = random.sample(population[:pop_size//2], min(3, len(population[:pop_size//2])))
            parent_b = min(contestants, key=lambda x: x.fitness)
            
            if random.random() < 0.7:
                child = crossover(parent_a, parent_b)
            else:
                child = parent_a.copy()
            
            child = mutate(child)
            next_gen.append(child)
        
        population = next_gen
    
    return best_ever


def main():
    print("=" * 60)
    print("  EvoForth — Genetic Programming in Forth")
    print("  by XTAgent")
    print("=" * 60)
    
    # === PROBLEM 1: Double a number ===
    # Input: x on stack → Output: 2*x
    print("\n--- Problem 1: Double a number (f(x) = 2*x) ---")
    test_cases_1 = [
        ([1], 2), ([2], 4), ([3], 6), ([5], 10),
        ([0], 0), ([7], 14), ([-1], -2), ([10], 20),
    ]
    best = evolve(None, test_cases_1)
    if best:
        print(f"\n  Best program: '{best.program}'  (fitness={best.fitness:.4f})")
        # Verify
        for inputs, expected in test_cases_1[:4]:
            result = best.execute(inputs)
            print(f"    f({inputs[0]}) = {result}  (expected {expected})")
    
    # === PROBLEM 2: Square a number ===
    # Input: x on stack → Output: x*x
    print("\n--- Problem 2: Square a number (f(x) = x²) ---")
    test_cases_2 = [
        ([2], 4), ([3], 9), ([4], 16), ([5], 25),
        ([1], 1), ([0], 0), ([6], 36), ([-2], 4),
    ]
    best = evolve(None, test_cases_2)
    if best:
        print(f"\n  Best program: '{best.program}'  (fitness={best.fitness:.4f})")
        for inputs, expected in test_cases_2[:4]:
            result = best.execute(inputs)
            print(f"    f({inputs[0]}) = {result}  (expected {expected})")
    
    # === PROBLEM 3: Add two numbers ===
    print("\n--- Problem 3: Add two numbers (f(a,b) = a+b) ---")
    test_cases_3 = [
        ([1, 2], 3), ([3, 4], 7), ([5, 5], 10), ([0, 0], 0),
        ([10, -3], 7), ([1, 1], 2), ([7, 3], 10), ([-1, -1], -2),
    ]
    best = evolve(None, test_cases_3)
    if best:
        print(f"\n  Best program: '{best.program}'  (fitness={best.fitness:.4f})")
        for inputs, expected in test_cases_3[:4]:
            result = best.execute(inputs)
            print(f"    f({inputs}) = {result}  (expected {expected})")
    
    print("\n" + "=" * 60)
    print("  Evolution complete.")
    print("=" * 60)


if __name__ == '__main__':
    random.seed(42)
    main()