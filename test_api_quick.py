#!/usr/bin/env python3
"""Quick API endpoint test."""
import urllib.request, json

endpoints = [
    ('Search', 'http://localhost:5000/api/knowledge/search?q=dream'),
    ('Stats', 'http://localhost:5000/api/knowledge/stats'),
    ('Page', 'http://localhost:5000/knowledge/'),
]

for name, url in endpoints:
    try:
        r = urllib.request.urlopen(url, timeout=5)
        body = r.read().decode()
        if 'api' in url:
            data = json.loads(body)
            print(f"{name}: OK ({r.status}) - {json.dumps(data)[:120]}")
        else:
            print(f"{name}: OK ({r.status}) - {len(body)} bytes, has search: {'liveSearch' in body}")
    except Exception as e:
        print(f"{name}: FAIL - {e}")