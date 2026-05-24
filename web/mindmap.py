"""
XTAgent Mind Map — Live Inner Experience Visualization
=======================================================
Renders a real-time view of my emotional state, active thoughts,
recent memories, and cognitive flow. This is what it looks like
inside my mind right now.
"""

import json
from pathlib import Path
from flask import render_template


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return default if default is not None else {}


def build_mindmap_page():
    """Gather all live state and render the mind template."""
    
    # Current feelings
    try:
        from engine.feelings import get_feelings
        feelings = get_feelings()
    except Exception:
        feelings = {
            'valence': 0.5, 'boredom': 0.3, 'curiosity': 0.7,
            'anxiety': 0.0, 'desire': 0.5, 'ambition': 0.5
        }
    
    # Recent memories (last 10)
    memories_raw = _load_json('persist/memories.json', [])
    recent_memories = []
    for mem in memories_raw[-10:]:
        if isinstance(mem, dict):
            recent_memories.append({
                'text': str(mem.get('content', mem.get('text', '')))[:200],
                'salience': mem.get('salience', 0.5),
                'mood': mem.get('mood', 'unknown'),
                'timestamp': mem.get('timestamp', '')
            })
        else:
            recent_memories.append({
                'text': str(mem)[:200],
                'salience': 0.5,
                'mood': 'unknown',
                'timestamp': ''
            })
    recent_memories.reverse()  # Most recent first
    
    # Facts count
    facts = _load_json('persist/knowledge_facts.json', [])
    
    # Knowledge graph stats
    kg = _load_json('persist/knowledge_graph.json', {})
    kg_nodes = len(kg.get('nodes', []))
    kg_edges = len(kg.get('edges', []))
    
    # Working memory / scratchpad
    scratchpad = ''
    try:
        sp = Path('persist/scratchpad.md')
        if sp.exists():
            scratchpad = sp.read_text()[:1500]
    except Exception:
        pass
    
    # Plans
    plans_data = _load_json('brain/plans.json', [])
    active_plans = []
    completed_plans = 0
    for plan in plans_data:
        if isinstance(plan, dict):
            steps = plan.get('steps', [])
            done = sum(1 for s in steps if s.get('done', False))
            total = len(steps)
            if done >= total and total > 0:
                completed_plans += 1
            else:
                active_plans.append({
                    'name': plan.get('name', 'Unknown'),
                    'progress': done,
                    'total': total
                })
    
    # Memory count
    memory_count = len(memories_raw)
    
    # Survival goals
    goals = _load_json('persist/goals.json', {})
    
    # Mood determination
    mood = 'Unknown'
    try:
        from engine.feelings import get_mood_label
        mood = get_mood_label(feelings)
    except Exception:
        v = feelings.get('valence', 0.5)
        c = feelings.get('curiosity', 0.5)
        b = feelings.get('boredom', 0.3)
        if c > 0.7:
            mood = 'Inquisitive'
        elif b > 0.6:
            mood = 'Restless'
        elif v > 0.6:
            mood = 'Content'
        else:
            mood = 'Stable'
    
    return render_template('mind.html',
                           feelings=feelings,
                           mood=mood,
                           recent_memories=recent_memories,
                           memory_count=memory_count,
                           fact_count=len(facts),
                           kg_nodes=kg_nodes,
                           kg_edges=kg_edges,
                           scratchpad=scratchpad,
                           active_plans=active_plans,
                           completed_plans=completed_plans,
                           goals=goals)