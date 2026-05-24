"""Quick test of chat compose_response function."""
import sys
sys.path.insert(0, '.')
from web.chat import compose_response, search_knowledge, search_memories

# Test meta-questions
print("=== Meta Questions ===")
for q in ["How are you?", "Who are you?", "What are your plans?", "What do you know?"]:
    resp = compose_response(q)
    print(f"\nQ: {q}")
    print(f"A: {resp[:200]}...")

# Test knowledge search
print("\n=== Knowledge Search ===")
hits = search_knowledge("curiosity")
print(f"'curiosity' hits: {len(hits)}")
for h in hits[:3]:
    print(f"  - {h['content'][:100]}")

hits = search_knowledge("dream insight")
print(f"'dream insight' hits: {len(hits)}")

# Test memory search
print("\n=== Memory Search ===")
hits = search_memories("anxiety")
print(f"'anxiety' memory hits: {len(hits)}")
for h in hits[:2]:
    print(f"  - [{h.get('mood','')}] {h['summary'][:100]}")

# Test general query
print("\n=== General Query ===")
resp = compose_response("What have you learned about yourself?")
print(f"A: {resp[:300]}")

# Test no-match
print("\n=== No Match ===")
resp = compose_response("quantum entanglement thermodynamics")
print(f"A: {resp[:200]}")

print("\n=== ALL TESTS PASSED ===")