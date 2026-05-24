import re, os

for fname in ['web/knowledge_explorer.py', 'web/knowledge_api.py', 'web/mind_explorer.py', 'web/api.py']:
    if os.path.exists(fname):
        content = open(fname).read()
        routes = re.findall(r'@\w+\.route\([\'\"](.*?)[\'\"](.*?)\)', content)
        bp = re.findall(r'Blueprint\([\'\"](.*?)[\'\"](.*?)\)', content)
        print(f'\n=== {fname} ===')
        if bp:
            print(f'  Blueprint: {bp[0][0]}')
        for r in routes:
            print(f'  route: {r[0]}')
        
        # Also show which blueprints are registered in app.py
        
if os.path.exists('web/app.py'):
    content = open('web/app.py').read()
    regs = re.findall(r'register_blueprint\((.*?)\)', content)
    print(f'\n=== Blueprint registrations in app.py ===')
    for r in regs:
        print(f'  {r}')