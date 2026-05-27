import sys
sys.path.insert(0, '/workspace')

from engine.helpfulness import analyze_user_need, _INTENT_SIGNALS
import re

# Trace the scoring for "What are your plans?"
msg = "What are your plans?"
ml = msg.lower().strip()
tokens = set(re.findall(r'[a-z]+', ml))
print(f"Message: {msg}")
print(f"Tokens: {tokens}")
print()

for intent, signals in _INTENT_SIGNALS.items():
    score = 0
    hits = []
    for signal in signals:
        signal_tokens = set(signal.split())
        if signal_tokens.issubset(tokens):
            score += len(signal_tokens)
            hits.append(signal)
    if hits:
        print(f"  {intent}: score={score}, hits={hits}")

print()

# Now test all cases
tests = [
    ("What are your plans?", "planning_query"),
    ("How are you feeling?", "internal_state"),
    ("Do you remember our last conversation?", "memory_query"),
    ("What is consciousness?", "knowledge_query"),
    ("Tell me a joke", "general_conversation"),
]

ok = True
for msg, expected in tests:
    need = analyze_user_need(msg)
    status = "✓" if need.intent == expected else "✗"
    if need.intent != expected:
        ok = False
    print(f"{status} '{msg}' → {need.intent} (expected {expected})")

if not ok:
    print("\nSome classifications failed!")
    sys.exit(1)
else:
    print("\nAll classifications correct!")