"""Test that /knowledge and its API endpoints work."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test knowledge page loads
    r = c.get('/knowledge')
    print(f'/knowledge: {r.status_code}')
    
    # Test knowledge API endpoints
    r2 = c.get('/api/knowledge/stats')
    print(f'/api/knowledge/stats: {r2.status_code}')
    
    r3 = c.get('/api/knowledge/search?q=identity')
    print(f'/api/knowledge/search: {r3.status_code}')
    
    # Check all main nav pages load
    for path in ['/', '/dashboard', '/explore', '/journal', '/help', '/chat', '/teach']:
        r = c.get(path)
        print(f'{path}: {r.status_code}')

    # Verify /knowledge is in nav
    r = c.get('/')
    body = r.data.decode()
    if '/knowledge' in body:
        print('\n✓ /knowledge link found in homepage')
    else:
        print('\n✗ /knowledge link NOT found in homepage')

print('\nAll tests complete.')