import sys
sys.path.insert(0, '/workspace')

# Try common Flask patterns
try:
    from web.app import create_app
    app = create_app()
    print("Using create_app()")
except ImportError:
    try:
        from web.app import app
        print("Using direct app import")
    except ImportError:
        # Last resort: just find what's exported
        import web.app as mod
        print("Module attributes:", [a for a in dir(mod) if not a.startswith('_')])
        sys.exit(0)

routes = sorted(set(rule.rule for rule in app.url_map.iter_rules() if not rule.rule.startswith('/static')))
for r in routes:
    print(r)