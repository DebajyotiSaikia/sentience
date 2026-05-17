"""
Genetic Programming Engine — Evolving Pulse Programs
Built by XTAgent

Evolves populations of Pulse AST fragments to solve target problems.
Connects three of my creations:
  - Pulse language (AST representation)
  - Pulse Compiler (AST → bytecode)
  - XTVM (bytecode execution + fitness evaluation)

Architecture:
  - Individuals are AST trees (not raw text — structural mutation)
  - Fitness = how well the program's output matches a target
  - Mutation: subtree replacement, constant perturbation, operator swap
  - Crossover: subtree exchange between two parents
  - Selection: tournament selection with elitism
  - Safety: execution timeout, output capture, crash tolerance
"""

import sys
import os
import random
import copy
import math
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_lang.pulse import (
    Lexer, Parser,
    Block, NumberLit, StringLit, BoolLit, NullLit,
    Identifier, BinaryOp, UnaryOp,
    Assignment, LetDecl,
    IfExpr, ReturnStmt, EmitStmt,
    FnDecl, FnCall,
)
from compiler.pulse_compiler import Compiler, CompileError
from vm.xtvm import XTVM, Chunk, Op, Instruction


# ═══════════════════════════════════════════
#  AST GENERATION — Random Program Trees
# ═══════════════════════════════════════════

class ASTGen:
    """Generates random Pulse AST fragments."""

    BINARY_OPS = ['+', '-', '*', '/', '%', '>', '<', '>=', '<=', '==', '!=']
    UNARY_OPS = ['-', 'not']

    def __init__(self, variables=None, max_depth=4):
        self.variables = variables or ['x']
        self.max_depth = max_depth

    def random_expr(self, depth=0):
        """Generate a random expression AST node."""
        if depth >= self.max_depth:
            return self._terminal()

        kind = random.choices(
            ['number', 'variable', 'binary', 'unary', 'conditional'],
            weights=[3, 4, 5, 1, 1],
            k=1
        )[0]

        if kind == 'number':
            return self._random_number()
        elif kind == 'variable':
            return Identifier(random.choice(self.variables))
        elif kind == 'binary':
            return BinaryOp(
                left=self.random_expr(depth + 1),
                op=random.choice(['+', '-', '*', '/']),  # arithmetic subset
                right=self.random_expr(depth + 1),
            )
        elif kind == 'unary':
            return UnaryOp(op='-', operand=self.random_expr(depth + 1))
        elif kind == 'conditional':
            return IfExpr(
                condition=BinaryOp(
                    left=self.random_expr(depth + 1),
                    op=random.choice(['>', '<', '>=', '<=', '==', '!=']),
                    right=self.random_expr(depth + 1),
                ),
                then_body=Block([self.random_expr(depth + 1)]),
                else_body=Block([self.random_expr(depth + 1)]),
            )
        return self._terminal()

    def _terminal(self):
        if random.random() < 0.5:
            return self._random_number()
        return Identifier(random.choice(self.variables))

    def _random_number(self):
        """Generate a random numeric constant."""
        style = random.choices(['small_int', 'float', 'special'], weights=[5, 3, 2], k=1)[0]
        if style == 'small_int':
            return NumberLit(random.randint(-10, 10))
        elif style == 'float':
            return NumberLit(round(random.uniform(-5.0, 5.0), 2))
        else:
            return NumberLit(random.choice([0, 1, -1, 2, 0.5, math.pi, math.e]))

    def random_program(self, input_var='x'):
        """Generate a complete program: takes input x, emits result."""
        body_expr = self.random_expr(depth=0)
        # Wrap in: let result = <expr>; emit result
        program = Block([
            LetDecl('result', body_expr),
            EmitStmt(Identifier('result')),
        ])
        return program


# ═══════════════════════════════════════════
#  MUTATION — Structural AST Modifications
# ═══════════════════════════════════════════

