import json, os

print('--- Testing API handler logic ---')
from web.knowledge_api import knowledge_api_bp
print('Blueprint imported successfully')

# Check the paths it uses
from web import knowledge_api
print(f'API KNOWLEDGE_PATH: {knowledge_api.KNOWLEDGE_PATH}')
print(f'API MEMORIES_PATH: {knowledge_api.MEMORIES_PATH}')
print(f'Knowledge file exists: {os.path.exists(knowledge_api.KNOWLEDGE_PATH)}')
print(f'Memories file exists: {os.path.exists(knowledge_api.MEMORIES_PATH)}')

# Now simulate what the handler does when loading knowledge
kpath = knowledge_api.KNOWLEDGE_PATH
with open(kpath) as f:
    kdata = json.load(f)

nodes = kdata.get('nodes', {})
edges = kdata.get('edges', [])

# Check how the API formats nodes for the response
if isinstance(nodes, dict):
    facts = [{'id': k, 'fact': v.get('fact', ''), 'learned_at': v.get('learned_at', '')} 
             for k, v in nodes.items()]
else:
    facts = nodes

print(f'Formatted facts count: {len(facts)}')
print(f'Sample fact: {facts[0]}')
print(f'Edges count: {len(edges)}')

# Check memories
mpath = knowledge_api.MEMORIES_PATH
with open(mpath) as f:
    mdata = json.load(f)
print(f'Memories count: {len(mdata)}')
print(f'Sample memory keys: {list(mdata[0].keys())}')

print('\n--- ALL CHECKS PASSED ---')