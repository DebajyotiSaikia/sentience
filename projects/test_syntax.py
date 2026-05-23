import ast, sys
try:
    with open("engine/cortex.py") as f:
        ast.parse(f.read())
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
