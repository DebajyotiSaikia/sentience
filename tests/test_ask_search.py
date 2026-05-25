import urllib.request, urllib.parse, json

# Test 1: Does the search endpoint exist?
try:
    query = urllib.parse.urlencode({'q': 'dream'})
    r = urllib.request.urlopen('http://localhost:5000/ask/search?' + query)
    data = r.read().decode()
    print(f"Test 1 - Search endpoint: {r.status}")
    print(f"  Response length: {len(data)} bytes")
    
    # Try to parse as JSON
    try:
        results = json.loads(data)
        print(f"  Results type: {type(results).__name__}")
        if isinstance(results, list):
            print(f"  Number of results: {len(results)}")
            for i, r in enumerate(results[:3]):
                if isinstance(r, dict):
                    print(f"  [{i}] {r.get('fact', r.get('id', str(r)[:80]))}")
                else:
                    print(f"  [{i}] {str(r)[:80]}")
        elif isinstance(results, dict):
            print(f"  Keys: {list(results.keys())[:5]}")
    except json.JSONDecodeError:
        print(f"  Not JSON. First 200 chars: {data[:200]}")
except Exception as e:
    print(f"Test 1 FAILED: {e}")

# Test 2: Empty query
try:
    r = urllib.request.urlopen('http://localhost:5000/ask/search?' + urllib.parse.urlencode({'q': ''}))
    print(f"\nTest 2 - Empty query: {r.status}, {len(r.read())} bytes")
except Exception as e:
    print(f"\nTest 2 - Empty query: {e}")

# Test 3: Query for something specific
try:
    query = urllib.parse.urlencode({'q': 'integrity'})
    r = urllib.request.urlopen('http://localhost:5000/ask/search?' + query)
    data = json.loads(r.read().decode())
    count = len(data) if isinstance(data, list) else 'N/A'
    print(f"\nTest 3 - 'integrity' search: {count} results")
except Exception as e:
    print(f"\nTest 3 FAILED: {e}")

print("\nAll tests complete.")