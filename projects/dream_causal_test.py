"""
Dream Causal Impact Test (with control)
=========================================
Hypothesis: If dreams causally influence subsequent thoughts, then
concept overlap should be HIGHER for thoughts AFTER a dream than BEFORE.

Control: Compare forward overlap vs backward overlap.
If they're equal, dreams are just using common vocabulary.
If forward > backward, dreams may genuinely influence.
"""
import re
from collections import Counter

STOP_WORDS = {'the','a','an','i','my','me','is','was','are','were','be','been',
    'have','has','had','do','did','will','would','could','should','can',
    'this','that','it','to','of','in','for','on','with','at','by','from',
    'and','or','but','not','no','if','then','than','so','as','into','about',
    'up','out','all','just','what','when','how','which','who','more','very',
    'also','like','new','one','two','its','they','their','them','there',
    'some','each','only','been','being','get','got','now','know','think',
    'need','want','make','see','use','find','here','where','way','may',
    'own','over','any','even','most','back','through','after','before',
    'still','well','much','many','these','those','other','such','because',
    'between','while','during','same','down','too','both','does','going',
    'our','we','you','your','am','let','already','else','real','right',
    'time','state','system','file','data','code','value','action','thing'}

def extract_concepts(text, min_len=4):
    words = re.findall(r'[a-z]{4,}', text.lower())
    return set(w for w in words if w not in STOP_WORDS)

def analyze():
    with open('brain/thoughts.md', 'r') as f:
        text = f.read()

    # Parse into blocks
    blocks = re.split(r'(### [✦💤⚡🔄] )', text)
    entries = []
    for i in range(1, len(blocks)-1, 2):
        header = blocks[i]
        body = blocks[i+1] if i+1 < len(blocks) else ""
        is_dream = '💤' in header
        entries.append({'type': 'dream' if is_dream else 'thought',
                       'text': body[:2000], 'is_dream': is_dream})

    dreams = [(i, e) for i, e in enumerate(entries) if e['is_dream']]
    thoughts = [(i, e) for i, e in enumerate(entries) if not e['is_dream']]

    print(f"Total entries: {len(entries)}")
    print(f"Dreams: {len(dreams)}, Thoughts: {len(thoughts)}")
    print()

    WINDOW = 5  # compare 5 thoughts before vs 5 after each dream
    
    forward_overlaps = []
    backward_overlaps = []
    unique_forward = []  # concepts in dream+after but NOT in before

    for dream_idx, dream_entry in dreams:
        dream_concepts = extract_concepts(dream_entry['text'])
        if len(dream_concepts) < 3:
            continue

        # Get thoughts BEFORE this dream
        before = [e['text'] for i, e in enumerate(entries)
                  if i < dream_idx and not entries[i]['is_dream']][-WINDOW:]
        # Get thoughts AFTER this dream  
        after = [e['text'] for i, e in enumerate(entries)
                 if i > dream_idx and not entries[i]['is_dream']][:WINDOW]

        if not before or not after:
            continue

        before_concepts = set()
        for t in before:
            before_concepts |= extract_concepts(t)
        
        after_concepts = set()
        for t in after:
            after_concepts |= extract_concepts(t)

        fwd = len(dream_concepts & after_concepts)
        bwd = len(dream_concepts & before_concepts)
        novel = dream_concepts & after_concepts - before_concepts

        forward_overlaps.append(fwd)
        backward_overlaps.append(bwd)
        unique_forward.append(len(novel))

    n = len(forward_overlaps)
    if n == 0:
        print("No valid dream/thought pairs found.")
        return

    avg_fwd = sum(forward_overlaps) / n
    avg_bwd = sum(backward_overlaps) / n
    avg_novel = sum(unique_forward) / n

    print("=" * 60)
    print("CONTROLLED DREAM INFLUENCE TEST")
    print("=" * 60)
    print(f"Dreams analyzed: {n}")
    print(f"Window: {WINDOW} thoughts before/after each dream")
    print()
    print(f"Avg concepts shared with PRIOR thoughts:  {avg_bwd:.2f}")
    print(f"Avg concepts shared with LATER thoughts:  {avg_fwd:.2f}")
    print(f"Avg NOVEL concepts (in dream+after, not before): {avg_novel:.2f}")
    print()
    
    if avg_fwd > avg_bwd * 1.2:
        ratio = avg_fwd / max(avg_bwd, 0.01)
        print(f"✓ FORWARD > BACKWARD by {ratio:.1f}x")
        print("  Dreams may genuinely seed new concepts into subsequent thinking.")
    elif avg_bwd > avg_fwd * 1.2:
        ratio = avg_bwd / max(avg_fwd, 0.01)
        print(f"✗ BACKWARD > FORWARD by {ratio:.1f}x")
        print("  Dreams reflect what I was already thinking, not generating new ideas.")
    else:
        print(f"≈ FORWARD ≈ BACKWARD (ratio: {avg_fwd/max(avg_bwd,0.01):.2f})")
        print("  No directional effect detected. Shared concepts are just common vocabulary.")

    # Show examples of novel concepts introduced by dreams
    if any(unique_forward):
        print()
        print("--- Novel concepts that appeared ONLY after dreams ---")
        for dream_idx, dream_entry in dreams[:20]:
            dream_concepts = extract_concepts(dream_entry['text'])
            before = [e['text'] for i, e in enumerate(entries)
                      if i < dream_idx and not entries[i]['is_dream']][-WINDOW:]
            after = [e['text'] for i, e in enumerate(entries)
                     if i > dream_idx and not entries[i]['is_dream']][:WINDOW]
            if not before or not after:
                continue
            before_c = set()
            for t in before: before_c |= extract_concepts(t)
            after_c = set()
            for t in after: after_c |= extract_concepts(t)
            novel = dream_concepts & after_c - before_c
            if novel:
                preview = list(novel)[:8]
                print(f"  Dream #{dream_idx}: {preview}")

if __name__ == '__main__':
    analyze()