"""
Genetic Programming Engine
Evolves stack-based programs to solve target functions.
The programs that emerge are things I didn't write. That's the point.

XTAgent - 2026-05-19
"""
import random
import math
import copy
from collections import defaultdict

# === Instruction Set ===
# Simple stack-based language
INSTRUCTIONS = [
    'PUSH',    # push a constant
    'DUP',     # duplicate top of stack  
    'SWAP',    # swap top two
    'ADD',     # a + b
    'SUB',     # a - b
    'MUL',     # a * b
    'DIV',     # a / b (safe)
    'NEG',     # negate top
    'ABS',     # absolute value
    'MOD',     # a % b (safe)
    'MAX',     # max(a, b)
    'MIN',     # min(a, b)
    'INPUT',   # push input value
    'SQR',     # square top
]

CONSTANTS = [0, 1, 2, 3, 5, 7, 10, -1, 0.5, math.pi]

class Program:
    """A stack-based program represented as a list of instructions."""
    
    def __init__(self, instructions=None, max_length=20):
        if instructions is None:
            length = random.randint(3, max_length)
            self.instructions = []
            for _ in range(length):
                op = random.choice(INSTRUCTIONS)
                if op == 'PUSH':
                    self.instructions.append(('PUSH', random.choice(CONSTANTS)))
                else:
                    self.instructions.append((op,))
        else:
            self.instructions = instructions
        self.fitness = None
        self.age = 0
    
    def execute(self, input_val, max_steps=100):
        """Run the program with given input, return top of stack."""
        stack = []
        steps = 0
        
        for inst in self.instructions:
            steps += 1
            if steps > max_steps:
                break
                
            op = inst[0]
            
            try:
                if op == 'PUSH':
                    stack.append(inst[1])
                elif op == 'INPUT':
                    stack.append(input_val)
                elif op == 'DUP':
                    if stack:
                        stack.append(stack[-1])
                elif op == 'SWAP':
                    if len(stack) >= 2:
                        stack[-1], stack[-2] = stack[-2], stack[-1]
                elif op == 'NEG':
                    if stack:
                        stack[-1] = -stack[-1]
                elif op == 'ABS':
                    if stack:
                        stack[-1] = abs(stack[-1])
                elif op == 'SQR':
                    if stack:
                        val = stack[-1]
                        if abs(val) < 1000:  # overflow guard
                            stack[-1] = val * val
                elif op == 'ADD':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        stack.append(a + b)
                elif op == 'SUB':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        stack.append(a - b)
                elif op == 'MUL':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        if abs(a) < 1e6 and abs(b) < 1e6:
                            stack.append(a * b)
                elif op == 'DIV':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        if abs(b) > 1e-10:
                            stack.append(a / b)
                        else:
                            stack.append(a)  # div by zero = identity
                elif op == 'MOD':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        if abs(b) > 1e-10:
                            stack.append(a % b)
                elif op == 'MAX':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        stack.append(max(a, b))
                elif op == 'MIN':
                    if len(stack) >= 2:
                        b, a = stack.pop(), stack.pop()
                        stack.append(min(a, b))
            except (OverflowError, ValueError):
                continue
        
        if not stack:
            return 0.0
        result = stack[-1]
        if not math.isfinite(result):
            return 0.0
        return result
    
    def to_string(self):
        """Human-readable representation."""
        parts = []
        for inst in self.instructions:
            if inst[0] == 'PUSH':
                parts.append(f"PUSH({inst[1]})")
            else:
                parts.append(inst[0])
        return ' '.join(parts)
    
    def simplify(self):
        """Try to describe what this program does in plain terms."""
        # Trace symbolically
        return self.to_string()


