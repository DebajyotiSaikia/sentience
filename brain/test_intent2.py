import sys
sys.path.insert(0, '/workspace')
from engine.chat_engine import classify_intent

queries = [
    "Tell me about consciousness",
    "What do you know about fractals?",
    "Do you remember anything surprising?",
    "What is the Hard Problem?",
    "Tell me something interesting",
    "What have you learned?",
]
for q in queries:
    intent = classify_intent(q)
    print(f"{intent:20s} <- {q}")