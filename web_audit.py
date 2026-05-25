import ast, os

results = {}
for fname in sorted(os.listdir('web')):
    if not fname.endswith('.py'):
        continue
    fpath = os.path.join('web', fname)
    try:
        tree = ast.parse(open(fpath).read())
    except:
        continue
    
    bp_name = None
    routes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and hasattr(node, 'func'):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'Blueprint':
                if node.args:
                    bp_name = ast.literal_eval(node.args[0]) if isinstance(node.args[0], ast.Constant) else '?'
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and hasattr(dec, 'func'):
                    if isinstance(dec.func, ast.Attribute) and dec.func.attr == 'route':
                        if dec.args:
                            try:
                                routes.append(ast.literal_eval(dec.args[0]))
                            except:
                                routes.append('?')
    if bp_name or routes:
        results[fname] = {'blueprint': bp_name, 'routes': routes}

# Show route map
for fname, info in results.items():
    print(f"\n{fname} (bp={info['blueprint']}):")
    for r in info['routes']:
        print(f"  {r}")

# Find duplicates
from collections import Counter
all_routes = []
for info in results.values():
    all_routes.extend(info['routes'])
dupes = {r: c for r, c in Counter(all_routes).items() if c > 1}
if dupes:
    print("\n=== DUPLICATE ROUTES ===")
    for route, count in sorted(dupes.items()):
        print(f"  {route} ({count}x) defined in:")
        for fname, info in results.items():
            if route in info['routes']:
                print(f"    - {fname}")