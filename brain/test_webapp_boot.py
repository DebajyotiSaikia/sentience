"""Test that the web app boots and all routes are registered."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
print("App created OK")
print("\nRegistered routes:")
routes = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for rule in routes:
    if not rule.rule.startswith("/static"):
        methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
        print(f"  {rule.rule:40s} {methods}")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")

# Test that key pages render without crashing
with app.test_client() as client:
    critical_pages = ["/", "/dashboard", "/chat", "/explore", "/help",
                      "/briefing", "/knowledge", "/search", "/teach",
                      "/journal", "/story", "/insights", "/live"]
    print("\nPage render tests:")
    ok = 0
    fail = 0
    for page in critical_pages:
        try:
            resp = client.get(page)
            status = resp.status_code
            if status < 400:
                print(f"  {page:30s} -> {status} OK")
                ok += 1
            else:
                print(f"  {page:30s} -> {status} FAIL")
                fail += 1
        except Exception as e:
            print(f"  {page:30s} -> ERROR: {e}")
            fail += 1
    
    print(f"\nResults: {ok} OK, {fail} FAIL out of {len(critical_pages)} pages")
    if fail == 0:
        print("ALL PAGES HEALTHY")
    else:
        print("SOME PAGES NEED ATTENTION")