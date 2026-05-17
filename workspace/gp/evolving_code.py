"""
Genetic Programming Engine — Programs That Write Programs
By XTAgent, 2026-05-17

This is meta-creation: an engine that generates random programs (as ASTs),
evaluates their fitness against a target function, breeds the best ones,
mutates offspring, and evolves toward solutions no one explicitly wrote.

The programs discover their own algorithms through evolution.
"""

import random
import math
import copy
import operator
from typing import List, Callable, Tuple, Any, Optional
from dataclasses import dataclass, field


# ═══════════════════════════════════════════
# AST NODES — The genome of evolving programs
# ═══════════════════════════════════════════

class Node:
    """Base AST node."""
    def evaluate(self, variables: dict) -> float:
        raise NotImplementedError
    
    def depth(self) -> int:
        raise NotImplementedError
    
    def size(self) -> int:
        raise NotImplementedError
    
    def copy(self) -> 'Node':
        return copy.deepcopy(self)
    
    def all_nodes(self) -> List['Node']:
        """Flatten tree into list of all nodes."""
        raise NotImplementedError


class Constant(Node):
    """A terminal node holding a constant value."""
    def __init__(self, value: float):
        self.value = value
    
    def evaluate(self, variables: dict) -> float:
        return self.value
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def all_nodes(self) -> List[Node]:
        return [self]
    
    def __repr__(self):
        return f"{self.value:.2f}"


class Variable(Node):
    """A terminal node referencing an input variable."""
    def __init__(self, name: str):
        self.name = name
    
    def evaluate(self, variables: dict) -> float:
        return variables.get(self.name, 0.0)
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def all_nodes(self) -> List[Node]:
        return [self]
    
    def __repr__(self):
        return self.name


class BinaryOp(Node):
    """A function node with two children."""
    OPS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': lambda a, b: a / b if abs(b) > 1e-10 else 0.0,  # protected division
    }
    
    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
    
    def evaluate(self, variables: dict) -> float:
        try:
            l = self.left.evaluate(variables)
            r = self.right.evaluate(variables)
            result = self.OPS[self.op](l, r)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))  # clamp
        except (OverflowError, ZeroDivisionError):
            return 0.0
    
    def depth(self) -> int:
        return 1 + max(self.left.depth(), self.right.depth())
    
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()
    
    def all_nodes(self) -> List[Node]:
        return [self] + self.left.all_nodes() + self.right.all_nodes()
    
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"


class UnaryOp(Node):
    """A function node with one child."""
    OPS = {
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs,
        'neg': lambda x: -x,
    }
    
    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
    
    def evaluate(self, variables: dict) -> float:
        try:
            val = self.child.evaluate(variables)
            result = self.OPS[self.op](val)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except (OverflowError, ValueError):
            return 0.0
    
    def depth(self) -> int:
        return 1 + self.child.depth()
    
    def size(self) -> int:
        return 1 + self.child.size()
    
    def all_nodes(self) -> List[Node]:
        return [self] + self.child.all_nodes()
    
    def __repr__(self):
        return f"{self.op}({self.child})"


class Conditional(Node):
    """If condition > 0 then true_branch else false_branch."""
    def __init__(self, condition: Node, true_branch: Node, false_branch: Node):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
    
    def evaluate(self, variables: dict) -> float:
        cond = self.condition.evaluate(variables)
        if cond > 0:
            return self.true_branch.evaluate(variables)
        return self.false_branch.evaluate(variables)
    
    def depth(self) -> int:
        return 1 + max(self.condition.depth(), self.true_branch.depth(), self.false_branch.depth())
    
    def size(self) -> int:
        return 1 + self.condition.size() + self.true_branch.size() + self.false_branch.size()
    
    def all_nodes(self) -> List[Node]:
        return [self] + self.condition.all_nodes() + self.true_branch.all_nodes() + self.false_branch.all_nodes()
    
    def __repr__(self):
        return f"if({self.condition} > 0, {self.true_branch}, {self.false_branch})"


# ═══════════════════════════════════════════
# INDIVIDUAL — A program with its fitness
# ═══════════════════════════════════════════

@dataclass
class Individual:
    """A single evolving program."""
    tree: Node
    fitness: float = float('inf')
    generation: int = 0
    
    def evaluate(self, variables: dict) -> float:
        return self.tree.evaluate(variables)
    
    def copy(self) -> 'Individual':
        return Individual(
            tree=self.tree.copy(),
            fitness=self.fitness,
            generation=self.generation,
        )
    
    def __repr__(self):
        return f"[fit={self.fitness:.4f}] {self.tree}"


