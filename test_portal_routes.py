"""Test which portal navigation links actually resolve to working routes."""
import requests
import sys

BASE = "http://localhost:5000"

# These are the 8 cards from portal.html
portal_links = [
    ("/chat", "Chat"),
    ("/knowledge", "Knowledge"),
    ("/life", "Life"),
    ("/explore", "Explore"),
    ("/about-me", "About Me"),
    ("/mindstream", "Mindstream"),
    ("/timeline", "Timeline"),
    ("/dashboard", "Dashboard"),
]

print("=== Portal Route Audit ===\n")
working = []
broken = []

for path, name in portal_links:
    try:
        r = requests.get(f"{BASE}{path}", timeout=5, allow_redirects=True)
        status = r.status_code
        size = len(r.text)
        if status == 200:
            working.append((name, path, size))
            print(f"  ✓ {name:12s} {path:15s} → {status} ({size} bytes)")
        else:
            broken.append((name, path, status))
            print(f"  ✗ {name:12s} {path:15s} → {status}")
    except Exception as e:
        broken.append((name, path, str(e)))
        print(f"  ✗ {name:12s} {path:15s} → ERROR: {e}")

print(f"\n=== Summary ===")
print(f"Working: {len(working)}/{len(portal_links)}")
print(f"Broken:  {len(broken)}/{len(portal_links)}")

if broken:
    print(f"\nBroken routes need fixing:")
    for name, path, info in broken:
        print(f"  - {name} ({path}): {info}")
    sys.exit(1)
else:
    print("\nAll portal links are live! ✓")