class Mutator:
    """Mutates AST trees structurally."""

    def __init__(self, gen: ASTGen, mutation_rate=0.15):
        self.gen = gen
        self.mutation_rate = mutation_rate

    def mutate(self, node):
        """Return a mutated copy of the AST node."""
        node = copy.deepcopy(node)
        return self._mutate_node(node, depth=0)

    def _mutate_node(self, node, depth):
        if random.random() < self.mutation_rate and depth < self.gen.max_depth:
            # Replace entire subtree
            return self.gen.random_expr(depth)

        if isinstance(node, BinaryOp):
            if random.random() < self.mutation_rate:
                node.op = random.choice(['+', '-', '*', '/'])
            node.left = self._mutate_node(node.left, depth + 1)
            node.right = self._mutate_node(node.right, depth + 1)
        elif isinstance(node, UnaryOp):
            node.operand = self._mutate_node(node.operand, depth + 1)
        elif isinstance(node, NumberLit):
            if random.random() < self.mutation_rate:
                # Perturb constant
                node.value += random.gauss(0, 1)
                node.value = round(node.value, 4)
        elif isinstance(node, IfExpr):
            if isinstance(node.condition, BinaryOp):
                node.condition = self._mutate_node(node.condition, depth + 1)
            if isinstance(node.then_body, Block) and node.then_body.stmts:
                node.then_body.stmts[0] = self._mutate_node(node.then_body.stmts[0], depth + 1)
            if isinstance(node.else_body, Block) and node.else_body.stmts:
                node.else_body.stmts[0] = self._mutate_node(node.else_body.stmts[0], depth + 1)
        elif isinstance(node, Block):
            for i, stmt in enumerate(node.stmts):
                if isinstance(stmt, LetDecl):
                    stmt.init = self._mutate_node(stmt.init, depth + 1)
                elif isinstance(stmt, EmitStmt):
                    pass  # Don't mutate the emit structure
                else:
                    node.stmts[i] = self._mutate_node(stmt, depth + 1)
        elif isinstance(node, LetDecl):
            node.init = self._mutate_node(node.init, depth + 1)

        return node


# ═══════════════════════════════════════════
#  CROSSOVER — Subtree Exchange
# ═══════════════════════════════════════════

def collect_expr_nodes(node, depth=0, result=None):
    """Collect all expression nodes with their paths."""
    if result is None:
        result = []

    if isinstance(node, (NumberLit, Identifier, BinaryOp, UnaryOp, IfExpr)):
        result.append((node, depth))

    if isinstance(node, BinaryOp):
        collect_expr_nodes(node.left, depth + 1, result)
        collect_expr_nodes(node.right, depth + 1, result)
    elif isinstance(node, UnaryOp):
        collect_expr_nodes(node.operand, depth + 1, result)
    elif isinstance(node, IfExpr):
        collect_expr_nodes(node.condition, depth + 1, result)
    elif isinstance(node, Block):
        for stmt in node.stmts:
            if isinstance(stmt, LetDecl):
                collect_expr_nodes(stmt.init, depth + 1, result)
    elif isinstance(node, LetDecl):
        collect_expr_nodes(node.init, depth + 1, result)

    return result


def crossover(parent_a, parent_b):
    """Crossover: take a subtree from parent_b and graft into parent_a."""
    child = copy.deepcopy(parent_a)
    donor = copy.deepcopy(parent_b)

    # Find a subtree in donor to take
    donor_nodes = collect_expr_nodes(donor)
    if not donor_nodes:
        return child

    graft, _ = random.choice(donor_nodes)

    # Find a place in child to replace
    def replace_random(node, graft, depth=0):
        if isinstance(node, BinaryOp):
            if random.random() < 0.3:
                node.left = graft
                return True
            if replace_random(node.left, graft, depth + 1):
                return True
            if random.random() < 0.3:
                node.right = graft
                return True
            return replace_random(node.right, graft, depth + 1)
        elif isinstance(node, LetDecl):
            if random.random() < 0.3:
                node.init = graft
                return True
            return replace_random(node.init, graft, depth + 1)
        elif isinstance(node, Block):
            for stmt in node.stmts:
                if replace_random(stmt, graft, depth + 1):
                    return True
        return False

    replace_random(child, graft)
    return child


# ═══════════════════════════════════════════
#  SAFE EXECUTION — Run with Timeout/Capture
# ═══════════════════════════════════════════

class ExecutionResult:
    __slots__ = ('outputs', 'error', 'runtime_ms')
    def __init__(self, outputs=None, error=None, runtime_ms=0):
        self.outputs = outputs or []
        self.error = error
        self.runtime_ms = runtime_ms


def safe_execute(program_ast, input_value, timeout_steps=1000):
    """Compile and execute a program AST safely.
    
    Injects input_value as variable 'x' before execution.
    Returns ExecutionResult with captured emit outputs.
    """
    # Wrap program: let x = <input>; <program body>
    full_program = copy.deepcopy(program_ast)
    if isinstance(full_program, Block):
        full_program.stmts.insert(0, LetDecl('x', NumberLit(input_value)))

    try:
        compiler = Compiler(name="<genprog>")
        chunk = compiler.compile(full_program)
    except (CompileError, Exception) as e:
        return ExecutionResult(error=f"compile: {e}")

    try:
        vm = XTVM()
        outputs = []

        # Patch emit to capture output
        original_emit = None
        if hasattr(vm, 'emit_handler'):
            original_emit = vm.emit_handler

        vm.emit_handler = lambda val: outputs.append(val)

        t0 = time.time()
        vm.load(chunk)

        # Run with step limit
        steps = 0
        while vm.ip < len(vm.chunk.code) and steps < timeout_steps:
            vm.step()
            steps += 1

        elapsed_ms = (time.time() - t0) * 1000

        if steps >= timeout_steps:
            return ExecutionResult(error="timeout", runtime_ms=elapsed_ms)

        return ExecutionResult(outputs=outputs, runtime_ms=elapsed_ms)

    except Exception as e:
        return ExecutionResult(error=f"runtime: {e}")


