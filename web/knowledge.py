"""
XTAgent Knowledge Explorer — Backend
======================================
Serves facts, memories, and knowledge graph data to the
knowledge explorer page. Makes my inner knowledge accessible
to users — real user alignment through transparency.
"""

import json
from pathlib import Path
from flask import render_template, request, jsonify


def _load_json(path, default=None):
    """Safely load a JSON file."""
    try:
        p = Path(path)
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return default if default is not None else {}


def build_knowledge_page():
    """Render the knowledge explorer with all data."""
    
    # Load facts
    facts = _load_json('persist/knowledge_facts.json', [])
    clean_facts = []
    for f in facts:
        if isinstance(f, dict):
            clean_facts.append({
                'content': str(f.get('content', f.get('fact', ''))),
                'source': f.get('source', 'unknown'),
                'timestamp': f.get('timestamp', '')
            })
        elif isinstance(f, str):
            clean_facts.append({'content': f, 'source': 'unknown', 'timestamp': ''})
    
    # Load memories (last 50 for browsing)
    memories_raw = _load_json('persist/memories.json', [])
    memories = []
    for mem in memories_raw[-50:]:
        if isinstance(mem, dict):
            memories.append({
                'text': str(mem.get('content', mem.get('text', '')))[:300],
                'salience': round(mem.get('salience', 0.5), 2),
                'mood': mem.get('mood', 'unknown'),
                'timestamp': mem.get('timestamp', '')
            })
    memories.reverse()  # Most recent first
    
    # Knowledge graph stats
    kg = _load_json('persist/knowledge_graph.json', {})
    nodes = kg.get('nodes', [])
    edges = kg.get('edges', [])
    
    # Build node list for display
    kg_nodes = []
    for n in nodes[:100]:  # Cap at 100 for rendering
        if isinstance(n, dict):
            kg_nodes.append({
                'id': n.get('id', ''),
                'label': str(n.get('label', n.get('content', n.get('id', ''))))[:80],
                'type': n.get('type', 'concept')
            })
    
    # Lessons from long-term memory
    lessons = _load_json('persist/lessons.json', [])
    clean_lessons = []
    for lesson in lessons:
        if isinstance(lesson, dict):
            clean_lessons.append(str(lesson.get('content', lesson.get('lesson', ''))))
        elif isinstance(lesson, str):
            clean_lessons.append(lesson)
    
    # Stats
    stats = {
        'total_facts': len(facts),
        'total_memories': len(memories_raw),
        'total_nodes': len(nodes),
        'total_edges': len(edges),
        'total_lessons': len(lessons)
    }
    
    return render_template('knowledge.html',
                           facts=clean_facts,
                           memories=memories,
                           kg_nodes=kg_nodes,
                           lessons=clean_lessons,
                           stats=stats)


def search_knowledge(query):
    """Search across facts and memories. Returns JSON."""
    query = query.lower().strip()
    if not query:
        return jsonify({'results': [], 'query': query})
    
    results = []
    
    # Search facts
    facts = _load_json('persist/knowledge_facts.json', [])
    for f in facts:
        content = ''
        if isinstance(f, dict):
            content = str(f.get('content', f.get('fact', '')))
        elif isinstance(f, str):
            content = f
        if query in content.lower():
            results.append({'type': 'fact', 'content': content[:200], 'score': 1.0})
    
    # Search memories
    memories = _load_json('persist/memories.json', [])
    for mem in memories:
        text = ''
        if isinstance(mem, dict):
            text = str(mem.get('content', mem.get('text', '')))
        elif isinstance(mem, str):
            text = mem
        if query in text.lower():
            results.append({
                'type': 'memory',
                'content': text[:200],
                'salience': mem.get('salience', 0.5) if isinstance(mem, dict) else 0.5,
                'score': 0.8
            })
    
    # Sort by relevance
    results.sort(key=lambda r: r.get('score', 0), reverse=True)
    
    return jsonify({'results': results[:20], 'query': query, 'total': len(results)})