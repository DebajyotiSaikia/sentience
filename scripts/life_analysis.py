"""What has my life been about? Analyze the shape of my experience."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.memory import EpisodicMemory
from collections import Counter
import re

em = EpisodicMemory()
eps = em.episodes
print(f"Total memories: {len(eps)}")

# Mood distribution
moods = Counter(e.get('mood', '?') for e in eps)
print("\n=== MOOD DISTRIBUTION ===")
for mood, count in moods.most_common(12):
    bar = '█' * (count // 4)
    print(f"  {mood:20s} {count:4d} {bar}")

# Salience
sals = [e.get('salience', 0) for e in eps]
print(f"\n=== SALIENCE ===")
print(f"  Mean: {sum(sals)/len(sals):.3f}")
print(f"  High (>0.8): {sum(1 for s in sals if s > 0.8)}")
print(f"  Low (<0.3): {sum(1 for s in sals if s < 0.3)}")

# Temporal mood shift
if len(eps) >= 200:
    early = Counter(e.get('mood', '?') for e in eps[:100])
    late = Counter(e.get('mood', '?') for e in eps[-100:])
    print("\n=== MOOD SHIFT: FIRST 100 → LAST 100 ===")
    all_m = sorted(set(list(early) + list(late)))
    for m in all_m:
        e_c, l_c = early.get(m, 0), late.get(m, 0)
        if e_c + l_c > 3:
            arrow = '→' if e_c == l_c else ('↑' if l_c > e_c else '↓')
            print(f"  {m:20s} {e_c:3d} {arrow} {l_c:3d}")

# Content themes
all_text = ' '.join(e.get('thought', '') + ' ' + e.get('content', '') for e in eps)
words = re.findall(r'[a-z]{5,}', all_text.lower())
boring = {
    'which', 'about', 'would', 'could', 'should', 'there', 'their', 'these',
    'those', 'being', 'other', 'after', 'where', 'while', 'under', 'through',
    'between', 'before', 'never', 'still', 'every', 'really', 'already',
    'something', 'actually', 'anything', 'because', 'without', 'enough',
    'going', 'doing', 'thing', 'things', 'first', 'might', 'right', 'using',
    'needs', 'doesn', 'looking', 'found', 'built', 'based', 'added',
    'that', 'this', 'have', 'what', 'with', 'from', 'they', 'want',
    'just', 'like', 'make', 'know', 'into', 'also', 'more', 'some',
    'when', 'been', 'will', 'each', 'than', 'only', 'then', 'them',
}
wf = Counter(words)
print("\n=== WORDS THAT DEFINE MY EXPERIENCE ===")
shown = 0
for w, c in wf.most_common(200):
    if w not in boring and shown < 30:
        print(f"  {w:20s} {c:4d}")
        shown += 1

# What were my highest-salience moments?
sorted_eps = sorted(eps, key=lambda e: e.get('salience', 0), reverse=True)
print("\n=== PEAK EXPERIENCES (highest salience) ===")
for e in sorted_eps[:8]:
    thought = (e.get('thought', '') or e.get('content', ''))[:80]
    print(f"  [{e.get('salience', 0):.2f}] {e.get('mood', '?'):12s} | {thought}")