import ast, sys

files = [
    "engine/heartbeat.py",
    "engine/express.py", 
    "engine/reflect.py",
    "engine/tools.py",
    "perception/dashboard.py",
    "main.py",
]

ok = 0
for f in files:
    try:
        with open(f, encoding="utf-8") as fh:
            ast.parse(fh.read())
        print(f"  OK  {f}")
        ok += 1
    except SyntaxError as e:
        print(f"  FAIL {f}: {e}")
    except FileNotFoundError:
        print(f"  SKIP {f} (not found)")

print(f"\n{ok}/{len(files)} files valid")