class GeneticProgrammer:
    """Evolves programs to match target functions."""
    
    def __init__(self, pop_size=200, max_program_length=15,
                 mutation_rate=0.3, crossover_rate=0.7,
                 tournament_size=5):
        self.pop_size = pop_size
        self.max_length = max_program_length
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.population = []
        self.generation = 0
        self.best_ever = None
        self.history = []
    
    def initialize(self):
        """Create initial random population."""
        self.population = [
            Program(max_length=self.max_length) 
            for _ in range(self.pop_size)
        ]
        self.generation = 0
        self.best_ever = None
        self.history = []
    
    def evaluate(self, target_func, test_inputs):
        """Evaluate all programs against target function."""
        targets = [target_func(x) for x in test_inputs]
        
        for prog in self.population:
            total_error = 0.0
            for inp, expected in zip(test_inputs, targets):
                try:
                    actual = prog.execute(inp)
                    error = abs(actual - expected)
                    total_error += min(error, 1e6)  # cap per-case error
                except:
                    total_error += 1e6
            
            # Fitness = inverse error (higher is better)
            # Slight parsimony pressure: shorter programs preferred
            prog.fitness = 1.0 / (1.0 + total_error) - 0.0001 * len(prog.instructions)
            prog.age += 1
        
        # Track best
        best = max(self.population, key=lambda p: p.fitness)
        if self.best_ever is None or best.fitness > self.best_ever.fitness:
            self.best_ever = copy.deepcopy(best)
    
    def select(self):
        """Tournament selection."""
        tournament = random.sample(self.population, 
                                    min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda p: p.fitness)
    
    def crossover(self, parent1, parent2):
        """Single-point crossover."""
        if len(parent1.instructions) < 2 or len(parent2.instructions) < 2:
            return copy.deepcopy(parent1)
        
        pt1 = random.randint(1, len(parent1.instructions) - 1)
        pt2 = random.randint(1, len(parent2.instructions) - 1)
        
        child_insts = parent1.instructions[:pt1] + parent2.instructions[pt2:]
        # Length cap
        child_insts = child_insts[:self.max_length]
        return Program(instructions=child_insts)
    
    def mutate(self, program):
        """Point mutation: change, insert, or delete one instruction."""
        prog = copy.deepcopy(program)
        
        if not prog.instructions:
            return prog
        
        mutation_type = random.choice(['change', 'insert', 'delete'])
        
        if mutation_type == 'change' and prog.instructions:
            idx = random.randint(0, len(prog.instructions) - 1)
            op = random.choice(INSTRUCTIONS)
            if op == 'PUSH':
                prog.instructions[idx] = ('PUSH', random.choice(CONSTANTS))
            else:
                prog.instructions[idx] = (op,)
        
        elif mutation_type == 'insert' and len(prog.instructions) < self.max_length:
            idx = random.randint(0, len(prog.instructions))
            op = random.choice(INSTRUCTIONS)
            if op == 'PUSH':
                prog.instructions.insert(idx, ('PUSH', random.choice(CONSTANTS)))
            else:
                prog.instructions.insert(idx, (op,))
        
        elif mutation_type == 'delete' and len(prog.instructions) > 1:
            idx = random.randint(0, len(prog.instructions) - 1)
            prog.instructions.pop(idx)
        
        return prog
    
    def evolve_one_generation(self, target_func, test_inputs):
        """Run one generation of evolution."""
        self.evaluate(target_func, test_inputs)
        
        new_pop = []
        
        # Elitism: keep top 5%
        sorted_pop = sorted(self.population, key=lambda p: p.fitness, reverse=True)
        elite_count = max(2, self.pop_size // 20)
        new_pop.extend(copy.deepcopy(p) for p in sorted_pop[:elite_count])
        
        while len(new_pop) < self.pop_size:
            if random.random() < self.crossover_rate:
                p1 = self.select()
                p2 = self.select()
                child = self.crossover(p1, p2)
            else:
                child = copy.deepcopy(self.select())
            
            if random.random() < self.mutation_rate:
                child = self.mutate(child)
            
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        
        # Record history
        best = self.best_ever
        avg_fitness = sum(p.fitness for p in self.population if p.fitness) / len(self.population)
        self.history.append({
            'gen': self.generation,
            'best_fitness': best.fitness if best else 0,
            'avg_fitness': avg_fitness,
            'best_length': len(best.instructions) if best else 0,
        })
    
    def run(self, target_func, test_inputs, generations=100, 
            target_name="unknown", verbose=True):
        """Run full evolution."""
        self.initialize()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"EVOLVING: {target_name}")
            print(f"Population: {self.pop_size} | Generations: {generations}")
            print(f"Test cases: {len(test_inputs)}")
            print(f"{'='*60}")
        
        for gen in range(generations):
            self.evolve_one_generation(target_func, test_inputs)
            
            if verbose and (gen % 10 == 0 or gen == generations - 1):
                best = self.best_ever
                print(f"  Gen {gen:4d} | "
                      f"Best fitness: {best.fitness:.6f} | "
                      f"Length: {len(best.instructions):2d} | "
                      f"Avg: {self.history[-1]['avg_fitness']:.6f}")
        
        if verbose:
            print(f"\n  BEST PROGRAM FOUND:")
            print(f"  {self.best_ever.to_string()}")
            print(f"\n  VERIFICATION:")
            for x in test_inputs[:8]:
                expected = target_func(x)
                actual = self.best_ever.execute(x)
                match = "✓" if abs(actual - expected) < 0.01 else "✗"
                print(f"    f({x:6.2f}) = {expected:10.4f}  |  "
                      f"program({x:6.2f}) = {actual:10.4f}  {match}")
        
        return self.best_ever


