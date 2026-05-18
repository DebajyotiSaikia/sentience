"""Quick test of the GP engine with lean parameters."""
import random
import math
random.seed(42)

from gp import evolve, CHALLENGES

print("=== GP Engine: Linear Challenge (lean) ===\n")

result = evolve(
    CHALLENGES['linear']['fn'],
    pop_size=40,
    max_generations=30,
    max_depth=4,
    verbose=True,
)

print(f"\nDiscovered: {result.best_program.to_str()}")
print(f"MSE: {result.best_fitness:.8f}")

# Verify
fn = CHALLENGES['linear']['fn']
print("\nVerification (f(x) = 2x + 1):")
for x in [-2, 0, 1, 3.5]:
    pred = result.best_program.evaluate(x)
    real = fn(x)
    print(f"  x={x:5.1f} | got={pred:8.3f} | want={real:8.3f} | err={abs(pred-real):.4f}")