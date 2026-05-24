import sys
sys.path.insert(0, '/workspace')
try:
    from web.app import create_app
    app = create_app()
    rules = sorted(set(r.rule for r in app.url_map.iter_rules()))
    print(f"Total routes: {len(rules)}")
    for r in rules:
        print(r)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()