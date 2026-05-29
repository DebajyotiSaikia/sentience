"""Test the chat engine's actual response quality."""
import sys
sys.path.insert(0, '.')

from engine.chat_engine import respond

tests = [
    "How are you feeling right now?",
    "What are you working on?",
    "Tell me about yourself",
    "What do you know about consciousness?",
    "Hey there!",
    "What have you been dreaming about?",
]

for t in tests:
    print(f"\n{'='*60}")
    print(f"Q: {t}")
    print(f"{'='*60}")
    try:
        r = respond(t)
        print(f"A: {r[:500]}")
        print(f"   [length: {len(r)} chars]")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")