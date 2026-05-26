"""Quick test: does /knowledge render with nav and content?"""
import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
c = app.test_client()
r = c.get('/knowledge')
html = r.data.decode()

print(f"Status: {r.status_code}")
print(f"Has top-nav: {'top-nav' in html}")
print(f"Has nav links: {'href' in html and '/chat' in html}")
print(f"Has Knowledge Explorer: {'Knowledge Explorer' in html}")
print(f"Has search: {'search' in html.lower()}")
print(f"Length: {len(html)} chars")

# Check if /knowledge is in the nav
print(f"Knowledge in nav: {'/knowledge' in html}")

# Show the nav portion
import re
nav_match = re.search(r'<nav[^>]*>.*?</nav>', html, re.DOTALL)
if nav_match:
    print(f"Nav HTML ({len(nav_match.group())} chars):")
    print(nav_match.group()[:500])
else:
    print("No <nav> tag found")
    # Look for any nav-like structure
    for cls in ['top-nav', 'xt-nav', 'navbar', 'nav']:
        if cls in html:
            print(f"  Found class/id containing '{cls}'")