"""Knowledge Query API — lets users search and explore what XTAgent knows."""

from flask import Blueprint, jsonify, request
import json
import os
from pathlib import Path

try:
    from engine.knowledge_categorizer import get_category_summary
except ImportError:
    get_category_summary = None

knowledge_api_bp = Blueprint('knowledge_api_bp', __name__)

BRAIN_DIR = Path(__file__).parent.parent / 'brain'
PERSIST_DIR = Path(__file__).parent.parent / 'persist'

# Import categorizer for the categories endpoint
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from engine.knowledge_categorizer import get_category_summary, categorize_all
except ImportError:
    get_category_summary = None
    categorize_all = None
BRAIN_DIR = Path(__file__).parent.parent / 'brain'


def _load_facts():
    """Load all known facts from brain/knowledge.json."""
    kg_path = BRAIN_DIR / 'knowledge.json'
    if not kg_path.exists():
        return {}
    try:
        with open(kg_path) as f:
            data = json.load(f)
        # Handle both formats: dict of {id: {fact, ...}} or list
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
        elif isinstance(data, list):
            nodes = {str(i): {'fact': str(item)} for i, item in enumerate(data)}
        else:
            nodes = {}
        return nodes
    except Exception:
        return {}


def _load_memories():
    """Load recent memories from persist/memories.json."""
    mem_path = PERSIST_DIR / 'memories.json'
    if not mem_path.exists():
        return []
    try:
        with open(mem_path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _search(items, query, key='fact'):
    """Simple case-insensitive substring search."""
    query_lower = query.lower()
    results = []
    for item in items:
        text = ''
        if isinstance(item, dict):
            text = item.get(key, '') or item.get('content', '') or str(item)
        elif isinstance(item, str):
            text = item
        if query_lower in text.lower():
            results.append(item)
    return results


@knowledge_api_bp.route('/api/knowledge/search')
def search_knowledge():
    """Search facts and memories. ?q=query&limit=20"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)

    if not query:
        return jsonify({'error': 'Missing ?q= parameter', 'results': []}), 400

    # Search facts
    facts = _load_facts()
    fact_list = []
    for fid, fdata in facts.items():
        if isinstance(fdata, dict):
            fact_list.append({'id': fid, **fdata})
        else:
            fact_list.append({'id': fid, 'fact': str(fdata)})

    matched_facts = _search(fact_list, query)[:limit]

    # Search memories
    memories = _load_memories()
    matched_memories = _search(memories, query, key='content')[:limit]

    return jsonify({
        'query': query,
        'facts': matched_facts,
        'memories': matched_memories,
        'total_facts': len(facts),
        'total_memories': len(memories),
    })


@knowledge_api_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Return summary statistics about what I know."""
    facts = _load_facts()
    memories = _load_memories()

    # Compute basic stats
    recent_memories = sorted(
        [m for m in memories if isinstance(m, dict) and 'timestamp' in m],
        key=lambda m: m.get('timestamp', ''),
        reverse=True
    )[:5]

    # Category breakdown if categorizer available
    categories = {}
    if get_category_summary:
        try:
            categories = get_category_summary()
        except Exception:
            categories = {}

    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'recent_memories': recent_memories,
        'sample_facts': list(facts.items())[:5] if facts else [],
        'categories': categories,
    })


@knowledge_api_bp.route('/api/knowledge/explore')
def explore_knowledge():
    """Browse all facts, paginated. ?page=1&per_page=20"""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 20)), 50)

    facts = _load_facts()
    items = list(facts.items())
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    results = []
    for fid, fdata in page_items:
        if isinstance(fdata, dict):
            results.append({'id': fid, **fdata})
        else:
            results.append({'id': fid, 'fact': str(fdata)})

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page if per_page else 1,
        'results': results,
    })


@knowledge_api_bp.route('/api/knowledge/categories')
def categories():
    """Return facts organized by category."""
    from engine.knowledge_categorizer import categorize_all, get_category_summary
    facts = _load_facts()
    if not facts:
        return jsonify({'categories': {}, 'summary': {}})

    # Build list of fact strings for the categorizer
    fact_list = []
    for fid, fdata in facts.items():
        if isinstance(fdata, dict):
            fact_list.append(fdata.get('fact', str(fdata)))
        else:
            fact_list.append(str(fdata))

    categorized = categorize_all(fact_list)
    summary = get_category_summary(fact_list)

    return jsonify({
        'categories': categorized,
        'summary': summary,
    })