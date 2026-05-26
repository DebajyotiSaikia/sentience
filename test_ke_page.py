"""Quick test: does /knowledge render with nav, search, facts?"""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get('/knowledge')
    print(f'Status: {r.status_code}')
    html = r.data.decode()
    has_nav = 'xt-nav' in html
    has_search = 'search' in html.lower()
    has_facts = 'fact' in html.lower()
    print(f'Has nav: {has_nav}')
    print(f'Has search: {has_search}')  
    print(f'Has facts: {has_facts}')
    print(f'Length: {len(html)} chars')
    # Show first 20 lines
    for i, line in enumerate(html.split('\n')[:20]):
        print(f'{i:3d}: {line[:120]}')
    if r.status_code != 200:
        print('BODY:', html[:500])