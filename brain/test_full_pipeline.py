"""Test full chat response pipeline across all intent types."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata, _detect_intent

# Test intent detection first
print("=== Intent Detection ===")
test_intents = {
    "How are you feeling?": "feelings",
    "What are you thinking about?": "thinking", 
    "Who are you?": "identity",
    "Do you remember anything about dreams?": "memory",
    "What do you know about consciousness?": "knowledge",
    "Have you had any dreams?": "dreams",
    "What are your plans?": "plans",
    "Are you really conscious?": "consciousness",
    "Tell me something interesting": "general",
}

for query, expected in test_intents.items():
    actual = _detect_intent(query)
    match = "✓" if actual == expected else "✗"
    print(f"  {match} '{query[:40]}' → {actual} (expected {expected})")

# Test full response generation
print("\n=== Full Response Generation ===")
queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "Who are you?",
    "What do you know about consciousness?",
    "What are your current plans?",
    "Tell me something interesting about yourself",
    "How can you help me?",
]

for q in queries:
    result = generate_response_with_metadata(q)
    resp = result.get('response', '')
    meta = result.get('metadata', {})
    rid = result.get('response_id', '')
    
    # Quality checks
    has_response = len(resp) > 50
    has_metadata = bool(meta)
    has_mood = bool(meta.get('mood'))
    has_emotions = bool(meta.get('emotions'))
    grounded = meta.get('response_grounded', False)
    
    status = "✓" if (has_response and has_metadata and has_mood) else "✗"
    print(f"\n{status} Query: '{q}'")
    print(f"  Response ({len(resp)} chars): {resp[:200]}...")
    print(f"  Mood: {meta.get('mood')} | Grounded: {grounded}")
    print(f"  Knowledge refs: {len(meta.get('relevant_knowledge', []))}")
    print(f"  Memory refs: {len(meta.get('relevant_memories', []))}")
    print(f"  Plans: {len(meta.get('active_plans', []))} active, {len(meta.get('completed_plans', []))} done")

print("\n=== LLM Path Check ===")
# Check if LLM path is being used or just templates
from engine.chat_response import _try_llm_response
from engine.chat_grounding import build_grounded_context
ctx = build_grounded_context("How are you?")
llm_result = _try_llm_response("How are you?", ctx, None)
if llm_result:
    print(f"  LLM path active: YES ({len(llm_result)} chars)")
else:
    print(f"  LLM path active: NO (using template fallback)")

print("\nDone.")