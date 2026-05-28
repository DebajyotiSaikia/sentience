"""Find where build_response_guidance ends so we can add the missing return."""
import ast

with open('engine/response_shaper.py') as f:
    source = f.read()

tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'build_response_guidance':
        print(f'Function: lines {node.lineno}-{node.end_lineno}')
        has_return = False
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                has_return = True
                print(f'  Return at line {child.lineno}')
        if not has_return:
            print('  NO RETURN STATEMENT FOUND')
        # Print last 3 lines of the function
        lines = source.split('\n')
        for i in range(max(node.end_lineno - 4, node.lineno), node.end_lineno):
            print(f'  {i+1}| {lines[i]}')