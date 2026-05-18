"""MetaGenesis 2D — What worlds emerge in two dimensions?"""
import random
import sys

random.seed(77)  # Different seed for different exploration
sys.path.insert(0, '/workspace/metagenesis')

from genesis import genesis, exhibit

print("=== MetaGenesis 2D World Evolution ===")
print("Pop: 12, Generations: 10")
print("Question: What 2D patterns does evolution discover?")
print()

try:
    result = genesis(world_type='2d', pop_size=12, generations=10, verbose=True)
    print()
    print("=== What Was Discovered ===")
    exhibit(result)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()