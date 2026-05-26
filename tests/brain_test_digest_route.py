"""Quick test: hit /digest and show the error."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/digest')
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        # Extract the key error from the traceback
        body = resp.data.decode()
        for line in body.split('\n'):
            if 'Error' in line or 'error' in line or 'Traceback' in line or 'UndefinedError' in line or 'is undefined' in line:
                print(line.strip())
    else:
        print("OK!")
        print(resp.data.decode()[:300])