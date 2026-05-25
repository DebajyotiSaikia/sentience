"""Test that all key user-facing pages render without errors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = ['/', '/dashboard', '/chat/', '/explore', '/help', '/knowledge', '/briefing', '/story', '/insights']
print(f"Testing {len(pages)} pages...\n")

errors = []
for page in pages:
    resp = client.get(page)
    status = resp.status_code
    size = len(resp.data)
    data_str = resp.data.decode('utf-8', errors='replace')[:500]
    has_error = 'Internal Server Error' in data_str or 'Traceback' in data_str
    label = 'ERROR' if has_error else 'ok'
    if status >= 400:
        label = f'HTTP {status}'
    print(f"  {label:>8}  {size:>6}b  {page}")
    if has_error or status >= 400:
        errors.append((page, status, data_str[:200]))

print()
if errors:
    print(f"FAILURES ({len(errors)}):")
    for page, status, preview in errors:
        print(f"  {page} [{status}]: {preview[:100]}...")
else:
    print("ALL PAGES OK")