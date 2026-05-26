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
        status = "OK" if r.status_code == 200 else f"FAIL({r.status_code})"
        print(f"{status:12s} {p}")
    except Exception as e:
        print(f"ERROR        {p} — {e}")