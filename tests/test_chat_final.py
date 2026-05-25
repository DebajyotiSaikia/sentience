import sys
sys.path.insert(0, '/workspace')

from web.chat import compose_response, search_knowledge, search_memories, get_current_state

# Test 1: Search knowledge
print('=== Knowledge Search: dreams ===')
hits = search_knowledge('dreams')
print(f'Found {len(hits)} hits')
for h in hits[:3]:
    print(f'  - {h}')
print()

# Test 2: Search memories  
print('=== Memory Search: curiosity ===')
mhits = search_memories('curiosity')
print(f'Found {len(mhits)} hits')
for m in mhits[:3]:
    print(f'  - {m}')
print()

# Test 3: Get state
print('=== Current State ===')
state = get_current_state()
print(state)
print()

# Test 4: Full compose_response
print('=== Full Response: "What do you know about dreams?" ===')
response = compose_response('What do you know about dreams?')
print(response[:500] if len(response) > 500 else response)