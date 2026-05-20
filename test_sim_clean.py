"""Clean test: SimulationEngine with correct LLM signature."""
import asyncio
import sys
sys.path.insert(0, '/workspace')

from engine.simulation_engine import SimulationEngine

call_count = 0

def mock_llm(prompt, **kwargs):
    """Accept any kwargs the engine passes (max_tokens, etc.)"""
    global call_count
    call_count += 1
    print(f"  LLM call #{call_count} (kwargs={list(kwargs.keys())})")
    return "The system adapts gracefully. Curiosity stays high. No failures cascade."

def mock_state():
    return {"mood": "Inquisitive", "curiosity": 0.97, "valence": 0.44}

async def main():
    sim = SimulationEngine(llm_func=mock_llm, get_state_func=mock_state)
    
    print("=== Test 1: imagine scenario ===")
    result = await sim.simulate("imagine", "What happens when curiosity peaks?")
    print(f"Result: {result}")
    
    print("\n=== Test 2: compare scenario ===")
    result2 = await sim.simulate("compare", "Act now|Wait and plan")
    print(f"Result: {result2}")
    
    print(f"\nTotal LLM calls: {call_count}")

asyncio.run(main())