"""Read the REST of compose_response from web/chat.py."""
lines = open('web/chat.py').readlines()
for i, line in enumerate(lines[406:616], start=407):
    print(f'{i}: {line}', end='')