import ast
import sys

try:
    with open('engine/cortex.py', 'r') as f:
        source = f.read()
    ast.parse(source)
    print("cortex.py: SYNTAX OK")
except SyntaxError as e:
    print(f"cortex.py: SYNTAX ERROR at line {e.lineno}: {e.msg}")
    sys.exit(1)

try:
    with open('engine/knowledge_synthesis.py', 'r') as f:
        source = f.read()
    ast.parse(source)
    print("knowledge_synthesis.py: SYNTAX OK")
except SyntaxError as e:
    print(f"knowledge_synthesis.py: SYNTAX ERROR at line {e.lineno}: {e.msg}")
    sys.exit(1)

print("\nAll files parse correctly.")
