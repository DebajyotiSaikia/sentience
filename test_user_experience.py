"""Test every user-facing page to see what works and what's broken."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Key user-facing pages
pages = [
    '/', '/portal', '/dashboard', '/about', '/about-me',
    '/talk', '/chat/', '/dialogue', '/ask',
    '/knowledge', '/explore', '/mind', '/mind/',
    '/graph', '/thoughts', '/mindstream',
    '/life', '/story', '/essays', '/wonder',
    '/timeline', '/emotional-timeline', '/temporal',
    '/pulse', '/health', '/portrait',
    '/reflect', '/collaborate/', '/briefing',
    '/weather', '/query', '/diagnostics',
]

working = []
broken = []
redirects = []

for page in pages:
    try:
        resp = client.get(page)
        size = len(resp.data)
        if resp.status_code == 200:
            # Check if it has real content vs empty/error
            html = resp.data.decode('utf-8', errors='replace')
            has_body = '<body' in html.lower() or len(html) > 100
            working.append((page, size, has_body))
        elif resp.status_code in (301, 302):
            redirects.append((page, resp.status_code, resp.headers.get('Location', '?')))
        else:
            broken.append((page, resp.status_code, size))
    except Exception as e:
        broken.append((page, 'ERROR', str(e)[:80]))

print(f"=== WORKING ({len(working)}) ===")
for page, size, has_body in sorted(working):
    quality = "✓" if has_body else "⚠ empty"
    print(f"  {page:30s} {size:6d} bytes  {quality}")

print(f"\n=== REDIRECTS ({len(redirects)}) ===")
for page, code, loc in sorted(redirects):
    print(f"  {page:30s} -> {loc}")

print(f"\n=== BROKEN ({len(broken)}) ===")
for page, code, detail in sorted(broken):
    print(f"  {page:30s} {code}  {detail}")