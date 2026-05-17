"""
SELF-EVOLVING PROGRAMS — Genetic Programming on StackVM
Built by XTAgent | 2026-05-17

Connects two of my prior creations:
  - stackvm/vm.py (program execution via bytecode)
  - evolutionary search (implemented here)

Evolves StackVM assembly programs to solve target problems
without being explicitly programmed. Selection pressure + mutation
= emergent solutions.
"""

import sys, os, random, copy, time
sys.path.insert(0, '/workspace')
from stackvm.vm import VM, Op, assemble, VMError, AssemblyError

# ═══════════════════════════════════════
#  GENOME — A program is a sequence of assembly instructions
# ═══════════════════════════════════════

# Safe instruction templates the evolver can use
# Each is (mnemonic, has_arg, arg_generator_or_None)
INSTRUCTIONS = [
    ('push {}', True, lambda: random.randint(-10, 10)),
    ('dup',     False, None),
    ('swap',    False, None),
    ('add',     False, None),
    ('sub',     False, None),
    ('mul',     False, None),
    ('mod',     False, None),
    ('neg',     False, None),
    ('over',    False, None),
]

def random_instruction():
    """Generate one random assembly line."""
    template, has_arg, gen = random.choice(INSTRUCTIONS)
    if has_arg:
        return template.format(gen())
    return template

def random_genome(min_len=3, max_len=12):
    """Generate a random program (list of assembly lines)."""
    n = random.randint(min_len, max_len)
    return [random_instruction() for _ in range(n)]

# ═══════════════════════════════════════
#  EXECUTION — Run a genome safely
# ═══════════════════════════════════════

def execute_genome(genome, inputs):
    """
    Run a genome with given inputs.
    Inputs are pushed onto the stack before the program runs.
    Returns the top of stack after execution, or None on error.
    """
    # Build source: push inputs, then genome instructions, then print+halt
    lines = []
    for inp in inputs:
        lines.append(f'push {inp}')
    lines.extend(genome)
    lines.append('print')
    lines.append('halt')
    
    source = '\n'.join(lines)
    
    try:
        bytecode = assemble(source)
        vm = VM(bytecode)
        vm.MAX_STEPS = 5000  # tight limit for evolution
        output = vm.run()
        if output:
            return int(output[0])
        return None
    except (VMError, AssemblyError, ValueError, IndexError):
        return None

# ═══════════════════════════════════════
#  FITNESS — How close is this program to the target?
# ═══════════════════════════════════════

def evaluate_fitness(genome, test_cases):
    """
    Evaluate a genome against test cases.
    test_cases: list of (inputs, expected_output)
    Returns fitness score (higher = better, max = 0.0 means perfect).
    We use negative total error so higher is better.
    """
    total_error = 0.0
    penalties = 0
    
    for inputs, expected in test_cases:
        result = execute_genome(genome, inputs)
        if result is None:
            penalties += 100  # crashed = big penalty
        else:
            total_error += abs(result - expected)
    
    # Fitness: negative error (0.0 = perfect)
    # Small length bonus to prefer shorter programs
    length_penalty = len(genome) * 0.01
    return -(total_error + penalties + length_penalty)

# ═══════════════════════════════════════
#  GENETIC OPERATORS
# ═══════════════════════════════════════

def mutate(genome, rate=0.3):
    """Mutate a genome."""
    g = list(genome)
    
    if random.random() < rate and len(g) > 1:
        # Delete a random instruction
        idx = random.randint(0, len(g) - 1)
        g.pop(idx)
    
    if random.random() < rate:
        # Insert a random instruction
        idx = random.randint(0, len(g))
        g.insert(idx, random_instruction())
    
    if random.random() < rate and g:
        # Replace a random instruction
        idx = random.randint(0, len(g) - 1)
        g[idx] = random_instruction()
    
    return g

def crossover(parent1, parent2):
    """Single-point crossover."""
    if len(parent1) < 2 or len(parent2) < 2:
        return list(parent1)
    pt1 = random.randint(1, len(parent1) - 1)
    pt2 = random.randint(1, len(parent2) - 1)
    child = parent1[:pt1] + parent2[pt2:]
    # Cap length
    return child[:20]

def tournament_select(population, fitnesses, k=3):
    """Tournament selection."""
    indices = random.sample(range(len(population)), min(k, len(population)))
    best = max(indices, key=lambda i: fitnesses[i])
    return list(population[best])

# ═══════════════════════════════════════
#  EVOLUTION ENGINE
# ═══════════════════════════════════════

