"""Debug the /search 500 error."""
import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = False

client = app.test_client()
resp = client.get('/search')
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Response body:\n{resp.data.decode('utf-8', errors='replace')[:2000]}")