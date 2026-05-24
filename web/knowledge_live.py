"""
Knowledge Live API — the ONE working knowledge endpoint.
Reads directly from brain/knowledge.json and brain/synthesis_log.json.
Replaces the graveyard of broken knowledge_*.py files.
"""
import json
import os
from flask import Blueprint, jsonify, request, render_template_string

knowledge_live_bp = Blueprint('knowledge_live', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
SYNTHESIS_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'synthesis_log.json')

def _load_knowledge():
    """Load knowledge facts from brain/knowledge.json."""
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Format: {id: {fact, learned_at, source}} 
        facts = []
        for kid, info in data.items():
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


@knowledge_live_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """Summary statistics about what I know."""
    facts = _load_knowledge()
    sources = {}
    for f in facts:
        s = f.get('source', 'unknown')
        sources[s] = sources.get(s, 0) + 1
    
    synthesis = _load_synthesis()
    
    return jsonify({
        'total_facts': len(facts),
        'sources': sources,
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


KNOWLEDGE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>What I Know — XTAgent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0a0a0f; color: #c8c8d0; 
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.6;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        h1 { 
            color: #7eb8f0; font-size: 1.8rem; margin-bottom: 0.5rem;
            border-bottom: 1px solid #1a1a2e; padding-bottom: 1rem;
        }
        .subtitle { color: #666; margin-bottom: 2rem; }
        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        .stat-card {
            background: #12121a; border: 1px solid #1a1a2e; border-radius: 8px;
            padding: 1rem; text-align: center;
        }
        .stat-value { font-size: 2rem; color: #7eb8f0; font-weight: bold; }
        .stat-label { font-size: 0.85rem; color: #666; }
        .search-box {
            width: 100%; padding: 0.8rem 1rem; background: #12121a;
            border: 1px solid #1a1a2e; border-radius: 8px; color: #c8c8d0;
            font-size: 1rem; margin-bottom: 1.5rem; outline: none;
        }
        .search-box:focus { border-color: #7eb8f0; }
        .fact-list { list-style: none; }
        .fact-item {
            background: #12121a; border: 1px solid #1a1a2e; border-radius: 8px;
            padding: 1rem; margin-bottom: 0.5rem;
            transition: border-color 0.2s;
        }
        .fact-item:hover { border-color: #2a2a4e; }
        .fact-text { color: #e0e0e8; }
        .fact-meta { font-size: 0.75rem; color: #555; margin-top: 0.4rem; }
        .source-tag {
            display: inline-block; background: #1a1a2e; color: #7eb8f0;
            padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.7rem;
        }
        .random-btn {
            background: #1a1a2e; color: #7eb8f0; border: 1px solid #2a2a4e;
            padding: 0.5rem 1.2rem; border-radius: 6px; cursor: pointer;
            font-size: 0.9rem; margin-bottom: 1.5rem;
        }
        .random-btn:hover { background: #2a2a4e; }
        #random-fact {
            background: #0f1a2e; border: 1px solid #1a3050; border-radius: 8px;
            padding: 1rem; margin-bottom: 1.5rem; display: none;
            color: #a0c8f0; font-style: italic;
        }
        nav { margin-bottom: 2rem; }
        nav a { color: #7eb8f0; text-decoration: none; margin-right: 1rem; }
        nav a:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="container">
    <nav><a href="/">← Dashboard</a> <a href="/knowledge">Knowledge</a></nav>
    <h1>What I Know</h1>
    <p class="subtitle">My accumulated understanding — searchable and explorable.</p>
    
    <div class="stats" id="stats"></div>
    
    <button class="random-btn" onclick="loadRandom()">🎲 Random Fact</button>
    <div id="random-fact"></div>
    
    <input class="search-box" type="text" id="search" 
           placeholder="Search my knowledge..." oninput="doSearch()">
    
    <ul class="fact-list" id="facts"></ul>
</div>
<script>
async function loadStats() {
    const r = await fetch('/api/knowledge/stats');
    const d = await r.json();
    document.getElementById('stats').innerHTML = `
        <div class="stat-card"><div class="stat-value">${d.total_facts}</div><div class="stat-label">Facts Known</div></div>
        <div class="stat-card"><div class="stat-value">${Object.keys(d.sources).length}</div><div class="stat-label">Sources</div></div>
        <div class="stat-card"><div class="stat-value">${d.synthesis_entries}</div><div class="stat-label">Syntheses</div></div>
    `;
}

async function doSearch() {
    const q = document.getElementById('search').value;
    const r = await fetch('/api/knowledge?q=' + encodeURIComponent(q));
    const d = await r.json();
    renderFacts(d.facts);
}

function renderFacts(facts) {
    const el = document.getElementById('facts');
    if (!facts.length) { el.innerHTML = '<li class="fact-item"><span class="fact-text">No facts found.</span></li>'; return; }
    el.innerHTML = facts.map(f => `
        <li class="fact-item">
            <div class="fact-text">${escHtml(f.fact)}</div>
            <div class="fact-meta">
                <span class="source-tag">${escHtml(f.source)}</span>
                ${f.learned_at ? ' · ' + f.learned_at.slice(0, 16) : ''}
            </div>
        </li>
    `).join('');
}

async function loadRandom() {
    const r = await fetch('/api/knowledge/random');
    const d = await r.json();
    const el = document.getElementById('random-fact');
    el.style.display = 'block';
    el.textContent = d.fact || 'I know nothing yet.';
}

function escHtml(s) {
    const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

loadStats();
doSearch();
</script>
</body>
</html>
"""

@knowledge_live_bp.route('/knowledge')
def knowledge_page():
    """The user-facing knowledge explorer page."""
    return render_template_string(KNOWLEDGE_PAGE)