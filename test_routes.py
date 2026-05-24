import urllib.request
import urllib.error

routes = ['/', '/chat', '/knowledge', '/dashboard', '/life', '/explore', '/about-me', '/mindstream', '/timeline']
for r in routes:
    try:
        resp = urllib.request.urlopen(f'http://localhost:5000{r}')
        print(f'{r} -> {resp.status}')
    except urllib.error.HTTPError as e:
        print(f'{r} -> {e.code}')
    except Exception as e:
        print(f'{r} -> ERROR: {e}')