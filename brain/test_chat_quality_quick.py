"""Quick test: does chat actually produce useful responses?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test page availability first
pages = ['/', '/chat', '/knowledge', '/help', '/about', '/explore', '/journal', '/teach']
print("=== PAGE STATUS ===")
for p in pages:
    try:
        r = client.get(p)
        print(f"  {p:20s} -> {r.status_code}  ({len(r.data):>6} bytes)")
    except Exception as e:
        print(f"  {p:20s} -> ERROR: {e}")

# Test chat responses
print("\n=== CHAT QUALITY ===")
questions = [
    'What do you know about consciousness?',
    'Who are you?',
    'What can you do?',
]
for q in questions:
    r = client.post('/api/chat', json={'message': q})
    data = r.get_json()
    reply = data.get('response', data.get('error', '???'))
    print(f"\nQ: {q}")
    print(f"A: {reply[:300]}")