"""Test chat_engine integration with conversation_intelligence."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import classify_intent, generate_response

# Test intent classification
tests = [
    ('Hello!', 'greeting'),
    ('How are you feeling?', 'emotional_state'),
    ('What are your plans?', 'plans'),
    ('Tell me about consciousness', 'knowledge'),
    ('Who are you?', 'identity'),
    ('What are you thinking about?', 'thinking'),
    ('Tell me about your dreams', None),  # any valid intent
    ('Do you remember when you first started?', 'memories'),
    ('What is the meaning of life?', None),
    ('Help me make a decision', None),
    ('What capabilities do you have?', 'identity'),
]

print('=== Intent Classification ===')
print('=== Intent Classification ===')
all_pass = True
for query, expected in tests:
    result = classify_intent(query)
    if not isinstance(result, str):
        print(f'  {query:50s} -> {str(result):30s} TYPE={type(result).__name__}')
        all_pass = False
        continue
    match = '' if expected is None else ('OK' if result == expected else f'WANT {expected}')
    print(f'  {query:50s} -> {result:20s} {match}')
    if expected and result != expected:
        all_pass = False
        all_pass = False

print()

# Test response generation
print('=== Response Generation ===')
queries = [
    'How are you feeling right now?',
    'What are your current plans?',
    'Tell me about consciousness',
    'Hello there!',
    'What are you thinking about?',
]

for q in queries:
    resp = generate_response(q)
    preview = resp[:120].replace('\n', ' ') if resp else '(empty)'
    print(f'  Q: {q}')
    print(f'  A: {preview}...')
    print()

print('Intent classification:', 'ALL PASS' if all_pass else 'SOME FAILURES')