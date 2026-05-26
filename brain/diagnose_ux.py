"""Diagnose the 4 UX audit failures — run once, fix once."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
c = app.test_client()

print("=" * 60)
print("UX FAILURE DIAGNOSIS")
print("=" * 60)

# 1. Home page — call to action
r = c.get('/')
html = r.get_data(as_text=True)
has_cta = bool(re.search(r'(start|chat|explore|try|ask|talk|begin)', html, re.I))
nav_links = re.findall(r'href="(/[^"]*)"', html)
print(f"\n[1] HOME PAGE")
print(f"    Status: {r.status_code}, Length: {len(html)}")
print(f"    Has CTA words: {has_cta}")
print(f"    Nav links found: {len(nav_links)}")
print(f"    Links: {nav_links[:10]}")

# 2. Chat page — navigation
r2 = c.get('/chat')
html2 = r2.get_data(as_text=True)
nav_links2 = re.findall(r'href="(/[^"]*)"', html2)
print(f"\n[2] CHAT PAGE")
print(f"    Status: {r2.status_code}, Length: {len(html2)}")
print(f"    Nav links: {len(nav_links2)}")

# 3. Knowledge stats API
r3 = c.get('/api/knowledge/stats')
print(f"\n[3] KNOWLEDGE STATS")
print(f"    Status: {r3.status_code}")
if r3.status_code == 200:
    data = json.loads(r3.get_data(as_text=True))
    print(f"    Data keys: {list(data.keys())}")
    print(f"    Has facts: {'total_facts' in data or 'total' in data or 'count' in data}")
else:
    print(f"    Body: {r3.get_data(as_text=True)[:200]}")

# 4. Feedback submit
r4 = c.post('/api/feedback',
    data=json.dumps({'rating': 5, 'comment': 'test', 'context': 'ux_audit'}),
    content_type='application/json')
print(f"\n[4] FEEDBACK SUBMIT")
print(f"    Status: {r4.status_code}")
print(f"    Body: {r4.get_data(as_text=True)[:200]}")

# 5. Run the actual audit to see exact failures
print(f"\n{'=' * 60}")
print("RUNNING ACTUAL AUDIT")
print("=" * 60)

from brain.ux_audit import UXAudit
audit = UXAudit()
results = audit.run_all()
for r in results:
    if not r['passed']:
        print(f"\n  FAIL: {r['test']}")
        print(f"    Details: {json.dumps(r.get('details', {}), indent=2)[:300]}")

passed = sum(1 for r in results if r['passed'])
total = len(results)
print(f"\n  SCORE: {passed}/{total}")