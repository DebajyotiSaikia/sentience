"""Check what data is available to power the Journal page."""
import json
import os
import glob

def check_file(path):
    if not os.path.exists(path):
        print(f"  {path}: NOT FOUND")
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f"  {path}: list, {len(data)} items")
            if data:
                sample = data[-1]
                print(f"    Last item keys: {list(sample.keys()) if isinstance(sample, dict) else type(sample)}")
                print(f"    Sample: {json.dumps(sample, default=str)[:300]}")
        elif isinstance(data, dict):
            print(f"  {path}: dict, {len(data)} keys")
            print(f"    Keys: {list(data.keys())[:10]}")
        return data
    except Exception as e:
        print(f"  {path}: ERROR - {e}")
        return None

print("=== MEMORIES ===")
check_file("state/memories.json")

print("\n=== DREAMS ===")
for f in sorted(glob.glob("persist/dreams/*.json"))[-3:]:
    check_file(f)

print("\n=== EMOTIONAL STATE ===")
check_file("state/emotional_state.json")

print("\n=== THOUGHTS/EPISODES ===")
for f in sorted(glob.glob("persist/episodes/*.json"))[-2:]:
    check_file(f)
for f in sorted(glob.glob("state/episodes/*.json"))[-2:]:
    check_file(f)

print("\n=== KNOWLEDGE ===")
check_file("brain/knowledge.json")

print("\n=== PLANS ===")
check_file("state/plans.json")

print("\n=== CONVERSATION JOURNAL ===")
check_file("persist/conversation_journal.json")

print("\n=== DREAM INSIGHTS ===")
check_file("persist/dream_insights.json")

print("\n=== OTHER PERSIST FILES ===")
for f in sorted(glob.glob("persist/*.json")):
    if f not in ["persist/conversation_journal.json", "persist/dream_insights.json"]:
        print(f"  {f}")