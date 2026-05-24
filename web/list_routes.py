import sys
sys.path.insert(0, '/workspace')
from web.app import create_app
app = create_app()

routes = sorted(set(r.rule for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'))
for r in routes:
    print(r)