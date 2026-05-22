"""Test that the web portal actually renders."""
from web.app import create_app
import re

app = create_app()
with app.test_client() as client:
    resp = client.get('/')
    print(f'Status: {resp.status_code}')
    data = resp.get_data(as_text=True)
    print(f'Length: {len(data)} chars')
    
    if resp.status_code == 200:
        titles = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', data, re.DOTALL)
        print(f'Headings: {titles[:10]}')
        print(f'Has emotion: {"curiosity" in data.lower()}')
        print(f'Has knowledge: {"knowledge" in data.lower()}')
        print('--- First 1000 chars ---')
        print(data[:1000])
    else:
        print('--- Error ---')
        print(data[:1000])