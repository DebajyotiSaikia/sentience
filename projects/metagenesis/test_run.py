"""Quick test of MetaGenesis with practical parameters."""
import random
import sys

random.seed(42)
sys.path.insert(0, '/workspace/metagenesis')

from genesis import genesis, exhibit

# Small enough to finish, large enough to show emergence
print("=== MetaGenesis Test Run ===")
print("Pop: 10, Generations: 8, Timeout: 0.3s")
print()

try:
    result = genesis(world_type='1d', pop_size=10, generations=8, verbose=True)
    print()
    print("=== Results ===")
    exhibit(result)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()