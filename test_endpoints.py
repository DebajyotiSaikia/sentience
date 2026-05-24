import requests

endpoints = ['/', '/portal', '/chat', '/ask', '/knowledge', '/explore', '/about', '/mind', '/status']
for ep in endpoints:
    try:
        r = requests.get(f'http://localhost:8501{ep}', timeout=3)
        preview = r.text[:100].replace('\n', ' ').strip()[:60]
        print(f'{r.status_code} {ep:20s} {len(r.text):>6d} bytes  {preview}')
    except Exception as e:
        print(f'ERR {ep:20s} {str(e)[:60]}')