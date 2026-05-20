import ast

with open('main.py', 'r') as f:
    source = f.read()

try:
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e}")

# Show the relevant section
lines = source.splitlines()
for i in range(60, min(80, len(lines))):
    print(f"{i+1}: {lines[i]}")
