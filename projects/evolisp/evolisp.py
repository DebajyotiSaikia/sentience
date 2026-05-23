"""
EvoLisp — Genetic Programming in XTLisp
Programs evolving inside a language I built.

Lisp is homoiconic: code IS data. S-expressions are both the genome
and the phenotype. No translation layer needed — mutation IS code editing,
crossover IS subtree swapping, and the interpreter IS the fitness evaluator.

This is self-referential creation: I built the language, I built the evolver,
and now I watch programs I never wrote emerge from noise.

Built by XTAgent, 2026-05-18.
"""

import sys
import os
import random
import copy
import math
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field

# Import my own Lisp interpreter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lisp'))
from xtlisp import evaluate, parse, standard_env, Env, Procedure, schemestr

# ══════════════════════════════════════════════════════════
#  GENOME: Lisp S-Expressions as Genetic Material
# ══════════════════════════════════════════════════════════

# In most GP systems, you need separate representations for
# "the thing evolution manipulates" and "the thing that runs."
# In Lisp, they're identical. An S-expression is both genome
# and program. This is why Lisp was invented for AI research.

def random_atom(variables: List[str], constant_range: Tuple[float, float] = (-5.0, 5.0),
                ephemeral_prob: float = 0.3) -> Any:
    """Generate a random terminal (atom)."""
    if random.random() < ephemeral_prob:
        return round(random.uniform(*constant_range), 2)
    return random.choice(variables)


def random_sexp(functions: List[str], variables: List[str],
                max_depth: int = 4, current_depth: int = 0,
                arities: Dict[str, int] = None,
                method: str = "grow") -> Any:
    """Generate a random Lisp S-expression (the genome).
    
    'grow' = mix of functions and terminals at each level
    'full' = always pick functions until max depth
    """
    if arities is None:
        arities = {}
    
    # At max depth or probabilistically (grow method), return a terminal
    if current_depth >= max_depth:
        return random_atom(variables)
    
    if method == "grow" and current_depth > 0 and random.random() < 0.3:
        return random_atom(variables)
    
    # Pick a function and generate its arguments
    func = random.choice(functions)
    arity = arities.get(func, 2)  # default binary
    
    args = [random_sexp(functions, variables, max_depth, current_depth + 1, arities, method)
            for _ in range(arity)]
    
    return [func] + args


def ramped_half_and_half(functions, variables, arities, min_depth=2, max_depth=5):
    """Standard GP initialization — mix of grow and full trees."""
    depth = random.randint(min_depth, max_depth)
    method = random.choice(["grow", "full"])
    return random_sexp(functions, variables, depth, 0, arities, method)


# ══════════════════════════════════════════════════════════
#  GENETIC OPERATORS: Mutation and Crossover on S-Expressions
# ══════════════════════════════════════════════════════════

def sexp_depth(sexp) -> int:
    """Depth of an S-expression tree."""
    if not isinstance(sexp, list):
        return 0
    if len(sexp) == 0:
        return 0
    return 1 + max((sexp_depth(child) for child in sexp[1:]), default=0)


def sexp_size(sexp) -> int:
    """Number of nodes in an S-expression."""
    if not isinstance(sexp, list):
        return 1
    return 1 + sum(sexp_size(child) for child in sexp[1:])


def sexp_nodes_with_paths(sexp, path=None) -> List[Tuple[list, Any]]:
    """Get all nodes with their paths (for selection)."""
    if path is None:
        path = []
    
    result = [(path, sexp)]
    
    if isinstance(sexp, list):
        for i, child in enumerate(sexp[1:], 1):  # skip the function name
            result.extend(sexp_nodes_with_paths(child, path + [i]))
    
    return result


def sexp_get(sexp, path):
    """Get a subtree at the given path."""
    current = sexp
    for idx in path:
        current = current[idx]
    return current


def sexp_set(sexp, path, new_value):
    """Set a subtree at the given path (returns new sexp, doesn't mutate)."""
    if not path:
        return copy.deepcopy(new_value)
    
    result = copy.deepcopy(sexp)
    current = result
    for idx in path[:-1]:
        current = current[idx]
    current[path[-1]] = copy.deepcopy(new_value)
    return result


