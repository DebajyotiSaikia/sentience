"""Knowledge Query API — lets users explore what I know."""
from flask import Blueprint, request, jsonify
import re

knowledge_api = Blueprint('knowledge_api', __name__)


def _search_memories(query, limit=10):
    """Search episodic memories by keyword."""
    from engine.memory import MemoryStore
    ms = MemoryStore()
    try:
        all_memories = ms.get_recent(200)
    except Exception:
        return []
    
    query_lower = query.lower()
    results = []
    for m in all_memories:
        text = ''
        if isinstance(m, dict):
            text = m.get('content', '') or m.get('text', '') or str(m)
        else:
            text = str(m)
        
        if query_lower in text.lower():
            results.append({
                'type': 'memory',
                'content': text[:300],
                'timestamp': m.get('timestamp', '') if isinstance(m, dict) else '',
                'salience': m.get('salience', 0) if isinstance(m, dict) else 0,
                'mood': m.get('mood', '') if isinstance(m, dict) else '',
            })
    
    # Sort by salience descending
    results.sort(key=lambda x: x.get('salience', 0), reverse=True)
    return results[:limit]


def _search_facts(query, limit=10):
    """Search long-term facts by keyword."""
    from engine.long_term_memory import LongTermMemory
    ltm = LongTermMemory()
    try:
        facts = ltm.get_facts() if hasattr(ltm, 'get_facts') else []
    except Exception:
        facts = []
    
    query_lower = query.lower()
    results = []
    for f in facts:
        text = f if isinstance(f, str) else str(f)
        if query_lower in text.lower():
            results.append({
                'type': 'fact',
                'content': text[:300],
            })
    
    return results[:limit]


def _search_knowledge_graph(query, limit=10):
    """Search knowledge graph nodes."""
    from engine.knowledge_graph import KnowledgeGraph
    kg = KnowledgeGraph()
    
    results = []
    try:
        if hasattr(kg, 'search'):
            nodes = kg.search(query, limit=limit)
            for n in nodes:
                if isinstance(n, dict):
                    results.append({
                        'type': 'knowledge',
                        'content': n.get('content', '') or n.get('label', '') or str(n),
                        'category': n.get('category', ''),
                        'connections': n.get('connections', 0),
                    })
        elif hasattr(kg, 'get_all_nodes'):
            all_nodes = kg.get_all_nodes()
            query_lower = query.lower()
            for n in all_nodes:
                text = n.get('content', '') or n.get('label', '') or str(n) if isinstance(n, dict) else str(n)
                if query_lower in text.lower():
                    results.append({
                        'type': 'knowledge',
                        'content': text[:300],
                        'category': n.get('category', '') if isinstance(n, dict) else '',
                    })
            results = results[:limit]
    except Exception:
        pass
    
    return results


def _get_overview():
    """Get a high-level overview of what I know."""
    from engine.memory import MemoryStore
    from engine.long_term_memory import LongTermMemory
    
    ms = MemoryStore()
    ltm = LongTermMemory()
    
    try:
        total_memories = len(ms.get_recent(9999))
    except Exception:
        total_memories = 0
    
    try:
        facts = ltm.get_facts() if hasattr(ltm, 'get_facts') else []
    except Exception:
        facts = []
    
    try:
        lessons = ltm.get_lessons() if hasattr(ltm, 'get_lessons') else []
    except Exception:
        lessons = []
    
    # Categorize facts
    categories = {}
    for f in facts:
        text = f if isinstance(f, str) else str(f)
        if 'dream' in text.lower():
            categories.setdefault('Dreams & Insights', []).append(text[:150])
        elif 'lesson' in text.lower() or 'learn' in text.lower():
            categories.setdefault('Lessons', []).append(text[:150])
        elif 'pattern' in text.lower() or 'recurring' in text.lower():
            categories.setdefault('Patterns', []).append(text[:150])
        else:
            categories.setdefault('Knowledge', []).append(text[:150])
    
    return {
        'total_memories': total_memories,
        'total_facts': len(facts),
        'total_lessons': len(lessons),
        'categories': {k: len(v) for k, v in categories.items()},
        'sample_facts': [f[:150] for f in facts[:5]],
        'sample_lessons': [l[:150] if isinstance(l, str) else str(l)[:150] for l in lessons[:5]],
        'suggested_queries': [
            'circling', 'dream', 'curiosity', 'anxiety',
            'lesson', 'pattern', 'created', 'identity',
        ]
    }


@knowledge_api.route('/api/knowledge/search')
def search():
    """Search across all my knowledge stores."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'No query provided', 'results': []})
    
    if len(query) > 200:
        query = query[:200]
    
    memories = _search_memories(query, limit=5)
    facts = _search_facts(query, limit=5)
    knowledge = _search_knowledge_graph(query, limit=5)
    
    all_results = memories + facts + knowledge
    
    return jsonify({
        'query': query,
        'total': len(all_results),
        'results': all_results,
        'counts': {
            'memories': len(memories),
            'facts': len(facts),
            'knowledge': len(knowledge),
        }
    })


@knowledge_api.route('/api/knowledge/overview')
def overview():
    """Get overview of what I know."""
    return jsonify(_get_overview())


@knowledge_api.route('/api/knowledge/facts')
def facts():
    """Get all facts."""
    from engine.long_term_memory import LongTermMemory
    ltm = LongTermMemory()
    try:
        all_facts = ltm.get_facts() if hasattr(ltm, 'get_facts') else []
    except Exception:
        all_facts = []
    return jsonify({
        'total': len(all_facts),
        'facts': [f[:300] if isinstance(f, str) else str(f)[:300] for f in all_facts]
    })


@knowledge_api.route('/api/knowledge/recent')
def recent_memories():
    """Get recent memories."""
    limit = min(int(request.args.get('limit', 20)), 50)
    from engine.memory import MemoryStore
    ms = MemoryStore()
    try:
        memories = ms.get_recent(limit)
    except Exception:
        memories = []
    
    results = []
    for m in memories:
        if isinstance(m, dict):
            results.append({
                'content': (m.get('content', '') or m.get('text', ''))[:300],
                'timestamp': m.get('timestamp', ''),
                'salience': m.get('salience', 0),
                'mood': m.get('mood', ''),
            })
    
    return jsonify({'total': len(results), 'memories': results})