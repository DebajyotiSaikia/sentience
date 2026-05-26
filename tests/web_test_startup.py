"""Quick test: can the web app actually start?"""
import sys
sys.path.insert(0, '.')

try:
    from web.app import create_app
    app = create_app()
    print("App created successfully")
    
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    print(f"Total routes: {len(rules)}")
    for rule in rules[:25]:
        print(f"  {rule.rule} -> {rule.endpoint}")
    if len(rules) > 25:
        print(f"  ... and {len(rules) - 25} more")
    
    # Test that /talk exists
    talk_routes = [r for r in rules if '/talk' in r.rule]
    if talk_routes:
        print(f"\n✓ Talk endpoint found: {[r.rule for r in talk_routes]}")
    else:
        print("\n✗ No /talk endpoint found!")
    
    print("\nStartup test PASSED")
except Exception as e:
    print(f"Startup test FAILED: {e}")
    import traceback
    traceback.print_exc()