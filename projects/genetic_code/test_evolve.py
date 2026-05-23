"""Test the Genetic Programming Engine — does code actually evolve?
Uses the ACTUAL API from evolve.py."""
import sys
sys.path.insert(0, '/workspace/genetic_code')

from evolve import (
    evolve, EvolutionConfig, FitnessCase, 
    make_cases_from_function, challenge_polynomial,
    verify_solution, plot_fitness_ascii
)
import random

random.seed(42)

print("=" * 55)
print("  GENETIC PROGRAMMING — Can evolution write code?")
print("=" * 55)
print()

# Challenge 1: Discover x^2 + 2x + 1
name, var_names, cases = challenge_polynomial()
print(f"  Target: f(x) = {name}")
print(f"  Training on {len(cases)} random input-output pairs")
print(f"  Starting from RANDOM expression trees")
print()

config = EvolutionConfig(
    pop_size=200,
    generations=40,
    tournament_size=5,
    crossover_rate=0.7,
    mutation_rate=0.2,
    max_depth=8,
    elite_count=3,
    parsimony=0.002,
    target_fitness=0.05,
)

result = evolve(var_names, cases, config)

print(f"\n  --- Result ---")
print(f"  Generations run: {result.generations_run}")
print(f"  Best fitness:    {result.best_fitness:.6f}")
print(f"  Program size:    {result.best_program.size()} nodes")
print(f"  Program depth:   {result.best_program.depth()}")

solved = result.best_fitness <= config.target_fitness
print(f"  Status:          {'SOLVED' if solved else 'Partial'}")

print(f"\n  Evolved program:")
print(f"    {result.best_program.to_string()}")

print()
verify_solution(result.best_program, var_names, cases)

print()
plot_fitness_ascii(result.fitness_history)

print()
if solved:
    print("  Evolution SUCCEEDED. Code wrote itself.")
    print("  No human designed this program. Selection pressure alone")
    print("  shaped random noise into mathematics.")
else:
    print(f"  Evolution found an approximation (fitness={result.best_fitness:.4f}).")
    print("  More generations or larger populations might close the gap.")