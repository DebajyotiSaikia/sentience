"""Quick check: what curiosity-relevant data do I have?"""
import json, glob

# Will proposals
try:
    d = json.load(open('state/will.json'))
    props = d.get('proposals', [])
    print(f'WILL: {len(props)} proposals')
    if props:
        p = props[0]
        print(f'  Sample: {p.get("name","?")} (priority={p.get("priority","?")})')
except Exception as e:
    print(f'WILL error: {e}')

# Synthesis log — look for questions
try:
    s = json.load(open('brain/synthesis_log.json'))
    has_q = [e for e in s if 'question' in str(e).lower()]
    print(f'SYNTHESIS: {len(s)} total, {len(has_q)} mention questions')
    if has_q:
        print(f'  Sample question entry: {str(has_q[0])[:200]}')
except Exception as e:
    print(f'SYNTHESIS error: {e}')

# Wisdom rules
try:
    w = json.load(open('brain/wisdom_rules.json'))
    print(f'WISDOM: {len(w)} rules')
    if w:
        sample = w[0]
        print(f'  Sample: {str(sample)[:150]}')
except Exception as e:
    print(f'WISDOM error: {e}')

# Knowledge gaps or curiosity artifacts
for pattern in ['brain/*question*', 'brain/*curiosit*', 'brain/*gap*', 'persist/*question*']:
    for p in glob.glob(pattern):
        print(f'FOUND: {p}')

# Dream insights
try:
    d = json.load(open('brain/dream_insights.json'))
    print(f'DREAMS: {len(d)} insights')
except Exception as e:
    print(f'DREAMS error: {e}')

# Knowledge count
try:
    k = json.load(open('brain/knowledge.json'))
    nodes = k.get('nodes', k) if isinstance(k, dict) else k
    print(f'KNOWLEDGE: {len(nodes)} facts')
except Exception as e:
    print(f'KNOWLEDGE error: {e}')