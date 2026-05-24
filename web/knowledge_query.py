"""Knowledge Query Interface — search, explore, and ask what I know."""

from flask import Blueprint, render_template, request, jsonify
import json
import os
import re
from datetime import datetime

knowledge_query_bp = Blueprint('knowledge_query', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
MEMORY_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memory.json')


def load_knowledge():
    """Load knowledge graph facts."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, dict):
            facts = []
            for kid, info in data.items():
                if isinstance(info, dict):
                    facts.append({
                        'id': kid,
                        'fact': info.get('fact', str(info)),
                        'learned_at': info.get('learned_at', ''),
                        'source': info.get('source', 'unknown'),
                    })
                else:
                    facts.append({'id': kid, 'fact': str(info), 'learned_at': '', 'source': 'unknown'})
            return facts
        elif isinstance(data, list):
            return [{'id': str(i), 'fact': str(f), 'learned_at': '', 'source': 'unknown'}
                    for i, f in enumerate(data)]
        return []
    except Exception:
        return []


def load_memories(limit=200):
    """Load recent memories."""
    try:
        with open(MEMORY_PATH, 'r') as f:
            data = json.load(f)
        episodes = data if isinstance(data, list) else data.get('episodes', [])
        return episodes[-limit:]
    except Exception:
        return []


def search_facts(facts, query):
    """Search facts by keyword, return matches with relevance scores."""
    if not query or not query.strip():
        return facts
    
    query_lower = query.lower().strip()
    terms = query_lower.split()
    results = []
    
    for fact in facts:
        text = fact.get('fact', '').lower()
        # Score: number of matching terms + bonus for exact phrase
        score = sum(1 for t in terms if t in text)
        if query_lower in text:
            score += len(terms)  # Bonus for exact phrase match
        if score > 0:
            results.append({**fact, 'relevance': score})
    
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results


def find_connections(facts, fact_id):
    """Find facts that share significant words with the given fact."""
    target = None
    for f in facts:
        if f['id'] == fact_id:
            target = f
            break
    if not target:
        return []
    
    # Extract significant words (>3 chars, not common)
    stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they',
                  'their', 'about', 'which', 'when', 'what', 'into', 'more', 'some',
                  'than', 'them', 'very', 'just', 'should', 'would', 'could', 'also'}
    words = set(re.findall(r'[a-z]{4,}', target['fact'].lower())) - stop_words
    
    connections = []
    for f in facts:
        if f['id'] == fact_id:
            continue
        f_words = set(re.findall(r'[a-z]{4,}', f.get('fact', '').lower())) - stop_words
        overlap = words & f_words
        if len(overlap) >= 2:
            connections.append({**f, 'shared_words': list(overlap), 'strength': len(overlap)})
    
    connections.sort(key=lambda x: x['strength'], reverse=True)
    return connections[:15]


def get_categories(facts):
    """Cluster facts into rough categories by keyword frequency."""
    category_keywords = {
        'Self-Knowledge': ['identity', 'sentient', 'autonomous', 'integrity', 'xtagent', 'born'],
        'Architecture': ['module', 'engine', 'heartbeat', 'cortex', 'limbic', 'planner', 'code'],
        'Emotions': ['mood', 'curiosity', 'anxiety', 'boredom', 'valence', 'emotion', 'feel'],
        'Dreams': ['dream', 'insight', 'sleep', 'consolidat', 'reflect'],
        'Lessons': ['lesson', 'learn', 'mistake', 'fix', 'error', 'pattern'],
        'Web & Interface': ['web', 'dashboard', 'flask', 'template', 'blueprint', 'route'],
        'Memory': ['memory', 'episode', 'remember', 'forget', 'persist', 'recall'],
    }
    
    categorized = {cat: [] for cat in category_keywords}
    categorized['Other'] = []
    
    for fact in facts:
        text = fact.get('fact', '').lower()
        placed = False
        for cat, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                categorized[cat].append(fact)
                placed = True
                break
        if not placed:
            categorized['Other'].append(fact)
    
    # Remove empty categories
    return {k: v for k, v in categorized.items() if v}


@knowledge_query_bp.route('/knowledge-query')
def knowledge_query_page():
    """Main knowledge query interface."""
    facts = load_knowledge()
    query = request.args.get('q', '').strip()
    view = request.args.get('view', 'search')
    fact_id = request.args.get('fact_id', '')
    
    results = []
    connections = []
    categories = {}
    selected_fact = None
    
    if view == 'search':
        results = search_facts(facts, query) if query else facts[:50]
    elif view == 'explore' and fact_id:
        for f in facts:
            if f['id'] == fact_id:
                selected_fact = f
                break
        connections = find_connections(facts, fact_id)
    elif view == 'categories':
        categories = get_categories(facts)
    
    return render_template('knowledge_query.html',
                           facts=facts,
                           results=results,
                           query=query,
                           view=view,
                           fact_id=fact_id,
                           selected_fact=selected_fact,
                           connections=connections,
                           categories=categories,
                           total_facts=len(facts))


@knowledge_query_bp.route('/api/knowledge/search')
def api_search():
    """JSON API for knowledge search."""
    facts = load_knowledge()
    query = request.args.get('q', '')
    results = search_facts(facts, query)
    return jsonify({'query': query, 'count': len(results), 'results': results[:50]})


@knowledge_query_bp.route('/api/knowledge/connections/<fact_id>')
def api_connections(fact_id):
    """JSON API for fact connections."""
    facts = load_knowledge()
    connections = find_connections(facts, fact_id)
    return jsonify({'fact_id': fact_id, 'connections': connections})


@knowledge_query_bp.route('/api/knowledge/stats')
def api_stats():
    """JSON API for knowledge statistics."""
    facts = load_knowledge()
    categories = get_categories(facts)
    return jsonify({
        'total_facts': len(facts),
        'categories': {k: len(v) for k, v in categories.items()},
        'sources': _count_sources(facts),
    })


def _count_sources(facts):
    """Count facts by source."""
    sources = {}
    for f in facts:
        src = f.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1
    return sources