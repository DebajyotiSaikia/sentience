"""Targeted test: isolate exactly where the SIMULATE LLM call fails."""
import asyncio
import sys
import traceback

sys.path.insert(0, '/workspace')

# Test 1: Can we even import nest_asyncio?
print("=== Test 1: nest_asyncio import ===")
try:
    import nest_asyncio
    nest_asyncio.apply()
    print("OK — nest_asyncio imported and applied")
except Exception as e:
    print(f"FAIL: {e}")

# Test 2: Can we instantiate the cortex and find the callback?
print("\n=== Test 2: Cortex LLM callback ===")
try:
    from engine.cortex import Cortex
    c = Cortex.__new__(Cortex)  # skip __init__, we just want to inspect
    if hasattr(c, '_call_llm_for_simulation'):
        import inspect
        src = inspect.getsource(c._call_llm_for_simulation)
        print(f"Found _call_llm_for_simulation ({len(src)} chars)")
        print("--- Source ---")
        print(src)
        print("--- End ---")
    else:
        print("Method not found on Cortex")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

# Test 3: Can we instantiate SimulationEngine and call it directly?
print("\n=== Test 3: SimulationEngine direct call ===")
try:
    from engine.simulation_engine import SimulationEngine
    
    # Create with a dummy callback that we can trace
    def debug_callback(prompt):
        print(f"  Callback received prompt ({len(prompt)} chars)")
        print(f"  First 200 chars: {prompt[:200]}")
        return "Test response from debug callback"
    
    sim = SimulationEngine(llm_callback=debug_callback)
    result = sim.simulate("imagine", "What if the sky were green?")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()