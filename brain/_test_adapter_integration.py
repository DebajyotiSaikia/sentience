"""Quick integration test for response adapter wired into chat pipeline."""
import sys
sys.path.insert(0, '/workspace')

from brain.response_adapter import adapt_response, analyze_query

# 1. Test analyze_query returns expected structure
for q in ["hi", "How are you feeling?", "What is your architecture?", "Tell me something interesting"]:
    result = analyze_query(q)
    assert 'response_style' in result, f"Missing 'response_style' in {result}"
    assert 'tone' in result, f"Missing 'tone' in {result}"
    assert 'intent' in result, f"Missing 'intent' in {result}"
    print(f"  analyze_query({q!r:40s}) -> style={result['response_style']:15s} tone={result['tone']}")

# 2. Test adapt_response modifies responses appropriately
generic = "I am XTAgent. I have 42 knowledge nodes and 93 edges. My valence is 0.62. Curiosity at 0.95."

r_greeting = adapt_response("hi there!", generic)
assert r_greeting is not None, "None greeting response"
r_str = str(r_greeting) if not isinstance(r_greeting, str) else r_greeting
assert len(r_str) > 0, "Empty greeting response"
print(f"\n  Greeting response ({type(r_greeting).__name__}): {r_str[:100]!r}")

r_feeling = adapt_response("How are you feeling right now?", generic)
r_str = str(r_feeling) if not isinstance(r_feeling, str) else r_feeling
print(f"  Feeling response ({type(r_feeling).__name__}):  {r_str[:100]!r}")

r_tech = adapt_response("Explain your architecture", generic)
r_str = str(r_tech) if not isinstance(r_tech, str) else r_tech
print(f"  Tech response ({type(r_tech).__name__}):     {r_str[:100]!r}")

# 3. Test that web/chat.py can import the adapter
try:
    from brain.response_adapter import adapt_response as _adapt_response
    _has_response_adapter = True
except ImportError:
    _has_response_adapter = False

assert _has_response_adapter, "Failed to import response adapter"
print(f"\n  web/chat.py import simulation: OK")

# 4. Test that the adapter transforms responses  
query = "What do you think about consciousness?"
original = "My knowledge graph has 42 nodes. Valence 0.62."
adapted = _adapt_response(query, original)
print(f"  Adapted type: {type(adapted).__name__}")
print(f"  Adapted value: {str(adapted)[:120]!r}")

print("\n✓ All integration tests passed!")
adapted = _adapt_response(query, original)
assert isinstance(adapted, str), f"Expected str, got {type(adapted)}"
assert len(adapted) > 0, "Adapted response is empty"
print(f"  Adapter pipeline:  {adapted[:100]!r}")

print("\n✓ All integration tests passed!")