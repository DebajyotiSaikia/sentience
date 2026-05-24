from web.app import create_app

app = create_app()
client = app.test_client()

routes = [
    '/', '/portal', '/story', '/emotions', '/memories', '/dreams', '/reflection',
    '/knowledge', '/graph', '/synthesis', '/wisdom', '/plans', '/will', '/episodes', '/tools'
]

for r in routes:
    resp = client.get(r)
    status = resp.status_code
    size = len(resp.data)
    flag = 'OK' if status == 200 else 'FAIL'
    print(f'{flag} {status} {r:20s} ({size:>8,} bytes)')