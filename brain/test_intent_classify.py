"""Test classify_intent to understand current behavior."""
import sys
sys.path.insert(0, '.')
from engine.chat_engine import classify_intent

tests = [
    'How are you feeling?',
    'What is on your mind?',
    'What are you working on?',
    'Tell me about yourself',
    'What do you know about consciousness?',
    'What do you remember?',
    'Hi there!',
    'What are your plans?',
    'Are you conscious?',
    'What changed recently?',
    'How is your mood?',
    'What drives you?',
    'What are you thinking about?',
    'Do you dream?',
    'What have you learned?',
    'How do you work?',
    'Can you help me?',
    'Write me a poem',
    'Hello',
    'What is 2+2?',
    'Tell me a joke',
    'What do you value?',
]
print("=== Intent Classification Results ===")
for t in tests:
    intent = classify_intent(t)
    print(f"  {intent:15s} | {t}")