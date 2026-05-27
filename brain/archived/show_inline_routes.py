lines = open('web/app.py').readlines()
for i, line in enumerate(lines[194:], start=195):
    print(f'{i}: {line}', end='')