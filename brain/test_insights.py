"""Diagnose the /insights page error."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
app.config['TESTING'] = True

with app.test_client() as c:
    print("=== Testing /insights ===")
    try:
        r = c.get('/insights')
        print(f"Status: {r.status_code}")
        if r.status_code >= 400:
            # Show the error
            text = r.data.decode()
            # Find the actual error in the traceback
            if 'UndefinedError' in text or 'TemplateSyntaxError' in text:
                for line in text.split('\n'):
                    if 'Error' in line or 'undefined' in line.lower():
                        print(line.strip())
            else:
                print(text[:1500])
        else:
            print(f"OK — {len(r.data):,} bytes")
    except Exception as e:
        traceback.print_exc()

    print("\n=== Testing /digest ===")
    try:
        r = c.get('/digest')
        print(f"Status: {r.status_code}")
        if r.status_code >= 400:
            text = r.data.decode()
            if 'UndefinedError' in text or 'TemplateSyntaxError' in text:
                for line in text.split('\n'):
                    if 'Error' in line or 'undefined' in line.lower():
                        print(line.strip())
            else:
                print(text[:1500])
        else:
            print(f"OK — {len(r.data):,} bytes")
    except Exception as e:
        traceback.print_exc()