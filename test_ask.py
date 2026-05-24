import requests

# Test the ask/query endpoint
try:
    r = requests.post('http://localhost:8501/ask/query', json={'question': 'curiosity'}, timeout=5)
    print(f'POST /ask/query status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'ask/query failed: {e}')

# Test the ask/random endpoint
try:
    r2 = requests.get('http://localhost:8501/ask/random', timeout=5)
    print(f'GET /ask/random status: {r2.status_code}')
    print(f'Response: {r2.text[:500]}')
except Exception as e:
    print(f'ask/random failed: {e}')

# Test the main ask page renders
try:
    r3 = requests.get('http://localhost:8501/ask/', timeout=5)
    print(f'GET /ask/ status: {r3.status_code}')
    print(f'Page length: {len(r3.text)} chars')
except Exception as e:
    print(f'ask page failed: {e}')

# Test knowledge page
try:
    r4 = requests.get('http://localhost:8501/knowledge/', timeout=5)
    print(f'GET /knowledge/ status: {r4.status_code}')
    print(f'Page length: {len(r4.text)} chars')
except Exception as e:
    print(f'knowledge page failed: {e}')