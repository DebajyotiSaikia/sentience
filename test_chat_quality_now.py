"""Quick quality check: does the chat reference real internal state?"""
import requests

questions = [
    "What are you working on right now?",
    "How do you feel?",
    "What have you learned recently?",
]

for q in questions:
    r = requests.post('http://localhost:8080/chat/ask', json={'message': q}, timeout=15)
    d = r.json()
    resp = d.get('response', 'NO RESPONSE')
    print(f"\nQ: {q}")
    print(f"A: {resp[:300]}")
    print(f"Length: {len(resp)}")