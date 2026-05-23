import sys
sys.path.insert(0, '.')

from web.app import create_app

app = create_app()

with app.app_context():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append((rule.rule, rule.methods - {'OPTIONS', 'HEAD'}))
    routes.sort()

    # Portal links to these pages:
    needed = ['/chat', '/knowledge', '/dashboard', '/life', '/explore',
              '/about-me', '/mindstream', '/timeline', '/talk', '/dialogue',
              '/mind', '/graph', '/pulse', '/weather', '/portrait',
              '/diagnostics', '/emotional-timeline', '/briefing', '/essays',
              '/search', '/collaborate', '/temporal']

    existing = {r[0] for r in routes}

    print('=== ROUTES THE PORTAL LINKS TO ===')
    for page in needed:
        # Check exact match or prefix match
        found = page in existing or any(e.startswith(page) for e in existing)
        status = 'OK' if found else 'MISSING'
        print(f'  {page}: {status}')

    print(f'\n=== ALL {len(routes)} REGISTERED ROUTES ===')
    for rule, methods in routes:
        print(f'  {rule} [{", ".join(sorted(methods))}]')