"""Read compose_response from web/chat.py and print it."""
lines = open('web/chat.py').readlines()
for i, line in enumerate(lines[329:616], start=330):
    print(f'{i}: {line}', end='')