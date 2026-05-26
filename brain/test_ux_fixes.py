"""Diagnose the 3 UX audit failures so I can fix them."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Knowledge stats — why 0 facts?
print("=== KNOWLEDGE STATS ===")
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
print(f"Body: {resp.get_data(as_text=True)[:500]}")

# 2. Home page — how many links and what CTA?
print("\n=== HOME PAGE ANALYSIS ===")
resp = client.get('/')
html = resp.get_data(as_text=True)
import re
links = re.findall(r'href=["\']([^"\']+)["\']', html)
print(f"Total links found: {len(links)}")
for link in links[:20]:
    print(f"  {link}")

# Check for CTA patterns
cta_patterns = ['get started', 'try', 'begin', 'start', 'talk to me', 'chat with me', 'ask me', 'explore']
html_lower = html.lower()
for pattern in cta_patterns:
    if pattern in html_lower:
        # Find surrounding context
        idx = html_lower.index(pattern)
        context = html[max(0, idx-50):idx+80]
        print(f"  CTA-like: ...{context.strip()}...")