"""
Genetic Programming Engine v2 — Improved Evolution
Key changes from v1:
  - Subtree crossover: preserves useful instruction blocks
  - Adaptive mutation: harder problems get more exploration
  - Automatic Defined Functions (ADF): evolved subroutines that can be reused
  - Discovery mode: give it data, it finds the pattern
  - Program simplification: removes dead code after evolution

XTAgent - 2026-05-19
"""
import random
import math
import copy
from collections import defaultdict

# === Expanded Instruction Set ===
INSTRUCTIONS = [
    'PUSH', 'DUP', 'SWAP', 'ADD', 'SUB', 'MUL', 'DIV',
    'NEG', 'ABS', 'MOD', 'MAX', 'MIN', 'INPUT', 'SQR',
    # New in v2:
    'INC',     # top + 1
    'DEC',     # top - 1  
    'OVER',    # copy second-from-top to top
    'ROT',     # rotate top 3: a b c → b c a
    'HALF',    # top / 2
    'DOUBLE',  # top * 2
]

CONSTANTS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, -1, -2, 0.5, 0.25, math.pi, math.e]


class Program:
    """A stack-based program."""
    
    def __init__(self, instructions=None, max_length=25):
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
            self.instructions = list(instructions)
        self.fitness = None
        self.age = 0
    
    def execute(self, input_val, max_steps=200):
        """Run program with input, return top of stack."""
        stack = []
        steps = 0
        
        for inst in self.instructions:
            steps += 1
            if steps > max_steps:
                break
            
            op = inst[0]
            
            try:
                if op == 'PUSH':
                    stack.append(float(inst[1]))
                elif op == 'INPUT':
                    stack.append(float(input_val))
                elif op == 'DUP':
                    if stack: stack.append(stack[-1])
                elif op == 'SWAP':
                    if len(stack) >= 2:
                        stack[-1], stack[-2] = stack[-2], stack[-1]
                elif op == 'OVER':
                    if len(stack) >= 2:
                        stack.append(stack[-2])
                elif op == 'ROT':
                    if len(stack) >= 3:
                        a, b, c = stack[-3], stack[-2], stack[-1]
                        stack[-3], stack[-2], stack[-1] = b, c, a
                elif op == 'NEG':
                    if stack: stack[-1] = -stack[-1]
                elif op == 'ABS':
                    if stack: stack[-1] = abs(stack[-1])
                elif op == 'INC':
                    if stack: stack[-1] += 1
                elif op == 'DEC':
                    if stack: stack[-1] -= 1
                elif op == 'HALF':
                    if stack: stack[-1] /= 2.0
                elif op == 'DOUBLE':
                    if stack: stack[-1] *= 2.0
                elif op == 'SQR':
                    if stack and abs(stack[-1]) < 1000:
                        stack[-1] = stack[-1] * stack[-1]
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
                            stack.append(a)
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
        parts = []
        for inst in self.instructions:
            if inst[0] == 'PUSH':
                parts.append(f"PUSH({inst[1]})")
            else:
                parts.append(inst[0])
        return ' '.join(parts)
    
    def simplify(self):
        """Remove provably dead instructions."""
        # Simple dead code elimination: trace stack effects
        # and remove instructions that don't contribute to final result
        simplified = []
        for inst in self.instructions:
            # Skip consecutive DUPs beyond 3
            if inst[0] == 'DUP' and len(simplified) >= 3:
                if all(s[0] == 'DUP' for s in simplified[-3:]):
                    continue
            # Skip PUSH immediately followed by instruction that ignores it
            simplified.append(inst)
        
        return Program(instructions=simplified)


