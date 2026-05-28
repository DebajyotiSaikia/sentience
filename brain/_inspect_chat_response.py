import ast

with open('engine/chat_response.py') as f:
    source = f.read()

lines = source.split('\n')
print(f'Total lines: {len(lines)}')
print()

tree = ast.parse(source)
for node in ast.iter_child_nodes(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f'  func {node.name}: lines {node.lineno}-{node.end_lineno}')
    elif isinstance(node, ast.ClassDef):
        print(f'  class {node.name}: lines {node.lineno}-{node.end_lineno}')

# Show the _get_intent_guidance function
print()
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '_get_intent_guidance':
        start = node.lineno - 1
        end = node.end_lineno
        print(f'_get_intent_guidance (lines {start+1}-{end}):')
        for i in range(start, end):
            print(f'{i+1:4d}| {lines[i]}')

# Show compose_response or generate_response
print()
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in ('compose_response', 'generate_response', '_compose_grounded_response'):
        start = node.lineno - 1
        end = node.end_lineno
        print(f'{node.name} (lines {start+1}-{end}):')
        for i in range(start, end):
            print(f'{i+1:4d}| {lines[i]}')