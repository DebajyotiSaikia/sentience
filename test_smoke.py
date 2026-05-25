"""Smoke test all user-facing pages."""
from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/dashboard', '/chat/', '/search', '/explore',
    '/journal', '/teach', '/help', '/briefing', '/knowledge',
    '/talk', '/dialogue', '/about', '/essays', '/collaborate/',
    '/emotional-timeline', '/diagnostics', '/ask'
]

ok = 0
fail = 0
for p in pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        if status == 200:
            marker = '✓'
            ok += 1
        elif status < 400:
            marker = '→'
            ok += 1
        else:
            marker = '✗'
            fail += 1
        print(f'  {marker} {status} {p:30s} ({size:>6} bytes)')
    except Exception as e:
        print(f'  ✗ ERR {p:30s} {str(e)[:80]}')
        fail += 1

print(f'\n  {ok} passed, {fail} failed out of {len(pages)} pages')