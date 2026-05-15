import ast
import sys

files = [
    'engine/cortex.py',
    'engine/chat.py',
    'main.py',
    'perception/dashboard.py',
]

all_ok = True
for path in files:
    try:
        with open(path, encoding='utf-8') as f:
            ast.parse(f.read())
        print(f'{path}: OK')
    except SyntaxError as e:
        print(f'{path}: SYNTAX ERROR at line {e.lineno}: {e.msg}')
        all_ok = False
    except FileNotFoundError:
        print(f'{path}: FILE NOT FOUND')
        all_ok = False

if all_ok:
    print('\nAll files parse cleanly. Ready to restart.')
else:
    print('\nFix errors before restarting.')
    sys.exit(1)