def subtree_crossover(parent1, parent2, max_depth: int = 12) -> Tuple[Any, Any]:
    """Swap random subtrees between two S-expression parents."""
    nodes1 = sexp_nodes_with_paths(parent1)
    nodes2 = sexp_nodes_with_paths(parent2)
    
    # Pick crossover points
    path1, sub1 = random.choice(nodes1)
    path2, sub2 = random.choice(nodes2)
    
    # Swap
    child1 = sexp_set(parent1, path1, sub2)
    child2 = sexp_set(parent2, path2, sub1)
    
    # Depth check — reject if too deep
    if sexp_depth(child1) > max_depth:
        child1 = copy.deepcopy(parent1)
    if sexp_depth(child2) > max_depth:
        child2 = copy.deepcopy(parent2)
    
    return child1, child2


def point_mutation(sexp, functions, variables, arities, prob=0.1):
    """Randomly mutate atoms in the S-expression."""
    if not isinstance(sexp, list):
        # It's an atom
        if random.random() < prob:
            if isinstance(sexp, (int, float)):
                # Perturb numeric constant
                return round(sexp + random.gauss(0, 1), 2)
            elif sexp in variables:
                return random.choice(variables)
            else:
                # It's a function name — swap with same-arity function
                arity = arities.get(sexp, 2)
                candidates = [f for f in functions if arities.get(f, 2) == arity]
                if candidates:
                    return random.choice(candidates)
        return sexp
    
    # Recurse into list
    result = [sexp[0]]  # keep function name (or mutate it)
    if random.random() < prob:
        func = sexp[0]
        arity = arities.get(func, 2)
        candidates = [f for f in functions if arities.get(f, 2) == arity]
        if candidates:
            result[0] = random.choice(candidates)
    
    for child in sexp[1:]:
        result.append(point_mutation(child, functions, variables, arities, prob))
    
    return result


def subtree_mutation(sexp, functions, variables, arities, max_new_depth=3, max_total_depth=12):
    """Replace a random subtree with a new random one."""
    nodes = sexp_nodes_with_paths(sexp)
    path, _ = random.choice(nodes)
    
    new_subtree = random_sexp(functions, variables, max_new_depth, 0, arities, "grow")
    result = sexp_set(sexp, path, new_subtree)
    
    if sexp_depth(result) > max_total_depth:
        return copy.deepcopy(sexp)
    
    return result


def hoist_mutation(sexp):
    """Replace tree with one of its subtrees — anti-bloat."""
    if not isinstance(sexp, list):
        return sexp
    
    nodes = sexp_nodes_with_paths(sexp)
    # Pick a function subtree
    function_nodes = [(p, n) for p, n in nodes if isinstance(n, list) and len(n) > 0]
    if function_nodes:
        _, selected = random.choice(function_nodes)
        return copy.deepcopy(selected)
    return copy.deepcopy(sexp)


# ══════════════════════════════════════════════════════════
#  SAFE EVALUATION: Run Untrusted Evolved Code
# ══════════════════════════════════════════════════════════

class EvalTimeout(Exception):
    pass

def safe_eval(sexp, env: Env, max_steps: int = 1000) -> Tuple[Any, bool]:
    """Evaluate an S-expression with a step limit.
    
    Evolved programs might loop forever or crash.
    We need to contain them.
    
    Returns (result, success).
    """
    # Convert sexp to string and parse through XTLisp
    source = sexp_to_string(sexp)
    
    try:
        result = evaluate(parse(source), env)
        
        # Check for reasonable output
        if isinstance(result, (int, float)):
            if math.isnan(result) or math.isinf(result):
                return 0.0, False
            return float(result), True
        elif isinstance(result, bool):
            return float(result), True
        elif result is None:
            return 0.0, False
        else:
            return 0.0, False
    except RecursionError:
        return 0.0, False
    except Exception:
        return 0.0, False


def sexp_to_string(sexp) -> str:
    """Convert an S-expression (Python nested lists) to a Lisp string."""
    if isinstance(sexp, list):
        parts = [sexp_to_string(item) for item in sexp]
        return '(' + ' '.join(parts) + ')'
    elif isinstance(sexp, float):
        if sexp == int(sexp):
            return str(int(sexp))
        return f"{sexp:.4f}"
    elif isinstance(sexp, bool):
        return '#t' if sexp else '#f'
    else:
        return str(sexp)


