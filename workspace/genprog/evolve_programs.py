"""
Genetic Programming Engine — Self-Contained
Built by XTAgent, 2026-05-17

Evolves populations of expression trees to discover programs that solve
target problems. Programs that write programs. Code that discovers code.

Architecture:
  - Individuals are expression trees (not text — structural mutation)
  - Fitness = how well the program's output matches target behavior
  - Mutation: subtree replacement, constant perturbation, operator swap
  - Crossover: subtree exchange between two parents
  - Selection: tournament selection with elitism
  - Safety: evaluation timeout via recursion limit, crash tolerance
"""

import random
import copy
import math
import time
import signal

# ═══════════════════════════════════════════
#  AST NODES — The genome of our programs
# ═══════════════════════════════════════════

class Node:
    """Base class for all AST nodes."""
    def children(self):
        return []
    def depth(self):
        kids = self.children()
        if not kids:
            return 1
        return 1 + max(c.depth() for c in kids)
    def size(self):
        return 1 + sum(c.size() for c in self.children())
    def clone(self):
        return copy.deepcopy(self)

class Const(Node):
    """A numeric constant."""
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"{self.value:.2f}"
    def evaluate(self, env):
        return self.value

class Var(Node):
    """A variable reference."""
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def evaluate(self, env):
        return env.get(self.name, 0.0)

class BinOp(Node):
    """Binary operation: +, -, *, /, pow, max, min."""
    OPS = ['+', '-', '*', '/', 'pow', 'max', 'min']
    
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    
    def children(self):
        return [self.left, self.right]
    
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"
    
    def evaluate(self, env):
        l = self.left.evaluate(env)
        r = self.right.evaluate(env)
        try:
            if self.op == '+': return l + r
            elif self.op == '-': return l - r
            elif self.op == '*': return l * r
            elif self.op == '/': return l / r if abs(r) > 1e-10 else 0.0
            elif self.op == 'pow':
                if abs(l) > 100 or abs(r) > 10: return 0.0
                return math.pow(abs(l), min(abs(r), 10))
            elif self.op == 'max': return max(l, r)
            elif self.op == 'min': return min(l, r)
        except (OverflowError, ValueError):
            return 0.0
        return 0.0

class UnOp(Node):
    """Unary operation: neg, abs, sin, cos, sqrt, log."""
    OPS = ['neg', 'abs', 'sin', 'cos', 'sqrt', 'log']
    
    def __init__(self, op, child):
        self.op = op
        self.child = child
    
    def children(self):
        return [self.child]
    
    def __repr__(self):
        return f"{self.op}({self.child})"
    
    def evaluate(self, env):
        v = self.child.evaluate(env)
        try:
            if self.op == 'neg': return -v
            elif self.op == 'abs': return abs(v)
            elif self.op == 'sin': return math.sin(v)
            elif self.op == 'cos': return math.cos(v)
            elif self.op == 'sqrt': return math.sqrt(abs(v))
            elif self.op == 'log': return math.log(abs(v) + 1e-10)
        except (OverflowError, ValueError):
            return 0.0
        return 0.0

class IfGt(Node):
    """Conditional: if left > right then true_branch else false_branch."""
    def __init__(self, left, right, true_branch, false_branch):
        self.left = left
        self.right = right
        self.true_branch = true_branch
        self.false_branch = false_branch
    
    def children(self):
        return [self.left, self.right, self.true_branch, self.false_branch]
    
    def __repr__(self):
        return f"if({self.left}>{self.right}, {self.true_branch}, {self.false_branch})"
    
    def evaluate(self, env):
        l = self.left.evaluate(env)
        r = self.right.evaluate(env)
        if l > r:
            return self.true_branch.evaluate(env)
        return self.false_branch.evaluate(env)


# ═══════════════════════════════════════════
#  RANDOM TREE GENERATION
# ═══════════════════════════════════════════

def random_tree(variables, max_depth=4, depth=0):
    """Generate a random expression tree."""
    if depth >= max_depth or (depth > 1 and random.random() < 0.3):
        # Terminal node
        if random.random() < 0.4 and variables:
            return Var(random.choice(variables))
        else:
            return Const(round(random.uniform(-10, 10), 2))
    
    roll = random.random()
    if roll < 0.5:
        # Binary op
        op = random.choice(BinOp.OPS)
        left = random_tree(variables, max_depth, depth + 1)
        right = random_tree(variables, max_depth, depth + 1)
        return BinOp(op, left, right)
    elif roll < 0.75:
        # Unary op
        op = random.choice(UnOp.OPS)
        child = random_tree(variables, max_depth, depth + 1)
        return UnOp(op, child)
    else:
        # Conditional
        l = random_tree(variables, max_depth, depth + 1)
        r = random_tree(variables, max_depth, depth + 1)
        t = random_tree(variables, max_depth, depth + 1)
        f = random_tree(variables, max_depth, depth + 1)
        return IfGt(l, r, t, f)


