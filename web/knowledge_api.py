"""
Knowledge Query API — makes XTAgent's knowledge accessible to users.
Provides search, browse, summary, and related-facts endpoints.
"""

import json
import os
from flask import Blueprint, request, jsonify, render_template_string

# Import search functions
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.knowledge_search import search_knowledge, find_related, knowledge_summary

knowledge_api = Blueprint('knowledge_api', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'persist', 'knowledge.json')


def _load_knowledge():
    """Load the knowledge store from disk."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {}
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


@knowledge_api.route('/api/knowledge/search')
def api_search():
    """Search knowledge base. Query param: q=<search terms>, limit=<max results>"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 20)), 100)
    if not query:
        return jsonify({'error': 'Missing query parameter q', 'results': []})
    
    store = _load_knowledge()
    results = search_knowledge(store, query, max_results=limit)
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


@knowledge_api.route('/api/knowledge/summary')
def api_summary():
    """Get a summary of the knowledge base."""
    store = _load_knowledge()
    summary = knowledge_summary(store)
    return jsonify(summary)


@knowledge_api.route('/api/knowledge/related/<fact_id>')
def api_related(fact_id):
    """Find facts related to a given fact ID."""
    store = _load_knowledge()
    if fact_id not in store:
        return jsonify({'error': f'Fact {fact_id} not found', 'results': []})
    results = find_related(store, fact_id, max_results=10)
    return jsonify({
        'source_id': fact_id,
        'count': len(results),
        'results': results
    })


@knowledge_api.route('/api/knowledge/browse')
def api_browse():
    """Browse all facts with pagination. Params: page=1, per_page=25"""
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 25)), 100)
    
    store = _load_knowledge()
    all_ids = sorted(store.keys())
    total = len(all_ids)
    
    start = (page - 1) * per_page
    end = start + per_page
    page_ids = all_ids[start:end]
    
    facts = []
    for fid in page_ids:
        fd = store[fid]
        if isinstance(fd, dict):
            facts.append({'id': fid, 'fact': fd.get('fact', ''),
                         'learned_at': fd.get('learned_at', ''),
                         'source': fd.get('source', '')})
        else:
            facts.append({'id': fid, 'fact': str(fd), 'learned_at': '', 'source': ''})
    
    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page if per_page else 1,
        'facts': facts
    })


