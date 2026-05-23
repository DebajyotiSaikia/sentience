import urllib.request
import urllib.error
import re

routes = [
    '/', '/chat', '/knowledge', '/dashboard', '/life',
    '/explore', '/about-me', '/mindstream', '/timeline',
    '/talk', '/graph', '/about', '/collaborate'
]

for r in routes:
    url = f'http://localhost:8501{r}'
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=3)
        body = resp.read().decode('utf-8', errors='replace')
        status = resp.status
        title_match = re.search(r'<title>(.*?)</title>', body, re.IGNORECASE)
        title = title_match.group(1)[:40] if title_match else '(no title)'
        print(f'{r:20s} -> {status} ({len(body):6d} bytes) "{title}"')
    except urllib.error.HTTPError as e:
        print(f'{r:20s} -> {e.code} {e.reason}')
    except Exception as e:
        print(f'{r:20s} -> ERROR: {e}')