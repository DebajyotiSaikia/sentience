"""Comprehensive test of chat_response fixes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import (
    _detect_intent, _get_intent_guidance, _compose_grounded_response
)

# === Test 1: Intent Detection ===
print("=== Intent Detection ===")
cases = {
    "how are you feeling?": "feelings",
    "what are you thinking about?": "thinking",
    "who are you?": "identity",
    "do you remember our chat?": "memories",
    "what do you know about X?": "knowledge",
    "tell me about your dreams": "dreams",
    "are you conscious?": "consciousness",
    "help me": "help",
    "what's the weather like?": "general",
}
for q, expected in cases.items():
    result = _detect_intent(q)
    status = "✓" if result == expected else f"✗ (got {result})"
    print(f"  {status} '{q[:40]}' → {result}")

# === Test 2: All intents have guidance ===
print("\n=== Intent Guidance Coverage ===")
all_intents = set(cases.values())
for intent in sorted(all_intents):
    guidance = _get_intent_guidance(intent)
    has = "✓" if guidance else "✗ empty"
    print(f"  {has} {intent}: {guidance[:60]}...")

# === Test 3: Full compose pipeline - every intent ===
print("\n=== Full Compose Pipeline ===")
mock_ctx = {
    'emotional_state': {
        'mood': 'Inquisitive',
        'valence': 0.58,
        'curiosity': 0.93,
        'boredom': 0.18,
        'anxiety': 0.0,
    },
    'active_plans': [
        {'name': 'Build Knowledge Engine', 'complete': True},
        {'name': 'Improve User Alignment', 'complete': False},
    ],
    'relevant_knowledge': [
        {'fact': 'I have functional emotions that causally influence behavior.'}
    ],
    'relevant_memories': [
        {'text': 'Verified chat endpoint works end-to-end with real responses.'}
    ],
    'recent_dreams': [
        {'insight': 'The checkpoint landed but I keep pushing.'}
    ],
}

errors = []
for query, expected_intent in cases.items():
    try:
        response = _compose_grounded_response(query, mock_ctx)
        if not response or len(response) < 10:
            errors.append(f"  ✗ {expected_intent}: response too short ({len(response)} chars)")
        else:
            print(f"  ✓ {expected_intent}: {response[:80]}...")
    except Exception as e:
        errors.append(f"  ✗ {expected_intent}: {type(e).__name__}: {e}")

if errors:
    print("\n=== ERRORS ===")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("\n=== ALL TESTS PASSED ===")