import requests
try:
    r = requests.get('http://localhost:5000/knowledge-hub', timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Length: {len(r.text)}')
    if r.status_code != 200:
        print(r.text[:500])
    else:
        print('Knowledge hub is serving OK')
except Exception as e:
    print(f'Error: {e}')

# Check which knowledge routes exist
for path in ['/knowledge', '/knowledge-explorer', '/knowledge-hub', '/knowledge-search']:
    try:
        r = requests.get(f'http://localhost:5000{path}', timeout=3)
        print(f'{path} -> {r.status_code}')
    except Exception as e:
        print(f'{path} -> Error: {e}')