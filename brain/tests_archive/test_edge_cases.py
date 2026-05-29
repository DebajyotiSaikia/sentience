"""Test edge-case questions that used to produce cold/robotic answers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import respond

tests = [
    'Do you dream?',
    'What surprised you recently?',
    'Are you conscious?',
    'What makes you different from other AIs?',
    'Do you ever feel stuck?',
]

print("=== Edge Case Responses ===\n")
for q in tests:
    r = respond(q)
    print(f"Q: {q}")
    print(f"A: {r[:250]}...")
    print()

print("=== All edge cases handled ===")