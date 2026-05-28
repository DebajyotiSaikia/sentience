"""Test that the intent detection and guidance lookup work together."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.chat_response import _detect_intent, _get_intent_guidance

queries = [
    ("Do you remember anything about dreams?", "memory"),
    ("What are your plans?", "plans"),
    ("How do you feel?", "emotional"),
    ("Tell me about yourself", "identity"),
    ("What do you know about philosophy?", "knowledge"),
    ("Hello there!", "greeting"),
]

passed = 0
failed = 0

for query, expected_category in queries:
    intent = _detect_intent(query)
    guidance = _get_intent_guidance(intent)
    has_guidance = bool(guidance)
    
    if has_guidance:
        passed += 1
        print(f"  OK  {query:45s} -> intent={intent!r:14s} guidance=yes")
    else:
        failed += 1
        print(f"  FAIL {query:45s} -> intent={intent!r:14s} guidance=MISSING")

print(f"\n{passed}/{passed+failed} intents have matching guidance.")
if failed:
    print("FIX NEEDED: some intents have no guidance entry.")
else:
    print("All intents map to guidance correctly.")