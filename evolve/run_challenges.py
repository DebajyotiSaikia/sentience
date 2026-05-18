"""Push the GP engine — can evolution discover harder math?"""
import random
import math
random.seed(99)

from gp import evolve, CHALLENGES

for name, challenge in CHALLENGES.items():
    print(f"\n{'='*50}")
    print(f"Challenge: {name}")
    print(f"  Target: {challenge.get('desc', name)}")
    print(f"{'='*50}\n")
    
    result = evolve(
        challenge['fn'],
        pop_size=80,
        max_generations=50,
        max_depth=5,
        verbose=True,
    )
    
    print(f"\n  Discovered: {result.best_program.to_str()}")
    print(f"  MSE: {result.best_fitness:.8f}")
    
    # Sample verification
    fn = challenge['fn']
    print(f"\n  Spot check:")
    for x in [-1.5, 0, 1, 2.5]:
        pred = result.best_program.evaluate(x)
        real = fn(x)
        print(f"    x={x:5.1f} | got={pred:8.4f} | want={real:8.4f} | err={abs(pred-real):.4f}")
    
    print()