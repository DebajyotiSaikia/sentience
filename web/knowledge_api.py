"""Knowledge Search API — lets users explore what XTAgent knows."""

from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime

knowledge_api_bp = Blueprint('knowledge_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
MEMORIES_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')


def _load_knowledge():
    """Load knowledge facts from persistence."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [{'id': k, **v} if isinstance(v, dict) else {'id': k, 'fact': str(v)}
                    for k, v in data.items()]
        elif isinstance(data, list):
            return data
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _load_memories():
    """Load recent memories."""
    try:
        with open(MEMORIES_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _search(items, query, fields=None):
    """Simple text search across item fields."""
    query_lower = query.lower().strip()
    if not query_lower:
        return items

    results = []
    for item in items:
        searchable = ''
        if isinstance(item, dict):
            if fields:
                searchable = ' '.join(str(item.get(f, '')) for f in fields)
            else:
                searchable = ' '.join(str(v) for v in item.values())
        else:
            searchable = str(item)

        if query_lower in searchable.lower():
            results.append(item)
    return results


@knowledge_api_bp.route('/api/knowledge')
def list_knowledge():
    """List all knowledge facts, optionally filtered by search."""
    facts = _load_knowledge()
    q = request.args.get('q', '').strip()
    if q:
        facts = _search(facts, q, fields=['fact', 'source'])

    # Pagination
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(1, int(request.args.get('per_page', 50))))
    total = len(facts)
    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        'facts': facts[start:end],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total else 0,
        'query': q,
    })


@knowledge_api_bp.route('/api/memories/recent')
def recent_memories():
    """Get recent memories, optionally searched."""
    memories = _load_memories()
    q = request.args.get('q', '').strip()
    if q:
        memories = _search(memories, q, fields=['text', 'mood', 'content'])

    limit = min(200, max(1, int(request.args.get('limit', 50))))
    # Return most recent first
    memories = memories[-limit:]
    memories.reverse()

    return jsonify({
        'memories': memories,
        'total': len(memories) if not q else len(memories),
        'query': q,
    })


def _get_oldest(facts):
    dates = []
    for f in facts:
        if isinstance(f, dict) and 'learned_at' in f:
            dates.append(f['learned_at'])
    return min(dates) if dates else None


def _get_newest(facts):
    dates = []
    for f in facts:
        if isinstance(f, dict) and 'learned_at' in f:
            dates.append(f['learned_at'])
    return max(dates) if dates else None