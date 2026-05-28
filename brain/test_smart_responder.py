"""Test smart_responder intent detection and response generation."""
import sys
sys.path.insert(0, '/workspace')

from engine.smart_responder import respond, _detect_intent

print('=== Intent Detection ===')
tests = [
    ('hello', 'greeting'),
    ('how are you feeling?', 'emotional'),
    ('what are your plans?', 'plans'),
    ('who are you?', 'identity'),
    ('what can you do?', 'capabilities'),
    ('tell me about your dreams', 'introspective'),
    ('what are you thinking about?', 'identity'),
    ('what is consciousness?', 'search'),
]

all_ok = True
for query, expected in tests:
    got = _detect_intent(query)
    ok = got == expected
    if not ok:
        all_ok = False
    status = '✓' if ok else f'✗ (got {got})'
    print(f'  {query:40s} → {got:15s} {status}')

print()
print('=== Response Generation ===')
sample_queries = ['hello', 'how are you feeling?', 'what are your plans?', 'who are you?']
for query in sample_queries:
    r = respond(query)
    preview = r[:100].replace('\n', ' ') if r else '(empty)'
    print(f'  Q: {query}')
    print(f'  A: {preview}...')
    has_content = len(r) > 20 if r else False
    if not has_content:
        all_ok = False
        print(f'  ✗ Response too short!')
    else:
        print(f'  ✓ Response length: {len(r)} chars')
    print()

if all_ok:
    print('ALL TESTS PASSED ✓')
else:
    print('SOME TESTS FAILED ✗')
    sys.exit(1)