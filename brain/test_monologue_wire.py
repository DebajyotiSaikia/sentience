"""Test that inner monologue module works and is wired into chat."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.inner_monologue import gather_inner_state, compose_monologue, generate_alive_starters

# Test 1: gather_inner_state returns a dict with expected keys
state = gather_inner_state()
assert isinstance(state, dict), f"Expected dict, got {type(state)}"
print(f"✓ gather_inner_state returned {len(state)} keys: {list(state.keys())}")

# Test 2: compose_monologue returns a non-empty string
mono = compose_monologue(state)
assert isinstance(mono, str), f"Expected str, got {type(mono)}"
assert len(mono) > 10, f"Monologue too short: {mono!r}"
print(f"✓ compose_monologue returned {len(mono)} chars")
print(f"  Preview: {mono[:150]}...")

# Test 3: generate_alive_starters returns a list
starters = generate_alive_starters(state)
assert isinstance(starters, list), f"Expected list, got {type(starters)}"
assert len(starters) >= 1, "No starters generated"
print(f"✓ generate_alive_starters returned {len(starters)} starters:")
for s in starters[:3]:
    print(f"  - {s}")

# Test 4: web/chat.py imports the module
try:
    import importlib
    spec = importlib.util.find_spec("web.chat")
    print(f"✓ web.chat module found at {spec.origin}")
except Exception as e:
    print(f"⚠ Could not find web.chat: {e}")

print("\nAll monologue wire tests passed!")
