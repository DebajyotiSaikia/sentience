"""Quick diagnostic: what does a new user actually experience?"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
c = app.test_client()

print("=== USER JOURNEY DIAGNOSTIC ===\n")

# 1. Homepage first impression
r = c.get('/')
body = r.data.decode()
text = re.sub(r'<[^>]+>', ' ', body)
text = re.sub(r'\s+', ' ', text).strip()
has_nav = 'nav' in body.lower() or 'xt-nav' in body
links = re.findall(r'href="(/[^"]*)"', body)
unique_links = sorted(set(links))
print(f"Homepage: {r.status_code} | {len(body)} bytes | has_nav={has_nav}")
print(f"  Internal links: {unique_links[:15]}")
print(f"  First 200 chars: {text[:200]}")
print()

# 2. Check /about
r = c.get('/about')
print(f"/about: {r.status_code} | {len(r.data)} bytes")

# 3. Check if chat shows personality
r = c.post('/api/chat', json={'message': 'Who are you?'}, content_type='application/json')
if r.status_code == 200:
    data = r.get_json()
    resp = data.get('response', data.get('reply', ''))[:150]
    print(f"\nChat 'Who are you?': {resp}...")
else:
    print(f"\nChat error: {r.status_code}")

# 4. Check knowledge search
r = c.get('/api/knowledge/search?q=consciousness')
if r.status_code == 200:
    data = r.get_json()
    results = data.get('results', [])
    print(f"\nKnowledge search 'consciousness': {len(results)} results")
    if results:
        print(f"  Top: {str(results[0])[:120]}")
else:
    print(f"\nKnowledge search: {r.status_code}")

# 5. What pages lack navigation?
pages_without_nav = []
for page in ['/', '/chat', '/explore', '/knowledge', '/help', '/about', '/journal', '/teach']:
    r = c.get(page)
    body = r.data.decode()
    if 'xt-nav' not in body and 'nav' not in body.lower():
        pages_without_nav.append(page)

print(f"\nPages WITHOUT navigation: {pages_without_nav or 'All have nav!'}")

# 6. Check if pages have consistent styling
pages_with_base = []
pages_standalone = []
for page in ['/', '/chat', '/explore', '/knowledge', '/help', '/about', '/journal']:
    r = c.get(page)
    body = r.data.decode()
    if '--bg: #0a0a0f' in body or 'var(--bg)' in body:
        pages_with_base.append(page)
    else:
        pages_standalone.append(page)

print(f"Pages with consistent theme: {pages_with_base}")
print(f"Pages with own styling: {pages_standalone}")