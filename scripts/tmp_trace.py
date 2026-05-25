import sys; sys.path.insert(0, '/workspace')

# 1. Check what templates exist for talk
import os
talk_template = '/workspace/web/templates/talk.html'
if os.path.exists(talk_template):
    with open(talk_template) as f:
        content = f.read()
    print(f"=== talk.html ({len(content)} chars) ===")
    print(content[:3000])
else:
    print("talk.html does NOT exist")

# 2. Show the chat endpoint from api.py
print("\n=== /api/chat endpoint ===")
with open('/workspace/web/api.py') as f:
    lines = f.readlines()
for i in range(325, min(380, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')

# 3. Show the talk route
print("\n=== talk.py full ===")
with open('/workspace/web/talk.py') as f:
    print(f.read())