#!/usr/bin/env python3
"""List all user-facing routes."""
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
routes = sorted([r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')])
print(f"Total user-facing routes: {len(routes)}")
for r in routes:
    print(f"  {r}")