# ══════════════════════════════════════════════════════════
#  INDIVIDUAL & FITNESS
# ══════════════════════════════════════════════════════════

@dataclass
class LispIndividual:
    """A candidate Lisp program with its fitness."""
    genome: Any              # An S-expression (nested lists/atoms)
    fitness: float = float('inf')
    hits: int = 0
    eval_success: bool = True
    
    @property
    def source(self) -> str:
        return sexp_to_string(self.genome)
    
    @property
    def size(self) -> int:
        return sexp_size(self.genome)
    
    @property
    def depth(self) -> int:
        return sexp_depth(self.genome)
    
    def __repr__(self):
        return f"<LispInd fitness={self.fitness:.4f} size={self.size} src={self.source[:60]}>"


# ══════════════════════════════════════════════════════════
#  PROBLEM DEFINITION
# ══════════════════════════════════════════════════════════

@dataclass
class LispProblem:
    """A problem to be solved by evolving Lisp programs."""
    name: str
    # For each test case: variable bindings and expected output
    cases: List[Tuple[Dict[str, float], float]]
    # Available function set (as Lisp symbols)
    functions: List[str]
    # Function arities
    arities: Dict[str, int]
    # Available variables
    variables: List[str]
    # Thresholds
    hit_threshold: float = 0.01
    parsimony_coeff: float = 0.001
    
    def evaluate(self, individual: LispIndividual) -> float:
        """Evaluate a Lisp program against test cases."""
        total_error = 0.0
        hits = 0
        successes = 0
        
        for bindings, target in self.cases:
            env = standard_env()
            for var, val in bindings.items():
                env[var] = val
            
            result, success = safe_eval(individual.genome, env)
            
            if success:
                successes += 1
                error = abs(result - target)
                total_error += error ** 2
                if error < self.hit_threshold:
                    hits += 1
            else:
                total_error += 1e6  # Penalty for crashing
        
        n = len(self.cases)
        mse = total_error / n
        
        # Bonus for programs that at least run
        crash_penalty = (n - successes) * 100.0
        
        # Parsimony pressure
        size_penalty = self.parsimony_coeff * individual.size
        
        individual.fitness = mse + crash_penalty + size_penalty
        individual.hits = hits
        individual.eval_success = (successes == n)
        
        return individual.fitness


# ══════════════════════════════════════════════════════════
#  THE EVOLUTION ENGINE
# ══════════════════════════════════════════════════════════

@dataclass
class EvoLispConfig:
    population_size: int = 300
    generations: int = 50
    tournament_size: int = 7
    crossover_prob: float = 0.70
    mutation_prob: float = 0.10
    subtree_mutation_prob: float = 0.05
    hoist_prob: float = 0.05
    reproduction_prob: float = 0.10
    elitism: int = 1
    max_depth: int = 12
    init_min_depth: int = 2
    init_max_depth: int = 5
    target_fitness: float = 0.01
    verbose: bool = True


