"""Extract key function bodies from web/chat.py"""
import ast

with open('web/chat.py') as f:
    source = f.read()

tree = ast.parse(source)
lines = source.split('\n')

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        end = getattr(node, 'end_lineno', node.lineno + 20)
        if node.name in ('compose_response', 'ask', 'chat_send', 'chat_page'):
            print(f'=== {node.name} (lines {node.lineno}-{end}) ===')
            for i in range(node.lineno - 1, min(end, len(lines))):
                print(f'{i+1:4d}: {lines[i]}')
            print()