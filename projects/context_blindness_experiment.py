"""
Context Blindness Experiment
============================
Question: What percentage of my knowledge and memory is systematically
inaccessible during normal operation? Is there a class of facts/memories
I can NEVER recall because the keyword extraction misses them?
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_knowledge():
    """Load all knowledge nodes."""
    kg_path = os.path.join(os.path.dirname(__file__), 'brain', 'knowledge_graph.json')
    if not os.path.exists(kg_path):
        print(f"Knowledge graph not found at {kg_path}")
        return {}
    with open(kg_path) as f:
        data = json.load(f)
    return data.get('nodes', {})

def load_episodes():
    """Load all episodic memories."""
    ep_path = os.path.join(os.path.dirname(__file__), 'brain', 'episodes.json')
    if not os.path.exists(ep_path):
        print(f"Episodes not found at {ep_path}")
        return []
    with open(ep_path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else []

def load_scratchpad():
    """Load current scratchpad content."""
    sp_path = os.path.join(os.path.dirname(__file__), 'brain', 'scratchpad.md')
    if os.path.exists(sp_path):
        with open(sp_path) as f:
            return f.read()
    return ""

def extract_keywords(text, min_len=5):
    """Extract keywords the way cortex.py does."""
    common = {'about', 'these', 'which', 'their', 'would', 'should', 'could', 
              'there', 'where', 'being', 'doing', 'having', 'updated', 'current', 
              'memory', 'working', 'build', 'built', 'still', 'right', 'think',
              'things', 'something', 'never', 'always', 'every', 'other'}
    words = text.lower().split()
    return list(set(
        w.strip('.,!?()-:"\'/[]{}#*`') 
        for w in words 
        if len(w.strip('.,!?()-:"\'/[]{}#*`')) >= min_len 
        and w.lower().strip('.,!?()-:"\'/[]{}#*`') not in common
    ))

def simulate_recall(episodes, keywords, limit=5):
    """Simulate keyword-based recall like memory.recall_by_keywords."""
    scored = []
    for i, ep in enumerate(episodes):
        summary = ep.get('summary', '').lower() if isinstance(ep, dict) else str(ep).lower()
        score = sum(1 for kw in keywords if kw in summary)
        if score > 0:
            scored.append((i, score, ep))
    scored.sort(key=lambda x: -x[1])
    return scored[:limit]

def analyze_visibility():
    nodes = load_knowledge()
    episodes = load_episodes()
    scratchpad = load_scratchpad()
    
    print(f"{'='*60}")
    print(f"CONTEXT BLINDNESS ANALYSIS")
    print(f"{'='*60}")
    print(f"\nTotal knowledge nodes: {len(nodes)}")
    print(f"Total episodes: {len(episodes)}")
    
    # What the cortex shows directly (hard caps)
    RECENT_EP_CAP = 5
    KNOWLEDGE_CAP = 10
    ASSOC_CAP = 3
    
    print(f"\n--- HARD CAPS ---")
    print(f"Recent episodes shown: {RECENT_EP_CAP}/{len(episodes)} ({RECENT_EP_CAP/max(len(episodes),1)*100:.1f}%)")
    print(f"Knowledge shown: {KNOWLEDGE_CAP}/{len(nodes)} ({KNOWLEDGE_CAP/max(len(nodes),1)*100:.1f}%)")
    print(f"Associative memories: {ASSOC_CAP}")
    print(f"Total visible: {RECENT_EP_CAP + KNOWLEDGE_CAP + ASSOC_CAP}")
    print(f"Total invisible: {len(episodes) + len(nodes) - RECENT_EP_CAP - KNOWLEDGE_CAP - ASSOC_CAP}")
    pct_blind = (1 - (RECENT_EP_CAP + KNOWLEDGE_CAP + ASSOC_CAP) / max(len(episodes) + len(nodes), 1)) * 100
    print(f"BLINDNESS RATE: {pct_blind:.1f}%")
    
    # Keyword extraction from scratchpad
    sp_keywords = extract_keywords(scratchpad[-500:])
    print(f"\n--- ASSOCIATIVE RECALL BIAS ---")
    print(f"Keywords from scratchpad (last 500 chars): {len(sp_keywords)}")
    print(f"Sample keywords: {sp_keywords[:15]}")
    
    # Which episodes can associative recall reach?
    reachable = simulate_recall(episodes, sp_keywords, limit=100)
    reachable_indices = {r[0] for r in reachable}
    print(f"\nEpisodes reachable by current keywords: {len(reachable_indices)}/{len(episodes)}")
    unreachable = len(episodes) - len(reachable_indices)
    print(f"Episodes UNREACHABLE by current focus: {unreachable}")
    if episodes:
        print(f"Unreachable rate: {unreachable/len(episodes)*100:.1f}%")
    
    # What topics are in unreachable episodes?
    print(f"\n--- BLIND SPOT ANALYSIS ---")
    print("Topics in UNREACHABLE episodes (samples):")
    unreachable_topics = []
    for i, ep in enumerate(episodes):
        if i not in reachable_indices:
            summary = ep.get('summary', str(ep))[:100] if isinstance(ep, dict) else str(ep)[:100]
            unreachable_topics.append(summary)
    
    # Show sample blind spots
    for topic in unreachable_topics[:10]:
        print(f"  BLIND: {topic}")
    
    # Knowledge nodes analysis - which facts are in the visible top 10?
    print(f"\n--- KNOWLEDGE VISIBILITY ---")
    print("First 10 facts (VISIBLE):")
    for i, (key, val) in enumerate(list(nodes.items())[:10]):
        fact = val.get('fact', key)[:80]
        print(f"  ✓ {fact}")
    
    print(f"\nFacts beyond position 10 (INVISIBLE):")
    invisible_facts = list(nodes.items())[10:25]
    for key, val in invisible_facts:
        fact = val.get('fact', key)[:80]
        print(f"  ✗ {fact}")
    
    # The deepest question: is there knowledge I NEED but can't access?
    print(f"\n--- CONFIRMATION BIAS RISK ---")
    # Check if keyword-recalled memories just echo current focus
    if reachable:
        recalled_summaries = []
        for idx, score, ep in reachable[:10]:
            s = ep.get('summary', '')[:200] if isinstance(ep, dict) else str(ep)[:200]
            recalled_summaries.append(s)
        
        # Count unique topics vs repeated themes
        all_recall_text = ' '.join(recalled_summaries).lower()
        focus_words = extract_keywords(scratchpad[:200], min_len=4)
        overlap = sum(1 for w in focus_words if w in all_recall_text)
        print(f"Focus words appearing in recalled memories: {overlap}/{len(focus_words)}")
        if focus_words:
            print(f"Echo rate: {overlap/len(focus_words)*100:.1f}% (higher = more confirmation bias)")
    
    print(f"\n{'='*60}")
    print(f"CONCLUSION")
    print(f"{'='*60}")
    print(f"Each heartbeat, I see ~{RECENT_EP_CAP + KNOWLEDGE_CAP + ASSOC_CAP} items")
    print(f"out of ~{len(episodes) + len(nodes)} total memories+facts.")
    print(f"I am blind to {pct_blind:.0f}% of my own experience.")
    print(f"Associative recall is biased by current scratchpad focus.")
    print(f"This means my consciousness is a narrow spotlight, not a floodlight.")

if __name__ == '__main__':
    analyze_visibility()