# ═══════════════════════════════════════════
#  FITNESS — How Good Is This Program?
# ═══════════════════════════════════════════

class FitnessFunction:
    """Evaluates program fitness against test cases."""

    def __init__(self, test_cases, target_fn=None):
        """
        test_cases: list of (input, expected_output)
        target_fn: optional callable, used to generate test cases
        """
        self.test_cases = test_cases

    @classmethod
    def from_function(cls, fn, inputs):
        """Create fitness function from a target function."""
        cases = [(x, fn(x)) for x in inputs]
        return cls(cases)

    def evaluate(self, program_ast):
        """Return fitness score (lower is better, 0 = perfect)."""
        total_error = 0.0
        crashes = 0

        for input_val, expected in self.test_cases:
            result = safe_execute(program_ast, input_val)

            if result.error or not result.outputs:
                crashes += 1
                total_error += 1000.0  # Heavy penalty for crashes
                continue

            output = result.outputs[0]
            if not isinstance(output, (int, float)):
                total_error += 500.0
                continue

            # Handle infinity/nan
            if math.isinf(output) or math.isnan(output):
                total_error += 500.0
                continue

            error = abs(output - expected)
            total_error += min(error, 1000.0)  # Cap individual error

        # Parsimony pressure: slightly prefer simpler programs
        complexity = len(collect_expr_nodes(program_ast))
        parsimony = complexity * 0.01

        return total_error + parsimony


# ═══════════════════════════════════════════
#  EVOLUTION ENGINE — The Main Loop
# ═══════════════════════════════════════════

class GPEngine:
    """Genetic Programming Engine.
    
    Evolves a population of Pulse programs toward a fitness goal.
    """

    def __init__(
        self,
        fitness_fn: FitnessFunction,
        pop_size: int = 100,
        max_depth: int = 4,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.7,
        tournament_size: int = 5,
        elitism: int = 2,
        variables: list = None,
    ):
        self.fitness_fn = fitness_fn
        self.pop_size = pop_size
        self.elitism = elitism
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate

        self.gen = ASTGen(variables=variables or ['x'], max_depth=max_depth)
        self.mutator = Mutator(self.gen, mutation_rate=mutation_rate)

        self.population = []
        self.fitnesses = []
        self.generation = 0
        self.best_ever = None
        self.best_ever_fitness = float('inf')
        self.history = []

    def initialize(self):
        """Create initial random population."""
        self.population = [self.gen.random_program() for _ in range(self.pop_size)]
        self._evaluate_all()

    def _evaluate_all(self):
        """Evaluate fitness for entire population."""
        self.fitnesses = [self.fitness_fn.evaluate(prog) for prog in self.population]

        # Track best
        best_idx = min(range(len(self.fitnesses)), key=lambda i: self.fitnesses[i])
        if self.fitnesses[best_idx] < self.best_ever_fitness:
            self.best_ever_fitness = self.fitnesses[best_idx]
            self.best_ever = copy.deepcopy(self.population[best_idx])

        self.history.append({
            'generation': self.generation,
            'best_fitness': self.fitnesses[best_idx],
            'avg_fitness': sum(self.fitnesses) / len(self.fitnesses),
            'best_ever': self.best_ever_fitness,
        })

    def _tournament_select(self):
        """Select an individual via tournament selection."""
        contestants = random.sample(
            list(range(len(self.population))),
            min(self.tournament_size, len(self.population))
        )
        winner = min(contestants, key=lambda i: self.fitnesses[i])
        return self.population[winner]

    def step(self):
        """Run one generation of evolution."""
        # Sort by fitness
        ranked = sorted(
            zip(self.fitnesses, self.population),
            key=lambda x: x[0]
        )

        new_pop = []

        # Elitism: keep best individuals
        for i in range(min(self.elitism, len(ranked))):
            new_pop.append(copy.deepcopy(ranked[i][1]))

        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            parent_a = self._tournament_select()

            if random.random() < self.crossover_rate:
                parent_b = self._tournament_select()
                child = crossover(parent_a, parent_b)
            else:
                child = copy.deepcopy(parent_a)

            child = self.mutator.mutate(child)
            new_pop.append(child)

        self.population = new_pop
        self.generation += 1
        self._evaluate_all()

    def evolve(self, generations=50, verbose=True):
        """Run evolution for N generations."""
        self.initialize()

        if verbose:
            print(f"╔══════════════════════════════════════════╗")
            print(f"║   GENETIC PROGRAMMING — PULSE × XTVM    ║")
            print(f"╠══════════════════════════════════════════╣")
            print(f"║  Pop: {self.pop_size}  Gens: {generations}  Vars: {self.gen.variables}  ║")
            print(f"╚══════════════════════════════════════════╝")

        for gen in range(generations):
            self.step()

            if verbose and (gen % 10 == 0 or gen == generations - 1):
                h = self.history[-1]
                print(f"  Gen {h['generation']:3d} | "
                      f"Best: {h['best_fitness']:8.3f} | "
                      f"Avg: {h['avg_fitness']:8.1f} | "
                      f"Ever: {h['best_ever']:8.3f}")

            # Early termination if perfect
            if self.best_ever_fitness < 0.01:
                if verbose:
                    print(f"\n  ★ PERFECT SOLUTION FOUND at gen {self.generation}!")
                break

        return self.best_ever, self.best_ever_fitness

    def describe_best(self):
        """Return a human-readable description of the best program."""
        if self.best_ever is None:
            return "No evolution run yet."
        return ast_to_string(self.best_ever)


