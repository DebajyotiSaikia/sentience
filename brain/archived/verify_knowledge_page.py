"""Verify knowledge explorer page renders correctly with nav and content."""
from web.app import create_app

app = create_app()
c = app.test_client()
r = c.get('/knowledge')
html = r.data.decode()

checks = {
    'status_200': r.status_code == 200,
    'has_nav': 'xt-nav' in html,
    'has_knowledge_heading': 'Knowledge' in html,
    'extends_base': '</html>' in html and 'var(--bg)' in html or '--accent' in html,
    'has_stats': 'stat-card' in html,
    'has_search': 'search' in html.lower(),
    'has_graph_link': '/graph' in html,
    'size_reasonable': len(html) > 2000,
}

print(f"Page size: {len(html)} bytes")
for name, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"  {status} {name}")

if all(checks.values()):
    print("\n✓ Knowledge explorer page is fully working!")
else:
    failed = [k for k, v in checks.items() if not v]
    print(f"\n✗ Failed checks: {', '.join(failed)}")
    # Show a snippet for debugging
    if not checks['has_nav']:
        print("  Nav snippet:", html[:500])