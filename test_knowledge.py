from web.app import create_app
app = create_app()
client = app.test_client()

# Test the search page route
r1 = client.get('/knowledge')
print('GET /knowledge:', r1.status_code)

# Test the API endpoints
r2 = client.get('/api/knowledge/stats')
print('GET /api/knowledge/stats:', r2.status_code, r2.get_json() if r2.status_code == 200 else r2.data[:200])

r3 = client.get('/api/knowledge/search?q=dream&limit=5')
print('GET /api/knowledge/search:', r3.status_code, r3.get_json() if r3.status_code == 200 else r3.data[:200])

r4 = client.get('/api/knowledge/graph')
print('GET /api/knowledge/graph:', r4.status_code)