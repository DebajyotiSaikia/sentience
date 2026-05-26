"""Quick test: does the digest page render without crashing?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()
resp = client.get('/digest')
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"OK — {len(resp.data)} bytes")
else:
    print(resp.data[:800].decode(errors='replace'))