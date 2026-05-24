from web.app import create_app

app = create_app()
client = app.test_client()

for path in ['/portal', '/story', '/', '/dashboard']:
    resp = client.get(path)
    print(f'{resp.status_code} {path}')