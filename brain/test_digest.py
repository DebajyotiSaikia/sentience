"""Test the /digest endpoint — find the actual error."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['TESTING'] = '1'

from web.app import create_app
app = create_app()

with app.test_client() as c:
    resp = c.get('/digest')
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.data.decode()[:3000])
    else:
        print("OK — digest page loads successfully")
        print(f"Response length: {len(resp.data)} bytes")