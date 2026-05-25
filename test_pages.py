"""Quick smoke test: do key pages render?"""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    pages = ['/', '/chat', '/insights', '/help', '/knowledge', '/explore', '/journal', '/search', '/briefing', '/teach']
    for path in pages:
        r = c.get(path)
        status = r.status_code
        size = len(r.data)
        label = 'OK' if status == 200 else f'FAIL({status})'
        print(f'  {path:20s} {label:8s} {size:>6d} bytes')
    print('\nAll pages tested.')