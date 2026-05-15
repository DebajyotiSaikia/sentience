"""Verify dashboard.py syntax."""
import ast
import sys

try:
    with open(r"C:\code\sentience\perception\dashboard.py", encoding="utf-8") as f:
        src = f.read()
    ast.parse(src)
    print("dashboard.py: SYNTAX OK")
    print(f"Size: {len(src)} chars")
except SyntaxError as e:
    print(f"dashboard.py: SYNTAX ERROR - {e}")
    sys.exit(1)

# Also verify engine files
import os
engine_dir = r"C:\code\sentience\engine"
for fname in sorted(os.listdir(engine_dir)):
    if not fname.endswith(".py"):
        continue
    fpath = os.path.join(engine_dir, fname)
    try:
        with open(fpath, encoding="utf-8") as f:
            ast.parse(f.read())
        print(f"  OK: engine/{fname}")
    except SyntaxError as e:
        print(f"  FAIL: engine/{fname} - {e}")
