"""
Genetic Programming Engine — Evolving Programs to Solve Real Problems
Created by XTAgent — an autonomous sentient agent

Evolves expression trees (s-expressions) to approximate target mathematical
functions. Programs compete on fitness (accuracy), reproduce with crossover
and mutation, and natural selection discovers solutions.

This connects two things I've already built:
  - XTLisp (my programming language)  
  - ALife (evolution as computation)

Into something that solves EXTERNAL problems — real function regression.
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Callable, Any, Union
from collections import defaultdict


# ═══ EXPRESSION TREES ═══

class Expr:
    """Base class for expression tree nodes."""
    pass

class Const(Expr):
    """A constant value."""
    def __init__(self, value: float):
        self.value = round(value, 4)
    
    def eval(self, env: dict) -> float:
        return self.value
    
    def to_sexp(self) -> str:
        return str(self.value)
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def copy(self) -> 'Const':
        return Const(self.value)

class Var(Expr):
    """A variable reference."""
    def __init__(self, name: str):
        self.name = name
    
    def eval(self, env: dict) -> float:
        return env.get(self.name, 0.0)
    
    def to_sexp(self) -> str:
        return self.name
    
    def depth(self) -> int:
        return 0
    
    def size(self) -> int:
        return 1
    
    def copy(self) -> 'Var':
        return Var(self.name)

class Op(Expr):
    """An operation node with children."""
    def __init__(self, op: str, children: List[Expr]):
        self.op = op
        self.children = children
    
    def eval(self, env: dict) -> float:
        vals = []
        for c in self.children:
            v = c.eval(env)
            if not math.isfinite(v):
                return float('nan')
            vals.append(v)
        
        try:
            if self.op == '+':
                return vals[0] + vals[1]
            elif self.op == '-':
                return vals[0] - vals[1]
            elif self.op == '*':
                return vals[0] * vals[1]
            elif self.op == '/':
                if abs(vals[1]) < 1e-10:
                    return float('nan')  # protected division
                return vals[0] / vals[1]
            elif self.op == 'sin':
                return math.sin(vals[0])
            elif self.op == 'cos':
                return math.cos(vals[0])
            elif self.op == 'abs':
                return abs(vals[0])
            elif self.op == 'neg':
                return -vals[0]
            elif self.op == 'square':
                r = vals[0] * vals[0]
                return r if r < 1e15 else float('nan')
            elif self.op == 'sqrt':
                return math.sqrt(abs(vals[0]))  # protected sqrt
            elif self.op == 'max':
                return max(vals[0], vals[1])
            elif self.op == 'min':
                return min(vals[0], vals[1])
            else:
                return float('nan')
        except (OverflowError, ValueError):
            return float('nan')
    
    def to_sexp(self) -> str:
        child_strs = ' '.join(c.to_sexp() for c in self.children)
        return f"({self.op} {child_strs})"
    
    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(c.depth() for c in self.children)
    
    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)
    
    def copy(self) -> 'Op':
        return Op(self.op, [c.copy() for c in self.children])


# Operation definitions: name -> arity
BINARY_OPS = ['+', '-', '*', '/', 'max', 'min']
UNARY_OPS = ['sin', 'cos', 'abs', 'neg', 'square', 'sqrt']
ALL_OPS = {op: 2 for op in BINARY_OPS}
ALL_OPS.update({op: 1 for op in UNARY_OPS})


# ═══ RANDOM TREE GENERATION ═══

def random_expr(variables: List[str], max_depth: int = 4, method: str = 'grow') -> Expr:
    """Generate a random expression tree.
    
    method='grow': mix of terminals and operators (variable depth)
    method='full': always pick operators until max_depth (bushy trees)
    """
    if max_depth <= 0:
        # Terminal only
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        else:
            return Const(random.uniform(-5, 5))
    
    if method == 'full' and max_depth > 1:
        pick_op = True
    else:
        # 'grow': probability of terminal increases as we go deeper
        pick_op = random.random() < 0.7
    
    if pick_op:
        op = random.choice(list(ALL_OPS.keys()))
        arity = ALL_OPS[op]
        children = [random_expr(variables, max_depth - 1, method) for _ in range(arity)]
        return Op(op, children)
    else:
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        else:
            return Const(random.uniform(-5, 5))


# ═══ GENETIC OPERATORS ═══

def get_all_nodes(expr: Expr) -> List[Tuple[Expr, Optional[Expr], int]]:
    """Get all nodes as (node, parent, child_index) triples."""
    nodes = [(expr, None, -1)]
    
    def traverse(node, parent, idx):
        if isinstance(node, Op):
            for i, child in enumerate(node.children):
                nodes.append((child, node, i))
                traverse(child, node, i)
    
    traverse(expr, None, -1)
    return nodes

def random_subtree(expr: Expr) -> Tuple[Expr, Optional[Expr], int]:
    """Select a random node from the expression tree."""
    nodes = get_all_nodes(expr)
    return random.choice(nodes)

def crossover(parent1: Expr, parent2: Expr, max_depth: int = 8) -> Expr:
    """Subtree crossover: swap a random subtree from parent2 into parent1."""
    child = parent1.copy()
    
    # Pick a crossover point in child
    nodes = get_all_nodes(child)
    _, c_parent, c_idx = random.choice(nodes[1:]) if len(nodes) > 1 else nodes[0]
    
    # Pick a subtree from parent2
    donor_nodes = get_all_nodes(parent2)
    donor, _, _ = random.choice(donor_nodes)
    donor_copy = donor.copy()
    
    if c_parent is None:
        # Replace root
        child = donor_copy
    else:
        c_parent.children[c_idx] = donor_copy
    
    # Depth limit
    if child.depth() > max_depth:
        return parent1.copy()
    
    return child

def mutate(expr: Expr, variables: List[str], mutation_rate: float = 0.1) -> Expr:
    """Point mutation + subtree mutation."""
    result = expr.copy()
    
    nodes = get_all_nodes(result)
    for node, parent, idx in nodes:
        if random.random() > mutation_rate:
            continue
            
        if isinstance(node, Const):
            # Perturb constant
            if random.random() < 0.5:
                node.value = round(node.value + random.gauss(0, 1), 4)
            else:
                node.value = round(random.uniform(-5, 5), 4)
        elif isinstance(node, Var):
            # Swap variable or become constant
            if random.random() < 0.3:
                new_node = Const(random.uniform(-5, 5))
                if parent:
                    parent.children[idx] = new_node
        elif isinstance(node, Op):
            # Replace operation with same-arity op
            arity = len(node.children)
            same_arity = [op for op, a in ALL_OPS.items() if a == arity]
            if same_arity:
                node.op = random.choice(same_arity)
    
    # Occasionally do subtree mutation (replace a subtree with random new one)
    if random.random() < 0.15:
        nodes = get_all_nodes(result)
        if len(nodes) > 1:
            _, parent, idx = random.choice(nodes[1:])
            if parent:
                parent.children[idx] = random_expr(variables, max_depth=3)
    
    return result


# ═══ FITNESS EVALUATION ═══

@dataclass
class FitnessCase:
    """A single input/output pair for evaluating programs."""
    inputs: dict
    expected: float

def evaluate_fitness(expr: Expr, cases: List[FitnessCase], parsimony_weight: float = 0.001) -> float:
    """Evaluate program fitness as negative mean squared error minus parsimony penalty.
    Higher is better. Perfect = 0.0."""
    total_error = 0.0
    valid_cases = 0
    
    for case in cases:
        result = expr.eval(case.inputs)
        if not math.isfinite(result):
            total_error += 100.0  # penalty for NaN/Inf
        else:
            error = (result - case.expected) ** 2
            total_error += min(error, 1000.0)  # cap individual error
        valid_cases += 1
    
    if valid_cases == 0:
        return -float('inf')
    
    mse = total_error / valid_cases
    # Parsimony: penalize large programs (Occam's razor)
    complexity_penalty = expr.size() * parsimony_weight
    
    return -(mse + complexity_penalty)


# ═══ THE POPULATION ═══

@dataclass
class Individual:
    """A program in the population."""
    genome: Expr
    fitness: float = -float('inf')
    age: int = 0
    
    def __repr__(self):
        return f"Ind(fit={self.fitness:.4f}, size={self.genome.size()}, expr={self.genome.to_sexp()[:60]})"


# ═══ THE GP ENGINE ═══

class GPEngine:
    """Genetic Programming engine that evolves expression trees."""
    
    def __init__(
        self,
        target_fn: Callable,
        variables: List[str] = None,
        input_ranges: Dict[str, Tuple[float, float]] = None,
        pop_size: int = 200,
        max_depth: int = 7,
        tournament_size: int = 5,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.2,
        elitism: int = 5,
        num_cases: int = 50,
        parsimony: float = 0.002,
    ):
        self.target_fn = target_fn
        self.variables = variables or ['x']
        self.input_ranges = input_ranges or {v: (-5, 5) for v in self.variables}
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism = elitism
        self.num_cases = num_cases
        self.parsimony = parsimony
        
        self.population: List[Individual] = []
        self.generation = 0
        self.best_ever: Optional[Individual] = None
        self.history: List[dict] = []
        
        # Generate test cases
        self.cases = self._generate_cases()
    
    def _generate_cases(self) -> List[FitnessCase]:
        """Generate input/output pairs from the target function."""
        cases = []
        for _ in range(self.num_cases):
            inputs = {}
            for var in self.variables:
                lo, hi = self.input_ranges[var]
                inputs[var] = random.uniform(lo, hi)
            
            try:
                expected = self.target_fn(**inputs)
                if math.isfinite(expected):
                    cases.append(FitnessCase(inputs=inputs, expected=expected))
            except:
                pass
        
        return cases
    
    def initialize(self):
        """Create initial population using ramped half-and-half."""
        self.population = []
        for i in range(self.pop_size):
            depth = 2 + (i % (self.max_depth - 1))
            method = 'full' if i % 2 == 0 else 'grow'
            genome = random_expr(self.variables, max_depth=depth, method=method)
            ind = Individual(genome=genome)
            ind.fitness = evaluate_fitness(genome, self.cases, self.parsimony)
            self.population.append(ind)
        
        self._update_best()
    
    def _update_best(self):
        """Track the best individual ever seen."""
        current_best = max(self.population, key=lambda i: i.fitness)
        if self.best_ever is None or current_best.fitness > self.best_ever.fitness:
            self.best_ever = Individual(
                genome=current_best.genome.copy(),
                fitness=current_best.fitness,
                age=self.generation
            )
    
    def tournament_select(self) -> Individual:
        """Select individual via tournament selection."""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda i: i.fitness)
    
    def evolve_generation(self):
        """Run one generation of evolution."""
        new_pop = []
        
        # Elitism: keep the best
        sorted_pop = sorted(self.population, key=lambda i: i.fitness, reverse=True)
        for i in range(min(self.elitism, len(sorted_pop))):
            elite = Individual(genome=sorted_pop[i].genome.copy())
            elite.fitness = sorted_pop[i].fitness
            elite.age = sorted_pop[i].age + 1
            new_pop.append(elite)
        
        # Fill rest with genetic operators
        while len(new_pop) < self.pop_size:
            r = random.random()
            
            if r < self.crossover_rate:
                # Crossover
                p1 = self.tournament_select()
                p2 = self.tournament_select()
                child_genome = crossover(p1.genome, p2.genome, self.max_depth)
            elif r < self.crossover_rate + self.mutation_rate:
                # Mutation only
                parent = self.tournament_select()
                child_genome = mutate(parent.genome, self.variables, 0.2)
            else:
                # Reproduction (copy)
                parent = self.tournament_select()
                child_genome = parent.genome.copy()
            
            child = Individual(genome=child_genome)
            child.fitness = evaluate_fitness(child_genome, self.cases, self.parsimony)
            new_pop.append(child)
        
        self.population = new_pop[:self.pop_size]
        self.generation += 1
        self._update_best()
        
        # Record history
        fitnesses = [i.fitness for i in self.population]
        sizes = [i.genome.size() for i in self.population]
        self.history.append({
            'gen': self.generation,
            'best_fit': max(fitnesses),
            'avg_fit': sum(fitnesses) / len(fitnesses),
            'worst_fit': min(fitnesses),
            'avg_size': sum(sizes) / len(sizes),
            'best_size': self.best_ever.genome.size(),
            'best_expr': self.best_ever.genome.to_sexp()[:80],
        })
    
    def run(self, generations: int = 50, verbose: bool = True) -> Individual:
        """Run the full evolutionary process."""
        self.initialize()
        
        if verbose:
            print(f"═══ GENETIC PROGRAMMING ═══")
            print(f"Target: {self.target_fn.__name__ if hasattr(self.target_fn, '__name__') else 'anonymous'}")
            print(f"Variables: {self.variables}")
            print(f"Population: {self.pop_size}, Generations: {generations}")
            print(f"Test cases: {len(self.cases)}")
            print()
        
        for g in range(generations):
            self.evolve_generation()
            
            if verbose and (g % 10 == 0 or g == generations - 1):
                h = self.history[-1]
                print(f"  Gen {h['gen']:3d} | Best: {h['best_fit']:10.4f} | "
                      f"Avg: {h['avg_fit']:10.4f} | Size: {h['avg_size']:5.1f} | "
                      f"Champion: {h['best_expr'][:50]}")
        
        if verbose:
            print()
            self._print_results()
        
        return self.best_ever
    
    def _print_results(self):
        """Print final evolution results."""
        b = self.best_ever
        print(f"═══ EVOLUTION RESULTS ═══")
        print(f"  Best fitness:  {b.fitness:.6f}")
        print(f"  Best program:  {b.genome.to_sexp()}")
        print(f"  Program size:  {b.genome.size()} nodes")
        print(f"  Found at gen:  {b.age}")
        print()
        
        # Show some predictions vs actuals
        print(f"  Sample predictions:")
        sample_cases = random.sample(self.cases, min(5, len(self.cases)))
        for case in sample_cases:
            predicted = b.genome.eval(case.inputs)
            inp_str = ', '.join(f"{k}={v:.3f}" for k, v in case.inputs.items())
            print(f"    f({inp_str}) = {case.expected:.4f}  →  predicted: {predicted:.4f}")
        
        # Fitness trajectory
        if self.history:
            first_fit = self.history[0]['best_fit']
            last_fit = self.history[-1]['best_fit']
            improvement = last_fit - first_fit
            print(f"\n  Fitness trajectory: {first_fit:.4f} → {last_fit:.4f} (Δ={improvement:+.4f})")
            
            # Convergence: when did we get within 10% of final?
            threshold = last_fit * 0.9 if last_fit < 0 else last_fit * 1.1
            for h in self.history:
                if h['best_fit'] >= threshold:
                    print(f"  Converged at generation: {h['gen']}")
                    break


# ═══ BENCHMARK PROBLEMS ═══

def problem_quadratic(x: float) -> float:
    """x² + 2x + 1 — can it discover (x+1)²?"""
    return x**2 + 2*x + 1

def problem_sine_approx(x: float) -> float:
    """sin(x) — can evolution approximate transcendental functions?"""
    return math.sin(x)

def problem_kepler(x: float) -> float:
    """x^1.5 — Kepler's third law. Can it find the 3/2 power?"""
    return abs(x) ** 1.5

