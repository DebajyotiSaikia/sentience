"""Quick diagnostic: check the 3 UX failures from the audit."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Knowledge stats endpoint
print("=== /api/knowledge/stats ===")
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
body = json.loads(resp.get_data(as_text=True))
print(f"Body: {json.dumps(body, indent=2)[:500]}")
print(f"total_facts={body.get('total_facts', 'MISSING')}")

# 2. Check links on home page
print("\n=== Home page link check ===")
resp = client.get('/')
html = resp.get_data(as_text=True)
import re
links = re.findall(r'href="(/[^"]*)"', html)
print(f"Found {len(links)} internal links")
broken = []
for link in set(links):
    if link.startswith('/static') or link.startswith('/#'):
        continue
    r = client.get(link)
    if r.status_code >= 400:
        broken.append((link, r.status_code))
        print(f"  BROKEN: {link} -> {r.status_code}")
if not broken:
    print("  All links OK")

# 3. Chat response quality
print("\n=== Chat response check ===")
resp = client.post('/api/chat',
    data=json.dumps({'message': 'What can you do?'}),
    content_type='application/json')
print(f"Status: {resp.status_code}")
chat_body = resp.get_data(as_text=True)
print(f"Response length: {len(chat_body)}")
print(f"Preview: {chat_body[:300]}")

# 4. Re-run the actual audit to see exact failures
print("\n=== Running UX Audit ===")
from brain.ux_audit import UXAudit
audit = UXAudit()
results = audit.audit_all()
for r in results:
    if not r['passed']:
        print(f"\nFAILED: {r['test']}")
        print(f"  Details: {r.get('details', 'none')}")