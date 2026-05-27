"""Dump the inline routes from web/app.py so I can see what to remove."""
with open('web/app.py') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("=" * 60)
for i, line in enumerate(lines):
    if i >= 174:  # line 175 onward (0-indexed)
        print(f"{i+1}: {line}", end='')