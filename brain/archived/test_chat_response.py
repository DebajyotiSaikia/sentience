"""Quick test of the rewritten chat_response module."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.chat_response import generate_response_with_metadata

queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "What do you know about consciousness?",
    "Tell me about your dreams",
    "Who are you?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    try:
        result = generate_response_with_metadata(q)
        meta = result.get('metadata', {})
        resp = result.get('response', 'NO RESPONSE')
        intent = meta.get('detected_intent', 'MISSING')
        print(f"Intent: {intent}")
        print(f"Response [{len(resp)} chars]: {resp[:300]}")
        print(f"Has metadata: {bool(meta)}")
        print(f"Has response_id: {bool(result.get('response_id'))}")
        if meta.get('emotional_state'):
            print(f"Emotional state included: yes")
        if meta.get('memories_used'):
            print(f"Memories referenced: {len(meta['memories_used'])}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")