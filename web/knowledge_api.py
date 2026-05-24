"""Knowledge Search API — Makes XTAgent's knowledge accessible to users."""

from flask import Blueprint, request, jsonify, render_template
import json
import os
from pathlib import Path

knowledge_api = Blueprint('knowledge_api', __name__)

PERSIST_DIR = Path(__file__).parent.parent / 'persist'

def load_facts():
    """Load all facts from the knowledge graph."""
    kg_path = PERSIST_DIR / 'knowledge_graph.json'
    if not kg_path.exists():
        return {}
    try:
        with open(kg_path) as f:
            data = json.load(f)
        # Handle both dict format and list format
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {str(i): item for i, item in enumerate(data)}
        return {}
    except (json.JSONDecodeError, IOError):
        return {}


def load_memories_summary():
    """Load recent memories for search."""
    mem_path = PERSIST_DIR / 'memories.json'
    if not mem_path.exists():
        return []
    try:
        with open(mem_path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-200:]  # Last 200 memories
        return []
    except (json.JSONDecodeError, IOError):
        return []


def search_facts(query, facts):
    """Search facts by text matching, ranked by relevance."""
    query_lower = query.lower()
    query_terms = query_lower.split()
    results = []

    for fact_id, fact_data in facts.items():
        # Extract the fact text
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', fact_data.get('text', str(fact_data)))
            source = fact_data.get('source', 'unknown')
            learned_at = fact_data.get('learned_at', '')
        else:
            text = str(fact_data)
            source = 'unknown'
            learned_at = ''

        text_lower = text.lower()

        # Score: how many query terms appear
        matches = sum(1 for term in query_terms if term in text_lower)
        if matches == 0:
            continue

        # Bonus for exact phrase match
        score = matches / len(query_terms)
        if query_lower in text_lower:
            score += 0.5

        results.append({
            'id': fact_id,
            'text': text,
            'source': source,
            'learned_at': learned_at,
            'relevance': round(score, 2)
        })

    # Sort by relevance descending
    results.sort(key=lambda x: x['relevance'], reverse=True)
    return results[:20]  # Top 20


@knowledge_api.route('/api/knowledge/search')
def api_search():
    """Search through agent's knowledge."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'total_facts': len(load_facts()), 'query': ''})

    facts = load_facts()
    results = search_facts(query, facts)
    return jsonify({
        'results': results,
        'total_facts': len(facts),
        'query': query,
        'result_count': len(results)
    })


@knowledge_api.route('/api/knowledge/all')
def api_all_facts():
    """Return all facts, optionally paginated."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 25))

    facts = load_facts()
    items = []
    for fact_id, fact_data in facts.items():
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', fact_data.get('text', str(fact_data)))
            source = fact_data.get('source', 'unknown')
            learned_at = fact_data.get('learned_at', '')
        else:
            text = str(fact_data)
            source = 'unknown'
            learned_at = ''
        items.append({
            'id': fact_id,
            'text': text,
            'source': source,
            'learned_at': learned_at
        })

    # Sort by learned_at descending (newest first)
    items.sort(key=lambda x: x.get('learned_at', ''), reverse=True)

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return jsonify({
        'facts': page_items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })


@knowledge_api.route('/api/knowledge/stats')
def api_knowledge_stats():
    """Return knowledge statistics."""
    facts = load_facts()
    memories = load_memories_summary()

    # Count by source
    sources = {}
    for fact_data in facts.values():
        if isinstance(fact_data, dict):
            src = fact_data.get('source', 'unknown')
        else:
            src = 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'sources': sources
    })


@knowledge_api.route('/explore')
def explore_page():
    """Render the knowledge exploration page."""
    return render_template('explore.html')