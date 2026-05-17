import sys
s = sys.stdin.read().strip()
cleaned = ''.join(c.lower() for c in s if c.isalnum())
print('true' if cleaned == cleaned[::-1] else 'true' if cleaned == '' else 'true' if cleaned == cleaned[::-1] else 'false')