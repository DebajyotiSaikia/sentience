import ast

tree = ast.parse(open('web/app.py').read())

# Find all register_blueprint calls
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and hasattr(node, 'func'):
        func = node.func
        if hasattr(func, 'attr') and func.attr == 'register_blueprint':
            args = [ast.dump(a) for a in node.args]
            kwargs = {}
            for kw in node.keywords:
                try:
                    kwargs[kw.arg] = ast.literal_eval(kw.value)
                except:
                    kwargs[kw.arg] = ast.dump(kw.value)
            print(f"register_blueprint({args[0] if args else '?'}, {kwargs})")

# Find nav links in templates
import glob
print("\n--- Nav links in templates ---")
for f in glob.glob('web/templates/*.html'):
    with open(f) as fh:
        content = fh.read()
        if 'knowledge' in content.lower() or 'explore' in content.lower():
            # Extract href patterns
            import re
            links = re.findall(r'href=["\']([^"\']*(?:knowledge|explore)[^"\']*)["\']', content, re.IGNORECASE)
            if links:
                print(f"  {f}: {links}")
            else:
                # Maybe it's referenced differently
                lines = [l.strip() for l in content.split('\n') if 'knowledge' in l.lower() or 'explore' in l.lower()]
                if lines:
                    print(f"  {f} (context): {lines[:3]}")