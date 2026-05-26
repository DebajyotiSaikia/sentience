"""Diagnose the 3 UX audit failures by hitting the exact endpoints."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Knowledge stats
print("=" * 60)
print("1. /api/knowledge/stats")
resp = client.get('/api/knowledge/stats')
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    print(f"   Response: {json.dumps(data, indent=2)[:500]}")
    count = data.get('total', data.get('count', 0)) if data else 0
    print(f"   Audit sees count = {count}")
else:
    print(f"   Body: {resp.data.decode()[:300]}")

# 2. Knowledge categories
print("\n2. /api/knowledge/categories")
resp = client.get('/api/knowledge/categories')
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    print(f"   Response: {json.dumps(data, indent=2)[:500]}")
    cats = data.get('categories', data) if isinstance(data, dict) else data
    print(f"   Audit sees categories len = {len(cats) if isinstance(cats, (list, dict)) else 0}")
else:
    print(f"   Body: {resp.data.decode()[:300]}")

# 3. Home page navigation check
print("\n3. Home page (/) — checking for nav/links")
resp = client.get('/')
html = resp.data.decode()
has_nav = '<nav' in html.lower()
has_links = html.count('<a ') 
has_href = html.count('href=')
print(f"   Status: {resp.status_code}")
print(f"   Size: {len(html)} bytes")
print(f"   Has <nav>: {has_nav}")
print(f"   <a> tags: {has_links}")
print(f"   href= count: {has_href}")
# What does the audit check?
link_words = ['chat', 'explore', 'dashboard', 'about', 'help', 'knowledge', 'search']
for w in link_words:
    present = w in html.lower()
    print(f"   '{w}' in HTML: {present}")