from web.app import create_app
app = create_app()
with app.test_client() as c:
    resp = c.get('/knowledge')
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.data.decode()
        print(f'Length: {len(data)} chars')
        if 'fact-card' in data: print('✓ Fact cards rendering')
        if 'search-box' in data: print('✓ Search box present')
        if 'Knowledge' in data: print('✓ Title present')
        print('First 300 chars:')
        print(data[:300])
    else:
        print(resp.data.decode()[:500])