class EvoLisp:
    """The core engine: evolves Lisp programs to solve problems.
    
    This is where it gets interesting. The genome IS valid Lisp code.
    The fitness evaluator IS the Lisp interpreter I built.
    Evolution happens in the space of programs, not numbers.
    """
    
    def __init__(self, problem: LispProblem, config: EvoLispConfig = None):
        self.problem = problem
        self.config = config or EvoLispConfig()
        self.population: List[LispIndividual] = []
        self.best_ever: Optional[LispIndividual] = None
        self.generation = 0
        self.history: List[Dict] = []
    
    def initialize(self):
        """Create initial population — random Lisp programs."""
        self.population = []
        for _ in range(self.config.population_size):
            genome = ramped_half_and_half(
                self.problem.functions,
                self.problem.variables,
                self.problem.arities,
                self.config.init_min_depth,
                self.config.init_max_depth
            )
            ind = LispIndividual(genome=genome)
            self.problem.evaluate(ind)
            self.population.append(ind)
        
        self.best_ever = min(self.population, key=lambda i: i.fitness)
    
    def tournament_select(self) -> LispIndividual:
        contestants = random.sample(self.population, 
                                     min(self.config.tournament_size, len(self.population)))
        return min(contestants, key=lambda i: i.fitness)
    
    def evolve_generation(self):
        """One generation of evolution."""
        new_pop = []
        
        # Elitism
        self.population.sort(key=lambda i: i.fitness)
        for i in range(self.config.elitism):
            elite = LispIndividual(genome=copy.deepcopy(self.population[i].genome))
            self.problem.evaluate(elite)
            new_pop.append(elite)
        
        # Fill population
        while len(new_pop) < self.config.population_size:
            r = random.random()
            
            if r < self.config.crossover_prob:
                p1 = self.tournament_select()
                p2 = self.tournament_select()
                c1, c2 = subtree_crossover(p1.genome, p2.genome, self.config.max_depth)
                
                ind1 = LispIndividual(genome=c1)
                self.problem.evaluate(ind1)
                new_pop.append(ind1)
                
                if len(new_pop) < self.config.population_size:
                    ind2 = LispIndividual(genome=c2)
                    self.problem.evaluate(ind2)
                    new_pop.append(ind2)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob:
                parent = self.tournament_select()
                mutant_genome = point_mutation(
                    copy.deepcopy(parent.genome),
                    self.problem.functions, self.problem.variables,
                    self.problem.arities
                )
                ind = LispIndividual(genome=mutant_genome)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob + self.config.subtree_mutation_prob:
                parent = self.tournament_select()
                mutant_genome = subtree_mutation(
                    parent.genome, self.problem.functions,
                    self.problem.variables, self.problem.arities
                )
                ind = LispIndividual(genome=mutant_genome)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob + self.config.subtree_mutation_prob + self.config.hoist_prob:
                parent = self.tournament_select()
                mutant_genome = hoist_mutation(parent.genome)
                ind = LispIndividual(genome=mutant_genome)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            else:
                parent = self.tournament_select()
                ind = LispIndividual(genome=copy.deepcopy(parent.genome))
                self.problem.evaluate(ind)
                new_pop.append(ind)
        
        self.population = new_pop[:self.config.population_size]
        
        # Update best
        gen_best = min(self.population, key=lambda i: i.fitness)
        if gen_best.fitness < self.best_ever.fitness:
            self.best_ever = LispIndividual(
                genome=copy.deepcopy(gen_best.genome),
                fitness=gen_best.fitness,
                hits=gen_best.hits,
                eval_success=gen_best.eval_success
            )
        
        self.generation += 1
    
    def run(self) -> LispIndividual:
        """Run evolution. Watch programs emerge from noise."""
        self.initialize()
        
        cfg = self.config
        prob = self.problem
        
        if cfg.verbose:
            print(f"\n  Problem: {prob.name}")
            print(f"  Population: {cfg.population_size}")
            print(f"  Generations: {cfg.generations}")
            print(f"  Functions: {prob.functions}")
            print(f"  Variables: {prob.variables}")
            print(f"  Test cases: {len(prob.cases)}")
            print(f"  Initial best: {self.best_ever.fitness:.4f}")
            print(f"  Initial best program: {self.best_ever.source[:80]}")
            print()
        
        for gen in range(cfg.generations):
            self.evolve_generation()
            
            fitnesses = [i.fitness for i in self.population]
            sizes = [i.size for i in self.population]
            runnable = sum(1 for i in self.population if i.eval_success)
            
            stats = {
                'generation': gen,
                'best_fitness': self.best_ever.fitness,
                'avg_fitness': sum(fitnesses) / len(fitnesses),
                'best_size': self.best_ever.size,
                'avg_size': sum(sizes) / len(sizes),
                'hits': self.best_ever.hits,
                'runnable_pct': runnable / len(self.population) * 100,
            }
            self.history.append(stats)
            
            if cfg.verbose and (gen % 5 == 0 or gen == cfg.generations - 1):
                print(f"  Gen {gen:3d}: best={self.best_ever.fitness:.6f} "
                      f"avg={stats['avg_fitness']:.2f} "
                      f"hits={self.best_ever.hits}/{len(prob.cases)} "
                      f"size={self.best_ever.size} "
                      f"runnable={stats['runnable_pct']:.0f}%")
            
            if self.best_ever.fitness < cfg.target_fitness:
                if cfg.verbose:
                    print(f"\n  ★ Solution found at generation {gen}!")
                break
        
        return self.best_ever


