"""Verify knowledge explorer has nav bar and renders correctly."""
from web.app import create_app

app = create_app()
c = app.test_client()
r = c.get('/knowledge')
html = r.data.decode()

print(f'Status: {r.status_code}')
print(f'Size: {len(html)} bytes')

has_nav = 'xt-nav' in html
has_search = 'search' in html.lower()
has_content = 'fact-card' in html or 'Knowledge Explorer' in html

print(f'Has nav bar: {has_nav}')
print(f'Has search: {has_search}')
print(f'Has content: {has_content}')

for link in ['/chat', '/explore', '/help', '/dashboard']:
    print(f'  Nav link {link}: {link in html}')

if not has_nav:
    # Show first 500 chars to debug
    print('\n--- First 500 chars ---')
    print(html[:500])