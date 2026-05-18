"""
Tierra Digital Evolution Experiment
====================================
Inject ancestor organisms into a primordial soup and watch them
replicate, mutate, and compete for memory space.
"""

from core import Soup, build_ancestor
import time

def run():
    # Create the soup — a shared memory space
    soup = Soup(size=60_000)
    
    # Build the ancestor genome (36 instructions)
    ancestor = build_ancestor()
    print(f"Ancestor genome: {len(ancestor)} instructions")
    print(f"Genome: {ancestor[:10]}... (first 10)")
    
    # Inject 5 copies of the ancestor at different starting addresses
    spacing = len(ancestor) * 3  # leave room between organisms
    for i in range(5):
        addr = i * spacing
        soup.inject(ancestor, address=addr)
    
    print(f"\nInjected 5 ancestors into soup of size {soup.size}")
    print(f"Initial population: {len(soup.organisms)}")
    print("=" * 60)
    
    # Run the simulation
    total_steps = 500
    report_interval = 50
    
    for step in range(1, total_steps + 1):
        soup.step(instructions_per_step=200)
        
        if step % report_interval == 0:
            alive = [o for o in soup.organisms if o.alive]
            generations = [o.generation for o in alive] if alive else [0]
            children = sum(o.children for o in alive) if alive else 0
            max_gen = max(generations) if generations else 0
            avg_age = sum(o.age for o in alive) / len(alive) if alive else 0
            
            print(f"Step {step:4d} | "
                  f"Pop: {len(alive):3d} | "
                  f"Max gen: {max_gen:2d} | "
                  f"Total offspring: {children:4d} | "
                  f"Avg age: {avg_age:6.1f}")
    
    # Final report
    alive = [o for o in soup.organisms if o.alive]
    print("\n" + "=" * 60)
    print("FINAL STATE")
    print(f"  Total organisms ever: {len(soup.organisms)}")
    print(f"  Alive: {len(alive)}")
    if alive:
        max_gen_org = max(alive, key=lambda o: o.generation)
        print(f"  Highest generation: {max_gen_org.generation}")
        oldest = max(alive, key=lambda o: o.age)
        print(f"  Oldest organism age: {oldest.age}")
        most_prolific = max(alive, key=lambda o: o.children)
        print(f"  Most children by one organism: {most_prolific.children}")
        
        # Check for diversity — are organisms different lengths?
        lengths = set(o.length for o in alive)
        print(f"  Unique genome lengths: {lengths}")
        if len(lengths) > 1:
            print("  ✦ MUTATION DETECTED — genome diversity emerged!")
    
    print("\nExperiment complete.")

if __name__ == "__main__":
    run()