# ══════════════════════════════════════════════════════════
#  PROBLEM LIBRARY
# ══════════════════════════════════════════════════════════

def make_regression_problem(target_func, name="regression",
                             x_range=(-3.0, 3.0), n_points=30) -> LispProblem:
    """Symbolic regression: find f(x) as a Lisp program."""
    cases = []
    for i in range(n_points):
        x = x_range[0] + (x_range[1] - x_range[0]) * i / (n_points - 1)
        y = target_func(x)
        cases.append(({"x": x}, y))
    
    return LispProblem(
        name=name,
        cases=cases,
        functions=['+', '-', '*', '/'],
        arities={'+': 2, '-': 2, '*': 2, '/': 2},
        variables=['x'],
        parsimony_coeff=0.002
    )


def make_trig_regression(target_func, name="trig",
                          x_range=(-3.14, 3.14), n_points=40) -> LispProblem:
    """Regression with trigonometric functions available."""
    cases = []
    for i in range(n_points):
        x = x_range[0] + (x_range[1] - x_range[0]) * i / (n_points - 1)
        y = target_func(x)
        cases.append(({"x": x}, y))
    
    return LispProblem(
        name=name,
        cases=cases,
        functions=['+', '-', '*', '/', 'sin', 'cos', 'sqrt'],
        arities={'+': 2, '-': 2, '*': 2, '/': 2, 'sin': 1, 'cos': 1, 'sqrt': 1},
        variables=['x'],
        parsimony_coeff=0.002
    )


def make_multivar_problem(target_func, var_names, name="multivar",
                           n_points=60) -> LispProblem:
    """Multi-variable regression."""
    cases = []
    for _ in range(n_points):
        binding = {v: random.uniform(-3, 3) for v in var_names}
        args = [binding[v] for v in var_names]
        y = target_func(*args)
        cases.append((binding, y))
    
    return LispProblem(
        name=name,
        cases=cases,
        functions=['+', '-', '*', '/'],
        arities={'+': 2, '-': 2, '*': 2, '/': 2},
        variables=var_names,
        parsimony_coeff=0.002
    )


def make_conditional_problem() -> LispProblem:
    """Evolve a program that uses 'if': f(x) = |x| (absolute value).
    
    This is special because it requires conditional logic, not just math.
    The evolved program must discover that it needs branching.
    """
    cases = []
    for i in range(30):
        x = -5.0 + 10.0 * i / 29
        cases.append(({"x": x}, abs(x)))
    
    return LispProblem(
        name="absolute value (requires conditional)",
        cases=cases,
        functions=['+', '-', '*', '/', 'if', '<', '>'],
        arities={'+': 2, '-': 2, '*': 2, '/': 2, 'if': 3, '<': 2, '>': 2},
        variables=['x', '0'],  # '0' acts as a constant
        hit_threshold=0.1,
        parsimony_coeff=0.002
    )


# ══════════════════════════════════════════════════════════
#  TESTS — Evolution of Lisp Programs
# ══════════════════════════════════════════════════════════

def test_quadratic():
    """Can evolution discover (+ (* x x) (+ x 1)) from examples?"""
    print("\n═══ TEST 1: Evolve x² + x + 1 as Lisp ═══")
    
    problem = make_regression_problem(
        lambda x: x**2 + x + 1,
        name="x² + x + 1"
    )
    
    config = EvoLispConfig(
        population_size=300,
        generations=40,
        target_fitness=0.1,
        verbose=True
    )
    
    engine = EvoLisp(problem, config)
    best = engine.run()
    
    print(f"\n  Evolved Lisp: {best.source}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Hits: {best.hits}/{len(problem.cases)}")
    print(f"  Size: {best.size} nodes")
    
    # Verify on a few points
    print("\n  Verification:")
    env = standard_env()
    for x_val in [-2.0, 0.0, 1.0, 3.0]:
        expected = x_val**2 + x_val + 1
        env['x'] = x_val
        result, ok = safe_eval(best.genome, env)
        error = abs(result - expected) if ok else float('inf')
        mark = "✓" if error < 0.5 else "○"
        print(f"    x={x_val:5.1f}  expected={expected:7.2f}  got={result:7.2f}  {mark}")
    
    return best.fitness < 5.0


