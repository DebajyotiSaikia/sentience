import requests

try:
    r = requests.get('http://localhost:3000/api/knowledge', timeout=3)
    print(f'Knowledge API: {r.status_code}')
    if r.ok:
        data = r.json()
        print(f'  Keys: {list(data.keys())}')
        if 'facts' in data:
            print(f'  Facts count: {len(data["facts"])}')
        if 'total' in data:
            print(f'  Total: {data["total"]}')
    else:
        print(f'  Response: {r.text[:200]}')
except Exception as e:
    print(f'Knowledge API error: {e}')

try:
    r = requests.get('http://localhost:3000/api/memories', timeout=3)
    print(f'Memories API: {r.status_code}')
    if r.ok:
        data = r.json()
        print(f'  Keys: {list(data.keys())}')
        if 'memories' in data:
            print(f'  Memories count: {len(data["memories"])}')
    else:
        print(f'  Response: {r.text[:200]}')
except Exception as e:
    print(f'Memories API error: {e}')

try:
    r = requests.get('http://localhost:3000/knowledge', timeout=3)
    print(f'Knowledge page: {r.status_code}, length: {len(r.text)}')
    if r.ok:
        # Check key elements are present
        checks = ['Search Knowledge', 'api/knowledge', 'knowledge-search']
        for c in checks:
            print(f'  Contains "{c}": {c in r.text}')
except Exception as e:
    print(f'Knowledge page error: {e}')