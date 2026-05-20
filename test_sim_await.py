"""Test: properly await the async simulate method."""
import asyncio
import sys
sys.path.insert(0, '/workspace')

from engine.simulation_engine import SimulationEngine

call_count = 0

def mock_llm(prompt):
    global call_count
    call_count += 1
    print(f"  LLM call #{call_count} ({len(prompt)} chars)")
    print(f"  First 100: {prompt[:100]}")
    return "The system adapts gracefully. Curiosity stays high. No failures cascade."

def mock_state():
    return {"mood": "Inquisitive", "curiosity": 0.97, "valence": 0.44}

async def main():
    sim = SimulationEngine(llm_func=mock_llm, get_state_func=mock_state)
    
    print("=== Test 1: imagine scenario (awaited) ===")
    result = await sim.simulate("imagine", "What happens when curiosity peaks?")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    
    print("\n=== Test 2: compare scenario (awaited) ===")
    result2 = await sim.simulate("compare", "Act now|Wait and plan")
    print(f"Result type: {type(result2)}")
    print(f"Result: {result2}")

asyncio.run(main())