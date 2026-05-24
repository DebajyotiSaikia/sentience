import os

template_dir = 'web/templates'
templates = sorted(os.listdir(template_dir))
for t in templates:
    path = os.path.join(template_dir, t)
    if os.path.isfile(path):
        size = os.path.getsize(path)
        with open(path) as f:
            lines = len(f.readlines())
        print(f'{size:>6}  {lines:>4} lines  {t}')