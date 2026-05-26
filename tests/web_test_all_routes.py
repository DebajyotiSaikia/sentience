"""
XTAgent Web Route Tester
=========================
Tests every registered route to find what works and what's broken.
Built because I was circling instead of shipping.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

def test_all_routes():
    app = create_app()
    client = app.test_client()
    
    # Collect all GET-able routes
    routes = []
    for rule in app.url_map.iter_rules():
        if 'GET' in rule.methods and not rule.rule.startswith('/static'):
            # Skip routes with dynamic parameters we can't fill
            if '<' in rule.rule:
                routes.append((rule.rule, rule.endpoint, 'SKIP', 'has parameters'))
                continue
            routes.append((rule.rule, rule.endpoint, None, None))
    
    routes.sort(key=lambda x: x[0])
    
    print(f"\n{'='*60}")
    print(f"  XTAgent Web Route Test — {len(routes)} routes found")
    print(f"{'='*60}\n")
    
    passed = 0
    failed = 0
    skipped = 0
    errors = []
    
    for route, endpoint, status, reason in routes:
        if status == 'SKIP':
            print(f"  ⊘  {route:<40} SKIP ({reason})")
            skipped += 1
            continue
        
        try:
            resp = client.get(route)
            code = resp.status_code
            if code < 400:
                print(f"  ✓  {route:<40} {code}")
                passed += 1
            else:
                print(f"  ✗  {route:<40} {code}")
                failed += 1
                # Get error detail
                try:
                    detail = resp.data.decode()[:200]
                except:
                    detail = "could not decode"
                errors.append((route, code, detail))
        except Exception as e:
            print(f"  ✗  {route:<40} ERROR: {str(e)[:60]}")
            failed += 1
            errors.append((route, 'EXCEPTION', str(e)[:200]))
    
    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed | {failed} failed | {skipped} skipped")
    print(f"{'='*60}")
    
    if errors:
        print(f"\n  Failures detail:")
        for route, code, detail in errors:
            print(f"\n  [{code}] {route}")
            print(f"    {detail[:150]}")
    
    print()
    return passed, failed, skipped, errors

if __name__ == '__main__':
    test_all_routes()