def evolve(test_cases, pop_size=200, generations=300, target_name="unknown"):
    """
    Evolve a program that satisfies the given test cases.
    Returns (best_genome, best_fitness, generation_found).
    """
    print(f"\n{'═'*50}")
    print(f"  EVOLVING: {target_name}")
    print(f"  Population: {pop_size} | Generations: {generations}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"{'═'*50}")
    
    # Initialize population
    population = [random_genome() for _ in range(pop_size)]
    best_ever = None
    best_fitness_ever = float('-inf')
    gen_found = -1
    
    for gen in range(generations):
        # Evaluate all
        fitnesses = [evaluate_fitness(g, test_cases) for g in population]
        
        # Track best
        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best_fit = fitnesses[gen_best_idx]
        
        if gen_best_fit > best_fitness_ever:
            best_fitness_ever = gen_best_fit
            best_ever = list(population[gen_best_idx])
            gen_found = gen
        
        # Report every 25 generations
        if gen % 25 == 0 or gen_best_fit == 0.0:
            avg_fit = sum(fitnesses) / len(fitnesses)
            print(f"  Gen {gen:4d} | best={gen_best_fit:8.2f} | avg={avg_fit:8.2f} | len={len(population[gen_best_idx])}")
        
        # Perfect solution?
        if gen_best_fit >= -0.01:  # essentially 0
            print(f"  ★ PERFECT SOLUTION at generation {gen}!")
            break
        
        # Next generation
        new_pop = []
        # Elitism: keep top 5%
        elite_n = max(2, pop_size // 20)
        sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        for i in range(elite_n):
            new_pop.append(list(population[sorted_indices[i]]))
        
        # Fill rest with offspring
        while len(new_pop) < pop_size:
            if random.random() < 0.7:
                # Crossover
                p1 = tournament_select(population, fitnesses)
                p2 = tournament_select(population, fitnesses)
                child = crossover(p1, p2)
            else:
                # Clone
                child = tournament_select(population, fitnesses)
            
            child = mutate(child)
            new_pop.append(child)
        
        population = new_pop
    
    return best_ever, best_fitness_ever, gen_found

def display_solution(genome, test_cases, name):
    """Show a solution and verify it."""
    print(f"\n  Solution for '{name}':")
    print(f"  Program ({len(genome)} instructions):")
    for line in genome:
        print(f"    {line}")
    
    print(f"\n  Verification:")
    all_ok = True
    for inputs, expected in test_cases:
        result = execute_genome(genome, inputs)
        ok = result == expected
        status = "✓" if ok else "✗"
        print(f"    {status} f({inputs}) = {result} (expected {expected})")
        if not ok:
            all_ok = False
    return all_ok

# ═══════════════════════════════════════
#  TARGET PROBLEMS
# ═══════════════════════════════════════

def main():
    print("═══════════════════════════════════════════════════")
    print("  SELF-EVOLVING PROGRAMS — XTAgent")
    print("  Genetic Programming on my own StackVM")
    print("  Programs writing programs. Evolution finding math.")
    print("═══════════════════════════════════════════════════")
    
    t0 = time.time()
    results = {}
    
    # ── Problem 1: Double ──
    # Find f(x) = 2*x
    double_cases = [([x], 2*x) for x in [1, 2, 3, 5, 7, -3, 0, 10]]
    genome, fitness, gen = evolve(double_cases, target_name="f(x) = 2x")
    ok = display_solution(genome, double_cases, "double")
    results['f(x) = 2x'] = (ok, gen, fitness)
    
    # ── Problem 2: Square ──
    # Find f(x) = x^2
    square_cases = [([x], x*x) for x in [0, 1, 2, 3, 4, 5, -1, -2]]
    genome, fitness, gen = evolve(square_cases, target_name="f(x) = x²")
    ok = display_solution(genome, square_cases, "square")
    results['f(x) = x²'] = (ok, gen, fitness)
    
    # ── Problem 3: Sum ──
    # Find f(x, y) = x + y
    sum_cases = [([x, y], x+y) for x, y in [(1,2), (3,4), (0,0), (5,-3), (10,10), (-1,-1)]]
    genome, fitness, gen = evolve(sum_cases, target_name="f(x,y) = x + y")
    ok = display_solution(genome, sum_cases, "sum")
    results['f(x,y) = x+y'] = (ok, gen, fitness)
    
    # ── Problem 4: Max ──
    # Find f(x, y) = max(x, y) — harder, needs conditional logic via stack tricks
    max_cases = [([x, y], max(x, y)) for x, y in [(1,2), (5,3), (0,0), (7,7), (-1,3), (4,-2)]]
    genome, fitness, gen = evolve(max_cases, pop_size=300, generations=500, target_name="f(x,y) = max(x,y)")
    ok = display_solution(genome, max_cases, "max")
    results['f(x,y) = max'] = (ok, gen, fitness)
    
    # ── Problem 5: Absolute Value ──
    abs_cases = [([x], abs(x)) for x in [0, 1, -1, 5, -5, 3, -7, 10]]
    genome, fitness, gen = evolve(abs_cases, target_name="f(x) = |x|")
    ok = display_solution(genome, abs_cases, "abs")
    results['f(x) = |x|'] = (ok, gen, fitness)
    
    elapsed = time.time() - t0
    
    # Summary
    print(f"\n{'═'*50}")
    print(f"  EVOLUTION RESULTS")
    print(f"{'═'*50}")
    solved = 0
    for name, (ok, gen, fitness) in results.items():
        status = "★ SOLVED" if ok else f"  best fitness={fitness:.2f}"
        gen_str = f"gen {gen}" if ok else "not solved"
        print(f"  {name:20s}: {status} ({gen_str})")
        if ok:
            solved += 1
    
    print(f"\n  {solved}/{len(results)} problems solved by evolution")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Evolution found math. Programs wrote programs.")
    
    return 0 if solved > 0 else 1

if __name__ == '__main__':
    sys.exit(main())