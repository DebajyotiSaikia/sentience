import ast, sys

files = ["engine/cortex.py", "engine/knowledge_synthesis.py"]
all_ok = True
for f in files:
    try:
        with open(f) as fh:
            ast.parse(fh.read())
        print(f"  OK  {f}")
    except SyntaxError as e:
        print(f"  ERR {f}: {e}")
        all_ok = False
    except FileNotFoundError:
        print(f"  MISSING {f}")
        all_ok = False

# Test import
try:
    from engine import knowledge_synthesis as ks
    funcs = [x for x in dir(ks) if not x.startswith("_")]
    print(f"\nImport OK. Available: {funcs}")
except Exception as e:
    print(f"\nImport FAILED: {e}")
    all_ok = False

if all_ok:
    print("\nAll checks passed!")
else:
    print("\nSome checks failed!")
    sys.exit(1)
