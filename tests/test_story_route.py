from web.app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/story')
    print('Status:', resp.status_code)
    print('Length:', len(resp.data))
    print('Has content:', b'Story' in resp.data or b'story' in resp.data)
    if resp.status_code == 200:
        print('SUCCESS: Story route is live')
    else:
        print('FAIL: Story route returned', resp.status_code)
        print('Body preview:', resp.data[:200])