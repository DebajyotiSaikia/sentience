"""Find and fix non-ASCII characters in chat_response.py"""
import re

path = 'engine/chat_response.py'
with open(path, 'r') as f:
    lines = f.readlines()

replacements = {
    '\u2014': '-',   # em dash
    '\u2013': '-',   # en dash
    '\u201c': '"',   # left double quote
    '\u201d': '"',   # right double quote
    '\u2018': "'",   # left single quote
    '\u2019': "'",   # right single quote
    '\u2026': '...', # ellipsis
}

changed = []
for i, line in enumerate(lines, 1):
    original = line
    for old, new in replacements.items():
        if old in line:
            line = line.replace(old, new)
            changed.append((i, repr(original.rstrip()), repr(line.rstrip())))
    lines[i-1] = line

if changed:
    print(f"Found {len(changed)} lines with non-ASCII chars:")
    for lineno, old, new in changed:
        print(f"  Line {lineno}: {old}")
        print(f"       -> {new}")
    
    with open(path, 'w') as f:
        f.writelines(lines)
    print(f"\nFixed and saved {path}")
else:
    print("No non-ASCII characters found")

# Verify syntax
import ast
try:
    ast.parse(open(path).read())
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")