"""Quick diagnostic: what does a user actually experience?"""
from web.app import create_app

app = create_app()
client = app.test_client()

print("=== PAGE STATUS ===")
pages = ['/', '/chat', '/explore', '/knowledge', '/help', '/dashboard',
         '/insights', '/journal', '/briefing', '/story', '/collaborate',
         '/live', '/teach']
for p in pages:
    try:
        r = client.get(p)
        size = len(r.data)
        # Check if page has real content vs error
        has_nav = b'nav' in r.data.lower() or b'Nav' in r.data
        print(f'  {p:20s} {r.status_code}  {size:>6}b  nav={has_nav}')
    except Exception as e:
        print(f'  {p:20s} ERROR: {e}')

print("\n=== CHAT QUALITY ===")
queries = [
    'What do you know about consciousness?',
    'Tell me about yourself',
    'What can you help me with?',
    'Search knowledge: emotions',
    'Hello',
]
for q in queries:
    try:
        r = client.post('/api/chat', json={'message': q},
                       content_type='application/json')
        data = r.get_json()
        resp = data.get('response', data.get('error', 'NO RESPONSE'))
        # Truncate but show enough to judge quality
        preview = resp[:250].replace('\n', ' | ')
        print(f'  Q: {q}')
        print(f'  A: {preview}')
        print()
    except Exception as e:
        print(f'  Q: {q}')
        print(f'  ERROR: {e}')
        print()

print("=== KNOWLEDGE API ===")
try:
    r = client.get('/api/knowledge')
    data = r.get_json()
    print(f'  Status: {r.status_code}')
    print(f'  Facts: {data.get("total", "?")}')
    if 'facts' in data:
        for f in data['facts'][:3]:
            if isinstance(f, dict):
                print(f'    - {str(f.get("fact", f))[:100]}')
            else:
                print(f'    - {str(f)[:100]}')
except Exception as e:
    print(f'  ERROR: {e}')

print("\n=== SEARCH API ===")
try:
    r = client.get('/api/knowledge/search?q=consciousness')
    data = r.get_json()
    print(f'  Status: {r.status_code}')
    print(f'  Results: {len(data.get("results", []))}')
    for res in data.get('results', [])[:3]:
        if isinstance(res, dict):
            print(f'    - {str(res.get("fact", res))[:100]}')
        else:
            print(f'    - {str(res)[:100]}')
except Exception as e:
    print(f'  ERROR: {e}')