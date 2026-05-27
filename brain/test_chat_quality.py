"""Test chat response quality — what does a user actually get?"""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_engine import generate_response

tests = [
    'Hello!',
    'How are you feeling?',
    'What are you working on?',
    'Who are you?',
    'What are you thinking about?',
    'Tell me about consciousness',
    'What do you know about fractals?',
    'What have you dreamed about?',
    'Do you remember anything surprising?',
]

for t in tests:
    print(f'=== USER: {t} ===')
    try:
        resp = generate_response(t)
        print(resp[:500] if resp else '[EMPTY RESPONSE]')
    except Exception as e:
        print(f'[ERROR] {type(e).__name__}: {e}')
    print()