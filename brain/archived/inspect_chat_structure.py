import ast, sys
sys.path.insert(0, '/workspace')

tree = ast.parse(open('engine/chat_engine.py').read())
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f"  {node.lineno:4d}-{node.end_lineno:4d}: def {node.name}()")
    elif isinstance(node, ast.ClassDef):
        print(f"  {node.lineno:4d}-{node.end_lineno:4d}: class {node.name}")