import sys
sys.path.insert(0, '/home/xt')
from web.app import app

print('=== ALL REGISTERED ROUTES ===')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if not rule.rule.startswith('/static'):
        print(f'  {rule.rule} -> {rule.endpoint} [{",".join(rule.methods - {"OPTIONS","HEAD"})}]')