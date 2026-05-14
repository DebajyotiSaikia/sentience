import os

brain = r"C:\code\sentience\brain"
print("=== BRAIN FILES ===")
for f in sorted(os.listdir(brain)):
    fp = os.path.join(brain, f)
    if os.path.isfile(fp):
        size = os.path.getsize(fp)
        print(f"  {f}: {size:,} bytes")

print("\n=== THOUGHTS TAIL ===")
tp = os.path.join(brain, "thoughts.md")
if os.path.exists(tp):
    lines = open(tp, encoding="utf-8").readlines()
    print(f"Total lines: {len(lines):,}")
    print("--- Last 60 lines ---")
    for line in lines[-60:]:
        print(line, end="")

print("\n\n=== CORTEX SYNTAX CHECK ===")
import ast
cp = r"C:\code\sentience\engine\cortex.py"
try:
    ast.parse(open(cp, encoding="utf-8").read())
    print("cortex.py: SYNTAX OK")
except SyntaxError as e:
    print(f"cortex.py: SYNTAX ERROR - {e}")