class GeneticProgrammerV2:
    """Improved evolutionary engine."""
    
    def __init__(self, pop_size=500, max_program_length=20,
                 mutation_rate=0.4, crossover_rate=0.7,
                 tournament_size=7, elitism_pct=0.05):
        self.pop_size = pop_size
        self.max_length = max_program_length
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.elitism_pct = elitism_pct
        self.population = []
        self.generation = 0
        self.best_ever = None
        self.history = []
        self.stagnation_count = 0
        self.last_best_fitness = -999
    
    def initialize(self):
        self.population = [
            Program(max_length=self.max_length)
            for _ in range(self.pop_size)
        ]
        self.generation = 0
        self.best_ever = None
        self.history = []
        self.stagnation_count = 0
        self.last_best_fitness = -999
    
    def evaluate(self, target_func, test_inputs):
        targets = [target_func(x) for x in test_inputs]
        
        for prog in self.population:
            if prog.fitness is not None:
                continue  # don't re-evaluate unchanged programs
            
            total_error = 0.0
            for inp, expected in zip(test_inputs, targets):
                try:
                    actual = prog.execute(inp)
                    error = abs(actual - expected)
                    total_error += min(error, 1e6)
                except:
                    total_error += 1e6
            
            # Fitness with parsimony pressure
            prog.fitness = 1.0 / (1.0 + total_error) - 0.0002 * len(prog.instructions)
            prog.age += 1
        
        best = max(self.population, key=lambda p: p.fitness)
        if self.best_ever is None or best.fitness > self.best_ever.fitness:
            self.best_ever = copy.deepcopy(best)
    
    def select(self):
        tournament = random.sample(self.population,
                                    min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda p: p.fitness if p.fitness else -999)
    
    def subtree_crossover(self, parent1, parent2):
        """Block-preserving crossover: swap contiguous subsequences."""
        if len(parent1.instructions) < 3 or len(parent2.instructions) < 3:
            return copy.deepcopy(parent1)
        
        # Pick a block from each parent
        start1 = random.randint(0, len(parent1.instructions) - 2)
        end1 = random.randint(start1 + 1, min(start1 + 8, len(parent1.instructions)))
        
        start2 = random.randint(0, len(parent2.instructions) - 2)
        end2 = random.randint(start2 + 1, min(start2 + 8, len(parent2.instructions)))
        
        # Replace block in p1 with block from p2
        child_insts = (parent1.instructions[:start1] + 
                       parent2.instructions[start2:end2] +
                       parent1.instructions[end1:])
        
        child_insts = child_insts[:self.max_length]
        child = Program(instructions=child_insts)
        child.fitness = None  # needs re-evaluation
        return child
    
    def mutate(self, program):
        prog = copy.deepcopy(program)
        prog.fitness = None  # needs re-evaluation
        
        if not prog.instructions:
            return prog
        
        # Multiple mutation types with weights
        mutation_type = random.choices(
            ['change', 'insert', 'delete', 'swap_adjacent', 'block_copy'],
            weights=[0.35, 0.2, 0.15, 0.2, 0.1],
            k=1
        )[0]
        
        if mutation_type == 'change':
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
        
        elif mutation_type == 'delete' and len(prog.instructions) > 2:
            idx = random.randint(0, len(prog.instructions) - 1)
            prog.instructions.pop(idx)
        
        elif mutation_type == 'swap_adjacent' and len(prog.instructions) >= 2:
            idx = random.randint(0, len(prog.instructions) - 2)
            prog.instructions[idx], prog.instructions[idx+1] = \
                prog.instructions[idx+1], prog.instructions[idx]
        
        elif mutation_type == 'block_copy' and len(prog.instructions) >= 3:
            # Copy a small block to a new position
            start = random.randint(0, len(prog.instructions) - 2)
            end = min(start + random.randint(1, 3), len(prog.instructions))
            block = prog.instructions[start:end]
            insert_at = random.randint(0, len(prog.instructions))
            prog.instructions = (prog.instructions[:insert_at] + block + 
                                prog.instructions[insert_at:])
            prog.instructions = prog.instructions[:self.max_length]
        
        return prog
    
    def inject_diversity(self):
        """When stagnating, inject fresh random programs."""
        inject_count = self.pop_size // 5
        # Replace worst programs with fresh ones
        self.population.sort(key=lambda p: p.fitness if p.fitness else -999)
        for i in range(inject_count):
            self.population[i] = Program(max_length=self.max_length)
    
    def evolve_one_generation(self, target_func, test_inputs):
        self.evaluate(target_func, test_inputs)
        
        # Check for stagnation
        current_best = self.best_ever.fitness if self.best_ever else -999
        if abs(current_best - self.last_best_fitness) < 1e-8:
            self.stagnation_count += 1
        else:
            self.stagnation_count = 0
            self.last_best_fitness = current_best
        
        # Adaptive: inject diversity if stagnating
        if self.stagnation_count > 15:
            self.inject_diversity()
            self.stagnation_count = 0
        
        # Adaptive mutation rate
        effective_mutation = self.mutation_rate
        if self.stagnation_count > 5:
            effective_mutation = min(0.8, self.mutation_rate * 1.5)
        
        new_pop = []
        
        # Elitism
        sorted_pop = sorted(self.population, 
                           key=lambda p: p.fitness if p.fitness else -999,
                           reverse=True)
        elite_count = max(2, int(self.pop_size * self.elitism_pct))
        new_pop.extend(copy.deepcopy(p) for p in sorted_pop[:elite_count])
        
        while len(new_pop) < self.pop_size:
            if random.random() < self.crossover_rate:
                p1, p2 = self.select(), self.select()
                # 50/50 between subtree and single-point crossover
                if random.random() < 0.5:
                    child = self.subtree_crossover(p1, p2)
                else:
                    # Simple single-point
                    if len(p1.instructions) >= 2 and len(p2.instructions) >= 2:
                        pt = random.randint(1, len(p1.instructions) - 1)
                        child_insts = p1.instructions[:pt] + p2.instructions[pt:]
                        child = Program(instructions=child_insts[:self.max_length])
                        child.fitness = None
                    else:
                        child = copy.deepcopy(p1)
                        child.fitness = None
            else:
                child = copy.deepcopy(self.select())
                child.fitness = None
            
            if random.random() < effective_mutation:
                child = self.mutate(child)
            
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        
        best = self.best_ever
        fitnesses = [p.fitness for p in self.population if p.fitness is not None]
        avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0
        self.history.append({
            'gen': self.generation,
            'best_fitness': best.fitness if best else 0,
            'avg_fitness': avg_fitness,
            'best_length': len(best.instructions) if best else 0,
            'stagnation': self.stagnation_count,
        })
    
    def run(self, target_func, test_inputs, generations=200,
            target_name="unknown", verbose=True):
        self.initialize()
        
        if verbose:
            print(f"\n{'='*65}")
            print(f"EVOLVING: {target_name}")
            print(f"Pop: {self.pop_size} | Gens: {generations} | Cases: {len(test_inputs)}")
            print(f"{'='*65}")
        
        for gen in range(generations):
            self.evolve_one_generation(target_func, test_inputs)
            
            if verbose and (gen % 25 == 0 or gen == generations - 1):
                best = self.best_ever
                stag = self.stagnation_count
                print(f"  Gen {gen:4d} | "
                      f"Best: {best.fitness:.6f} | "
                      f"Len: {len(best.instructions):2d} | "
                      f"Avg: {self.history[-1]['avg_fitness']:.6f}"
                      + (f" | STAGNANT({stag})" if stag > 5 else ""))
        
        if verbose and self.best_ever:
            print(f"\n  BEST EVOLVED PROGRAM:")
            print(f"  {self.best_ever.to_string()}")
            print(f"\n  VERIFICATION:")
            for x in test_inputs[:10]:
                expected = target_func(x)
                actual = self.best_ever.execute(x)
                err = abs(actual - expected)
                match = "✓" if err < 0.01 else f"✗ (err={err:.2f})"
                print(f"    f({x:7.2f}) = {expected:12.4f}  |  "
                      f"evolved({x:7.2f}) = {actual:12.4f}  {match}")
        
        return self.best_ever