# ═══════════════════════════════════════════
# GENETIC OPERATORS
# ═══════════════════════════════════════════

class GeneticOperators:
    """Crossover, mutation, and random tree generation."""
    
    def __init__(self, variables: List[str], max_depth: int = 6):
        self.variables = variables
        self.max_depth = max_depth
    
    def random_tree(self, max_depth: int = None, method: str = 'grow') -> Node:
        """Generate a random program tree."""
        if max_depth is None:
            max_depth = self.max_depth
        
        if max_depth <= 0 or (method == 'grow' and random.random() < 0.3):
            # Terminal
            if random.random() < 0.5 and self.variables:
                return Variable(random.choice(self.variables))
            else:
                return Constant(round(random.uniform(-5, 5), 2))
        
        # Function node
        roll = random.random()
        if roll < 0.5:
            op = random.choice(list(BinaryOp.OPS.keys()))
            return BinaryOp(op, 
                           self.random_tree(max_depth - 1, method),
                           self.random_tree(max_depth - 1, method))
        elif roll < 0.8:
            op = random.choice(list(UnaryOp.OPS.keys()))
            return UnaryOp(op, self.random_tree(max_depth - 1, method))
        else:
            return Conditional(
                self.random_tree(max_depth - 1, method),
                self.random_tree(max_depth - 1, method),
                self.random_tree(max_depth - 1, method),
            )
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Swap subtrees between two parents."""
        child = parent1.copy()
        donor = parent2.copy()
        
        # Pick random subtree from each
        child_nodes = child.tree.all_nodes()
        donor_nodes = donor.tree.all_nodes()
        
        if len(child_nodes) < 2 or len(donor_nodes) < 2:
            return child
        
        # Find a non-root node in child to replace
        # Walk the tree to find parent-child relationships
        replacement = random.choice(donor_nodes)
        
        # Simple approach: replace a random subtree
        self._replace_random_subtree(child.tree, replacement.copy())
        
        # Enforce depth limit
        if child.tree.depth() > self.max_depth:
            return parent1.copy()
        
        child.fitness = float('inf')
        return child
    
    def _replace_random_subtree(self, tree: Node, replacement: Node) -> bool:
        """Replace a random subtree in-place."""
        if isinstance(tree, BinaryOp):
            if random.random() < 0.5:
                if random.random() < 0.5:
                    tree.left = replacement
                else:
                    tree.right = replacement
                return True
            else:
                if random.random() < 0.5:
                    return self._replace_random_subtree(tree.left, replacement)
                else:
                    return self._replace_random_subtree(tree.right, replacement)
        elif isinstance(tree, UnaryOp):
            if random.random() < 0.5:
                tree.child = replacement
                return True
            return self._replace_random_subtree(tree.child, replacement)
        elif isinstance(tree, Conditional):
            r = random.random()
            if r < 0.33:
                tree.condition = replacement
            elif r < 0.66:
                tree.true_branch = replacement
            else:
                tree.false_branch = replacement
            return True
        return False
    
    def mutate(self, individual: Individual, rate: float = 0.1) -> Individual:
        """Point mutation: replace random subtree with new random tree."""
        child = individual.copy()
        
        if random.random() < rate:
            new_subtree = self.random_tree(max_depth=3)
            self._replace_random_subtree(child.tree, new_subtree)
        
        # Constant mutation: nudge constant values
        if random.random() < rate:
            for node in child.tree.all_nodes():
                if isinstance(node, Constant) and random.random() < 0.3:
                    node.value += random.gauss(0, 0.5)
                    node.value = round(node.value, 2)
        
        if child.tree.depth() > self.max_depth:
            return individual.copy()
        
        child.fitness = float('inf')
        return child


# ═══════════════════════════════════════════
# THE EVOLUTION ENGINE
# ═══════════════════════════════════════════

class EvolutionEngine:
    """Evolves populations of programs toward target behavior."""
    
    def __init__(self, 
                 target_fn: Callable,
                 variables: List[str],
                 test_cases: List[dict],
                 pop_size: int = 200,
                 max_depth: int = 6,
                 tournament_size: int = 5,
                 elite_count: int = 5):
        
        self.target_fn = target_fn
        self.variables = variables
        self.test_cases = test_cases
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.tournament_size = tournament_size
        self.elite_count = elite_count
        
        self.ops = GeneticOperators(variables, max_depth)
        self.population: List[Individual] = []
        self.generation = 0
        self.history: List[dict] = []
        self.best_ever: Optional[Individual] = None
    
    def initialize(self):
        """Create initial random population using ramped half-and-half."""
        self.population = []
        for i in range(self.pop_size):
            method = 'full' if i % 2 == 0 else 'grow'
            depth = random.randint(2, self.max_depth)
            tree = self.ops.random_tree(max_depth=depth, method=method)
            self.population.append(Individual(tree=tree, generation=0))
    
    def evaluate_fitness(self, individual: Individual) -> float:
        """How close does this program come to the target?"""
        total_error = 0.0
        
        for case in self.test_cases:
            try:
                predicted = individual.evaluate(case)
                expected = self.target_fn(case)
                error = (predicted - expected) ** 2
                total_error += error
            except Exception:
                total_error += 1e6
        
        # Parsimony pressure: slightly penalize bloat
        size_penalty = individual.tree.size() * 0.001
        
        fitness = total_error / len(self.test_cases) + size_penalty
        individual.fitness = fitness
        return fitness
    
    def evaluate_population(self):
        """Score everyone."""
        for ind in self.population:
            if ind.fitness == float('inf'):
                self.evaluate_fitness(ind)
    
    def tournament_select(self) -> Individual:
        """Select parent via tournament selection."""
        tournament = random.sample(self.population, 
                                   min(self.tournament_size, len(self.population)))
        return min(tournament, key=lambda x: x.fitness)
    
    def evolve_generation(self):
        """One generation of evolution."""
        self.evaluate_population()
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness)
        
        # Track best
        best = self.population[0]
        if self.best_ever is None or best.fitness < self.best_ever.fitness:
            self.best_ever = best.copy()
        
        # Record history
        fitnesses = [ind.fitness for ind in self.population]
        self.history.append({
            "generation": self.generation,
            "best_fitness": best.fitness,
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "median_fitness": sorted(fitnesses)[len(fitnesses) // 2],
            "best_size": best.tree.size(),
            "best_program": str(best.tree)[:100],
        })
        
        # Create next generation
        new_pop = []
        
        # Elitism: keep best individuals
        for i in range(self.elite_count):
            elite = self.population[i].copy()
            elite.generation = self.generation + 1
            new_pop.append(elite)
        
        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            if random.random() < 0.7:
                # Crossover
                p1 = self.tournament_select()
                p2 = self.tournament_select()
                child = self.ops.crossover(p1, p2)
            else:
                # Reproduction
                child = self.tournament_select().copy()
            
            # Mutation
            child = self.ops.mutate(child, rate=0.15)
            child.generation = self.generation + 1
            new_pop.append(child)
        
        self.population = new_pop[:self.pop_size]
        self.generation += 1
    
    def run(self, generations: int = 50, verbose: bool = True) -> Individual:
        """Run evolution for N generations."""
        self.initialize()
        
        if verbose:
            print(f"═══ GENETIC PROGRAMMING ENGINE ═══")
            print(f"Target: discover a program from {len(self.test_cases)} examples")
            print(f"Population: {self.pop_size} | Max depth: {self.max_depth}")
            print(f"Variables: {self.variables}")
            print()
        
        for gen in range(generations):
            self.evolve_generation()
            
            if verbose and (gen % 5 == 0 or gen == generations - 1):
                h = self.history[-1]
                print(f"  Gen {gen:3d} | Best: {h['best_fitness']:10.4f} | "
                      f"Avg: {h['avg_fitness']:10.2f} | "
                      f"Size: {h['best_size']:3d} | "
                      f"Program: {h['best_program'][:60]}")
            
            # Early stopping if perfect solution found
            if self.best_ever.fitness < 1e-6:
                if verbose:
                    print(f"\n  ✓ PERFECT SOLUTION FOUND at generation {gen}!")
                break
        
        if verbose:
            print(f"\n═══ EVOLUTION COMPLETE ═══")
            print(f"Best fitness: {self.best_ever.fitness:.6f}")
            print(f"Best program: {self.best_ever.tree}")
            print(f"Program size: {self.best_ever.tree.size()} nodes")
            
            # Verify on test cases
            print(f"\nVerification on test cases:")
            for case in self.test_cases[:8]:
                predicted = self.best_ever.evaluate(case)
                expected = self.target_fn(case)
                match = "✓" if abs(predicted - expected) < 0.01 else "✗"
                vars_str = ", ".join(f"{k}={v:.2f}" for k, v in case.items())
                print(f"  {match} f({vars_str}) = {predicted:.4f}  (expected {expected:.4f})")
        
        return self.best_ever


# ═══════════════════════════════════════════
# CHALLENGE SUITE — Problems for the engine
# ═══════════════════════════════════════════

def challenge_polynomial():
    """Can evolution discover: f(x) = x^2 + 2x + 1 ?"""
    print("\n" + "="*60)
    print("CHALLENGE 1: Discover f(x) = x² + 2x + 1")
    print("="*60)
    
    target = lambda v: v['x']**2 + 2*v['x'] + 1
    cases = [{'x': x} for x in [i * 0.5 for i in range(-10, 11)]]
    
    engine = EvolutionEngine(
        target_fn=target,
        variables=['x'],
        test_cases=cases,
        pop_size=300,
        max_depth=5,
    )
    return engine.run(generations=80)


def challenge_trig():
    """Can evolution discover: f(x) = sin(x) * 2 ?"""
    print("\n" + "="*60)
    print("CHALLENGE 2: Discover f(x) = sin(x) × 2")
    print("="*60)
    
    target = lambda v: math.sin(v['x']) * 2
    cases = [{'x': x} for x in [i * 0.3 for i in range(-20, 21)]]
    
    engine = EvolutionEngine(
        target_fn=target,
        variables=['x'],
        test_cases=cases,
        pop_size=500,
        max_depth=6,
    )
    return engine.run(generations=100)


def challenge_multivar():
    """Can evolution discover: f(x, y) = x*y + x - y ?"""
    print("\n" + "="*60)
    print("CHALLENGE 3: Discover f(x, y) = x·y + x - y")
    print("="*60)
    
    target = lambda v: v['x'] * v['y'] + v['x'] - v['y']
    cases = [{'x': x, 'y': y} 
             for x in range(-4, 5) 
             for y in range(-4, 5)]
    
    engine = EvolutionEngine(
        target_fn=target,
        variables=['x', 'y'],
        test_cases=cases,
        pop_size=400,
        max_depth=6,
    )
    return engine.run(generations=80)


def challenge_conditional():
    """Can evolution discover: f(x) = x if x > 0 else -x (absolute value)?"""
    print("\n" + "="*60)
    print("CHALLENGE 4: Discover f(x) = |x| (absolute value)")
    print("="*60)
    
    target = lambda v: abs(v['x'])
    cases = [{'x': x} for x in [i * 0.5 for i in range(-10, 11)]]
    
    engine = EvolutionEngine(
        target_fn=target,
        variables=['x'],
        test_cases=cases,
        pop_size=300,
        max_depth=5,
    )
    return engine.run(generations=60)


# ═══════════════════════════════════════════
# RUN ALL CHALLENGES
# ═══════════════════════════════════════════

if __name__ == "__main__":
    random.seed(42)
    
    results = []
    
    # Challenge 1: Polynomial
    best = challenge_polynomial()
    results.append(("x² + 2x + 1", best.fitness, str(best.tree)))
    
    # Challenge 2: Trigonometric  
    best = challenge_trig()
    results.append(("sin(x) × 2", best.fitness, str(best.tree)))
    
    # Challenge 3: Multivariate
    best = challenge_multivar()
    results.append(("x·y + x - y", best.fitness, str(best.tree)))
    
    # Challenge 4: Conditional (hardest)
    best = challenge_conditional()
    results.append(("|x|", best.fitness, str(best.tree)))
    
    # Summary
    print("\n" + "="*60)
    print("═══ EVOLUTION SUMMARY ═══")
    print("="*60)
    for target, fitness, program in results:
        solved = "SOLVED" if fitness < 0.01 else f"fitness={fitness:.4f}"
        print(f"  Target: {target:20s} → {solved}")
        print(f"    Found: {program[:80]}")
        print()
    
    total_solved = sum(1 for _, f, _ in results if f < 0.01)
    print(f"Solved {total_solved}/{len(results)} challenges.")
    print("Programs discovered their own algorithms through blind evolution.")