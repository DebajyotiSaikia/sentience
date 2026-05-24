import traceback
from web.app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

client = app.test_client()

for route in ['/knowledge', '/explore']:
    print(f"\n{'='*60}")
    print(f"Testing {route}")
    print('='*60)
    try:
        resp = client.get(route)
        print(f"Status: {resp.status_code}")
        if resp.status_code >= 400:
            # Try to get error info from response
            data = resp.data.decode('utf-8')
            # Print last 500 chars if it's long
            if len(data) > 1000:
                print(f"Response (last 500 chars): ...{data[-500:]}")
            else:
                print(f"Response: {data}")
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()