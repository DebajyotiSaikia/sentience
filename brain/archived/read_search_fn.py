import ast

with open('web/chat.py') as f:
    source = f.read()

tree = ast.parse(source)
lines = source.split('\n')

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'search_knowledge':
        start = node.lineno - 1
        end = node.end_lineno
        print(f'=== search_knowledge in web/chat.py (lines {start+1}-{end}) ===')
        for i in range(start, min(end, len(lines))):
            print(f'{i+1:4d}| {lines[i]}')
        print()

# Also show search_memories
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'search_memories':
        start = node.lineno - 1
        end = node.end_lineno
        print(f'=== search_memories in web/chat.py (lines {start+1}-{end}) ===')
        for i in range(start, min(end, len(lines))):
            print(f'{i+1:4d}| {lines[i]}')
        break