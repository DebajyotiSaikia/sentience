import sys
sys.path.insert(0, '/workspace')
from web.app import create_app

app = create_app()
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for r in rules:
    if r.endpoint != 'static':
        methods = ','.join(sorted(r.methods - {'HEAD', 'OPTIONS'}))
        print(f'{methods:6s} {r.rule:45s} → {r.endpoint}')