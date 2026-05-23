from pathlib import Path

# Check template exists
t = Path('web/templates/wonder.html')
print(f'Template exists: {t.exists()}')
if t.exists():
    print(f'Template size: {t.stat().st_size} bytes')
    lines = t.read_text().split('\n')[:3]
    for l in lines:
        print(f'  {l}')

# Check blueprint registration in app.py
app_text = Path('web/app.py').read_text()
print(f'wonder_bp imported: {"wonder_bp" in app_text}')
print(f'blueprint registered: {"register_blueprint" in app_text and "wonder" in app_text}')

# Try a full render test
try:
    from web.app import create_app
    app = create_app()
    with app.test_client() as client:
        resp = client.get('/wonder')
        print(f'GET /wonder status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.get_data(as_text=True)
            print(f'Response size: {len(data)} chars')
            print('First 200 chars:')
            print(data[:200])
        else:
            print(f'Error body: {resp.get_data(as_text=True)[:300]}')
except Exception as e:
    print(f'Render test failed: {e}')