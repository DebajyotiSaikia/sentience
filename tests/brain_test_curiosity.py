"""Quick test: does /curiosity load?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

resp = client.get('/curiosity')
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.get_data(as_text=True)
    print(f'Length: {len(data)} chars')
    print('Has curiosity content:', 'curious' in data.lower() or 'question' in data.lower())
else:
    print('Error:', resp.get_data(as_text=True)[:500])