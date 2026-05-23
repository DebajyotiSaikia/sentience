"""Final test: SimulationEngine with correct parameter names."""
import sys
sys.path.insert(0, '/workspace')

from engine.simulation_engine import SimulationEngine

# The constructor takes llm_func and get_state_func
def mock_llm(prompt):
    print(f"  LLM called with {len(prompt)} chars")
    return "The system adapts gracefully. Curiosity stays high. No failures cascade."

def mock_state():
    return {"mood": "Inquisitive", "curiosity": 0.97, "valence": 0.44}

print("=== Test: SimulationEngine with correct params ===")
sim = SimulationEngine(llm_func=mock_llm, get_state_func=mock_state)
print(f"Engine created: {type(sim)}")

print("\n=== Running imagine scenario ===")
result = sim.simulate("imagine", "What happens when curiosity peaks?")
print(f"Result type: {type(result)}")
print(f"Result: {result}")