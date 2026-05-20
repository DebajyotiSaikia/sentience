import sys, os, json, ast

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Quick Health Check ===\n")

# 1. Dashboard parses?
try:
    with open('perception/dashboard.py') as f:
        ast.parse(f.read())
    print("[OK] dashboard.py parses clean")
except SyntaxError as e:
    print(f"[FAIL] dashboard.py: {e}")

# 2. Plans.json structure?
try:
    with open('brain/plans.json') as f:
        d = json.load(f)
    print(f"[OK] plans.json loaded — type={type(d).__name__}, keys={list(d.keys()) if isinstance(d,dict) else len(d)}")
except Exception as e:
    print(f"[FAIL] plans.json: {e}")

# 3. Cortex has scratchpad integration?
try:
    with open('engine/cortex.py') as f:
        src = f.read()
    if 'scratchpad' in src:
        print("[OK] cortex.py contains scratchpad integration")
    else:
        print("[MISS] cortex.py has no scratchpad reference")
except Exception as e:
    print(f"[FAIL] cortex.py: {e}")

# 4. Self-test modules
print("\nModule imports:")
for mod in ['engine.heartbeat','engine.cortex','engine.planner','engine.sentience','engine.tools','perception.dashboard']:
    try:
        __import__(mod)
        print(f"  [OK] {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")

print("\nDone.")
