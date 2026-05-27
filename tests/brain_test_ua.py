"""Quick test: does the knowledge explorer actually work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge page
r = client.get('/knowledge')
print(f'/knowledge: {r.status_code}, len={len(r.data)}')

# Test home page
r = client.get('/')
print(f'/: {r.status_code}, location={r.headers.get("Location", "none")}')

# Test chat page
r = client.get('/chat')
print(f'/chat: {r.status_code}, len={len(r.data)}')

# Test knowledge search API
r = client.get('/knowledge/search?q=consciousness')
print(f'/knowledge/search?q=consciousness: {r.status_code}')
if r.status_code == 200:
    data = r.get_json()
    print(f'  Results: {len(data.get("results", []))} facts found')

# Check what templates exist
templates = sorted(os.listdir('web/templates'))
print(f'Templates: {templates}')

# Check what routes exist
with app.app_context():
    rules = sorted([r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')])
    print(f'Routes ({len(rules)}):')
    for rule in rules:
        print(f'  {rule}')