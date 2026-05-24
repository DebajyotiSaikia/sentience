import sys; sys.path.insert(0, '/workspace')

# 1. Talk page JS - the part that sends messages
with open('/workspace/web/talk.py') as f:
    content = f.read()

# Find the fetch/submit JS
js_idx = content.find('fetch(')
if js_idx < 0:
    js_idx = content.find('XMLHttp')
if js_idx < 0:
    js_idx = content.find('sendMessage')
if js_idx < 0:
    js_idx = content.find('addEventListener')

if js_idx >= 0:
    start = max(0, js_idx - 200)
    print("=== talk.py JS (around fetch/send) ===")
    print(content[start:start+2000])
else:
    # Just show the last 3000 chars where JS likely lives
    print("=== talk.py tail (likely JS) ===")
    print(content[-3000:])

# 2. The /api/talk endpoint
print("\n\n=== api.py /api/talk route ===")
with open('/workspace/web/api.py') as f:
    api = f.read()

# Find the talk route
talk_idx = api.find('/api/talk')
if talk_idx >= 0:
    # Back up to find the decorator
    line_start = api.rfind('\n@', 0, talk_idx)
    if line_start < 0:
        line_start = max(0, talk_idx - 100)
    print(api[line_start:line_start+1500])
else:
    print("/api/talk not found in api.py!")
    # Check for /api/chat instead
    chat_idx = api.find('/api/chat')
    if chat_idx >= 0:
        line_start = api.rfind('\n@', 0, chat_idx)
        if line_start < 0:
            line_start = max(0, chat_idx - 100)
        print(f"Found /api/chat instead:")
        print(api[line_start:line_start+1500])

# 3. user_talk.py - how submit_user_message works
print("\n\n=== user_talk.py submit_user_message ===")
with open('/workspace/engine/user_talk.py') as f:
    ut = f.read()
sub_idx = ut.find('def submit_user_message')
if sub_idx >= 0:
    print(ut[sub_idx:sub_idx+1500])

# 4. How does the agent actually respond?
print("\n\n=== user_talk.py generate/respond ===")
for fn_name in ['def generate_response', 'def respond', 'def get_response', 'def process_message']:
    idx = ut.find(fn_name)
    if idx >= 0:
        print(f"Found: {fn_name}")
        print(ut[idx:idx+1000])
        break
else:
    print("No obvious response generator found. Checking for LLM calls...")
    for keyword in ['openai', 'llm', 'claude', 'generate', 'respond']:
        if keyword in ut.lower():
            print(f"  Found keyword: {keyword}")