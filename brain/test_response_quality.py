"""Test actual response quality from engine/chat_engine.py"""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_engine import generate_response

queries = [
    "What are you feeling right now?",
    "What are you working on?",
    "Tell me something interesting",
    "Hello!",
    "How many knowledge nodes do you have?",
    "What do you remember from recently?",
    "Who are you?",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    resp = generate_response(q)
    if isinstance(resp, dict):
        text = resp.get('response', resp.get('text', str(resp)))
        intent = resp.get('intent', 'unknown')
        print(f"Intent: {intent}")
        print(f"A: {text[:500]}")
    else:
        print(f"A: {str(resp)[:500]}")
    print(f"Type: {type(resp).__name__}")