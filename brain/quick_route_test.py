"""Quick route health check — script file to avoid shell quoting issues."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

routes = ['/digest', '/briefing', '/dashboard', '/chat', '/explore', 
          '/insights', '/story', '/journal', '/about', '/help', '/teach',
          '/collaborate', '/live', '/', '/knowledge']

ok = 0
fail = 0
for r in routes:
    try:
        resp = client.get(r)
        status = 'OK' if resp.status_code == 200 else f'FAIL({resp.status_code})'
        if resp.status_code == 200:
            ok += 1
        else:
            fail += 1
        print(f"  {'✓' if resp.status_code == 200 else '✗'} {r:20s} -> {status}")
    except Exception as e:
        fail += 1
        print(f"  ✗ {r:20s} -> ERROR: {e}")

print(f"\n{ok}/{ok+fail} routes OK")