"""Quick smoke test for improved chat engine responses."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.chat_engine import generate_response

tests = [
    'hello',
    'how do you feel?',
    'what are you working on?',
    'what do you know about consciousness?',
    'tell me about yourself',
    'what are you thinking about?',
    'what can you do?',
    'tell me about your dreams',
]

for msg in tests:
    resp = generate_response(msg)
    preview = resp[:120].replace('\n', ' | ')
    print(f'[{msg}]')
    print(f'  → {preview}...')
    print()