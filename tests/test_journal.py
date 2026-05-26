"""Quick test: can the Flask app serve the journal page?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test journal route
r = client.get('/journal')
print(f"Journal status: {r.status_code}")
print(f"Journal size: {len(r.data)} bytes")

# Test a few other key routes
for route in ['/', '/chat', '/explore', '/help', '/teach']:
    r2 = client.get(route)
    print(f"{route:20s} -> {r2.status_code}")