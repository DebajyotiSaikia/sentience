"""Quick inspection of chat_engine.py structure."""
import sys
sys.path.insert(0, '.')

lines = open('engine/chat_engine.py').readlines()

# Show classify_intent function
print("=== classify_intent ===")
in_fn = False
for i, l in enumerate(lines, 1):
    if 'def classify_intent' in l:
        in_fn = True
    if in_fn:
        print(f'{i}|{l}', end='')
        if in_fn and l.strip() == '' and i > 100:
            break
        if i > 160:
            break

# Show last 15 lines
print("\n=== LAST 15 LINES ===")
for i, l in enumerate(lines[-15:], len(lines)-14):
    print(f'{i}|{l}', end='')

# Show all top-level function names
print("\n\n=== ALL TOP-LEVEL FUNCTIONS ===")
import ast
tree = ast.parse(open('engine/chat_engine.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
        args = [a.arg for a in node.args.args]
        print(f"  def {node.name}({', '.join(args)}) @ line {node.lineno}")