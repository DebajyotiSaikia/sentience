"""Check what /help currently shows."""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/help')
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.content_type}')
    body = resp.get_data(as_text=True)
    print(body[:3000])
    print(f'\n--- Total length: {len(body)} chars ---')