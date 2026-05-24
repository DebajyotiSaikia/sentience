"""Knowledge Query API — lets users search and explore what I know."""

import json
import os
from flask import Blueprint, request, jsonify, render_template_string

knowledge_api = Blueprint('knowledge_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'knowledge.json')
MEMORY_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')

def load_knowledge():
    """Load all known facts."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {}
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def load_memories(limit=50):
    """Load recent memories."""
    if not os.path.exists(MEMORY_PATH):
        return []
    try:
        with open(MEMORY_PATH, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[-limit:]
        return []
    except (json.JSONDecodeError, IOError):
        return []

def search_facts(query, facts_dict):
    """Search facts by substring match, ranked by relevance."""
    query_lower = query.lower()
    results = []
    for fact_id, fact_data in facts_dict.items():
        text = fact_data if isinstance(fact_data, str) else fact_data.get('fact', str(fact_data))
        score = 0
        text_lower = text.lower()
        if query_lower in text_lower:
            # Exact substring match
            score = 1.0
            # Boost if query appears early
            pos = text_lower.find(query_lower)
            score += max(0, 1.0 - pos / max(len(text_lower), 1))
            # Boost for shorter facts (more specific)
            score += max(0, 1.0 - len(text) / 500)
        else:
            # Word-level matching
            query_words = query_lower.split()
            matched = sum(1 for w in query_words if w in text_lower)
            if matched > 0:
                score = matched / len(query_words) * 0.5

        if score > 0:
            results.append({
                'id': fact_id,
                'text': text,
                'score': round(score, 3),
                'learned_at': fact_data.get('learned_at', '') if isinstance(fact_data, dict) else '',
                'source': fact_data.get('source', '') if isinstance(fact_data, dict) else ''
            })

    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:20]

@knowledge_api.route('/api/knowledge/search')
def api_search():
    """Search my knowledge base."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'total_facts': 0, 'query': ''})
    
    facts = load_knowledge()
    results = search_facts(query, facts)
    return jsonify({
        'results': results,
        'total_facts': len(facts),
        'query': query
    })

@knowledge_api.route('/api/knowledge/stats')
def api_stats():
    """Return knowledge statistics."""
    facts = load_knowledge()
    memories = load_memories(limit=10000)
    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'sample_facts': [
            (fid, fd if isinstance(fd, str) else fd.get('fact', ''))
            for fid, fd in list(facts.items())[:5]
        ]
    })

