import ast

# Parse the knowledge explorer and find all routes
tree = ast.parse(open('web/knowledge_explorer.py').read())
routes = []
functions = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        functions.append(node.name)
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and hasattr(dec.func, 'attr') and dec.func.attr == 'route':
                if dec.args:
                    route_path = dec.args[0].value if hasattr(dec.args[0], 'value') else str(dec.args[0])
                    routes.append((route_path, node.name))

print("=== Routes in knowledge_explorer.py ===")
for path, fn in routes:
    print(f"  {path} -> {fn}()")

print(f"\n=== All functions ({len(functions)}) ===")
for f in functions:
    print(f"  {f}")

# Check if /ask route exists
ask_routes = [r for r in routes if 'ask' in r[0]]
if ask_routes:
    print("\n✅ /ask route exists!")
else:
    print("\n❌ No /ask route found — need to add it")

# Check if the file even parses cleanly
print("\n✅ File parses without syntax errors")