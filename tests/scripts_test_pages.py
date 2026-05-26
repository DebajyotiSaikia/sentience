from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/dashboard', '/knowledge', '/temporal', '/life', '/me', '/search',
    '/explore', '/briefing', '/essays', '/chat', '/timeline', '/talk',
    '/mind', '/stream', '/collaborate/', '/graph', '/diagnostics',
    '/emotional-timeline', '/portrait', '/about', '/ask'
]

for p in pages:
    try:
        r = client.get(p)
        status = '✓' if r.status_code == 200 else f'✗ {r.status_code}'
        print(f'{status} {p}')
    except Exception as e:
        print(f'✗ {p} — {type(e).__name__}: {e}')