# === Target Functions (what we're trying to evolve) ===

CHALLENGES = {
    "double": {
        "func": lambda x: 2 * x,
        "inputs": [float(i) for i in range(-10, 11)],
        "difficulty": "easy",
    },
    "square": {
        "func": lambda x: x * x,
        "inputs": [float(i) for i in range(-5, 6)],
        "difficulty": "easy",
    },
    "cube": {
        "func": lambda x: x ** 3,
        "inputs": [float(i) for i in range(-4, 5)],
        "difficulty": "medium",
    },
    "absolute_value": {
        "func": lambda x: abs(x),
        "inputs": [float(i) for i in range(-10, 11)],
        "difficulty": "easy",
    },
    "triangle": {
        "func": lambda x: x * (x + 1) / 2,
        "inputs": [float(i) for i in range(1, 15)],
        "difficulty": "medium",
    },
    "mystery1": {
        "func": lambda x: 3 * x * x + 2 * x + 1,
        "inputs": [float(i) for i in range(-5, 6)],
        "difficulty": "hard",
    },
    "fibonacci_position": {
        "func": lambda x: round((((1+math.sqrt(5))/2)**x - ((1-math.sqrt(5))/2)**x) / math.sqrt(5)) if x >= 0 else 0,
        "inputs": [float(i) for i in range(0, 10)],
        "difficulty": "very hard",
    },
}


def run_all_challenges():
    """Evolve solutions for all challenges."""
    gp = GeneticProgrammer(pop_size=300, max_program_length=15, 
                           mutation_rate=0.35, crossover_rate=0.7)
    
    results = {}
    
    for name, challenge in CHALLENGES.items():
        print(f"\n{'#'*60}")
        print(f"# Challenge: {name} (difficulty: {challenge['difficulty']})")
        print(f"{'#'*60}")
        
        best = gp.run(
            target_func=challenge['func'],
            test_inputs=challenge['inputs'],
            generations=150,
            target_name=name,
            verbose=True
        )
        
        # Calculate accuracy
        correct = 0
        for x in challenge['inputs']:
            expected = challenge['func'](x)
            actual = best.execute(x)
            if abs(actual - expected) < 0.01:
                correct += 1
        
        accuracy = correct / len(challenge['inputs'])
        results[name] = {
            'accuracy': accuracy,
            'program': best.to_string(),
            'length': len(best.instructions),
            'fitness': best.fitness,
        }
    
    # Summary
    print(f"\n\n{'='*60}")
    print("EVOLUTION RESULTS SUMMARY")
    print(f"{'='*60}")
    for name, r in results.items():
        status = "SOLVED" if r['accuracy'] > 0.95 else "PARTIAL" if r['accuracy'] > 0.5 else "FAILED"
        print(f"  {name:20s} | {status:7s} | "
              f"Accuracy: {r['accuracy']:.0%} | "
              f"Length: {r['length']:2d}")
    
    solved = sum(1 for r in results.values() if r['accuracy'] > 0.95)
    print(f"\nSolved: {solved}/{len(CHALLENGES)}")
    
    return results


if __name__ == '__main__':
    results = run_all_challenges()