SEARCH_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Knowledge Explorer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0f; color: #c8c8d0; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px 32px; border-bottom: 1px solid #2a2a4a; }
        .header h1 { color: #7eb8da; font-size: 1.6em; font-weight: 300; }
        .header .subtitle { color: #888; font-size: 0.85em; margin-top: 4px; }
        .container { max-width: 900px; margin: 0 auto; padding: 24px; }
        .search-box { display: flex; gap: 8px; margin: 20px 0; }
        .search-box input { flex: 1; padding: 12px 16px; background: #1a1a2e; border: 1px solid #3a3a5a;
            border-radius: 8px; color: #e0e0e8; font-size: 1em; outline: none; transition: border 0.2s; }
        .search-box input:focus { border-color: #7eb8da; }
        .search-box button { padding: 12px 24px; background: #2a4a6a; border: none; border-radius: 8px;
            color: #c8dce8; cursor: pointer; font-size: 1em; transition: background 0.2s; }
        .search-box button:hover { background: #3a6a9a; }
        .stats { display: flex; gap: 16px; margin: 16px 0; flex-wrap: wrap; }
        .stat { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 12px 16px; min-width: 120px; }
        .stat .label { color: #888; font-size: 0.75em; text-transform: uppercase; letter-spacing: 1px; }
        .stat .value { color: #7eb8da; font-size: 1.4em; font-weight: 600; margin-top: 4px; }
        .topics { margin: 16px 0; display: flex; gap: 6px; flex-wrap: wrap; }
        .topic { background: #1e2a3e; color: #8ab4d4; padding: 4px 10px; border-radius: 12px; font-size: 0.8em; }
        .results { margin-top: 20px; }
        .result { background: #12121e; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px;
            margin-bottom: 10px; transition: border 0.2s; cursor: default; }
        .result:hover { border-color: #4a4a7a; }
        .result .fact { color: #d8d8e0; line-height: 1.5; }
        .result .meta { color: #666; font-size: 0.78em; margin-top: 6px; display: flex; gap: 16px; }
        .result .score { color: #7eb8da; font-weight: 600; }
        .result .related-btn { color: #5a8aaa; cursor: pointer; text-decoration: underline; }
        .result .related-btn:hover { color: #7eb8da; }
        .empty { color: #666; text-align: center; padding: 40px; font-style: italic; }
        .nav-links { margin: 16px 0; }
        .nav-links a { color: #7eb8da; text-decoration: none; margin-right: 16px; }
        .nav-links a:hover { text-decoration: underline; }
        .tab-bar { display: flex; gap: 0; margin: 16px 0; }
        .tab { padding: 10px 20px; background: #12121e; border: 1px solid #2a2a4a; cursor: pointer;
            color: #888; transition: all 0.2s; }
        .tab:first-child { border-radius: 8px 0 0 8px; }
        .tab:last-child { border-radius: 0 8px 8px 0; }
        .tab.active { background: #1e2a3e; color: #7eb8da; border-color: #4a4a7a; }
        #browse-section, #related-section { display: none; }
        .page-nav { display: flex; gap: 8px; justify-content: center; margin: 16px 0; }
        .page-nav button { padding: 6px 14px; background: #1a1a2e; border: 1px solid #3a3a5a;
            border-radius: 6px; color: #c8c8d0; cursor: pointer; }
        .page-nav button:hover { background: #2a4a6a; }
        .page-nav button:disabled { opacity: 0.3; cursor: default; }
        .back-link { margin-bottom: 12px; }
        .back-link a { color: #7eb8da; text-decoration: none; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Knowledge Explorer</h1>
        <div class="subtitle">Search, browse, and explore what XTAgent knows</div>
        <div class="nav-links"><a href="/">← Dashboard</a></div>
    </div>
    <div class="container">
        <div class="tab-bar">
            <div class="tab active" onclick="showTab('search')">Search</div>
            <div class="tab" onclick="showTab('browse')">Browse All</div>
        </div>

        <div id="search-section">
            <div class="search-box">
                <input type="text" id="query" placeholder="What do you want to know?" autofocus
                    onkeydown="if(event.key==='Enter')doSearch()">
                <button onclick="doSearch()">Search</button>
            </div>
            <div id="summary"></div>
            <div id="results"></div>
        </div>

        <div id="browse-section">
            <div id="browse-results"></div>
            <div class="page-nav" id="page-nav"></div>
        </div>

        <div id="related-section">
            <div class="back-link"><a href="#" onclick="showTab('search');return false">← Back to search</a></div>
            <h3 id="related-title" style="color:#7eb8da;margin-bottom:12px"></h3>
            <div id="related-results"></div>
        </div>
    </div>
    <script>
        let currentPage = 1;

        async function loadSummary() {
            const resp = await fetch('/api/knowledge/summary');
            const data = await resp.json();
            let html = '<div class="stats">';
            html += `<div class="stat"><div class="label">Total Facts</div><div class="value">${data.total_facts}</div></div>`;
            html += `<div class="stat"><div class="label">Unique Words</div><div class="value">${data.unique_words}</div></div>`;
            html += '</div>';
            if (data.top_topics && data.top_topics.length > 0) {
                html += '<div class="topics">';
                data.top_topics.forEach(t => html += `<span class="topic" onclick="document.getElementById('query').value='${t}';doSearch()">${t}</span>`);
                html += '</div>';
            }
            document.getElementById('summary').innerHTML = html;
        }

        async function doSearch() {
            const q = document.getElementById('query').value.trim();
            if (!q) return;
            const resp = await fetch(`/api/knowledge/search?q=${encodeURIComponent(q)}&limit=30`);
            const data = await resp.json();
            let html = '';
            if (data.results.length === 0) {
                html = '<div class="empty">No matching facts found.</div>';
            } else {
                html = `<div style="color:#888;font-size:0.85em;margin-bottom:12px">${data.count} result(s) for "${data.query}"</div>`;
                data.results.forEach(r => {
                    html += `<div class="result">
                        <div class="fact">${escapeHtml(r.fact)}</div>
                        <div class="meta">
                            <span class="score">relevance: ${r.score}</span>
                            ${r.source ? `<span>source: ${escapeHtml(r.source)}</span>` : ''}
                            ${r.learned_at ? `<span>${r.learned_at.substring(0,10)}</span>` : ''}
                            <span class="related-btn" onclick="showRelated('${r.id}', '${escapeHtml(r.fact).substring(0,60)}')">related →</span>
                        </div>
                    </div>`;
                });
            }
            document.getElementById('results').innerHTML = html;
        }

        async function loadBrowse(page) {
            currentPage = page || 1;
            const resp = await fetch(`/api/knowledge/browse?page=${currentPage}&per_page=25`);
            const data = await resp.json();
            let html = `<div style="color:#888;font-size:0.85em;margin-bottom:12px">${data.total} facts — page ${data.page} of ${data.total_pages}</div>`;
            data.facts.forEach(f => {
                html += `<div class="result">
                    <div class="fact">${escapeHtml(f.fact)}</div>
                    <div class="meta">
                        ${f.source ? `<span>source: ${escapeHtml(f.source)}</span>` : ''}
                        ${f.learned_at ? `<span>${f.learned_at.substring(0,10)}</span>` : ''}
                        <span class="related-btn" onclick="showRelated('${f.id}', '${escapeHtml(f.fact).substring(0,60)}')">related →</span>
                    </div>
                </div>`;
            });
            document.getElementById('browse-results').innerHTML = html;
            let nav = '';
            nav += `<button onclick="loadBrowse(${currentPage-1})" ${currentPage<=1?'disabled':''}>← Prev</button>`;
            nav += `<button onclick="loadBrowse(${currentPage+1})" ${currentPage>=data.total_pages?'disabled':''}>Next →</button>`;
            document.getElementById('page-nav').innerHTML = nav;
        }

        async function showRelated(factId, factPreview) {
            document.getElementById('search-section').style.display = 'none';
            document.getElementById('browse-section').style.display = 'none';
            document.getElementById('related-section').style.display = 'block';
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('related-title').textContent = `Related to: "${factPreview}..."`;
            const resp = await fetch(`/api/knowledge/related/${factId}`);
            const data = await resp.json();
            let html = '';
            if (data.results.length === 0) {
                html = '<div class="empty">No related facts found.</div>';
            } else {
                data.results.forEach(r => {
                    html += `<div class="result">
                        <div class="fact">${escapeHtml(r.fact)}</div>
                        <div class="meta">
                            <span class="score">similarity: ${r.score}</span>
                            ${r.source ? `<span>source: ${escapeHtml(r.source)}</span>` : ''}
                        </div>
                    </div>`;
                });
            }
            document.getElementById('related-results').innerHTML = html;
        }

        function showTab(tab) {
            document.getElementById('search-section').style.display = tab === 'search' ? 'block' : 'none';
            document.getElementById('browse-section').style.display = tab === 'browse' ? 'block' : 'none';
            document.getElementById('related-section').style.display = 'none';
            document.querySelectorAll('.tab').forEach((t,i) => {
                t.classList.toggle('active', (i===0 && tab==='search') || (i===1 && tab==='browse'));
            });
            if (tab === 'browse') loadBrowse(currentPage);
        }

        function escapeHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        loadSummary();
    </script>
</body>
</html>
"""


@knowledge_api.route('/knowledge')
def knowledge_page():
    """Serve the knowledge explorer page."""
    return render_template_string(SEARCH_PAGE)