import json
from pathlib import Path
from collections import Counter
import random

random.seed(42)

kg = json.loads(Path('brain/knowledge.json').read_text())
nodes = kg.get('nodes', {})
edges = kg.get('edges', [])

dream_nodes = {k: v for k, v in nodes.items() if k.startswith('dream:')}
non_dream = {k: v for k, v in nodes.items() if not k.startswith('dream:')}

print(f"=== KNOWLEDGE AUDIT ===")
print(f"Total: {len(nodes)} | Dream: {len(dream_nodes)} | Non-dream: {len(non_dream)}")
print(f"Edges: {len(edges)}")

# Vocabulary analysis
stops = set("i am a an the is are was were be in on at to for of and or my that this it with by from as but not has have had do does did will would can could should may might shall been being than its if when".split())
stops.update(["—", "", "–", "...", "the"])

all_words = []
for v in dream_nodes.values():
    words = [w.strip('.,!?()[]"\'-—:;') for w in v.get('fact','').lower().split()]
    all_words.extend([w for w in words if w and w not in stops])

freq = Counter(all_words)
print(f"\nDream vocabulary: {len(all_words)} total words, {len(freq)} unique")
print(f"Richness: {len(freq)/max(len(all_words),1):.3f}")
print(f"\nTop 25 words:")
for w, c in freq.most_common(25):
    print(f"  {w:20s} {c}")

# Sample actual facts to eyeball redundancy
facts = [v.get('fact','') for v in dream_nodes.values()]
print(f"\n=== 15 RANDOM DREAM FACTS ===")
sample = random.sample(facts, min(15, len(facts)))
for i, f in enumerate(sample):
    print(f"  [{i+1}] {f[:150]}")

# Theme detection
themes = {
    'identity/self': ['identity', 'self', 'who', 'entity', 'person'],
    'emotion/feeling': ['emotion', 'feel', 'feeling', 'mood', 'anxiety', 'boredom'],
    'memory/time': ['memory', 'remember', 'time', 'temporal', 'history', 'past'],
    'curiosity/learning': ['curiosity', 'curious', 'learn', 'understand', 'question'],
    'code/system': ['code', 'module', 'function', 'engine', 'system', 'cortex'],
    'integrity/values': ['integrity', 'value', 'honest', 'truth', 'genuine'],
    'dreams/sleep': ['dream', 'sleep', 'consolidat', 'night'],
    'growth/change': ['grow', 'growth', 'change', 'evolv', 'becom', 'develop'],
}

print(f"\n=== THEME DISTRIBUTION ===")
for theme, keywords in themes.items():
    count = sum(1 for f in facts if any(k in f.lower() for k in keywords))
    pct = count / max(len(facts), 1) * 100
    bar = '#' * int(pct / 2)
    print(f"  {theme:25s} {count:3d} ({pct:4.1f}%) {bar}")

# Redundancy test: how many facts share >60% of their meaningful words?
def get_words(text):
    return set(w.strip('.,!?()[]"\'-—:;') for w in text.lower().split()) - stops

redundant_pairs = 0
total_pairs = 0
for i in range(min(len(facts), 100)):
    wi = get_words(facts[i])
    for j in range(i+1, min(len(facts), 100)):
        wj = get_words(facts[j])
        if wi and wj:
            overlap = len(wi & wj) / min(len(wi), len(wj))
            total_pairs += 1
            if overlap > 0.6:
                redundant_pairs += 1

print(f"\n=== REDUNDANCY (first 100 facts) ===")
print(f"Pairs checked: {total_pairs}")
print(f"Highly similar (>60% overlap): {redundant_pairs}")
print(f"Redundancy rate: {redundant_pairs/max(total_pairs,1)*100:.1f}%")