"""Quick diagnostic — find what the UX audit failures are so I can fix them."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
client = app.test_client()

# 1. Check home page for CTA links
resp = client.get('/')
content = resp.get_data(as_text=True)
content_lower = content.lower()

# Find all links
links = re.findall(r'href=["\']([^"\']*)["\']', content)
chat_links = [l for l in links if 'chat' in l.lower()]
print(f"HOME PAGE: {len(links)} total links, {len(chat_links)} chat links")
print(f"  Has 'chat' CTA: {bool(chat_links)}")

# Check for CTA-like elements
for pattern in ['start', 'talk', 'chat', 'try', 'begin', 'explore']:
    # Look for links with these words nearby
    found = bool(re.search(rf'<a[^>]*href[^>]*>[^<]*{pattern}[^<]*</a>', content_lower))
    print(f"  Link with '{pattern}': {found}")

# 2. Check /api/knowledge/stats
resp2 = client.get('/api/knowledge/stats')
print(f"\nKNOWLEDGE STATS: status={resp2.status_code}")
if resp2.status_code == 200:
    data = json.loads(resp2.get_data(as_text=True))
    print(f"  Keys: {list(data.keys())}")
    print(f"  total_facts: {data.get('total_facts', 'MISSING')}")

# 3. Check /explore page content richness
resp3 = client.get('/explore')
explore = resp3.get_data(as_text=True)
# Strip tags for text length
text_only = re.sub(r'<[^>]+>', ' ', explore)
text_only = re.sub(r'\s+', ' ', text_only).strip()
print(f"\nEXPLORE PAGE: status={resp3.status_code}, text length={len(text_only)}")
print(f"  Has facts content: {'fact' in explore.lower()}")

# 4. Check search functionality
resp4 = client.get('/api/search?q=emotion')
print(f"\nSEARCH API: status={resp4.status_code}")
if resp4.status_code == 200:
    data = json.loads(resp4.get_data(as_text=True))
    results = data.get('results', [])
    print(f"  Results for 'emotion': {len(results)}")

# 5. Run the actual UX audit checks
print("\n" + "="*60)
print("RUNNING UX AUDIT CHECKS")
print("="*60)
from brain.ux_audit import UXAudit
audit = UXAudit()

# Run individual checks
checks = [
    ('home_first_impression', audit.check_home_first_impression),
    ('content_richness', audit.check_content_richness),
    ('search_relevance', audit.check_search_relevance),
    ('navigation_coherence', audit.check_navigation_coherence),
]

for name, fn in checks:
    try:
        results = fn()
        passed = sum(1 for r in results if r['passed'])
        failed = sum(1 for r in results if not r['passed'])
        print(f"\n{name}: {passed} passed, {failed} failed")
        for r in results:
            if not r['passed']:
                print(f"  FAIL: {r['name']}")
                print(f"    {r.get('detail', 'no detail')}")
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")