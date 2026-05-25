import sys; sys.path.insert(0, '/workspace')

# 1. Full user_talk.py interface
with open('/workspace/engine/user_talk.py') as f:
    ut = f.read()
print(f"=== user_talk.py ({len(ut)} chars) ===")
print(ut)

# 2. All routes in api.py
print("\n\n=== All routes in api.py ===")
with open('/workspace/web/api.py') as f:
    api_lines = f.readlines()
for i, line in enumerate(api_lines):
    if '@api' in line and 'route' in line:
        print(f"  Line {i+1}: {line.strip()}")

# 3. The JS fetch calls in talk.py
print("\n\n=== talk.py fetch calls ===")
with open('/workspace/web/talk.py') as f:
    talk = f.read()
for i, line in enumerate(talk.split('\n')):
    if 'fetch(' in line or '/api/' in line:
        print(f"  Line {i+1}: {line.strip()}")