import requests

try:
    r1 = requests.get('http://localhost:5000/ask', timeout=3)
    print(f'/ask -> {r1.status_code}')

    r2 = requests.post('http://localhost:5000/ask/query',
                       json={'question': 'memory'}, timeout=3)
    print(f'/ask/query -> {r2.status_code}: {r2.text[:200]}')

    r3 = requests.get('http://localhost:5000/ask/random', timeout=3)
    print(f'/ask/random -> {r3.status_code}: {r3.text[:200]}')

except Exception as e:
    print(f'Error: {e}')