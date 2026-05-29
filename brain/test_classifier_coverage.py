"""Quick coverage test for intent classifier."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.response_intelligence import classify_intent

tests = [
    ('what lessons have you learned?', 'lessons'),
    ('what have you learned?', 'lessons'),
    ('how are you feeling?', 'emotion'),
    ('who are you?', 'identity'),
    ('what are your plans?', 'plans'),
    ('tell me about your dreams', 'dreams'),
    ('what do you remember?', 'memories'),
    ('what do you know?', 'knowledge'),
    ('hello', 'greeting'),
    ('can you write code?', 'capability'),
    ('how have you grown?', 'lessons'),
]

passed = 0
failed = 0
for query, expected in tests:
    r = classify_intent(query)
    status = '✓' if r.kind == expected else '✗'
    if r.kind != expected:
        failed += 1
        print(f'  {status} "{query}" → {r.kind} (expected {expected})')
    else:
        passed += 1
        print(f'  {status} "{query}" → {r.kind}')

print(f'\n{passed}/{passed+failed} passed')
if failed:
    print(f'{failed} FAILED')