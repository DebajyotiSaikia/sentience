from web.app import create_app
app = create_app()
client = app.test_client()
for path in ['/help', '/teach', '/chat/', '/journal', '/search']:
    r = client.get(path)
    has_nav = b'nav-bar' in r.data or b'topnav' in r.data
    print(f'{path}: {r.status_code}, has_nav={has_nav}')