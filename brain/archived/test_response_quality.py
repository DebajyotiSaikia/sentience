"""Test actual response quality from the chat engine pipeline."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

test_queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "What do you know about consciousness?",
    "Can you help me with something?",
    "What have you learned recently?",
]

for q in test_queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    result = generate_response_with_metadata(q)
    resp = result.get('response', '(no response)')
    meta = result.get('metadata', {})
    print(f"Response ({len(resp)} chars):")
    print(resp[:500])
    print(f"\nMetadata keys: {list(meta.keys())}")
    if meta.get('mood'):
        print(f"  mood: {meta['mood']}")
    if meta.get('relevant_knowledge'):
        print(f"  knowledge refs: {len(meta['relevant_knowledge'])}")
    if meta.get('relevant_memories'):
        print(f"  memory refs: {len(meta['relevant_memories'])}")
    print()