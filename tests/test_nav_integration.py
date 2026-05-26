"""Test that nav.js is present on all pages."""
from web.app import create_app

app = create_app()
c = app.test_client()

all_good = True
for path in ['/', '/dashboard', '/chat', '/explore', '/teach']:
    r = c.get(path)
    has_nav = b'nav.js' in r.data
    status = r.status_code
    icon = '✓' if (status == 200 and has_nav) else '✗'
    print(f'  {icon} {path:12} status={status} nav.js={has_nav}')
    if status != 200 or not has_nav:
        all_good = False

if all_good:
    print('\n✓ All pages have navigation!')
else:
    print('\n✗ Some pages missing navigation')