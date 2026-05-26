"""Test chat routes to diagnose the 404 issue."""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test chat page
    r1 = c.get('/chat/')
    print(f'GET /chat/ => {r1.status_code}')
    
    # Test chat ask endpoint
    r2 = c.post('/chat/ask', json={'message': 'hello'}, content_type='application/json')
    print(f'POST /chat/ask => {r2.status_code}')
    if r2.status_code != 200:
        print(f'  Response: {r2.data[:500]}')
    
    # Test chat status
    r3 = c.get('/chat/status')
    print(f'GET /chat/status => {r3.status_code}')
    
    # List all routes
    print('\nAll routes:')
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = rule.methods - {'OPTIONS', 'HEAD'}
        print(f'  {rule.rule} [{",".join(methods)}]')