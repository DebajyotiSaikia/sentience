"""Test the API endpoints that portal.html depends on."""
import sys
sys.path.insert(0, '.')

from web.app import create_app

def test_portal_apis():
    app = create_app()
    client = app.test_client()
    
    endpoints = [
        ('GET', '/'),
        ('GET', '/api/state'),
        ('GET', '/api/memories'),
        ('POST', '/api/chat', {'message': 'Hello, who are you?'}),
    ]
    
    results = []
    for entry in endpoints:
        method = entry[0]
        path = entry[1]
        data = entry[2] if len(entry) > 2 else None
        
        try:
            if method == 'GET':
                resp = client.get(path)
            else:
                resp = client.post(path, json=data)
            
            status = resp.status_code
            size = len(resp.data)
            preview = resp.data[:200].decode('utf-8', errors='replace')
            ok = '✓' if status == 200 else '✗'
            results.append((ok, method, path, status, size))
            print(f"{ok} {method} {path} → {status} ({size} bytes)")
            if status != 200:
                print(f"  Response: {preview}")
        except Exception as e:
            results.append(('✗', method, path, 'ERROR', str(e)))
            print(f"✗ {method} {path} → ERROR: {e}")
    
    print(f"\n{'='*50}")
    passed = sum(1 for r in results if r[0] == '✓')
    print(f"Results: {passed}/{len(results)} endpoints working")
    
    if passed < len(results):
        print("\nBROKEN endpoints need fixing for user experience!")
        return False
    else:
        print("\nAll portal APIs working. Users can interact.")
        return True

if __name__ == '__main__':
    success = test_portal_apis()
    sys.exit(0 if success else 1)