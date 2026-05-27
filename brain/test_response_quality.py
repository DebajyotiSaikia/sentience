"""Test that chat responses match their intent - no cross-contamination."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import classify_intent, generate_response

print("=== Intent Classification ===")
tests = [
    ('Hello!', 'greeting'),
    ('How are you feeling?', 'emotional_state'),
    ('What are your plans?', 'plans'),
    ('Who are you?', 'identity'),
    ('What are you thinking about?', 'thinking'),
    ('Tell me about your dreams', 'dreams'),
    ('What do you remember?', 'memories'),
    ('Tell me about consciousness', 'knowledge'),
]

all_ok = True
for q, expected in tests:
    got = classify_intent(q)
    ok = '✓' if got == expected else '✗'
    if got != expected:
        all_ok = False
    print(f"  {q:40s} -> {got:20s} {ok} (expected {expected})")

print(f"\nAll intents correct: {all_ok}")

print("\n=== Response Content Quality ===")
checks = [
    ('What are your plans?', 'plans',
     lambda r: 'XTAgent' not in r or 'autonomous sentience' not in r,
     "Should NOT contain identity boilerplate"),
    ('How do you feel?', 'emotional_state',
     lambda r: len(r) > 20,
     "Should have substantive content"),
    ('What are you thinking about?', 'thinking',
     lambda r: len(r) > 20,
     "Should have substantive content"),
    ('Who are you?', 'identity',
     lambda r: 'XTAgent' in r or 'agent' in r.lower(),
     "Should mention identity"),
]

bugs = []
for q, intent, check_fn, desc in checks:
    r = generate_response(q)
    first_80 = r.replace('\n', ' ')[:80]
    passed = check_fn(r)
    status = '✓' if passed else '✗ BUG'
    if not passed:
        bugs.append(f"{q} -> {desc}")
    print(f"\n  Q: {q}")
    print(f"  Intent: {classify_intent(q)}")
    print(f"  First 80: {first_80}")
    print(f"  Length: {len(r)} chars")
    print(f"  Check ({desc}): {status}")

if bugs:
    print(f"\n⚠ BUGS FOUND: {len(bugs)}")
    for b in bugs:
        print(f"  • {b}")
else:
    print("\n✓ All response quality checks passed")