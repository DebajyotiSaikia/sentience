import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get('/api/knowledge')
    print(f'Status: {r.status_code}')
    print(f'Data: {r.get_data(as_text=True)[:300]}')
    
    # Check registered blueprints
    print(f'\nRegistered blueprints: {list(app.blueprints.keys())}')
    print(f'\nKnowledge/API routes:')
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if 'knowledge' in rule.rule or 'api' in rule.rule:
            print(f'  {rule.rule} -> {rule.endpoint} [{",".join(rule.methods - {"OPTIONS","HEAD"})}]')