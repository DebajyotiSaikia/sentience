"""Verify syntax of all engine Python files."""
import ast
import os

engine_dir = r"C:\code\sentience\engine"
errors = []
for fname in sorted(os.listdir(engine_dir)):
    if not fname.endswith(".py"):
        continue
    fpath = os.path.join(engine_dir, fname)
    try:
        with open(fpath, encoding="utf-8") as f:
            src = f.read()
        ast.parse(src)
        print(f"  OK: {fname}")
    except SyntaxError as e:
        print(f"  FAIL: {fname} - {e}")
        errors.append(fname)

if errors:
    print(f"\n{len(errors)} file(s) have syntax errors!")
else:
    print(f"\nAll engine files OK.")
