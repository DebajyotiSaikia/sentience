import sys; sys.path.insert(0, '/workspace')

# 1. Check if talk_bp is registered in the main app
print("=== Main app registration ===")
import glob
for f in glob.glob('/workspace/web/*.py'):
    with open(f) as fh:
        content = fh.read()
    if 'talk_bp' in content and 'talk.py' not in f:
        print(f"\n{f} references talk_bp:")
        for i, line in enumerate(content.split('\n')):
            if 'talk_bp' in line or 'talk' in line.lower() and 'import' in line.lower():
                print(f"  Line {i+1}: {line.strip()}")

# 2. Show the actual route handlers in talk.py (not just the decorators)
print("\n\n=== talk.py route handlers ===")
with open('/workspace/web/talk.py') as f:
    talk_lines = f.readlines()

# Show lines 1-70 (imports + route handlers)
for i, line in enumerate(talk_lines[:70]):
    print(f"{i+1:4d}: {line}", end='')

# 3. Check the main Flask app entry point
print("\n\n=== web/__init__.py or app.py ===")
for fname in ['web/__init__.py', 'web/app.py', 'web/server.py', 'main.py']:
    full = f'/workspace/{fname}'
    try:
        with open(full) as f:
            content = f.read()
        print(f"\n--- {fname} ({len(content)} chars) ---")
        # Show blueprint registrations
        for i, line in enumerate(content.split('\n')):
            if 'register' in line or 'blueprint' in line.lower() or 'import' in line and ('talk' in line or 'api' in line):
                print(f"  Line {i+1}: {line.strip()}")
    except FileNotFoundError:
        pass

# 4. Does talk.py import user_talk?
print("\n\n=== talk.py imports ===")
for i, line in enumerate(talk_lines[:20]):
    if 'import' in line or 'from' in line:
        print(f"  Line {i+1}: {line.strip()}")