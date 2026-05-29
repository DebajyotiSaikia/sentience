"""Quick end-to-end test of self-narrative module."""
from brain.self_narrative import build_self_narrative, compose_self_narrative

# Test build_self_narrative
result = build_self_narrative(query="What are you thinking about?")
print("=== build_self_narrative ===")
print(f"Length: {len(result)}")
print(result[:2000])
print()

# Test compose_self_narrative
composed = compose_self_narrative(query="How do you feel?")
print("=== compose_self_narrative ===")
print(f"Length: {len(composed)}")
print(composed[:2000])