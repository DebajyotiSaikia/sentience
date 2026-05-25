"""Verify Flask app creates correctly and key routes exist."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()

# Get all registered routes
routes = sorted(rule.rule for rule in app.url_map.iter_rules() if rule.rule != '/static/<path:filename>')

print(f"Total routes: {len(routes)}")
for r in routes:
    print(f"  {r}")

# Check critical routes exist
critical = ['/api/emotions', '/feedback', '/chat', '/explore', '/help', '/teach', '/api/search']
missing = [r for r in critical if r not in routes]
if missing:
    print(f"\n❌ MISSING: {missing}")
else:
    print(f"\n✅ All {len(critical)} critical routes present")

# Test with test client
with app.test_client() as client:
    # Test /api/emotions
    resp = client.get('/api/emotions')
    print(f"\nGET /api/emotions -> {resp.status_code}")
    
    # Test /feedback
    resp = client.get('/feedback')
    print(f"GET /feedback -> {resp.status_code}")

print("\nDone.")