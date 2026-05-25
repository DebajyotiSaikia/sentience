"""Extract blueprint registration logic from web/app.py"""
import ast

tree = ast.parse(open('web/app.py').read())

print("=== IMPORTS ===")
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        if node.module and 'web' in (node.module or ''):
            names = [a.name + (f' as {a.asname}' if a.asname else '') for a in node.names]
            print(f"  from {node.module} import {', '.join(names)}  (line {node.lineno})")
    if isinstance(node, ast.Import):
        for alias in node.names:
            if 'web' in alias.name:
                print(f"  import {alias.name}  (line {node.lineno})")

print("\n=== REGISTER_BLUEPRINT CALLS ===")
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and hasattr(node, 'func'):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'register_blueprint':
            args = []
            for a in node.args:
                if isinstance(a, ast.Attribute):
                    args.append(f"{ast.dump(a.value)}.{a.attr}" if hasattr(a, 'attr') else '?')
                elif isinstance(a, ast.Name):
                    args.append(a.id)
                else:
                    args.append('?')
            kwargs = {kw.arg: ast.literal_eval(kw.value) if isinstance(kw.value, ast.Constant) else '?' for kw in node.keywords}
            print(f"  register_blueprint({', '.join(args)}, {kwargs})  (line {node.lineno})")

print("\n=== DIRECT ROUTE DECORATORS IN APP.PY ===")
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and hasattr(dec, 'func'):
                if isinstance(dec.func, ast.Attribute) and dec.func.attr == 'route':
                    if dec.args:
                        try:
                            route = ast.literal_eval(dec.args[0])
                            print(f"  @app.route('{route}') -> {node.name}()  (line {node.lineno})")
                        except:
                            pass

# Count total files in web/
import os
py_files = [f for f in os.listdir('web') if f.endswith('.py') and f != '__init__.py' and f != 'app.py']
print(f"\n=== SUMMARY ===")
print(f"  Total .py files in web/ (excluding app.py): {len(py_files)}")
print(f"  Files: {', '.join(sorted(py_files))}")