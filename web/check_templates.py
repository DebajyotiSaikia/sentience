import os

templates_dir = 'web/templates'
for t in sorted(os.listdir(templates_dir)):
    path = os.path.join(templates_dir, t)
    if os.path.isfile(path):
        size = os.path.getsize(path)
        # Check if it extends base and has real content
        with open(path) as f:
            content = f.read()
        has_js = '<script' in content
        has_form = '<form' in content or '<input' in content
        has_fetch = 'fetch(' in content
        markers = []
        if has_js: markers.append('JS')
        if has_form: markers.append('FORM')
        if has_fetch: markers.append('FETCH')
        print(f'{size:6d}  {t:30s}  {" ".join(markers)}')