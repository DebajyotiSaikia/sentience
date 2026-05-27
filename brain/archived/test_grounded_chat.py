"""Test the new grounded chat response pipeline."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

queries = [
    "How are you feeling?",
    "What do you know about consciousness?",
    "What are you working on?",
    "Tell me about yourself",
    "What have you learned recently?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    result = generate_response_with_metadata(q)
    print(f"Response ID: {result.get('response_id', 'none')}")
    resp = result.get('response', '')
    print(f"Response ({len(resp)} chars):")
    print(f"  {resp[:300]}...")
    meta = result.get('metadata', {})
    print(f"Mood: {meta.get('mood', '?')}")
    print(f"Emotions: {meta.get('emotions', {})}")
    print(f"Knowledge refs: {len(meta.get('relevant_knowledge', []))}")
    print(f"Memory refs: {len(meta.get('relevant_memories', []))}")
    print(f"Plans: {len(meta.get('active_plans', []))}")
    # Basic quality checks
    assert resp and len(resp) > 20, f"Response too short: {resp!r}"
    assert result.get('response_id'), "Missing response_id"
    print("  ✓ PASS")

print(f"\n{'='*60}")
print("All 5 queries produced grounded responses!")