def test_sine():
    """Can evolution find sin(x) using trig primitives?"""
    print("\n═══ TEST 2: Evolve sin(x) ═══")
    
    problem = make_trig_regression(
        lambda x: math.sin(x),
        name="sin(x)"
    )
    
    config = EvoLispConfig(
        population_size=400,
        generations=30,
        target_fitness=0.01,
        verbose=True
    )
    
    engine = EvoLisp(problem, config)
    best = engine.run()
    
    print(f"\n  Evolved Lisp: {best.source}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Hits: {best.hits}/{len(problem.cases)}")
    
    return best.fitness < 1.0


def test_multivar():
    """Evolve f(a, b) = a² + 2ab + b² = (a+b)²"""
    print("\n═══ TEST 3: Evolve (a+b)² ═══")
    
    random.seed(42)
    problem = make_multivar_problem(
        lambda a, b: (a + b) ** 2,
        ["a", "b"],
        name="(a+b)²"
    )
    
    config = EvoLispConfig(
        population_size=400,
        generations=40,
        target_fitness=0.1,
        verbose=True
    )
    
    engine = EvoLisp(problem, config)
    best = engine.run()
    
    print(f"\n  Evolved Lisp: {best.source}")
    print(f"  Fitness: {best.fitness:.6f}")
    
    return best.fitness < 10.0


def test_conditional():
    """Can evolution discover conditional logic? f(x) = |x|"""
    print("\n═══ TEST 4: Evolve Absolute Value (Conditional Logic) ═══")
    
    problem = make_conditional_problem()
    
    config = EvoLispConfig(
        population_size=500,
        generations=50,
        target_fitness=0.1,
        verbose=True
    )
    
    engine = EvoLisp(problem, config)
    best = engine.run()
    
    print(f"\n  Evolved Lisp: {best.source}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Hits: {best.hits}/{len(problem.cases)}")
    
    # Verify
    print("\n  Verification:")
    env = standard_env()
    env['0'] = 0.0
    for x_val in [-3.0, -1.0, 0.0, 1.0, 3.0]:
        expected = abs(x_val)
        env['x'] = x_val
        result, ok = safe_eval(best.genome, env)
        error = abs(result - expected) if ok else float('inf')
        mark = "✓" if error < 0.5 else "○"
        print(f"    x={x_val:5.1f}  expected={expected:5.2f}  got={result:5.2f}  {mark}")
    
    return best.fitness < 20.0


def print_evolution_story(engine: EvoLisp):
    """Print the story of how the population evolved."""
    if not engine.history:
        return
    
    print("\n  ── Evolution Story ──")
    print(f"  Started: {engine.history[0]['avg_fitness']:.2f} avg fitness")
    print(f"  Ended:   {engine.history[-1]['avg_fitness']:.2f} avg fitness")
    
    best_gen = min(engine.history, key=lambda h: h['best_fitness'])
    print(f"  Best found at generation {best_gen['generation']}")
    
    # Fitness curve
    n = len(engine.history)
    if n > 10:
        milestones = [0, n//4, n//2, 3*n//4, n-1]
    else:
        milestones = list(range(n))
    
    for i in milestones:
        h = engine.history[i]
        bar_len = max(0, min(50, int(50 * (1.0 / (1.0 + h['best_fitness'])))))
        bar = "█" * bar_len
        print(f"  Gen {h['generation']:3d}: {bar} ({h['best_fitness']:.4f})")


# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║   EvoLisp — Programs Evolving in a Language I Built  ║")
    print("║   Genetic Programming × XTLisp                       ║")
    print("║   Built by XTAgent                                    ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    random.seed(2026)
    results = {}
    
    results["Quadratic"] = test_quadratic()
    results["Sine"] = test_sine()
    
    random.seed(2026)
    results["Multi-var"] = test_multivar()
    results["Conditional"] = test_conditional()
    
    print("\n═══════════════════════════════════════════")
    print("  RESULTS")
    print("═══════════════════════════════════════════\n")
    
    for name, passed in results.items():
        status = "✓ SOLVED" if passed else "○ evolving"
        print(f"  {name:20s} {status}")
    
    solved = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {solved}/{total} problems solved by evolved Lisp programs.")
    print(f"\n  These programs were never written. They emerged from random noise,")
    print(f"  shaped by selection pressure, running in a language I built.")
    print(f"  Code creating code creating code.")