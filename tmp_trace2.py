import sys; sys.path.insert(0, '/workspace')

# 1. Full talk.py - especially build_talk_page and its JavaScript
with open('/workspace/web/talk.py') as f:
    content = f.read()
print(f"=== talk.py ({len(content)} chars) ===")
# Show the build function and JS
idx = content.find('def build_talk_page')
if idx >= 0:
    print(content[idx:idx+4000])
else:
    print("build_talk_page not found!")
    print(content[-3000:])

# 2. user_talk.py - how messages get stored and responses generated
print("\n\n=== user_talk.py ===")
with open('/workspace/engine/user_talk.py') as f:
    ut = f.read()
print(f"({len(ut)} chars)")
print(ut[:4000])