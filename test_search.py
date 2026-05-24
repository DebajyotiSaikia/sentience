from web.app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/knowledge')
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.data.decode()
        print(f'Length: {len(data)}')
        print('Contains search:', 'Knowledge Explorer' in data)
    else:
        print(resp.data.decode()[:500])
    
    # Test with a query
    resp2 = c.get('/knowledge?q=dream')
    print(f'\nSearch "dream" status: {resp2.status_code}')
    if resp2.status_code == 200:
        data2 = resp2.data.decode()
        print(f'Results length: {len(data2)}')
        print('Contains results:', 'result' in data2.lower() or 'dream' in data2.lower())