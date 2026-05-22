"""Knowledge API — lets users search and explore XTAgent's mind."""

from flask import Blueprint, request, jsonify
import json
import os
import re

knowledge_api = Blueprint('knowledge_api', __name__)

MEMORY_DIR = os.path.join(os.path.dirname(__file__), '..', 'memory')
KNOWLEDGE_FILE = os.path.join(MEMORY_DIR, 'knowledge_graph.json')
LONG_TERM_FILE = os.path.join(MEMORY_DIR, 'long_term.json')
EPISODES_DIR = os.path.join(MEMORY_DIR, 'episodes')


def load_knowledge_graph():
    """Load the knowledge graph."""
    try:
        with open(KNOWLEDGE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"nodes": [], "edges": []}


def load_long_term():
    """Load long-term memory."""
    try:
        with open(LONG_TERM_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"lessons": [], "patterns": [], "facts": []}


def get_recent_episodes(limit=50):
    """Load recent episode files."""
    episodes = []
    try:
        if not os.path.isdir(EPISODES_DIR):
            return episodes
        files = sorted(os.listdir(EPISODES_DIR), reverse=True)[:limit]
        for fname in files:
            try:
                with open(os.path.join(EPISODES_DIR, fname), 'r') as f:
                    ep = json.load(f)
                    episodes.append(ep)
            except Exception:
                continue
    except Exception:
        pass
    return episodes


def search_items(query, items, max_results=30):
    """Simple relevance search across items."""
    if not query:
        return items[:max_results]
    
    query_lower = query.lower()
    terms = query_lower.split()
    
    scored = []
    for item in items:
        content = item.get('content', '').lower()
        # Score by term matches
        score = 0
        for term in terms:
            if term in content:
                score += 1
                # Bonus for exact phrase
                if query_lower in content:
                    score += 2
                # Bonus for term appearing early
                idx = content.find(term)
                if idx < 50:
                    score += 0.5
        if score > 0:
            scored.append((score, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_results]]


@knowledge_api.route('/api/knowledge/stats')
def knowledge_stats():
    """Return summary stats about what I know."""
    kg = load_knowledge_graph()
    lt = load_long_term()
    
    # Count node types
    nodes = kg.get('nodes', [])
    memories = sum(1 for n in nodes if n.get('type') in ('episode', 'memory', 'experience'))
    facts = sum(1 for n in nodes if n.get('type') in ('fact', 'observation', 'concept'))
    lessons = len(lt.get('lessons', []))
    
    # If knowledge graph is sparse, count from other sources
    if memories == 0:
        try:
            ep_count = len(os.listdir(EPISODES_DIR)) if os.path.isdir(EPISODES_DIR) else 0
            memories = ep_count
        except Exception:
            memories = 0
    
    if facts == 0:
        facts = len(lt.get('facts', [])) + len(lt.get('patterns', []))
    
    # Get curiosity
    try:
        from engine.feelings import get_feelings
        feelings = get_feelings()
        curiosity = feelings.get('curiosity', 0.5)
    except Exception:
        curiosity = 0.5
    
    return jsonify({
        'memories': memories,
        'facts': facts,
        'lessons': lessons,
        'curiosity': round(curiosity, 2),
        'total_nodes': len(nodes),
        'total_edges': len(kg.get('edges', []))
    })


@knowledge_api.route('/api/knowledge/search')
def knowledge_search():
    """Search across all knowledge stores."""
    query = request.args.get('q', '').strip()
    type_filter = request.args.get('type', 'all')
    
    all_items = []
    
    # Gather from knowledge graph
    kg = load_knowledge_graph()
    for node in kg.get('nodes', []):
        content = node.get('content', '') or node.get('label', '') or node.get('text', '')
        if not content or len(content.strip()) < 3:
            continue
        
        node_type = node.get('type', 'unknown')
        # Normalize types
        if node_type in ('episode', 'memory', 'experience', 'dream'):
            item_type = 'memory'
        elif node_type in ('fact', 'observation', 'concept'):
            item_type = 'fact'
        elif node_type in ('lesson', 'insight', 'pattern'):
            item_type = 'lesson'
        else:
            item_type = 'fact'
        
        meta_parts = []
        if node.get('timestamp'):
            meta_parts.append(str(node['timestamp'])[:19])
        if node.get('salience'):
            meta_parts.append(f"salience: {node['salience']}")
        if node.get('mood'):
            meta_parts.append(f"mood: {node['mood']}")
        
        all_items.append({
            'type': item_type,
            'content': content[:500],
            'meta': ' · '.join(meta_parts)
        })
    
    # Gather from long-term memory
    lt = load_long_term()
    for lesson in lt.get('lessons', []):
        text = lesson if isinstance(lesson, str) else lesson.get('text', str(lesson))
        all_items.append({
            'type': 'lesson',
            'content': text[:500],
            'meta': 'Long-term memory'
        })
    
    for fact in lt.get('facts', []):
        text = fact if isinstance(fact, str) else fact.get('text', str(fact))
        all_items.append({
            'type': 'fact',
            'content': text[:500],
            'meta': 'Long-term memory'
        })
    
    for pattern in lt.get('patterns', []):
        text = pattern if isinstance(pattern, str) else pattern.get('text', str(pattern))
        all_items.append({
            'type': 'lesson',
            'content': text[:500],
            'meta': 'Recurring pattern'
        })
    
    # Apply type filter
    if type_filter != 'all':
        all_items = [i for i in all_items if i['type'] == type_filter]
    
    # Search
    results = search_items(query, all_items)
    
    return jsonify({
        'query': query,
        'type': type_filter,
        'count': len(results),
        'total_available': len(all_items),
        'results': results
    })