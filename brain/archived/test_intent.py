"""Test classify_intent with internal-state queries."""
import sys; sys.path.insert(0, '/workspace')
from engine.conversation_intelligence import classify_intent

tests = [
    'How are you feeling?',
    'What are your plans?',
    'Tell me about consciousness',
    'What are you thinking about?',
    'Who are you?',
    'Hello!',
    'What do you remember?',
    'What do you know about dreams?',
    'Help me decide something',
]

for t in tests:
    intent, conf = classify_intent(t)
    print(f'{t:45s} -> {intent:20s} ({conf:.2f})')