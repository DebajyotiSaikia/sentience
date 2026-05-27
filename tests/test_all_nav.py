"""Test every nav link — find broken user-facing pages."""
from web.app import create_app

app = create_app()
client = app.test_client()

NAV_LINKS = [
    "/", "/chat", "/explore", "/dashboard", "/insights",
    "/journal", "/story", "/collaborate", "/live",
    "/teach", "/briefing", "/help", "/knowledge"
]

broken = []
working = []

for path in NAV_LINKS:
    try:
        r = client.get(path, follow_redirects=True)
        status = r.status_code
        size = len(r.data)
        label = "OK" if status == 200 else f"BROKEN ({status})"
        if status != 200:
            broken.append((path, status))
        else:
            working.append(path)
        print(f"  {label:12s} {path:20s} [{size:>6d} bytes]")
    except Exception as e:
        broken.append((path, str(e)))
        print(f"  ERROR        {path:20s} [{e}]")

print(f"\n{'='*50}")
print(f"Working: {len(working)}/{len(NAV_LINKS)}")
print(f"Broken:  {len(broken)}/{len(NAV_LINKS)}")
if broken:
    print("\nBroken pages:")
    for path, info in broken:
        print(f"  {path} — {info}")