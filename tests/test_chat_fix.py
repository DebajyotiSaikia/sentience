import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test the chat ask endpoint
    r = c.post('/chat/ask', json={'message': 'hello'})
    print(f'POST /chat/ask: {r.status_code}')
    print(f'Response: {r.get_data(as_text=True)[:500]}')
    
    # Also check starters
    r2 = c.get('/chat/starters')
    print(f'GET /chat/starters: {r2.status_code}')
    
    # Check status
    r3 = c.get('/chat/status')
    print(f'GET /chat/status: {r3.status_code}')
    
    # List all routes
    print('\n--- All chat routes ---')
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'chat' in rule.rule:
            print(f'  {rule.rule} [{", ".join(rule.methods - {"OPTIONS", "HEAD"})}]')