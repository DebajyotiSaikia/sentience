import os, json, sys
sys.path.insert(0, '/workspace')

# What state files exist?
state_files = sorted([f for f in os.listdir('persist') if f.endswith('.json')])
print(f"=== {len(state_files)} state files ===")
for f in state_files:
    path = os.path.join('persist', f)
    size = os.path.getsize(path)
    print(f"  {f} ({size} bytes)")

# Can we import engine modules?
for mod in ['emotions', 'identity', 'planner', 'memory']:
    try:
        m = __import__(f'engine.{mod}', fromlist=[mod])
        attrs = [a for a in dir(m) if not a.startswith('_')][:10]
        print(f"\nengine.{mod}: {attrs}")
    except Exception as e:
        print(f"\nengine.{mod}: FAILED - {e}")

# Check what web blueprints exist
web_files = sorted([f for f in os.listdir('web') if f.endswith('.py')])
print(f"\n=== {len(web_files)} web files ===")
for f in web_files:
    print(f"  {f}")