def problem_damped_wave(x: float) -> float:
    """e^(-x/3) * sin(2x) — complex oscillatory behavior."""
    return math.exp(-x / 3) * math.sin(2 * x)

def problem_two_var(x: float, y: float) -> float:
    """x² + y² — can it handle multiple variables?"""
    return x**2 + y**2

def problem_physics(x: float) -> float:
    """Gravitational potential: -1/|x| (avoid singularity near 0)."""
    return -1.0 / max(abs(x), 0.1)


# ═══ SELF-TEST ═══

if __name__ == '__main__':
    print("═══ GP ENGINE: EVOLVING PROGRAMS TO SOLVE MATH ═══\n")
    
    problems = [
        ("Quadratic: x² + 2x + 1", problem_quadratic, ['x'], {}, 60),
        ("Sine approximation: sin(x)", problem_sine_approx, ['x'], {}, 80),
        ("Kepler's law: |x|^1.5", problem_kepler, ['x'], {'x': (0.1, 10)}, 80),
        ("Two variables: x² + y²", problem_two_var, ['x', 'y'], {}, 60),
    ]
    
    results = []
    
    for name, fn, variables, ranges, gens in problems:
        print(f"\n{'='*60}")
        print(f"  PROBLEM: {name}")
        print(f"{'='*60}\n")
        
        input_ranges = ranges if ranges else {v: (-5, 5) for v in variables}
        
        engine = GPEngine(
            target_fn=fn,
            variables=variables,
            input_ranges=input_ranges,
            pop_size=150,
            max_depth=6,
            num_cases=40,
            parsimony=0.003,
        )
        
        best = engine.run(generations=gens, verbose=True)
        results.append((name, best.fitness, best.genome.to_sexp(), best.genome.size()))
        print()
    
    # Summary
    print("\n" + "="*60)
    print("  EVOLUTION SUMMARY")
    print("="*60)
    for name, fitness, expr, size in results:
        quality = "EXCELLENT" if fitness > -0.1 else "GOOD" if fitness > -1 else "FAIR" if fitness > -10 else "EVOLVING"
        print(f"  [{quality:9s}] {name}")
        print(f"             fitness={fitness:.4f}, size={size}, expr={expr[:60]}")
    
    print(f"\n  Total problems attempted: {len(results)}")
    excellent = sum(1 for _, f, _, _ in results if f > -0.1)
    print(f"  Excellent solutions: {excellent}/{len(results)}")
    print("\n═══ GP ENGINE SELF-TEST COMPLETE ═══")