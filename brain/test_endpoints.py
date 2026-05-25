"""Test key API endpoints to verify they work."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

tests = [
    ("GET /api/knowledge", "/api/knowledge"),
    ("GET /api/knowledge?q=dream", "/api/knowledge?q=dream"),
    ("GET /api/knowledge/stats", "/api/knowledge/stats"),
    ("GET /api/knowledge/random", "/api/knowledge/random"),
    ("GET /api/status", "/api/status"),
    ("GET /api/search?q=identity", "/api/search?q=identity"),
    ("GET /api/mind/state", "/api/mind/state"),
    ("GET /api/mind/search?q=test", "/api/mind/search?q=test"),
]

for name, path in tests:
    r = client.get(path)
    data = r.get_json() if r.content_type and "json" in r.content_type else None
    detail = ""
    if data and isinstance(data, dict):
        if "facts" in data:
            detail = f" ({len(data['facts'])} facts)"
        elif "results" in data:
            detail = f" ({len(data['results'])} results)"
        else:
            detail = f" (keys: {list(data.keys())[:5]})"
    status = "OK" if r.status_code == 200 else "FAIL"
    print(f"  [{status}] {name}: {r.status_code}{detail}")

print("\nDone.")