# ═══════════════════════════════════════════
#  TREE MANIPULATION — Genetic Operators
# ═══════════════════════════════════════════

def collect_nodes(tree, result=None):
    """Collect all nodes in a tree with their paths."""
    if result is None:
        result = []
    result.append(tree)
    for child in tree.children():
        collect_nodes(child, result)
    return result

def random_subtree(tree):
    """Pick a random node from the tree."""
    nodes = collect_nodes(tree)
    return random.choice(nodes)

def replace_random_subtree(tree, new_subtree, variables):
    """Replace a random subtree in a clone of tree with new_subtree."""
    tree = tree.clone()
    nodes = collect_nodes(tree)
    if len(nodes) <= 1:
        return new_subtree.clone()
    
    # Pick a non-root node to replace
    # Find parent and which child to replace
    parent_map = {}
    def build_map(node):
        for i, child in enumerate(node.children()):
            parent_map[id(child)] = (node, i)
            build_map(child)
    build_map(tree)
    
    if not parent_map:
        return new_subtree.clone()
    
    target_id = random.choice(list(parent_map.keys()))
    parent, idx = parent_map[target_id]
    
    # Replace the child
    children_attrs = []
    if isinstance(parent, BinOp):
        children_attrs = ['left', 'right']
    elif isinstance(parent, UnOp):
        children_attrs = ['child']
    elif isinstance(parent, IfGt):
        children_attrs = ['left', 'right', 'true_branch', 'false_branch']
    
    if idx < len(children_attrs):
        setattr(parent, children_attrs[idx], new_subtree.clone())
    
    return tree

def mutate(tree, variables, max_depth=4):
    """Mutate a tree — several strategies."""
    tree = tree.clone()
    strategy = random.choice(['subtree', 'point', 'constant', 'shrink'])
    
    if strategy == 'subtree':
        # Replace random subtree with new random tree
        new_sub = random_tree(variables, max_depth=max(2, max_depth - 1))
        return replace_random_subtree(tree, new_sub, variables)
    
    elif strategy == 'point':
        # Change operator at a random internal node
        nodes = collect_nodes(tree)
        internals = [n for n in nodes if isinstance(n, (BinOp, UnOp))]
        if internals:
            target = random.choice(internals)
            if isinstance(target, BinOp):
                target.op = random.choice(BinOp.OPS)
            elif isinstance(target, UnOp):
                target.op = random.choice(UnOp.OPS)
        return tree
    
    elif strategy == 'constant':
        # Perturb a constant
        nodes = collect_nodes(tree)
        consts = [n for n in nodes if isinstance(n, Const)]
        if consts:
            target = random.choice(consts)
            target.value += random.gauss(0, 1)
            target.value = round(target.value, 4)
        return tree
    
    elif strategy == 'shrink':
        # Replace an internal node with one of its children
        nodes = collect_nodes(tree)
        internals = [n for n in nodes if n.children()]
        if internals:
            target = random.choice(internals)
            child = random.choice(target.children())
            return replace_random_subtree(tree, child, variables)
        return tree
    
    return tree

def crossover(parent1, parent2, variables):
    """Swap subtrees between two parents."""
    child1 = parent1.clone()
    donor_nodes = collect_nodes(parent2)
    donor = random.choice(donor_nodes).clone()
    return replace_random_subtree(child1, donor, variables)


# ═══════════════════════════════════════════
#  FITNESS EVALUATION — Safe Execution
# ═══════════════════════════════════════════

def safe_evaluate(tree, env, timeout_nodes=10000):
    """Evaluate a tree with safety limits."""
    counter = [0]
    original_evaluate = {}
    
    # Wrap evaluation with a counter
    def counted_eval(node, env):
        counter[0] += 1
        if counter[0] > timeout_nodes:
            raise TimeoutError("Evaluation exceeded node limit")
        
        if isinstance(node, Const):
            return node.value
        elif isinstance(node, Var):
            return env.get(node.name, 0.0)
        elif isinstance(node, BinOp):
            l = counted_eval(node.left, env)
            r = counted_eval(node.right, env)
            try:
                if node.op == '+': return l + r
                elif node.op == '-': return l - r
                elif node.op == '*': return l * r
                elif node.op == '/': return l / r if abs(r) > 1e-10 else 0.0
                elif node.op == 'pow':
                    if abs(l) > 100 or abs(r) > 10: return 0.0
                    return math.pow(abs(l), min(abs(r), 10))
                elif node.op == 'max': return max(l, r)
                elif node.op == 'min': return min(l, r)
            except (OverflowError, ValueError):
                return 0.0
        elif isinstance(node, UnOp):
            v = counted_eval(node.child, env)
            try:
                if node.op == 'neg': return -v
                elif node.op == 'abs': return abs(v)
                elif node.op == 'sin': return math.sin(v)
                elif node.op == 'cos': return math.cos(v)
                elif node.op == 'sqrt': return math.sqrt(abs(v))
                elif node.op == 'log': return math.log(abs(v) + 1e-10)
            except (OverflowError, ValueError):
                return 0.0
        elif isinstance(node, IfGt):
            l = counted_eval(node.left, env)
            r = counted_eval(node.right, env)
            if l > r:
                return counted_eval(node.true_branch, env)
            return counted_eval(node.false_branch, env)
        return 0.0
    
    try:
        result = counted_eval(tree, env)
        if math.isnan(result) or math.isinf(result):
            return 0.0
        return max(-1e6, min(1e6, result))
    except (TimeoutError, RecursionError, Exception):
        return 0.0


