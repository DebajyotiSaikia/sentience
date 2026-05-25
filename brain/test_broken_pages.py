"""Diagnose broken pages with full tracebacks."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

broken_pages = ['/digest', '/ask']

for p in broken_pages:
    print(f"\n{'='*60}")
    print(f"Testing: {p}")
    print('='*60)
    try:
        with app.test_client() as client:
            resp = client.get(p)
            print(f"Status: {resp.status_code}")
            if resp.status_code >= 400:
                # Show error body
                body = resp.data.decode('utf-8', errors='replace')
                # Extract just the traceback part
                if 'Traceback' in body:
                    start = body.index('Traceback')
                    print(body[start:start+2000])
                else:
                    print(body[:1000])
    except Exception as e:
        traceback.print_exc()