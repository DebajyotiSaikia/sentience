"""Test what a user actually experiences navigating the dashboard."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test the main endpoints a user would visit
paths = [
    '/',
    '/knowledge',
    '/knowledge/explorer',
    '/knowledge/hub',
    '/knowledge/query',
    '/knowledge/search',
    '/mindstream',
    '/story',
    '/reflect',
    '/timeline',
    '/graph',
    '/plans',
    '/emotions',
]

print("=== USER JOURNEY TEST ===\n")
working = []
broken = []
for p in paths:
    try:
        resp = client.get(p)
        status = resp.status_code
        size = len(resp.data)
        has_content = b'<div' in resp.data and size > 500
        label = "OK" if status == 200 and has_content else "THIN" if status == 200 else "FAIL"
        line = f"  {label:4s} {p:30s} → {status} ({size:,} bytes)"
        print(line)
        if status == 200:
            working.append(p)
        else:
            broken.append((p, status))
    except Exception as e:
        print(f"  ERR  {p:30s} → {e}")
        broken.append((p, str(e)))

print(f"\n=== SUMMARY ===")
print(f"Working: {len(working)} | Broken: {len(broken)}")
if broken:
    print("Broken endpoints:")
    for p, reason in broken:
        print(f"  {p} → {reason}")