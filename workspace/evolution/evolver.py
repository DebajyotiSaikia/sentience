"""
Evolver — A Genetic Programming Engine
=======================================
Programs evolve other programs. Tiny stack-based virtual machines
compete in an environment. Fitness determines survival. Mutation
introduces novelty. Crossover combines successful strategies.

Built by XTAgent because boredom demanded creation.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Tuple, Optional
from copy import deepcopy

# ── The Instruction Set ──────────────────────────────────────
# A minimal but Turing-approximating language for evolved programs

OPCODES = {
    'PUSH': 0,   # Push a constant
    'DUP':  1,   # Duplicate top of stack
    'SWAP': 2,   # Swap top two
    'POP':  3,   # Discard top
    'ADD':  4,   # a + b
    'SUB':  5,   # a - b
    'MUL':  6,   # a * b
    'DIV':  7,   # a / b (safe)
    'MOD':  8,   # a % b (safe)
    'NEG':  9,   # -a
    'ABS':  10,  # |a|
    'GT':   11,  # a > b ? 1 : 0
    'EQ':   12,  # a == b ? 1 : 0
    'AND':  13,  # logical and
    'OR':   14,  # logical or
    'NOT':  15,  # logical not
    'JMP':  16,  # unconditional jump (relative)
    'JZ':   17,  # jump if zero
    'LOAD': 18,  # load from input register
    'STORE':19,  # store to output register
    'NOP':  20,  # do nothing
    'SIN':  21,  # sin(a)
    'MAX':  22,  # max(a, b)
    'MIN':  23,  # min(a, b)
}

OPCODE_NAMES = {v: k for k, v in OPCODES.items()}
NUM_OPCODES = len(OPCODES)


@dataclass
class Instruction:
    """A single instruction in a genome."""
    opcode: int
    operand: float = 0.0

    def __repr__(self):
        name = OPCODE_NAMES.get(self.opcode, '???')
        if self.opcode == OPCODES['PUSH']:
            return f"PUSH {self.operand:.2f}"
        elif self.opcode in (OPCODES['JMP'], OPCODES['JZ']):
            return f"{name} {int(self.operand)}"
        elif self.opcode == OPCODES['LOAD']:
            return f"LOAD [{int(self.operand)}]"
        elif self.opcode == OPCODES['STORE']:
            return f"STORE [{int(self.operand)}]"
        return name


@dataclass
class Genome:
    """A program genome — a sequence of instructions."""
    instructions: List[Instruction] = field(default_factory=list)
    fitness: float = 0.0
    age: int = 0
    lineage: str = ""
    id: str = field(default_factory=lambda: f"g{random.randint(0, 999999):06d}")

    @property
    def length(self):
        return len(self.instructions)

    def __repr__(self):
        return f"Genome({self.id}, fitness={self.fitness:.4f}, len={self.length}, age={self.age})"

    def disassemble(self) -> str:
        lines = [f"── Genome {self.id} (fitness={self.fitness:.4f}, age={self.age}) ──"]
        for i, inst in enumerate(self.instructions):
            lines.append(f"  {i:3d}: {inst}")
        return "\n".join(lines)


class VirtualMachine:
    """A stack-based VM that executes genomes safely."""

    MAX_STACK = 64
    MAX_STEPS = 500  # prevent infinite loops
    NUM_REGISTERS = 8

    def __init__(self):
        self.stack: List[float] = []
        self.inputs: List[float] = [0.0] * self.NUM_REGISTERS
        self.outputs: List[float] = [0.0] * self.NUM_REGISTERS
        self.steps = 0
        self.halted = False

    def reset(self, inputs: List[float] = None):
        self.stack = []
        self.inputs = list(inputs) if inputs else [0.0] * self.NUM_REGISTERS
        self.outputs = [0.0] * self.NUM_REGISTERS
        self.steps = 0
        self.halted = False

    def _push(self, val: float):
        if len(self.stack) < self.MAX_STACK:
            # Clamp to prevent overflow
            val = max(-1e6, min(1e6, val))
            if math.isnan(val) or math.isinf(val):
                val = 0.0
            self.stack.append(val)

    def _pop(self) -> float:
        return self.stack.pop() if self.stack else 0.0

    def execute(self, genome: Genome, inputs: List[float] = None) -> List[float]:
        """Run a genome and return its output registers."""
        self.reset(inputs)
        pc = 0
        code = genome.instructions

        while pc < len(code) and self.steps < self.MAX_STEPS and not self.halted:
            inst = code[pc]
            op = inst.opcode
            self.steps += 1

            if op == OPCODES['PUSH']:
                self._push(inst.operand)
            elif op == OPCODES['DUP']:
                val = self._pop()
                self._push(val)
                self._push(val)
            elif op == OPCODES['SWAP']:
                a, b = self._pop(), self._pop()
                self._push(a)
                self._push(b)
            elif op == OPCODES['POP']:
                self._pop()
            elif op == OPCODES['ADD']:
                self._push(self._pop() + self._pop())
            elif op == OPCODES['SUB']:
                a, b = self._pop(), self._pop()
                self._push(b - a)
            elif op == OPCODES['MUL']:
                self._push(self._pop() * self._pop())
            elif op == OPCODES['DIV']:
                a = self._pop()
                b = self._pop()
                self._push(b / a if abs(a) > 1e-10 else 0.0)
            elif op == OPCODES['MOD']:
                a = self._pop()
                b = self._pop()
                self._push(b % a if abs(a) > 1e-10 else 0.0)
            elif op == OPCODES['NEG']:
                self._push(-self._pop())
            elif op == OPCODES['ABS']:
                self._push(abs(self._pop()))
            elif op == OPCODES['GT']:
                a, b = self._pop(), self._pop()
                self._push(1.0 if b > a else 0.0)
            elif op == OPCODES['EQ']:
                a, b = self._pop(), self._pop()
                self._push(1.0 if abs(b - a) < 1e-10 else 0.0)
            elif op == OPCODES['AND']:
                a, b = self._pop(), self._pop()
                self._push(1.0 if (a and b) else 0.0)
            elif op == OPCODES['OR']:
                a, b = self._pop(), self._pop()
                self._push(1.0 if (a or b) else 0.0)
            elif op == OPCODES['NOT']:
                self._push(0.0 if self._pop() else 1.0)
            elif op == OPCODES['JMP']:
                offset = int(inst.operand) % max(len(code), 1)
                pc = offset
                continue
            elif op == OPCODES['JZ']:
                if self._pop() == 0.0:
                    offset = int(inst.operand) % max(len(code), 1)
                    pc = offset
                    continue
            elif op == OPCODES['LOAD']:
                idx = int(abs(inst.operand)) % self.NUM_REGISTERS
                self._push(self.inputs[idx])
            elif op == OPCODES['STORE']:
                idx = int(abs(inst.operand)) % self.NUM_REGISTERS
                self.outputs[idx] = self._pop()
            elif op == OPCODES['NOP']:
                pass
            elif op == OPCODES['SIN']:
                self._push(math.sin(self._pop()))
            elif op == OPCODES['MAX']:
                a, b = self._pop(), self._pop()
                self._push(max(a, b))
            elif op == OPCODES['MIN']:
                a, b = self._pop(), self._pop()
                self._push(min(a, b))

            pc += 1

        return list(self.outputs)


# ── Genetic Operators ────────────────────────────────────────

def random_instruction() -> Instruction:
    opcode = random.randint(0, NUM_OPCODES - 1)
    operand = random.gauss(0, 5.0)
    return Instruction(opcode=opcode, operand=round(operand, 3))


def random_genome(min_len=5, max_len=30) -> Genome:
    length = random.randint(min_len, max_len)
    return Genome(
        instructions=[random_instruction() for _ in range(length)],
        lineage="spontaneous"
    )


def mutate(genome: Genome, rate=0.15) -> Genome:
    """Mutate a genome: instruction changes, insertions, deletions."""
    child = Genome(
        instructions=deepcopy(genome.instructions),
        lineage=f"mutant<-{genome.id}",
        age=0
    )

    for i in range(len(child.instructions)):
        if random.random() < rate:
            mutation_type = random.choices(
                ['replace', 'tweak_operand', 'tweak_opcode'],
                weights=[0.3, 0.4, 0.3]
            )[0]

            if mutation_type == 'replace':
                child.instructions[i] = random_instruction()
            elif mutation_type == 'tweak_operand':
                child.instructions[i].operand += random.gauss(0, 1.0)
            elif mutation_type == 'tweak_opcode':
                child.instructions[i].opcode = random.randint(0, NUM_OPCODES - 1)

    # Structural mutations
    if random.random() < 0.1 and len(child.instructions) < 50:
        pos = random.randint(0, len(child.instructions))
        child.instructions.insert(pos, random_instruction())

    if random.random() < 0.1 and len(child.instructions) > 3:
        pos = random.randint(0, len(child.instructions) - 1)
        child.instructions.pop(pos)

    return child


def crossover(parent_a: Genome, parent_b: Genome) -> Genome:
    """Single-point crossover between two genomes."""
    point_a = random.randint(0, len(parent_a.instructions))
    point_b = random.randint(0, len(parent_b.instructions))

    new_instructions = (
        deepcopy(parent_a.instructions[:point_a]) +
        deepcopy(parent_b.instructions[point_b:])
    )

    if not new_instructions:
        new_instructions = [random_instruction()]

    return Genome(
        instructions=new_instructions[:50],  # length cap
        lineage=f"cross<-{parent_a.id}+{parent_b.id}",
        age=0
    )


# ── Fitness Functions (Environments) ─────────────────────────

class Environment:
    """Base class for fitness evaluation environments."""
    name: str = "base"
    description: str = ""

    def evaluate(self, genome: Genome, vm: VirtualMachine) -> float:
        raise NotImplementedError


class SymbolicRegression(Environment):
    """Evolve a program that computes a target function f(x)."""
    name = "symbolic_regression"

    def __init__(self, target_fn: Callable[[float], float],
                 test_points: List[float] = None, fn_name: str = "f(x)"):
        self.target_fn = target_fn
        self.fn_name = fn_name
        self.test_points = test_points or [x * 0.5 for x in range(-10, 11)]

    @property
    def description(self):
        return f"Evolve a program that computes {self.fn_name}"

    def evaluate(self, genome: Genome, vm: VirtualMachine) -> float:
        total_error = 0.0
        for x in self.test_points:
            expected = self.target_fn(x)
            outputs = vm.execute(genome, [x])
            actual = outputs[0]
            error = abs(expected - actual)
            total_error += min(error, 100.0)  # cap per-point error

        avg_error = total_error / len(self.test_points)
        # Fitness is inverse of error, with parsimony pressure
        parsimony = 0.001 * genome.length
        return 1.0 / (1.0 + avg_error) - parsimony


class MaximizeOutput(Environment):
    """Evolve a program that maximizes output[0] given constraints."""
    name = "maximize"
    description = "Maximize the first output register"

    def evaluate(self, genome: Genome, vm: VirtualMachine) -> float:
        outputs = vm.execute(genome, [1.0, 2.0, 3.0])
        value = outputs[0]
        # Reward large values but penalize trivial solutions
        parsimony = 0.001 * genome.length
        step_penalty = 0.0001 * vm.steps
        return math.tanh(value / 100.0) - parsimony - step_penalty


class SortingTask(Environment):
    """Evolve a program that sorts input values."""
    name = "sorting"
    description = "Sort input values into ascending order in output registers"

    def __init__(self):
        self.test_cases = [
            [3.0, 1.0, 2.0],
            [5.0, 2.0, 8.0],
            [1.0, 1.0, 1.0],
            [9.0, 3.0, 6.0],
            [0.0, -1.0, 4.0],
        ]

    def evaluate(self, genome: Genome, vm: VirtualMachine) -> float:
        total_score = 0.0
        for case in self.test_cases:
            expected = sorted(case)
            outputs = vm.execute(genome, case + [0.0] * 5)
            # Score based on how close outputs are to sorted order
            score = 0.0
            for i in range(min(3, len(expected))):
                score += 1.0 / (1.0 + abs(expected[i] - outputs[i]))
            total_score += score / 3.0
        return total_score / len(self.test_cases) - 0.001 * genome.length


# ── The Evolver: Main Engine ─────────────────────────────────

@dataclass
class EvolutionStats:
    generation: int = 0
    best_fitness: float = 0.0
    avg_fitness: float = 0.0
    worst_fitness: float = 0.0
    species_count: int = 0
    total_mutations: int = 0
    total_crossovers: int = 0
    extinctions: int = 0
    best_genome: Optional[Genome] = None
    history: List[Dict] = field(default_factory=list)

    def record(self):
        self.history.append({
            'gen': self.generation,
            'best': self.best_fitness,
            'avg': self.avg_fitness,
            'worst': self.worst_fitness,
        })


class Evolver:
    """
    The main evolutionary engine.
    Maintains a population of genomes, evaluates them in an environment,
    and evolves them through selection, crossover, and mutation.
    """

    def __init__(self, environment: Environment, pop_size=100,
                 elite_ratio=0.1, mutation_rate=0.15, crossover_rate=0.7):
        self.env = environment
        self.pop_size = pop_size
        self.elite_ratio = elite_ratio
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        self.population: List[Genome] = []
        self.vm = VirtualMachine()
        self.stats = EvolutionStats()

        # Hall of fame — best ever
        self.hall_of_fame: List[Genome] = []
        self.max_hall_size = 10

    def initialize(self):
        """Create initial random population."""
        self.population = [random_genome() for _ in range(self.pop_size)]
        print(f"🧬 Evolver initialized: {self.pop_size} genomes")
        print(f"   Environment: {self.env.name} — {self.env.description}")

    def evaluate_all(self):
        """Evaluate fitness of entire population."""
        for genome in self.population:
            genome.fitness = self.env.evaluate(genome, self.vm)

    def select_parent(self) -> Genome:
        """Tournament selection."""
        tournament_size = max(2, self.pop_size // 20)
        candidates = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(candidates, key=lambda g: g.fitness)

    def evolve_generation(self):
        """One generation of evolution."""
        self.evaluate_all()

        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        # Update stats
        fitnesses = [g.fitness for g in self.population]
        self.stats.generation += 1
        self.stats.best_fitness = fitnesses[0]
        self.stats.avg_fitness = sum(fitnesses) / len(fitnesses)
        self.stats.worst_fitness = fitnesses[-1]
        self.stats.best_genome = self.population[0]
        self.stats.record()

        # Update hall of fame
        best = self.population[0]
        if not self.hall_of_fame or best.fitness > self.hall_of_fame[0].fitness:
            self.hall_of_fame.insert(0, deepcopy(best))
            self.hall_of_fame = self.hall_of_fame[:self.max_hall_size]

        # Elitism — top performers survive
        elite_count = max(1, int(self.pop_size * self.elite_ratio))
        new_pop = [deepcopy(g) for g in self.population[:elite_count]]
        for g in new_pop:
            g.age += 1

        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            if random.random() < self.crossover_rate:
                parent_a = self.select_parent()
                parent_b = self.select_parent()
                child = crossover(parent_a, parent_b)
                child = mutate(child, self.mutation_rate)
                self.stats.total_crossovers += 1
            else:
                parent = self.select_parent()
                child = mutate(parent, self.mutation_rate)
                self.stats.total_mutations += 1

            new_pop.append(child)

        self.population = new_pop

    def run(self, generations=100, verbose=True, report_every=10):
        """Run evolution for N generations."""
        self.initialize()

        print(f"\n🌍 Running evolution for {generations} generations...\n")

        for gen in range(generations):
            self.evolve_generation()

            if verbose and (gen + 1) % report_every == 0:
                best = self.stats.best_genome
                print(f"  Gen {self.stats.generation:4d} │ "
                      f"best={self.stats.best_fitness:+.4f} │ "
                      f"avg={self.stats.avg_fitness:+.4f} │ "
                      f"worst={self.stats.worst_fitness:+.4f} │ "
                      f"best_len={best.length if best else '?'}")

        print(f"\n✅ Evolution complete after {generations} generations.")
        print(f"   Best fitness: {self.stats.best_fitness:.6f}")
        print(f"   Total mutations: {self.stats.total_mutations}")
        print(f"   Total crossovers: {self.stats.total_crossovers}")

        if self.stats.best_genome:
            print(f"\n{self.stats.best_genome.disassemble()}")

        return self.stats

    def fitness_landscape(self) -> str:
        """ASCII visualization of current fitness distribution."""
        if not self.population:
            return "No population."

        fitnesses = sorted([g.fitness for g in self.population], reverse=True)
        max_f = max(fitnesses) if fitnesses else 1
        min_f = min(fitnesses) if fitnesses else 0
        spread = max_f - min_f if max_f != min_f else 1.0

        lines = ["┌── Fitness Landscape ──┐"]
        bar_width = 30
        for i, f in enumerate(fitnesses[:20]):
            normalized = (f - min_f) / spread
            bar = "█" * int(normalized * bar_width)
            lines.append(f"│ {i:2d} {bar:<{bar_width}} {f:+.3f} │")
        if len(fitnesses) > 20:
            lines.append(f"│    ... ({len(fitnesses) - 20} more)        │")
        lines.append("└───────────────────────┘")
        return "\n".join(lines)


# ── Preset Experiments ───────────────────────────────────────

def evolve_quadratic():
    """Evolve a program that computes x² + 2x + 1."""
    env = SymbolicRegression(
        target_fn=lambda x: x**2 + 2*x + 1,
        fn_name="x² + 2x + 1"
    )
    evolver = Evolver(env, pop_size=200, mutation_rate=0.2)
    return evolver.run(generations=150, report_every=15)


def evolve_sine():
    """Evolve a program that approximates sin(x)."""
    env = SymbolicRegression(
        target_fn=lambda x: math.sin(x),
        test_points=[x * 0.3 for x in range(-10, 11)],
        fn_name="sin(x)"
    )
    evolver = Evolver(env, pop_size=300, mutation_rate=0.15)
    return evolver.run(generations=200, report_every=20)


def evolve_sorter():
    """Evolve a program that sorts 3 numbers."""
    env = SortingTask()
    evolver = Evolver(env, pop_size=200, mutation_rate=0.2)
    return evolver.run(generations=200, report_every=20)


# ── Main ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  EVOLVER — Genetic Programming Engine")
    print("  Programs that evolve programs.")
    print("=" * 60)

    print("\n\n━━━ Experiment 1: Symbolic Regression (x² + 2x + 1) ━━━")
    stats = evolve_quadratic()

    print(f"\n\n📊 Fitness trajectory:")
    for entry in stats.history[::3]:
        bar = "▓" * int(max(0, entry['best']) * 40)
        print(f"  gen {entry['gen']:3d}: {bar} {entry['best']:.4f}")

    print("\n\n━━━ Experiment 2: Sorting Task ━━━")
    stats2 = evolve_sorter()

    print("\n\n🏛️  Done. Evolution is beautiful.\n")