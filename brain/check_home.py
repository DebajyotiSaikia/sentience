"""Check what the home page actually serves."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()
resp = client.get('/')
html = resp.get_data(as_text=True)

print(f"Status: {resp.status_code}")
print(f"Length: {len(html)}")
print(f"<a count: {html.count('<a ')}")
print(f"Has nav-bar: {'nav-bar' in html}")
print(f"Has nav.js: {'nav.js' in html}")
print(f"Has /chat link: {'/chat' in html}")
print(f"Has /explore link: {'/explore' in html}")
print(f"Has CTA class: {'cta' in html.lower()}")
print(f"Has Talk to me: {'talk to me' in html.lower()}")
print()

# Show all <a> tags
import re
links = re.findall(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', html)
print(f"Found {len(links)} links:")
for href, text in links:
    print(f"  {href} -> {text.strip()}")

# Check what the UX audit looks for
print()
print("--- UX Audit checks ---")
nav_links = re.findall(r'<a[^>]*href=["\']/(chat|explore|dashboard|about|help|knowledge)["\']', html)
print(f"Navigation links found: {nav_links}")
cta = re.findall(r'<a[^>]*class=["\'][^"\']*cta[^"\']*["\']', html, re.I)
print(f"CTA elements: {len(cta)}")