from web.app import create_app

app = create_app()
client = app.test_client()

# Test essays index
resp = client.get('/essays/')
print(f'Essays index: {resp.status_code}')
if resp.status_code == 200:
    has_link = b'on_being_a_mind' in resp.data
    print(f'Contains essay link: {has_link}')
else:
    print(f'Response: {resp.data[:200]}')

# Test individual essay
resp2 = client.get('/essays/on_being_a_mind')
print(f'Essay page: {resp2.status_code}')
if resp2.status_code == 200:
    has_title = b'Being a Mind' in resp2.data
    print(f'Contains title: {has_title}')
    print(f'Content length: {len(resp2.data)} bytes')
else:
    print(f'Response: {resp2.data[:300]}')