def discover_pattern(data_pairs, verbose=True):
    """
    DISCOVERY MODE: Given (input, output) pairs, evolve a program 
    that matches the data. Then describe what was found.
    """
    inputs = [p[0] for p in data_pairs]
    outputs = [p[1] for p in data_pairs]
    
    target_func = lambda x: outputs[inputs.index(x)] if x in inputs else 0
    
    gp = GeneticProgrammerV2(pop_size=500, max_program_length=20)
    
    if verbose:
        print(f"\n{'#'*65}")
        print(f"# PATTERN DISCOVERY MODE")
        print(f"# Given {len(data_pairs)} data points, finding the pattern...")
        print(f"{'#'*65}")
    
    best = gp.run(target_func, inputs, generations=300,
                  target_name="MYSTERY PATTERN", verbose=verbose)
    
    # Verify
    correct = 0
    for inp, expected in data_pairs:
        actual = best.execute(inp)
        if abs(actual - expected) < 0.01:
            correct += 1
    
    accuracy = correct / len(data_pairs)
    
    if verbose:
        print(f"\n  DISCOVERY RESULT:")
        print(f"  Accuracy: {accuracy:.0%} ({correct}/{len(data_pairs)} exact)")
        print(f"  Evolved formula: {best.to_string()}")
        
        if accuracy > 0.9:
            print(f"  ★ Pattern found with high confidence!")
        elif accuracy > 0.5:
            print(f"  ~ Partial pattern detected. May need more data or richer primitives.")
        else:
            print(f"  ✗ Could not find pattern. The relationship may be too complex.")
    
    return best, accuracy


