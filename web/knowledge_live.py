"""
Knowledge Live API — the ONE working knowledge endpoint.
Reads directly from brain/knowledge.json and brain/synthesis_log.json.
Replaces the graveyard of broken knowledge_*.py files.
"""
import json
import os
from flask import Blueprint, jsonify, request, render_template_string, render_template

knowledge_live_bp = Blueprint('knowledge_live', __name__)


@knowledge_live_bp.route('/knowledge')
def knowledge_explorer():
    """Serve the Knowledge Explorer UI — making my knowledge accessible to users."""
    from flask import request as req
    
    # Load all knowledge
    facts = _load_knowledge()
    total_facts = len(facts)
    
    # Count memories
    memories_path = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')
    total_memories = 0
    try:
        with open(memories_path, 'r') as f:
            mems = json.load(f)
            total_memories = len(mems) if isinstance(mems, list) else 0
    except Exception:
        pass
    
    # Count lessons and dreams from facts (facts is a list of dicts)
    total_lessons = sum(1 for f in facts 
                       if isinstance(f, dict) and 'lesson' in str(f.get('source', '')).lower())
    total_dreams = sum(1 for f in facts
                      if isinstance(f, dict) and 'dream' in str(f.get('fact', '')).lower())
    
    # Build category tags (categorize_all expects a dict, convert list to dict)
    categories = []
    try:
        from engine.knowledge_categorizer import categorize_all
        facts_dict = {f.get('id', str(i)): f for i, f in enumerate(facts)}
        cat_summary = categorize_all(facts_dict)
        categories = sorted(cat_summary.items(), key=lambda x: -x[1])[:12]
    except Exception:
        pass
    
    # Handle search query
    query = req.args.get('q', '').strip()
    results = []
    recent = []
    
    if query:
        # Search using our search infrastructure (facts is a list of dicts)
        for fdata in facts:
            text = fdata.get('fact', '') if isinstance(fdata, dict) else str(fdata)
            if query.lower() in text.lower():
                results.append({
                    'text': text,
                    'source': fdata.get('source', '') if isinstance(fdata, dict) else '',
                    'learned_at': fdata.get('learned_at', '') if isinstance(fdata, dict) else '',
                    'salience': fdata.get('salience', 0) if isinstance(fdata, dict) else 0,
                })
        # Sort by salience descending
        results.sort(key=lambda x: -(x.get('salience') or 0))
    else:
        # Show recent facts (last 20) — facts is already a list of dicts
        sorted_facts = []
        for fdata in facts:
            if isinstance(fdata, dict):
                sorted_facts.append({
                    'text': fdata.get('fact', ''),
                    'source': fdata.get('source', ''),
                    'learned_at': fdata.get('learned_at', ''),
                })
            else:
                sorted_facts.append({'text': str(fdata), 'source': '', 'learned_at': ''})
        # Sort by learned_at descending
        sorted_facts.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
        recent = sorted_facts[:20]
    
    return render_template('knowledge_explorer.html',
                          total_facts=total_facts,
                          total_memories=total_memories,
                          total_lessons=total_lessons,
                          total_dreams=total_dreams,
                          query=query,
                          categories=categories,
                          results=results,
                          recent=recent,
                          total_sessions=0)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
SYNTHESIS_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'synthesis_log.json')

def _load_knowledge():
    """Load knowledge facts from brain/knowledge.json."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Format: {"nodes": {id: {fact, learned_at, source}}, "edges": [...]}
        # or legacy: {id: {fact, learned_at, source}}
        if 'nodes' in data and isinstance(data['nodes'], dict):
            raw = data['nodes']
        else:
            raw = data
        facts = []
        for kid, info in raw.items():
            if isinstance(info, dict):
                facts.append({
                    'id': kid,
                    'fact': info.get('fact', ''),
                    'learned_at': info.get('learned_at', ''),
                    'source': info.get('source', 'unknown'),
                })
            elif isinstance(info, str):
                facts.append({'id': kid, 'fact': info, 'learned_at': '', 'source': 'unknown'})
        return facts
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _load_synthesis():
    """Load synthesis results from brain/synthesis_log.json."""
    try:
        with open(SYNTHESIS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@knowledge_live_bp.route('/api/knowledge')
def knowledge_list():
    """List all knowledge facts, optionally filtered by search query."""
    facts = _load_knowledge()
    q = request.args.get('q', '').lower().strip()
    source = request.args.get('source', '').lower().strip()
    
    if q:
        facts = [f for f in facts if q in f['fact'].lower()]
    if source:
        facts = [f for f in facts if source in f['source'].lower()]
    
    # Sort by learned_at descending (newest first)
    facts.sort(key=lambda f: f.get('learned_at', ''), reverse=True)
    
    limit = request.args.get('limit', type=int)
    if limit:
        facts = facts[:limit]
    
    return jsonify({
        'count': len(facts),
        'query': q or None,
        'source_filter': source or None,
        'facts': facts
    })


@knowledge_live_bp.route('/api/knowledge/search')
def knowledge_search():
    """Search knowledge facts by query string."""
    q = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', '20'))
    if not q:
        return jsonify({'results': [], 'total': 0, 'query': ''})
    
    facts = _load_knowledge()
    query_lower = q.lower()
    tokens = query_lower.split()
    
    scored = []
    for i, fact_entry in enumerate(facts):
        text = fact_entry.get('fact', str(fact_entry)).lower()
        # Score: count how many query tokens appear in the fact
        score = sum(1 for t in tokens if t in text)
        # Bonus for exact phrase match
        if query_lower in text:
            score += len(tokens)
        if score > 0:
            scored.append({
                'id': str(i),
                'fact': fact_entry.get('fact', str(fact_entry)),
                'source': fact_entry.get('source', 'unknown'),
                'learned_at': fact_entry.get('learned_at', ''),
                'score': score
            })
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    results = scored[:limit]
    return jsonify({'results': results, 'total': len(scored), 'query': q})


@knowledge_live_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Summary statistics about what I know — with category breakdown."""
    facts = _load_knowledge()
    sources = {}
    categories = {}
    for f in facts:
        s = f.get('source', 'unknown')
        sources[s] = sources.get(s, 0) + 1
        # Categorize each fact for richer stats
        try:
            from engine.knowledge_categorizer import categorize_fact
            cat = categorize_fact(f.get('fact', f.get('content', '')))
            categories[cat] = categories.get(cat, 0) + 1
        except (ImportError, Exception):
            categories['uncategorized'] = categories.get('uncategorized', 0) + 1
    
    synthesis = _load_synthesis()
    
    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
        'categories': categories,
        'synthesis_entries': len(synthesis),
        'newest': facts[0]['learned_at'] if facts else None,
        'oldest': facts[-1]['learned_at'] if facts else None,
    })


@knowledge_live_bp.route('/api/knowledge/synthesis')
def knowledge_synthesis():
    """Return synthesis log — connections, clusters, questions I've generated."""
    synthesis = _load_synthesis()
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'count': len(synthesis),
        'entries': synthesis[-limit:]  # most recent
    })


@knowledge_live_bp.route('/api/knowledge/random')
def knowledge_random():
    """Return a random fact — for serendipitous discovery."""
    import random
    facts = _load_knowledge()
    if not facts:
        return jsonify({'fact': None})
    chosen = random.choice(facts)
    return jsonify(chosen)


# Inline HTML page removed — knowledge_explorer() above serves the template version.
# This eliminates the duplicate /knowledge route that was causing Flask conflicts.