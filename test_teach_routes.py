"""Diagnose teach route registration."""
from web.app import create_app

app = create_app()
rules = sorted([(r.rule, list(r.methods - {'OPTIONS', 'HEAD'})) for r in app.url_map.iter_rules()])
print("=== ALL ROUTES ===")
for rule, methods in rules:
    print(f"  {methods} {rule}")

print("\n=== TEACH ROUTES ===")
for rule, methods in rules:
    if 'teach' in rule.lower():
        print(f"  {methods} {rule}")

print("\n=== Testing /api/teach/submit ===")
with app.test_client() as client:
    resp = client.post('/api/teach/submit', json={"content": "test fact", "type": "fact"})
    print(f"  POST /api/teach/submit -> {resp.status_code}")
    print(f"  Response: {resp.get_data(as_text=True)[:200]}")