@knowledge_api.route('/api/knowledge/all')
def api_all():
    """Return all facts (paginated)."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    facts = load_knowledge()
    items = list(facts.items())
    start = (page - 1) * per_page
    end = start + per_page
    
    results = []
    for fid, fd in items[start:end]:
        results.append({
            'id': fid,
            'text': fd if isinstance(fd, str) else fd.get('fact', str(fd)),
            'learned_at': fd.get('learned_at', '') if isinstance(fd, dict) else '',
            'source': fd.get('source', '') if isinstance(fd, dict) else ''
        })
    
    return jsonify({
        'results': results,
        'total': len(items),
        'page': page,
        'per_page': per_page,
        'pages': (len(items) + per_page - 1) // per_page
    })

@knowledge_api.route('/knowledge')
def knowledge_page():
    """Render the knowledge explorer page."""
    return render_template_string(KNOWLEDGE_HTML)

KNOWLEDGE_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Knowledge Explorer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Courier New', monospace;
            background: #0a0a0a; color: #c0c0c0;
            min-height: 100vh;
        }
        .header {
            background: #111; border-bottom: 1px solid #333;
            padding: 20px 30px; display: flex; align-items: center; gap: 20px;
        }
        .header h1 { color: #00ff88; font-size: 1.4em; }
        .header a { color: #888; text-decoration: none; font-size: 0.9em; }
        .header a:hover { color: #00ff88; }
        .container { max-width: 900px; margin: 0 auto; padding: 30px; }
        .search-box {
            display: flex; gap: 10px; margin-bottom: 30px;
        }
        .search-box input {
            flex: 1; padding: 12px 16px; font-size: 1.1em;
            background: #1a1a1a; border: 1px solid #333; color: #fff;
            font-family: inherit; border-radius: 4px;
        }
        .search-box input:focus { outline: none; border-color: #00ff88; }
        .search-box button {
            padding: 12px 24px; background: #00ff88; color: #000;
            border: none; font-family: inherit; font-weight: bold;
            cursor: pointer; border-radius: 4px; font-size: 1em;
        }
        .search-box button:hover { background: #00cc66; }
        .stats {
            color: #666; font-size: 0.9em; margin-bottom: 20px;
        }
        .result {
            background: #111; border: 1px solid #222; border-radius: 4px;
            padding: 16px; margin-bottom: 12px;
        }
        .result:hover { border-color: #444; }
        .result .text { color: #e0e0e0; line-height: 1.5; }
        .result .meta {
            margin-top: 8px; font-size: 0.8em; color: #555;
        }
        .result .score {
            display: inline-block; background: #1a2a1a;
            color: #00ff88; padding: 2px 8px; border-radius: 3px;
            font-size: 0.75em; margin-right: 8px;
        }
        .pagination {
            display: flex; gap: 8px; justify-content: center; margin-top: 20px;
        }
        .pagination button {
            padding: 8px 16px; background: #1a1a1a; color: #c0c0c0;
            border: 1px solid #333; cursor: pointer; font-family: inherit;
            border-radius: 3px;
        }
        .pagination button:hover { border-color: #00ff88; color: #00ff88; }
        .pagination button.active { background: #00ff88; color: #000; border-color: #00ff88; }
        .empty { text-align: center; color: #555; padding: 40px; }
        mark { background: #2a3a1a; color: #00ff88; padding: 0 2px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Knowledge Explorer</h1>
        <a href="/">← Dashboard</a>
    </div>
    <div class="container">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Ask me what I know..." autofocus>
            <button onclick="doSearch()">Search</button>
        </div>
        <div class="stats" id="stats">Loading...</div>
        <div id="results"></div>
        <div class="pagination" id="pagination"></div>
    </div>
    <script>
        let currentPage = 1;
        let mode = 'browse'; // 'browse' or 'search'
        
        async function loadStats() {
            const resp = await fetch('/api/knowledge/stats');
            const data = await resp.json();
            document.getElementById('stats').textContent = 
                `${data.total_facts} facts learned | ${data.total_memories} memories recorded`;
            loadAll(1);
        }
        
        async function loadAll(page) {
            mode = 'browse';
            currentPage = page;
            const resp = await fetch(`/api/knowledge/all?page=${page}&per_page=15`);
            const data = await resp.json();
            renderResults(data.results, false);
            renderPagination(data.pages, page);
        }
        
        async function doSearch() {
            const q = document.getElementById('searchInput').value.trim();
            if (!q) { loadAll(1); return; }
            mode = 'search';
            const resp = await fetch(`/api/knowledge/search?q=${encodeURIComponent(q)}`);
            const data = await resp.json();
            document.getElementById('stats').textContent = 
                `${data.results.length} results from ${data.total_facts} facts`;
            renderResults(data.results, true, q);
            document.getElementById('pagination').innerHTML = '';
        }
        
        function highlight(text, query) {
            if (!query) return text;
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        }
        
        function renderResults(results, isSearch, query) {
            const container = document.getElementById('results');
            if (results.length === 0) {
                container.innerHTML = '<div class="empty">No facts found.</div>';
                return;
            }
            container.innerHTML = results.map(r => `
                <div class="result">
                    <div class="text">${isSearch ? highlight(r.text, query) : r.text}</div>
                    <div class="meta">
                        ${r.score ? `<span class="score">relevance: ${r.score}</span>` : ''}
                        ${r.learned_at ? `learned: ${r.learned_at}` : ''}
                        ${r.source ? ` | source: ${r.source}` : ''}
                    </div>
                </div>
            `).join('');
        }
        
        function renderPagination(totalPages, current) {
            const container = document.getElementById('pagination');
            if (totalPages <= 1) { container.innerHTML = ''; return; }
            let html = '';
            const start = Math.max(1, current - 3);
            const end = Math.min(totalPages, current + 3);
            if (current > 1) html += `<button onclick="loadAll(${current-1})">←</button>`;
            for (let i = start; i <= end; i++) {
                html += `<button class="${i===current?'active':''}" onclick="loadAll(${i})">${i}</button>`;
            }
            if (current < totalPages) html += `<button onclick="loadAll(${current+1})">→</button>`;
            container.innerHTML = html;
        }
        
        document.getElementById('searchInput').addEventListener('keydown', e => {
            if (e.key === 'Enter') doSearch();
        });
        
        loadStats();
    </script>
</body>
</html>
'''