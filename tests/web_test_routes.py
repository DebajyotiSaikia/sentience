"""Quick route verification — write once, run once, move on."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

print("=== All Registered Routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:6s} {rule.rule} -> {rule.endpoint}")

print("\n=== Route Tests ===")
tests = ['/', '/dashboard/', '/chat/', '/ask/', '/graph/']
for path in tests:
    try:
        r = client.get(path)
        status = r.status_code
        size = len(r.data)
        label = "OK" if status == 200 else ("REDIRECT" if status in (301,302,308) else "FAIL")
        print(f"  {label:8s} GET {path} -> {status} ({size} bytes)")
    except Exception as e:
        print(f"  ERROR   GET {path} -> {e}")

print("\nDone.")