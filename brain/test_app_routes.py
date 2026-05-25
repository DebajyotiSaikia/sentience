"""Test: can the Flask app start? Are there duplicate routes?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import Counter

try:
    from web.app import create_app
    app = create_app()
    all_rules = [r.rule for r in app.url_map.iter_rules()]
    unique = sorted(set(all_rules))
    print(f"App created OK. {len(unique)} unique routes, {len(all_rules)} total.")
    
    dupes = {r: c for r, c in Counter(all_rules).items() if c > 1}
    if dupes:
        print(f"\nDUPLICATE ROUTES ({len(dupes)}):")
        for route, count in sorted(dupes.items()):
            print(f"  {route} x{count}")
    else:
        print("No duplicate routes.")
    
    # Show all /api/* and /knowledge* routes
    print("\nKnowledge/API routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if '/api/' in rule.rule or '/knowledge' in rule.rule:
            print(f"  {rule.rule:45s} -> {rule.endpoint}")

except Exception as e:
    import traceback
    print(f"FAILED: {e}")
    traceback.print_exc()