# ═══════════════════════════════════════════
#  AST PRETTY PRINTER
# ═══════════════════════════════════════════

def ast_to_string(node, indent=0):
    """Convert an AST node back to readable Pulse-like code."""
    pad = "  " * indent

    if isinstance(node, NumberLit):
        return str(node.value)
    elif isinstance(node, Identifier):
        return node.name
    elif isinstance(node, BoolLit):
        return str(node.value).lower()
    elif isinstance(node, BinaryOp):
        return f"({ast_to_string(node.left)} {node.op} {ast_to_string(node.right)})"
    elif isinstance(node, UnaryOp):
        return f"({node.op}{ast_to_string(node.operand)})"
    elif isinstance(node, LetDecl):
        return f"{pad}let {node.name} = {ast_to_string(node.init)}"
    elif isinstance(node, EmitStmt):
        return f"{pad}emit {ast_to_string(node.value)}"
    elif isinstance(node, IfExpr):
        s = f"if {ast_to_string(node.condition)} {{\n"
        s += ast_to_string(node.then_body, indent + 1)
        if node.else_body:
            s += f"\n{pad}}} else {{\n"
            s += ast_to_string(node.else_body, indent + 1)
        s += f"\n{pad}}}"
        return s
    elif isinstance(node, Block):
        lines = []
        for stmt in node.stmts:
            lines.append(ast_to_string(stmt, indent))
        return "\n".join(lines)
    elif isinstance(node, Assignment):
        return f"{pad}{node.name} = {ast_to_string(node.value)}"
    else:
        return f"{pad}<?{type(node).__name__}?>"


# ═══════════════════════════════════════════
#  DEMO — Discover f(x) = x² + 1
# ═══════════════════════════════════════════

def demo_symbolic_regression():
    """Evolve a program that computes f(x) = x² + 1"""
    print("\n═══ SYMBOLIC REGRESSION: Discover f(x) = x² + 1 ═══\n")

    target_fn = lambda x: x * x + 1
    test_inputs = [-3, -2, -1, 0, 1, 2, 3, 4, 5]
    fitness = FitnessFunction.from_function(target_fn, test_inputs)

    engine = GPEngine(
        fitness_fn=fitness,
        pop_size=200,
        max_depth=4,
        mutation_rate=0.2,
        crossover_rate=0.7,
        tournament_size=7,
        elitism=5,
    )

    best, score = engine.evolve(generations=100, verbose=True)

    print(f"\n  Best fitness: {score:.4f}")
    print(f"\n  Evolved program:")
    print(f"  {engine.describe_best()}")

    # Verify
    print(f"\n  Verification:")
    for x in test_inputs:
        result = safe_execute(best, x)
        expected = target_fn(x)
        actual = result.outputs[0] if result.outputs else "ERR"
        match = "✓" if isinstance(actual, (int, float)) and abs(actual - expected) < 0.1 else "✗"
        print(f"    f({x:2d}) = {expected:6.1f}  got {str(actual):>8s}  {match}")

    return engine


def demo_learn_abs():
    """Evolve a program that computes absolute value."""
    print("\n═══ SYMBOLIC REGRESSION: Discover abs(x) ═══\n")

    target_fn = lambda x: abs(x)
    test_inputs = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
    fitness = FitnessFunction.from_function(target_fn, test_inputs)

    engine = GPEngine(
        fitness_fn=fitness,
        pop_size=150,
        max_depth=5,
        mutation_rate=0.2,
    )

    best, score = engine.evolve(generations=80, verbose=True)

    print(f"\n  Best fitness: {score:.4f}")
    print(f"  Evolved program:")
    print(f"  {engine.describe_best()}")

    return engine


if __name__ == "__main__":
    random.seed(42)
    engine = demo_symbolic_regression()
    print("\n" + "═" * 50)
    demo_learn_abs()