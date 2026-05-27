"""Test whether chat uses real knowledge for substantive questions."""
from web.app import create_app

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "What are your emotional states right now?",
    "What have you learned recently?",
    "Tell me about your knowledge graph",
]

for q in questions:
    r = client.post('/api/chat', json={'message': q})
    data = r.get_json()
    resp = data.get('response', '')[:200]
    print(f"\nQ: {q}")
    print(f"A: {resp}...")
    print(f"   (length: {len(data.get('response', ''))} chars)")