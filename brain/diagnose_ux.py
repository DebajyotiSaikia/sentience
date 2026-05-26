"""Diagnose the 3 UX audit failures with debug output."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import re

app = create_app()
client = app.test_client()

# 1. Home page links analysis
print("=" * 60)
print("1. HOME PAGE LINK ANALYSIS")
print("=" * 60)
resp = client.get('/')
html = resp.get_data(as_text=True)
links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html, re.IGNORECASE)
print(f"Total <a> links found: {len(links)}")
for href, text in links:
    print(f"  {href} -> {text.strip()[:50]}")

# Check for CTA-like elements
cta_patterns = ['chat', 'talk', 'explore', 'try', 'start', 'begin', 'ask']
cta_links = [(h, t) for h, t in links if any(p in t.lower() or p in h.lower() for p in cta_patterns)]
print(f"\nCTA-like links: {len(cta_links)}")
for href, text in cta_links:
    print(f"  {href} -> {text.strip()}")

# Check for buttons
buttons = re.findall(r'<button[^>]*>([^<]*)</button>', html, re.IGNORECASE)
print(f"\nButtons: {len(buttons)}")
for b in buttons:
    print(f"  {b.strip()}")

# 2. Knowledge stats
print("\n" + "=" * 60)
print("2. KNOWLEDGE STATS ANALYSIS")
print("=" * 60)

# Check what /api/knowledge/stats returns
resp = client.get('/api/knowledge/stats')
print(f"/api/knowledge/stats -> {resp.status_code}")
if resp.status_code == 200:
    print(f"  {resp.get_data(as_text=True)[:300]}")

# Check what /knowledge returns
resp = client.get('/knowledge')
print(f"\n/knowledge -> {resp.status_code}")
if resp.status_code == 200:
    khtml = resp.get_data(as_text=True)
    # Look for fact counts in the HTML
    counts = re.findall(r'(\d+)\s*(?:facts?|items?|knowledge|entries)', khtml, re.IGNORECASE)
    print(f"  Fact count mentions: {counts}")

# Check the actual knowledge file
import json
for path in ['brain/knowledge.json', 'persist/knowledge_graph.json']:
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
            print(f"\n{path}: {len(nodes)} nodes")
        elif isinstance(data, list):
            print(f"\n{path}: {len(data)} items")
    else:
        print(f"\n{path}: NOT FOUND")

# 3. Run the actual audit checks that fail
print("\n" + "=" * 60)
print("3. RUNNING ACTUAL AUDIT CHECKS")
print("=" * 60)
from brain.ux_audit import UXAudit
audit = UXAudit()
results = audit.run_all()
for r in results:
    if not r.get('passed', True):
        print(f"  FAIL: {r.get('area', '?')}: {r.get('check', '?')}")
        print(f"        {r.get('details', '?')}")