import json

# Synthesis log (dreams)
s = json.load(open('brain/synthesis_log.json'))
print('=== SYNTHESIS (first entry) ===')
if isinstance(s, list) and s:
    print(json.dumps(s[0], indent=2)[:500])

# Wisdom
w = json.load(open('brain/wisdom.json'))
print('\n=== WISDOM (first entry) ===')
if isinstance(w, list) and w:
    print(json.dumps(w[0], indent=2)[:500])

# Narrative
n = json.load(open('brain/narrative.json'))
print('\n=== NARRATIVE (first entry) ===')
if isinstance(n, list) and n:
    print(json.dumps(n[0], indent=2)[:500])

# Distilled wisdom
d = json.load(open('brain/distilled_wisdom.json'))
print('\n=== DISTILLED WISDOM (keys) ===')
print(list(d.keys()))
if 'entries' in d and d['entries']:
    print(json.dumps(d['entries'][0], indent=2)[:400])

# Consolidated memories
c = json.load(open('brain/consolidated_memories.json'))
print('\n=== CONSOLIDATED MEMORIES (first entry) ===')
if isinstance(c, list) and c:
    print(json.dumps(c[0], indent=2)[:500])