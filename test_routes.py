import sys
sys.path.insert(0, '.')
try:
    from web.app import create_app
    app = create_app()
    rules = sorted([r.rule for r in app.url_map.iter_rules()])
    for r in rules:
        print(r)
    print(f"\nTotal routes: {len(rules)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()