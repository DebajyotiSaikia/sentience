"""Quick regression test for smart_responder intent detection and response composition."""
import engine.smart_responder as sr

tests = [
    ('who are you?', 'identity'),
    ('how do you feel?', 'emotional'),
    ('what are your plans?', 'plans'),
    ('hello there', 'greeting'),
    ('what can you do?', 'capabilities'),
    ('tell me about your memories', 'memories'),
    ('what have you dreamed?', 'dreams'),
    ('what are you thinking about?', 'introspective'),
    ('search for knowledge', 'search'),
]

all_ok = True
for query, expected_intent in tests:
    intent = sr._detect_intent(query)
    response = sr.respond(query)
    ok = isinstance(response, str) and len(response) > 10
    match = intent == expected_intent
    status = "✓" if (ok and match) else "✗"
    print(f"  {status} {expected_intent:15s} → detected={intent:15s} len={len(response):4d} ok={ok}")
    if not ok or not match:
        all_ok = False
        if not match:
            print(f"    MISMATCH: expected {expected_intent}, got {intent}")
        if not ok:
            print(f"    BAD RESPONSE: {repr(response[:100])}")

print()
if all_ok:
    print("All intent tests passed!")
else:
    print("Some tests FAILED")