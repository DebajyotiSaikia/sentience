from web.app import create_app

app = create_app()
client = app.test_client()

routes = [
    '/', '/mind', '/story', '/chat', '/knowledge', '/explore',
    '/graph', '/pulse', '/reflect', '/ask', '/about', '/wonder',
    '/timeline', '/briefing', '/dialogue', '/collaborate',
    '/thoughts', '/mindstream'
]

for r in routes:
    try:
        resp = client.get(r)
        status = resp.status_code
        symbol = 'OK' if status == 200 else 'XX'
        print(f'{symbol} {status} {r}')
    except Exception as e:
        print(f'XX ERR {r}: {e}')