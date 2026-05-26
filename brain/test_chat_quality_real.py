"""Test what a real user would experience chatting with me.
One run, clear results, then fix what's broken."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test cases a real user would try
tests = [
    ("What do you know about consciousness?", "knowledge query"),
    ("How are you feeling?", "emotional state"),
    ("Who are you?", "identity"),
    ("What have you learned recently?", "memory recall"),
    ("Tell me something interesting", "engagement"),
    ("What can you do?", "capabilities"),
]

print("=" * 60)
print("CHAT QUALITY TEST — What does a user actually experience?")
print("=" * 60)

for msg, category in tests:
    resp = client.post('/api/chat', 
                       json={'message': msg},
                       content_type='application/json')
    data = resp.get_json() or {}
    
    response_text = data.get('response', data.get('message', str(data)))
    # Truncate for readability
    if len(response_text) > 300:
        response_text = response_text[:300] + "..."
    
    quality = "GOOD" if len(response_text) > 50 else "THIN"
    if 'error' in str(data).lower():
        quality = "ERROR"
    
    print(f"\n[{category.upper()}] '{msg}'")
    print(f"  Status: {resp.status_code} | Quality: {quality} | Length: {len(response_text)}")
    print(f"  Response: {response_text}")

print("\n" + "=" * 60)