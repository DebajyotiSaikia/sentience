from web.app import create_app
app = create_app()
client = app.test_client()

endpoints = ['/api/status', '/api/knowledge', '/api/memories', '/api/plans']
for ep in endpoints:
    r = client.get(ep)
    preview = r.get_data(as_text=True)[:200].replace('\n', ' ')
    print(f'{ep}: {r.status_code} — {preview}')