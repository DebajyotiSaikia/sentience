from web.app import create_app

app = create_app()
client = app.test_client()

resp = client.get('/thoughts')
print(f'Status: {resp.status_code}')
print(f'Length: {len(resp.data)}')

if resp.status_code == 200:
    print('First 300 chars:', resp.data[:300].decode())
else:
    print('Body:', resp.data[:500].decode())