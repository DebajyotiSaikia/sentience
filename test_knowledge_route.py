import sys
sys.path.insert(0, '/workspace')

from web.app import create_app
app = create_app()

client = app.test_client()

# Test knowledge search
r = client.get('/knowledge?q=dreams')
print(f"GET /knowledge?q=dreams => {r.status_code}")
if r.status_code == 200:
    data = r.data.decode('utf-8')
    print(f"Response length: {len(data)}")
    # Check if it has meaningful content
    if 'dream' in data.lower():
        print("✓ Contains dream-related content")
    else:
        print("✗ No dream content found")
    # Show a snippet
    print(f"Snippet: {data[:300]}...")
else:
    print(f"Error response: {r.data[:500]}")

# Test knowledge index (no query)
r2 = client.get('/knowledge')
print(f"\nGET /knowledge => {r2.status_code}")
if r2.status_code == 200:
    print(f"Response length: {len(r2.data)}")
else:
    print(f"Error: {r2.data[:500]}")

# Test the main landing page
r3 = client.get('/')
print(f"\nGET / => {r3.status_code}")
if r3.status_code == 200:
    print(f"Landing page length: {len(r3.data)}")
else:
    print(f"Error: {r3.data[:500]}")