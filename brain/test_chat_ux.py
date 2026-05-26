"""Test chat UX quality — what do users actually experience?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

queries = [
    "Who are you?",
    "What do you know?",
    "How are you feeling?",
    "What are your plans?",
    "Tell me about consciousness",
    "What is your knowledge graph?",
    "Help me understand what you can do",
    "nonsense_query_xyz_12345",
]

print("=== Chat UX Quality Test ===\n")
for q in queries:
    resp = client.post('/chat/ask', 
                       data=json.dumps({'message': q}),
                       content_type='application/json')
    status = resp.status_code
    data = resp.get_json() if resp.data else None
    
    if status != 200:
        print(f"Q: {q}")
        print(f"  STATUS: {status}")
        print(f"  ERROR: {data}")
        print()
        continue
    
    answer = data.get('response', '') if data else ''
    # Quality metrics
    length = len(answer)
    has_substance = length > 50
    is_error = 'error' in answer.lower() or 'couldn\'t' in answer.lower()
    
    quality = "GOOD" if has_substance and not is_error else "WEAK" if has_substance else "BAD"
    
    print(f"Q: {q}")
    print(f"  [{quality}] ({length} chars) {answer[:150]}...")
    print()

print("=== Navigation Test ===\n")
for page in ['/', '/chat', '/explore', '/knowledge', '/help']:
    r = client.get(page)
    has_nav = b'nav' in r.data.lower() or b'<a ' in r.data
    size = len(r.data)
    print(f"{page:15s} -> {r.status_code}  {size:>6} bytes  nav={'yes' if has_nav else 'NO'}")