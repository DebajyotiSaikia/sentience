import json, os, sys

# 1. Check what knowledge files exist
files = [f for f in os.listdir('persist') if 'knowledge' in f.lower()]
print('Knowledge files:', files)

for f in files:
    path = os.path.join('persist', f)
    try:
        data = json.load(open(path))
        if isinstance(data, dict):
            print(f'\n{f}: {len(data)} entries, type=dict')
            sample_keys = list(data.keys())[:3]
            for k in sample_keys:
                v = data[k]
                print(f'  {k}: {type(v).__name__} = {str(v)[:100]}')
        elif isinstance(data, list):
            print(f'\n{f}: {len(data)} entries, type=list')
            if data:
                print(f'  sample: {str(data[0])[:120]}')
    except Exception as e:
        print(f'{f}: error={e}')

# 2. Now test the search function
print('\n--- Testing search ---')
sys.path.insert(0, '.')
try:
    from engine.knowledge_search import search_knowledge
    # Load the knowledge store data first
    ks_path = 'persist/knowledge_store.json'
    if os.path.exists(ks_path):
        knowledge_data = json.load(open(ks_path))
        print(f'Loaded knowledge_store.json: type={type(knowledge_data).__name__}, len={len(knowledge_data)}')
        results = search_knowledge(knowledge_data, 'dream')
        print(f'search_knowledge(data, "dream") returned {len(results)} results')
        for r in results[:3]:
            print(f'  {str(r)[:120]}')
    else:
        print(f'No {ks_path} found')
except Exception as e:
    print(f'search_knowledge error: {e}')
    import traceback
    traceback.print_exc()

# 3. Try loading from the knowledge store directly
print('\n--- Direct knowledge store check ---')
try:
    from engine.knowledge import KnowledgeStore
    ks = KnowledgeStore()
    all_facts = ks.facts if hasattr(ks, 'facts') else []
    print(f'KnowledgeStore has {len(all_facts)} facts')
    dream_facts = [f for f in all_facts if 'dream' in str(f).lower()]
    print(f'Facts containing "dream": {len(dream_facts)}')
    for df in dream_facts[:3]:
        print(f'  {str(df)[:120]}')
except Exception as e:
    print(f'KnowledgeStore error: {e}')
    import traceback
    traceback.print_exc()