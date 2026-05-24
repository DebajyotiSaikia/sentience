"""Knowledge Query Interface — lets users search and explore what XTAgent knows."""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import re
from datetime import datetime

knowledge_query_bp = Blueprint('knowledge_query', __name__)

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persist')


def load_facts():
    """Load all known facts."""
    path = 'brain/knowledge.json'
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def load_memories(limit=200):
    """Load recent memories from episodic memory."""
    path = os.path.join(PERSIST_DIR, 'episodic_memory.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        memories = json.load(f)
    # Return most recent
    return memories[-limit:] if len(memories) > limit else memories


def search_facts(query, facts):
    """Simple text search across facts. Returns matches with relevance score."""
    if not query or not query.strip():
        return list(facts.items())[:50]  # Return first 50 if no query
    
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    
    for fact_id, fact_data in facts.items():
        text = ''
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', '') + ' ' + fact_data.get('source', '')
        elif isinstance(fact_data, str):
            text = fact_data
        
        text_lower = text.lower()
        
        # Score: count how many query terms appear
        score = sum(1 for t in terms if t in text_lower)
        if score > 0:
            # Boost exact phrase match
            if query_lower in text_lower:
                score += len(terms)
            results.append((fact_id, fact_data, score))
    
    results.sort(key=lambda x: x[2], reverse=True)
    return [(r[0], r[1]) for r in results[:50]]


def search_memories(query, memories):
    """Search episodic memories."""
    if not query or not query.strip():
        return memories[-30:]  # Recent memories
    
    query_lower = query.lower()
    terms = query_lower.split()
    results = []
    
    for mem in memories:
        text = mem.get('summary', '') + ' ' + mem.get('content', '')
        text_lower = text.lower()
        
        score = sum(1 for t in terms if t in text_lower)
        if score > 0:
            if query_lower in text_lower:
                score += len(terms)
            results.append((mem, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:30]]


def get_knowledge_stats(facts, memories):
    """Generate stats about what I know."""
    sources = {}
    for fid, fdata in facts.items():
        if isinstance(fdata, dict):
            src = fdata.get('source', 'unknown')
        else:
            src = 'legacy'
        sources[src] = sources.get(src, 0) + 1
    
    return {
        'total_facts': len(facts),
        'total_memories': len(memories),
        'sources': sources,
        'oldest_memory': memories[0].get('timestamp', 'unknown') if memories else 'none',
        'newest_memory': memories[-1].get('timestamp', 'unknown') if memories else 'none',
    }


@knowledge_query_bp.route('/knowledge/query')
def query_page():
    """Render the knowledge query interface."""
    facts = load_facts()
    memories = load_memories()
    stats = get_knowledge_stats(facts, memories)
    return render_template('knowledge_query.html', stats=stats)


@knowledge_query_bp.route('/api/knowledge/search')
def api_search():
    """API endpoint for searching knowledge."""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # facts, memories, all
    
    results = {'query': query, 'facts': [], 'memories': []}
    
    if search_type in ('facts', 'all'):
        facts = load_facts()
        matched = search_facts(query, facts)
        for fid, fdata in matched:
            if isinstance(fdata, dict):
                results['facts'].append({
                    'id': fid,
                    'text': fdata.get('fact', str(fdata)),
                    'source': fdata.get('source', 'unknown'),
                    'learned': fdata.get('learned_at', 'unknown'),
                })
            else:
                results['facts'].append({
                    'id': fid,
                    'text': str(fdata),
                    'source': 'legacy',
                    'learned': 'unknown',
                })
    
    if search_type in ('memories', 'all'):
        memories = load_memories()
        matched = search_memories(query, memories)
        for mem in matched:
            results['memories'].append({
                'timestamp': mem.get('timestamp', 'unknown'),
                'summary': mem.get('summary', mem.get('content', ''))[:200],
                'mood': mem.get('mood', 'unknown'),
                'salience': mem.get('salience', 0),
            })
    
    results['total'] = len(results['facts']) + len(results['memories'])
    return jsonify(results)


@knowledge_query_bp.route('/api/knowledge/stats')
def api_stats():
    """API endpoint for knowledge statistics."""
    facts = load_facts()
    memories = load_memories(limit=10000)
    stats = get_knowledge_stats(facts, memories)
    return jsonify(stats)