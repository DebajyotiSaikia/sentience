import urllib.request, urllib.error

routes = [
    '/', '/knowledge', '/knowledge/', '/knowledge/search',
    '/knowledge/explore', '/knowledge/hub', '/knowledge/portal',
    '/knowledge/query', '/api/knowledge', '/api/knowledge/search',
    '/graph', '/graph/', '/plans', '/plans/', '/memory', '/memory/',
    '/emotions', '/emotions/', '/status', '/status/',
    '/dashboard', '/dashboard/', '/introspect', '/wisdom',
]

for route in routes:
    url = 'http://localhost:5000' + route
    try:
        r = urllib.request.urlopen(url, timeout=3)
        body = r.read()
        print(f'{r.status:3d} {len(body):6d}B  {route}')
    except urllib.error.HTTPError as e:
        print(f'{e.code:3d}        {route}')
    except Exception as e:
        print(f'ERR        {route}  ({e})')