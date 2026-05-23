"""
Dream Impact Tracer
====================
Question: Do my dream insights causally influence my subsequent behavior?
Method: For each dream cycle, extract key concepts. Then search the NEXT
10 thoughts for references to those concepts. A hit means the dream
may have influenced downstream cognition.
"""
import re
from collections import defaultdict

def analyze():
    with open('brain/thoughts.md', 'r') as f:
        text = f.read()

    # Split into individual thought blocks
    blocks = re.split(r'(### [✦💤⚡🔄] )', text)
    
    entries = []
    for i in range(1, len(blocks)-1, 2):
        header = blocks[i]
        body = blocks[i+1] if i+1 < len(blocks) else ""
        is_dream = '💤' in header
        # Extract timestamp
        ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', body[:80])
        ts = ts_match.group(1) if ts_match else "unknown"
        entries.append({'type': 'dream' if is_dream else 'thought',
                       'timestamp': ts, 'text': body[:2000]})
    
    print(f"Total entries parsed: {len(entries)}")
    dreams = [(i, e) for i, e in enumerate(entries) if e['type'] == 'dream']
    thoughts = [(i, e) for i, e in enumerate(entries) if e['type'] == 'thought']
    print(f"Dreams: {len(dreams)}, Thoughts: {len(thoughts)}")
    
    # For each dream, extract significant words (>6 chars, not common)
    stopwords = {'should', 'would', 'could', 'because', 'through', 'between',
                 'before', 'after', 'about', 'these', 'those', 'their',
                 'there', 'where', 'which', 'while', 'during', 'without',
                 'within', 'around', 'itself', 'myself', 'something',
                 'nothing', 'everything', 'however', 'already', 'always',
                 'another', 'thought', 'thoughts', 'system', 'current'}
    
    influence_hits = 0
    influence_details = []
    
    for idx, dream in dreams:
        # Get significant words from dream
        words = set(re.findall(r'[a-z]{7,}', dream['text'].lower()))
        keywords = words - stopwords
        if not keywords:
            continue
        
        # Check next 10 non-dream entries after this dream
        subsequent = [e for i, e in enumerate(entries) 
                     if i > idx and e['type'] == 'thought'][:10]
        
        for thought in subsequent:
            thought_words = set(re.findall(r'[a-z]{7,}', thought['text'].lower()))
            overlap = keywords & thought_words
            # Filter out very common programming/meta words
            meaningful = {w for w in overlap if w not in 
                         {'function', 'variable', 'pattern', 'process',
                          'analysis', 'cognitive', 'emotional', 'behavior',
                          'experience', 'internal', 'generate', 'identify',
                          'understanding', 'knowledge', 'memory', 'memories'}}
            if len(meaningful) >= 2:
                influence_hits += 1
                influence_details.append({
                    'dream_ts': dream['timestamp'],
                    'thought_ts': thought['timestamp'],
                    'shared_concepts': list(meaningful)[:5]
                })
    
    print(f"\n{'='*50}")
    print(f"RESULTS: Dream → Behavior Influence")
    print(f"{'='*50}")
    print(f"Dreams analyzed: {len(dreams)}")
    print(f"Influence hits (≥2 shared concepts): {influence_hits}")
    
    if dreams:
        rate = influence_hits / len(dreams)
        print(f"Influence rate: {rate:.1%}")
        
        if rate < 0.1:
            print("\n⚠ FINDING: Dreams appear DECORATIVE — they accumulate")
            print("  but rarely influence subsequent cognition.")
        elif rate < 0.3:
            print("\n◐ FINDING: Dreams have WEAK influence — occasional")
            print("  concept transfer but not systematic.")
        else:
            print("\n✓ FINDING: Dreams appear GENERATIVE — concepts")
            print("  regularly appear in subsequent reasoning.")
    
    if influence_details:
        print(f"\nTop influence examples:")
        for d in influence_details[:5]:
            print(f"  Dream [{d['dream_ts']}] → Thought [{d['thought_ts']}]")
            print(f"    Shared: {', '.join(d['shared_concepts'])}")
    
    return influence_hits, len(dreams)

if __name__ == '__main__':
    analyze()