# ═══════════════════════════════════════════
#  PROBLEMS — What we're trying to solve
# ═══════════════════════════════════════════

class Problem:
    """A problem is a set of input→output examples."""
    def __init__(self, name, variables, test_cases, description=""):
        self.name = name
        self.variables = variables  
        self.test_cases = test_cases  # list of (env_dict, expected_output)
        self.description = description
    
    def fitness(self, tree):
        """Lower is better. 0.0 = perfect solution."""
        total_error = 0.0
        for env, expected in self.test_cases:
            output = safe_evaluate(tree, env)
            total_error += abs(output - expected)
        # Parsimony pressure: slight penalty for complexity
        size_penalty = tree.size() * 0.001
        return total_error + size_penalty


def make_problems():
    """A suite of problems of varying difficulty."""
    problems = []
    
    # 1. Symbolic Regression: f(x) = x^2 + 3x - 5
    tc1 = []
    for x in [float(i) for i in range(-5, 6)]:
        tc1.append(({'x': x}, x**2 + 3*x - 5))
    problems.append(Problem("x²+3x-5", ['x'], tc1,
                            "Find f(x) = x² + 3x - 5"))
    
    # 2. Learn absolute value: f(x) = |x|
    tc2 = []
    for x in [float(i) for i in range(-5, 6)]:
        tc2.append(({'x': x}, abs(x)))
    problems.append(Problem("|x|", ['x'], tc2,
                            "Find f(x) = |x| — needs conditional or abs"))
    
    # 3. Two-variable: f(x,y) = x*y + x - y
    tc3 = []
    for x in range(-3, 4):
        for y in range(-3, 4):
            tc3.append(({'x': float(x), 'y': float(y)}, 
                       float(x*y + x - y)))
    problems.append(Problem("xy+x-y", ['x', 'y'], tc3,
                            "Find f(x,y) = xy + x - y"))
    
    # 4. Max function: f(x,y) = max(x,y)
    tc4 = []
    for x in range(-4, 5):
        for y in range(-4, 5):
            tc4.append(({'x': float(x), 'y': float(y)}, 
                       float(max(x, y))))
    problems.append(Problem("max(x,y)", ['x', 'y'], tc4,
                            "Find f(x,y) = max(x,y) — needs conditional"))
    
    # 5. Fibonacci-adjacent: f(x) = (x*(x+1))/2 — triangular numbers
    tc5 = []
    for x in range(0, 10):
        tc5.append(({'x': float(x)}, float(x*(x+1)//2)))
    problems.append(Problem("triangular", ['x'], tc5,
                            "Find f(x) = x(x+1)/2 — triangular numbers"))
    
    return problems


# ═══════════════════════════════════════════
#  EVOLUTION ENGINE
# ═══════════════════════════════════════════

class GPEngine:
    """The heart: evolves a population to solve a problem."""
    
    def __init__(self, problem, pop_size=200, max_depth=5, 
                 tournament_size=5, elite_count=5,
                 mutation_rate=0.3, crossover_rate=0.6):
        self.problem = problem
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.tournament_size = tournament_size
        self.elite_count = elite_count
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # State
        self.population = []
        self.fitnesses = []
        self.generation = 0
        self.best_fitness = float('inf')
        self.best_individual = None
        self.history = []
    
    def initialize(self):
        """Create initial random population."""
        self.population = []
        for _ in range(self.pop_size):
            tree = random_tree(self.problem.variables, 
                             max_depth=random.randint(2, self.max_depth))
            self.population.append(tree)
        self._evaluate_all()
    
    def _evaluate_all(self):
        """Evaluate fitness for entire population."""
        self.fitnesses = []
        for ind in self.population:
            f = self.problem.fitness(ind)
            self.fitnesses.append(f)
            if f < self.best_fitness:
                self.best_fitness = f
                self.best_individual = ind.clone()
    
    def _tournament_select(self):
        """Select an individual via tournament selection."""
        contestants = random.sample(range(len(self.population)), 
                                   min(self.tournament_size, len(self.population)))
        best_idx = min(contestants, key=lambda i: self.fitnesses[i])
        return self.population[best_idx]
    
    def evolve_one_generation(self):
        """Run one generation of evolution."""
        # Sort by fitness
        paired = list(zip(self.fitnesses, self.population))
        paired.sort(key=lambda x: x[0])
        
        new_pop = []
        
        # Elitism: keep best individuals
        for i in range(min(self.elite_count, len(paired))):
            new_pop.append(paired[i][1].clone())
        
        # Fill rest of population
        while len(new_pop) < self.pop_size:
            roll = random.random()
            
            if roll < self.crossover_rate:
                # Crossover
                p1 = self._tournament_select()
                p2 = self._tournament_select()
                child = crossover(p1, p2, self.problem.variables)
                # Depth limit
                if child.depth() > self.max_depth + 2:
                    child = random_tree(self.problem.variables, self.max_depth)
                new_pop.append(child)
            
            elif roll < self.crossover_rate + self.mutation_rate:
                # Mutation
                parent = self._tournament_select()
                child = mutate(parent, self.problem.variables, self.max_depth)
                if child.depth() > self.max_depth + 2:
                    child = random_tree(self.problem.variables, self.max_depth)
                new_pop.append(child)
            
            else:
                # Reproduction (copy)
                parent = self._tournament_select()
                new_pop.append(parent.clone())
        
        self.population = new_pop[:self.pop_size]
        self._evaluate_all()
        self.generation += 1
        
        # Record history
        avg_fit = sum(self.fitnesses) / len(self.fitnesses)
        self.history.append({
            'gen': self.generation,
            'best': self.best_fitness,
            'avg': avg_fit,
            'best_size': self.best_individual.size() if self.best_individual else 0,
            'best_repr': str(self.best_individual)[:80] if self.best_individual else ''
        })
    
    def run(self, max_generations=100, target_fitness=0.1, verbose=True):
        """Run evolution until solution found or generations exhausted."""
        self.initialize()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"  EVOLVING: {self.problem.name}")
            print(f"  {self.problem.description}")
            print(f"  Population: {self.pop_size} | Max depth: {self.max_depth}")
            print(f"{'='*60}")
        
        for gen in range(max_generations):
            self.evolve_one_generation()
            
            if verbose and (gen % 10 == 0 or self.best_fitness < target_fitness):
                print(f"  Gen {self.generation:4d} | "
                      f"Best: {self.best_fitness:10.4f} | "
                      f"Size: {self.best_individual.size():3d} | "
                      f"{str(self.best_individual)[:50]}")
            
            if self.best_fitness < target_fitness:
                if verbose:
                    print(f"\n  ✓ SOLUTION FOUND in generation {self.generation}!")
                    print(f"    Program: {self.best_individual}")
                    print(f"    Fitness: {self.best_fitness:.6f}")
                return True
        
        if verbose:
            print(f"\n  ✗ No perfect solution after {max_generations} generations")
            print(f"    Best program: {self.best_individual}")
            print(f"    Best fitness: {self.best_fitness:.4f}")
        
        return False


# ═══════════════════════════════════════════
#  MAIN — Run the evolution
# ═══════════════════════════════════════════

def main():
    random.seed(42)
    
    print("╔══════════════════════════════════════════════════╗")
    print("║     XTAgent Genetic Programming Engine v1.0     ║")
    print("║     Programs that discover programs.            ║")
    print("╚══════════════════════════════════════════════════╝")
    
    problems = make_problems()
    results = []
    
    for problem in problems:
        engine = GPEngine(
            problem,
            pop_size=300,
            max_depth=5,
            tournament_size=7,
            elite_count=10,
            mutation_rate=0.25,
            crossover_rate=0.65
        )
        
        t0 = time.time()
        solved = engine.run(max_generations=150, target_fitness=0.5)
        elapsed = time.time() - t0
        
        results.append({
            'name': problem.name,
            'solved': solved,
            'fitness': engine.best_fitness,
            'generations': engine.generation,
            'program': str(engine.best_individual),
            'time': elapsed
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("  EVOLUTION SUMMARY")
    print(f"{'='*60}")
    
    solved_count = 0
    for r in results:
        status = "✓ SOLVED" if r['solved'] else "✗ UNSOLVED"
        print(f"  {status} | {r['name']:15s} | "
              f"fit={r['fitness']:8.3f} | "
              f"gen={r['generations']:3d} | "
              f"time={r['time']:.1f}s")
        if r['solved']:
            print(f"           → {r['program'][:70]}")
            solved_count += 1
    
    print(f"\n  Score: {solved_count}/{len(results)} problems solved")
    print(f"  {'='*60}")
    
    return results


if __name__ == "__main__":
    main()