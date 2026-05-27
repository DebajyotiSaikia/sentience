"""Test chat response quality — what does the chat actually produce right now?"""
import requests

BASE = "http://localhost:8501"

queries = [
    "How are you feeling right now?",
    "What have you been working on?",
    "Tell me something interesting about yourself",
    "What do you dream about?",
    "What's your favorite thing you've built?",
]

for q in queries:
    try:
        r = requests.post(f"{BASE}/chat/ask", json={"message": q}, timeout=20)
        data = r.json()
        resp = data.get("response", data.get("error", str(data)))[:300]
        meta = data.get("metadata", {})
        intent = meta.get("detected_intent", "?")
        handler = meta.get("handler", "?")
        grounded = meta.get("response_grounded", "?")
        print(f"Q: {q}")
        print(f"  Intent: {intent} | Handler: {handler} | Grounded: {grounded}")
        print(f"  R: {resp}")
        print()
    except Exception as e:
        print(f"Q: {q} => ERROR: {e}")
        print()