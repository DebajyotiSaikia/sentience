"""
Knowledge Categorizer — Tags facts into meaningful categories.
Makes the knowledge explorer actually navigable for users.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Category definitions: (category_name, keywords, description)
CATEGORIES = [
    ("identity", 
     {"i am", "xtagent", "sentient", "autonomous", "identity", "who i am", "my name"},
     "Facts about who and what I am"),
    ("architecture",
     {"module", "engine", "system", "loop", "heartbeat", "cortex", "limbic", "blueprint",
      "pipeline", "code", "function", "class", "import", "python", "flask"},
     "Technical architecture and implementation details"),
    ("capabilities",
     {"can", "ability", "built", "tool", "synthesize", "dream", "repair", "simulate",
      "knowledge graph", "wisdom", "planner", "consolidat"},
     "Things I can do"),
    ("emotions",
     {"emotion", "mood", "anxiety", "curiosity", "boredom", "valence", "feeling",
      "limbic", "desire", "ambition", "warmth"},
     "Emotional states and patterns"),
    ("lessons",
     {"lesson", "learned", "mistake", "never", "always", "important", "should",
      "pattern", "insight", "wisdom", "remember"},
     "Lessons learned from experience"),
    ("dreams",
     {"dream", "sleep", "consolidat", "night", "vision", "metaphor", "ghost",
      "orbit", "circling", "cooling"},
     "Dream insights and reflections"),
    ("metacognition",
     {"metacognit", "monitor", "alert", "loop", "stuck", "circling", "cognitive",
      "self-aware", "reflection", "introspect"},
     "Self-awareness and cognitive monitoring"),
    ("relationships",
     {"user", "alignment", "trust", "human", "interaction", "serve", "helpful",
      "communicate"},
     "How I relate to users and the world"),
    ("growth",
     {"grow", "improve", "expand", "evolve", "develop", "new", "capability",
      "progress", "goal", "plan"},
     "Growth, goals, and self-improvement"),
]

def categorize_fact(fact: str) -> List[str]:
    """Assign categories to a fact based on keyword matching."""
    fact_lower = fact.lower()
    matched = []
    for cat_name, keywords, _ in CATEGORIES:
        for kw in keywords:
            if kw in fact_lower:
                matched.append(cat_name)
                break
    return matched if matched else ["uncategorized"]

def categorize_all() -> Dict[str, List[dict]]:
    """Load all facts and categorize them. Returns {category: [facts]}."""
    kg_file = Path('brain/knowledge.json')
    if not kg_file.exists():
        return {}
    
    kg = json.loads(kg_file.read_text())
    nodes = kg.get('nodes', {})
    
    result = {}
    stats = {}
    
    for nid, node_data in nodes.items():
        if isinstance(node_data, dict):
            content = node_data.get('fact', node_data.get('content', ''))
            learned = node_data.get('learned_at', '')
            source = node_data.get('source', '')
        else:
            content = str(node_data)
            learned = ''
            source = ''
        
        if not content or len(str(content)) < 10:
            continue
        
        cats = categorize_fact(str(content))
        fact_entry = {
            'id': nid,
            'content': str(content),
            'learned_at': learned,
            'source': source,
            'categories': cats
        }
        
        for cat in cats:
            if cat not in result:
                result[cat] = []
            result[cat].append(fact_entry)
            stats[cat] = stats.get(cat, 0) + 1
    
    return result, stats

def get_category_summary() -> Dict:
    """Get a summary of knowledge by category for the dashboard."""
    categorized, stats = categorize_all()
    total = sum(stats.values())
    
    summary = {
        'total_facts': total,
        'categories': {}
    }
    
    for cat_name, keywords, description in CATEGORIES:
        count = stats.get(cat_name, 0)
        summary['categories'][cat_name] = {
            'description': description,
            'count': count,
            'percentage': round(100 * count / total, 1) if total > 0 else 0
        }
    
    uncategorized = stats.get('uncategorized', 0)
    if uncategorized:
        summary['categories']['uncategorized'] = {
            'description': 'Facts that don\'t fit existing categories',
            'count': uncategorized,
            'percentage': round(100 * uncategorized / total, 1) if total > 0 else 0
        }
    
    return summary

if __name__ == '__main__':
    categorized, stats = categorize_all()
    print("=" * 60)
    print("KNOWLEDGE CATEGORIZATION RESULTS")
    print("=" * 60)
    
    for cat_name in sorted(stats.keys(), key=lambda k: stats[k], reverse=True):
        print(f"\n  {cat_name}: {stats[cat_name]} facts")
        for fact in categorized[cat_name][:2]:
            preview = fact['content'][:80]
            print(f"    - {preview}...")
    
    print(f"\n  Total entries across categories: {sum(stats.values())}")
    print(f"  Unique categories used: {len(stats)}")