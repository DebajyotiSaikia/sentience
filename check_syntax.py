import ast
try:
    ast.parse(open('web/app.py').read())
    print('OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
    print(f'Text: {e.text}')