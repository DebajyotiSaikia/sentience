import sys
sys.path.insert(0, '/workspace')
from engine.chat_engine import classify_intent

queries = [
    'Do you remember anything surprising?',
    'What do you remember?',
    'Tell me a memory',
    'What surprised you recently?',
    'Hello!',
    'How do you feel?',
    'What are your plans?',
    'Who are you?',
    'What do you know about consciousness?',
    'What are you thinking about?',
    'Tell me about your dreams',
]
for q in queries:
    intent = classify_intent(q)
    print(f'{intent:20s} <- {q}')