"""Test the /api/knowledge/stats endpoint to find why it returns 0 facts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test the stats endpoint
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
print(f"Data: {resp.get_data(as_text=True)[:500]}")

# Also test the main knowledge page
resp2 = client.get('/knowledge')
html = resp2.get_data(as_text=True)
print(f"\n/knowledge status: {resp2.status_code}")
print(f"/knowledge length: {len(html)} chars")

# Check if stats are embedded in the page
if 'total_facts' in html or '127' in html or 'fact' in html.lower():
    print("Facts data found in knowledge page")
else:
    print("No facts data visible in knowledge page")