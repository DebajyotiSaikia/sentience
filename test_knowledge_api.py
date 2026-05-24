import requests

base = 'http://localhost:8501'

# Test stats endpoint
print("=== Testing /api/knowledge/stats ===")
try:
    r = requests.get(f'{base}/api/knowledge/stats', timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:400]}')
except Exception as e:
    print(f'Failed: {e}')

# Test knowledge list endpoint
print("\n=== Testing /api/knowledge ===")
try:
    r = requests.get(f'{base}/api/knowledge', timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:400]}')
except Exception as e:
    print(f'Failed: {e}')

# Test query endpoint
print("\n=== Testing /api/knowledge/query ===")
try:
    r = requests.post(f'{base}/api/knowledge/query', json={'question': 'what do you know about yourself'}, timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:400]}')
except Exception as e:
    print(f'Failed: {e}')

# Test search
print("\n=== Testing /api/knowledge?search=dream ===")
try:
    r = requests.get(f'{base}/api/knowledge?search=dream', timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:400]}')
except Exception as e:
    print(f'Failed: {e}')