"""Diagnose knowledge search - what works, what's 404?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge page
r1 = client.get('/knowledge')
print(f'GET /knowledge: {r1.status_code}')

# Test knowledge search via query param
r2 = client.get('/knowledge?q=consciousness')
print(f'GET /knowledge?q=consciousness: {r2.status_code}')
data2 = r2.data.decode()
has_results = 'consciousness' in data2.lower()
print(f'  Contains "consciousness": {has_results}')

# Test API knowledge search
r3 = client.get('/api/knowledge/search?q=consciousness')
print(f'GET /api/knowledge/search: {r3.status_code}')
if r3.status_code == 200:
    print(f'  Response: {r3.data.decode()[:200]}')

# Test /knowledge/search directly
r4 = client.get('/knowledge/search?q=consciousness')
print(f'GET /knowledge/search: {r4.status_code}')

# List all knowledge-related routes
with app.test_request_context():
    rules = sorted([r.rule for r in app.url_map.iter_rules() if 'knowledge' in r.rule.lower()])
    print(f'\nKnowledge routes: {rules}')

# Check what the template JS actually calls
template_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'templates', 'knowledge_explorer.html')
if os.path.exists(template_path):
    with open(template_path) as f:
        content = f.read()
    # Find fetch/ajax calls
    import re
    fetches = re.findall(r'fetch\([\'"]([^\'"]+)', content)
    xhrs = re.findall(r'\.open\([\'"][^"\']+[\'"],\s*[\'"]([^\'"]+)', content)
    form_actions = re.findall(r'action=[\'"]([^\'"]+)', content)
    print(f'\nTemplate fetch() calls: {fetches}')
    print(f'Template XHR calls: {xhrs}')
    print(f'Template form actions: {form_actions}')
    
    # Check for any URL patterns in script tags
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for i, script in enumerate(scripts):
        urls = re.findall(r'[\'"](/[a-z/]+)[\'"]', script)
        if urls:
            print(f'Script {i} URL references: {urls}')