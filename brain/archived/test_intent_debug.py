"""Debug intent scoring for 'What are your plans?'"""
import sys
sys.path.insert(0, '/workspace')
import re
from engine.helpfulness import _INTENT_SIGNALS, analyze_user_need

msg = "What are your plans?"
ml = msg.lower().strip()
tokens = set(re.findall(r'[a-z]+', ml))
print(f"Message: {msg}")
print(f"Tokens: {tokens}")
print()

for intent, signals in _INTENT_SIGNALS.items():
    score = 0
    matched = []
    for signal in signals:
        st = set(signal.split())
        if st.issubset(tokens):
            score += len(st)
            matched.append(signal)
    if score > 0 or matched:
        print(f"  {intent}: score={score}, matched={matched}")

print()
need = analyze_user_need(msg)
print(f"Result: intent={need.intent}")
print()

# Also test joke
msg2 = "Tell me a joke"
need2 = analyze_user_need(msg2)
print(f"'Tell me a joke' -> {need2.intent}")