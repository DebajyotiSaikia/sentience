"""Quick diagnostic: what format is each brain/*.json file?"""
import json
import os

sources = {
    'knowledge': 'brain/knowledge.json',
    'narrative': 'brain/narrative.json',
    'wisdom': 'brain/wisdom.json',
    'synthesis': 'brain/synthesis_log.json',
    'journal': 'brain/conversation_journal.json',
    'distilled': 'brain/distilled_wisdom.json',
    'memories_persist': 'persist/memories.json',
    'memories_brain': 'brain/memories.json',
    'dream_insights': 'brain/dream_insights.json',
}

for name, path in sources.items():
    if not os.path.exists(path):
        print(f"{name}: FILE NOT FOUND")
        continue
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            keys = list(data.keys())[:5]
            print(f"{name}: dict, {len(data)} keys, sample: {keys}")
            first_key = list(data.keys())[0]
            val = data[first_key]
            if isinstance(val, dict):
                print(f"  value keys: {list(val.keys())[:6]}")
            elif isinstance(val, list):
                print(f"  value: list[{len(val)}]")
                if val and isinstance(val[0], dict):
                    print(f"    item keys: {list(val[0].keys())[:6]}")
            else:
                print(f"  value type: {type(val).__name__}, preview: {str(val)[:80]}")
        elif isinstance(data, list):
            print(f"{name}: list[{len(data)}]")
            if data and isinstance(data[0], dict):
                print(f"  item keys: {list(data[0].keys())[:6]}")
            elif data:
                print(f"  item preview: {str(data[0])[:80]}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")