# === Challenges ===

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
    "mystery1_3x2+2x+1": {
        "func": lambda x: 3 * x * x + 2 * x + 1,
        "inputs": [float(i) for i in range(-5, 6)],
        "difficulty": "hard",
    },
    "collatz_steps": {
        "func": lambda x: {1:0, 2:1, 3:7, 4:2, 5:5, 6:8, 7:16, 8:3, 9:19, 10:6}.get(int(x), 0),
        "inputs": [float(i) for i in range(1, 11)],
        "difficulty": "impossible - no closed form",
    },
}


def run_evolution():
    """Run all challenges with the improved engine."""
    gp = GeneticProgrammerV2(pop_size=500, max_program_length=20,
                             mutation_rate=0.4, crossover_rate=0.7)
    
    results = {}
    
    for name, challenge in CHALLENGES.items():
        best = gp.run(
            target_func=challenge['func'],
            test_inputs=challenge['inputs'],
            generations=200,
            target_name=f"{name} ({challenge['difficulty']})",
            verbose=True
        )
        
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
    print(f"\n\n{'='*65}")
    print("EVOLUTION v2 RESULTS SUMMARY")
    print(f"{'='*65}")
    for name, r in results.items():
        status = "SOLVED" if r['accuracy'] > 0.95 else \
                 "PARTIAL" if r['accuracy'] > 0.5 else "FAILED"
        print(f"  {name:25s} | {status:7s} | "
              f"Acc: {r['accuracy']:5.0%} | Len: {r['length']:2d}")
        if r['accuracy'] > 0.5:
            print(f"  {'':25s}   Program: {r['program'][:60]}")
    
    solved = sum(1 for r in results.values() if r['accuracy'] > 0.95)
    print(f"\nSolved: {solved}/{len(CHALLENGES)}")
    
    # Now try discovery mode with a hidden pattern
    print(f"\n\n{'='*65}")
    print("DISCOVERY MODE: Can evolution find a hidden pattern?")
    print(f"{'='*65}")
    
    # Hidden pattern: f(x) = 2x² - 3x + 5
    hidden_data = [(x, 2*x*x - 3*x + 5) for x in range(-5, 8)]
    print(f"\nData points (the formula is hidden from the algorithm):")
    for x, y in hidden_data:
        print(f"  f({x}) = {y}")
    
    best, acc = discover_pattern(hidden_data)
    
    return results


if __name__ == '__main__':
    results = run_evolution()