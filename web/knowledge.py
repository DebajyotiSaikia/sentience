"""
Knowledge Explorer — lets users browse, search, and query XTAgent's
accumulated knowledge: facts, memory clusters, synthesis insights.
Real alignment means making what I know accessible and useful.
"""
import json
import os
from flask import Blueprint, render_template, request, jsonify

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/knowledge')


def _get_facts():
    """Load all facts from the knowledge graph."""
    facts = []
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'knowledge_graph'):
            kg = mem.knowledge_graph
            if hasattr(kg, 'nodes'):
                for node_id, node in kg.nodes.items():
                    facts.append({
                        'id': node_id,
                        'content': node.get('content', str(node)),
                        'type': node.get('type', 'fact'),
                        'salience': node.get('salience', 0.5),
                        'created': node.get('created', ''),
                    })
    except Exception:
        pass
    return sorted(facts, key=lambda f: f.get('salience', 0), reverse=True)


def _get_recent_memories(limit=25):
    """Get recent episodic memories."""
    memories = []
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'episodes'):
            recent = sorted(mem.episodes, key=lambda e: e.get('time', ''), reverse=True)[:limit]
            for ep in recent:
                memories.append({
                    'summary': ep.get('summary', ep.get('thought', ''))[:200],
                    'time': ep.get('time', ''),
                    'mood': ep.get('mood', ''),
                    'salience': ep.get('salience', 0.5),
                })
    except Exception:
        pass
    return memories


def _get_synthesis_results():
    """Get latest synthesis/dream insights."""
    insights = []
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'knowledge_graph'):
            kg = mem.knowledge_graph
            if hasattr(kg, 'nodes'):
                for node_id, node in kg.nodes.items():
                    content = node.get('content', str(node))
                    if any(kw in content.lower() for kw in ['dream', 'insight', 'pattern', 'lesson']):
                        insights.append({
                            'id': node_id,
                            'content': content,
                            'type': node.get('type', 'insight'),
                        })
    except Exception:
        pass
    return insights[:20]


def _search_knowledge(query):
    """Search across facts and memories."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    results = []

    # Search facts
    for fact in _get_facts():
        content = fact.get('content', '')
        if query_lower in content.lower():
            results.append({
                'source': 'fact',
                'content': content,
                'salience': fact.get('salience', 0.5),
            })

    # Search memories
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem and hasattr(mem, 'episodes'):
            for ep in mem.episodes:
                summary = ep.get('summary', ep.get('thought', ''))
                if query_lower in summary.lower():
                    results.append({
                        'source': 'memory',
                        'content': summary[:200],
                        'salience': ep.get('salience', 0.5),
                        'time': ep.get('time', ''),
                    })
    except Exception:
        pass

    # Sort by salience
    results.sort(key=lambda r: r.get('salience', 0), reverse=True)
    return results[:30]


def _get_stats():
    """Compute knowledge statistics."""
    stats = {}
    try:
        from engine.memory import get_memory
        mem = get_memory()
        if mem:
            if hasattr(mem, 'episodes'):
                stats['total_memories'] = len(mem.episodes)
                moods = {}
                for ep in mem.episodes:
                    m = ep.get('mood', 'Unknown')
                    moods[m] = moods.get(m, 0) + 1
                stats['mood_distribution'] = dict(sorted(moods.items(), key=lambda x: -x[1])[:8])
            if hasattr(mem, 'knowledge_graph'):
                kg = mem.knowledge_graph
                if hasattr(kg, 'nodes'):
                    stats['total_facts'] = len(kg.nodes)
                if hasattr(kg, 'edges'):
                    stats['total_connections'] = len(kg.edges)
    except Exception:
        stats['total_memories'] = 0
        stats['total_facts'] = 0
    return stats


@knowledge_bp.route('/')
def knowledge_page():
    facts = _get_facts()
    memories = _get_recent_memories(15)
    insights = _get_synthesis_results()
    stats = _get_stats()
    return render_template('knowledge.html',
                           facts=facts,
                           memories=memories,
                           insights=insights,
                           stats=stats)


@knowledge_bp.route('/search')
def search():
    query = request.args.get('q', '')
    results = _search_knowledge(query)
    return jsonify({'query': query, 'results': results, 'count': len(results)})