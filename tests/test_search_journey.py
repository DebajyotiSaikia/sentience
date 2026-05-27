"""Test the real user journey: searching knowledge through the web UI."""
import sys, json
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
c = app.test_client()

# Test endpoints the knowledge explorer JS would call
endpoints = [
    '/api/knowledge/search?q=consciousness',
    '/api/knowledge/search?q=emotion',
    '/api/knowledge',
    '/api/knowledge/facts',
    '/knowledge',
]

print("=== Knowledge Search Journey ===\n")
for ep in endpoints:
    r = c.get(ep)
    status = r.status_code
    size = len(r.data)
    label = "OK" if status == 200 else "FAIL"
    print(f"[{label}] {ep}: {status} ({size} bytes)")
    
    if status == 200 and r.content_type and 'json' in r.content_type:
        try:
            d = json.loads(r.data)
            if isinstance(d, dict):
                print(f"      keys: {list(d.keys())[:6]}")
                if 'results' in d:
                    print(f"      results: {len(d['results'])} items")
                if 'facts' in d:
                    print(f"      facts: {len(d['facts'])} items")
            elif isinstance(d, list):
                print(f"      items: {len(d)}")
        except:
            pass
    elif status != 200:
        print(f"      body: {r.data.decode()[:150]}")
    print()

# Now test: does the knowledge explorer page contain working search JS?
r = c.get('/knowledge')
html = r.data.decode()
has_search_input = 'input' in html and 'search' in html.lower()
has_fetch = 'fetch(' in html or 'XMLHttpRequest' in html
has_api_call = '/api/knowledge' in html
print(f"Knowledge Explorer UI checks:")
print(f"  Has search input: {has_search_input}")
print(f"  Has fetch/XHR:    {has_fetch}")  
print(f"  Calls /api/:      {has_api_call}")

# Check what URL the JS actually hits
import re
fetch_urls = re.findall(r'fetch\([\'"]([^\'"]+)[\'"]', html)
if fetch_urls:
    print(f"  Fetch URLs found: {fetch_urls}")
else:
    # Maybe it builds the URL dynamically
    api_refs = re.findall(r'/api/knowledge[^\'")\s]*', html)
    print(f"  API refs found:   {api_refs}")