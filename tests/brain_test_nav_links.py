"""Audit all navigation links — which ones work, which 404?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Nav links from web/nav.py
nav_links = [
    ("/", "Home"),
    ("/chat", "Chat"),
    ("/explore", "Explore"),
    ("/dashboard", "Dashboard"),
    ("/insights", "Insights"),
    ("/journal", "Journal"),
    ("/story", "Story"),
    ("/collaborate", "Collaborate"),
    ("/live", "Live"),
    ("/teach", "Teach"),
    ("/briefing", "Briefing"),
    ("/help", "Help"),
]

# Also test pages NOT in nav that should be
extra_pages = [
    ("/knowledge", "Knowledge Explorer"),
    ("/graph", "Knowledge Graph"),
]

print("=== Navigation Link Audit ===\n")
broken = []
working = []

for path, label in nav_links + extra_pages:
    r = client.get(path)
    status = r.status_code
    in_nav = any(p == path for p, _ in nav_links)
    marker = "NAV" if in_nav else "HIDDEN"
    
    if status == 200:
        working.append((path, label, marker))
        print(f"  ✅ {status} [{marker}] {path} — {label}")
    elif status in (301, 302, 308):
        location = r.headers.get('Location', '?')
        working.append((path, label, marker))
        print(f"  ↪️  {status} [{marker}] {path} → {location}")
    else:
        broken.append((path, label, marker, status))
        print(f"  ❌ {status} [{marker}] {path} — {label}")

print(f"\n--- Summary ---")
print(f"Working: {len(working)}")
print(f"Broken:  {len(broken)}")
if broken:
    print(f"\nBroken pages:")
    for path, label, marker, status in broken:
        print(f"  {path} ({label}) — {status} [{marker}]")