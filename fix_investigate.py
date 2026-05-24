import os, json

# 1. Timeline - what route does it register?
print("=== TIMELINE ===")
with open('web/timeline.py') as f:
    content = f.read()
    # Find route decorators
    for i, line in enumerate(content.split('\n')):
        if '@' in line and 'route' in line:
            print(f"  Line {i+1}: {line.strip()}")
        if 'Blueprint' in line:
            print(f"  Line {i+1}: {line.strip()}")

# 2. About-me 
print("\n=== ABOUT-ME ===")
with open('web/about_me.py') as f:
    content = f.read()
    for i, line in enumerate(content.split('\n')):
        if '@' in line and 'route' in line:
            print(f"  Line {i+1}: {line.strip()}")
        if 'Blueprint' in line:
            print(f"  Line {i+1}: {line.strip()}")

# 3. Chat
print("\n=== CHAT ===")
with open('web/chat.py') as f:
    content = f.read()
    for i, line in enumerate(content.split('\n')):
        if '@' in line and 'route' in line:
            print(f"  Line {i+1}: {line.strip()}")
        if 'Blueprint' in line:
            print(f"  Line {i+1}: {line.strip()}")

# 4. Check persist/state.json
print("\n=== PERSIST STATE ===")
state_path = 'persist/state.json'
if os.path.exists(state_path):
    with open(state_path) as f:
        d = json.load(f)
        print(f"  Keys: {list(d.keys())}")
        if 'emotions' in d:
            print(f"  Emotions: {d['emotions']}")
else:
    print("  MISSING")

# 5. List persist dir
print("\n=== PERSIST FILES ===")
for f in sorted(os.listdir('persist')):
    size = os.path.getsize(f'persist/{f}')
    print(f"  {f}: {size} bytes")

# 6. Check what API endpoints exist
print("\n=== API ===")
with open('web/api.py') as f:
    content = f.read()
    for i, line in enumerate(content.split('\n')):
        if '@' in line and 'route' in line:
            print(f"  Line {i+1}: {line.strip()}")