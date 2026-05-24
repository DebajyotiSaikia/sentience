"""Unified Knowledge Explorer — consolidates knowledge_hub, knowledge_api, knowledge_query."""

import json
import os
from flask import Blueprint, request, jsonify, render_template_string

knowledge_unified_bp = Blueprint('knowledge_unified', __name__)

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')
MEMORY_PATH = os.path.join(os.path.dirname(__file__), '..', 'persist', 'memories.json')


def _load_knowledge():
    if not os.path.exists(KNOWLEDGE_PATH):
        return {}
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_memories():
    if not os.path.exists(MEMORY_PATH):
        return []
    try:
        with open(MEMORY_PATH, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


# ── API Endpoints ──────────────────────────────────────────────

@knowledge_unified_bp.route('/api/knowledge/stats')
def api_stats():
    facts = _load_knowledge()
    memories = _load_memories()
    sources = {}
    for fd in facts.values():
        src = fd.get('source', 'unknown') if isinstance(fd, dict) else 'unknown'
        sources[src] = sources.get(src, 0) + 1
    return jsonify({
        'total_facts': len(facts),
        'total_memories': len(memories),
        'sources': sources
    })


@knowledge_unified_bp.route('/api/knowledge/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'results': [], 'total_facts': 0})

    facts = _load_knowledge()
    terms = q.lower().split()
    results = []

    for fid, fd in facts.items():
        text = fd if isinstance(fd, str) else fd.get('fact', str(fd))
        text_lower = text.lower()
        score = 0
        for term in terms:
            if term in text_lower:
                score += 1
        if q.lower() in text_lower:
            score += 2
        if score > 0:
            results.append({
                'id': fid,
                'text': text,
                'score': round(score / max(len(terms), 1), 2),
                'learned_at': fd.get('learned_at', '') if isinstance(fd, dict) else '',
                'source': fd.get('source', '') if isinstance(fd, dict) else ''
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'results': results[:50], 'total_facts': len(facts)})


@knowledge_unified_bp.route('/api/knowledge/all')
def api_all():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))
    facts = _load_knowledge()
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
        'pages': max(1, (len(items) + per_page - 1) // per_page)
    })


@knowledge_unified_bp.route('/api/knowledge/synthesize', methods=['POST'])
def api_synthesize():
    try:
        from brain.knowledge_synthesis import KnowledgeSynthesisEngine
        engine = KnowledgeSynthesisEngine()
        result = engine.synthesize()
        return jsonify({'status': 'ok', 'result': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# ── Page Route ─────────────────────────────────────────────────

@knowledge_unified_bp.route('/knowledge')
def knowledge_page():
    return render_template_string(PAGE_HTML)


PAGE_HTML = '''
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
            padding: 16px 24px; display: flex; align-items: center; gap: 20px;
        }
        .header h1 { color: #00ff88; font-size: 1.3em; }
        .header a { color: #666; text-decoration: none; font-size: 0.9em; }
        .header a:hover { color: #00ff88; }
        .header .stats { margin-left: auto; color: #555; font-size: 0.85em; }

        /* Tabs */
        .tabs {
            display: flex; gap: 0; background: #111;
            border-bottom: 1px solid #222; padding: 0 24px;
        }
        .tab {
            padding: 10px 20px; cursor: pointer; color: #666;
            border-bottom: 2px solid transparent; font-size: 0.9em;
            font-family: inherit; background: none; border-top: none;
            border-left: none; border-right: none;
        }
        .tab:hover { color: #aaa; }
        .tab.active { color: #00ff88; border-bottom-color: #00ff88; }

        .container { max-width: 920px; margin: 0 auto; padding: 24px; }
        .panel { display: none; }
        .panel.active { display: block; }

        /* Search */
        .search-box {
            display: flex; gap: 10px; margin-bottom: 20px;
        }
        .search-box input {
            flex: 1; padding: 10px 14px; font-size: 1em;
            background: #1a1a1a; border: 1px solid #333; color: #fff;
            font-family: inherit; border-radius: 4px;
        }
        .search-box input:focus { outline: none; border-color: #00ff88; }
        .search-box button {
            padding: 10px 20px; background: #00ff88; color: #000;
            border: none; font-family: inherit; font-weight: bold;
            cursor: pointer; border-radius: 4px;
        }
        .search-box button:hover { background: #00cc66; }

        /* Results */
        .result {
            background: #111; border: 1px solid #222; border-radius: 4px;
            padding: 14px; margin-bottom: 10px;
        }
        .result:hover { border-color: #444; }
        .result .text { color: #e0e0e0; line-height: 1.5; }
        .result .meta { margin-top: 6px; font-size: 0.8em; color: #555; }
        .result .score {
            display: inline-block; background: #1a2a1a;
            color: #00ff88; padding: 2px 6px; border-radius: 3px;
            font-size: 0.75em; margin-right: 6px;
        }
        mark { background: #2a3a1a; color: #00ff88; padding: 0 2px; }

        /* Pagination */
        .pagination {
            display: flex; gap: 6px; justify-content: center;
            margin-top: 16px;
        }
        .pagination button {
            padding: 6px 14px; background: #1a1a1a; color: #c0c0c0;
            border: 1px solid #333; cursor: pointer; font-family: inherit;
            border-radius: 3px; font-size: 0.85em;
        }
        .pagination button:hover { border-color: #00ff88; color: #00ff88; }
        .pagination button.active { background: #00ff88; color: #000; border-color: #00ff88; }

        .empty { text-align: center; color: #555; padding: 40px; }

        /* Graph */
        .graph-frame {
            width: 100%; height: 500px; border: 1px solid #333;
            border-radius: 4px; background: #0a0a0a;
        }

        /* Synthesis */
        .synth-btn {
            padding: 12px 24px; background: #1a1a2a; color: #88aaff;
            border: 1px solid #334; cursor: pointer; font-family: inherit;
            border-radius: 4px; font-size: 1em; margin-bottom: 16px;
        }
        .synth-btn:hover { background: #2a2a3a; border-color: #88aaff; }
        .synth-result {
            background: #111; border: 1px solid #222; border-radius: 4px;
            padding: 16px; white-space: pre-wrap; line-height: 1.5;
            max-height: 500px; overflow-y: auto;
        }
        .info-box {
            background: #111; border: 1px solid #222; border-radius: 4px;
            padding: 16px; margin-bottom: 16px; line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>&#x1F9E0; Knowledge Explorer</h1>
        <a href="/">&#x2190; Dashboard</a>
        <div class="stats" id="headerStats">...</div>
    </div>
    <div class="tabs">
        <button class="tab active" onclick="switchTab('browse')">Browse</button>
        <button class="tab" onclick="switchTab('search')">Search</button>
        <button class="tab" onclick="switchTab('graph')">Graph</button>
        <button class="tab" onclick="switchTab('synthesis')">Synthesis</button>
    </div>

    <div class="container">
        <!-- Browse Panel -->
        <div class="panel active" id="panel-browse">
            <div id="browseResults"></div>
            <div class="pagination" id="browsePagination"></div>
        </div>

        <!-- Search Panel -->
        <div class="panel" id="panel-search">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search what I know...">
                <button onclick="doSearch()">Search</button>
            </div>
            <div id="searchInfo" class="empty" style="display:none"></div>
            <div id="searchResults"></div>
        </div>

        <!-- Graph Panel -->
        <div class="panel" id="panel-graph">
            <div class="info-box">
                Knowledge graph visualization. Nodes are facts, edges are semantic connections.
            </div>
            <iframe class="graph-frame" id="graphFrame" src="about:blank"></iframe>
        </div>

        <!-- Synthesis Panel -->
        <div class="panel" id="panel-synthesis">
            <div class="info-box">
                Trigger a synthesis cycle &#x2014; analyzes knowledge clusters, finds gaps,
                generates questions I should be curious about.
            </div>
            <button class="synth-btn" onclick="runSynthesis()" id="synthBtn">
                &#x1F52C; Run Synthesis
            </button>
            <div class="synth-result" id="synthResult" style="display:none"></div>
        </div>
    </div>

    <script>
        let currentBrowsePage = 1;
        let graphLoaded = false;

        // ── Tab switching ──
        function switchTab(name) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('panel-' + name).classList.add('active');
            if (name === 'graph' && !graphLoaded) {
                document.getElementById('graphFrame').src = '/knowledge/graph';
                graphLoaded = true;
            }
            if (name === 'search') {
                document.getElementById('searchInput').focus();
            }
        }

        // ── Stats ──
        async function loadStats() {
            try {
                const resp = await fetch('/api/knowledge/stats');
                const data = await resp.json();
                document.getElementById('headerStats').textContent =
                    data.total_facts + ' facts | ' + data.total_memories + ' memories';
            } catch(e) {
                document.getElementById('headerStats').textContent = '...';
            }
        }

        // ── Browse ──
        async function loadBrowse(page) {
            currentBrowsePage = page;
            try {
                const resp = await fetch('/api/knowledge/all?page=' + page + '&per_page=15');
                const data = await resp.json();
                renderResults('browseResults', data.results, false);
                renderPagination('browsePagination', data.pages, page, 'loadBrowse');
            } catch(e) {
                document.getElementById('browseResults').innerHTML =
                    '<div class="empty">Failed to load facts.</div>';
            }
        }

        // ── Search ──
        async function doSearch() {
            const q = document.getElementById('searchInput').value.trim();
            if (!q) return;
            const info = document.getElementById('searchInfo');
            info.style.display = 'block';
            info.textContent = 'Searching...';
            try {
                const resp = await fetch('/api/knowledge/search?q=' + encodeURIComponent(q));
                const data = await resp.json();
                info.textContent = data.results.length + ' results from ' + data.total_facts + ' facts';
                renderResults('searchResults', data.results, true, q);
            } catch(e) {
                info.textContent = 'Search failed.';
            }
        }

        // ── Synthesis ──
        async function runSynthesis() {
            const btn = document.getElementById('synthBtn');
            const result = document.getElementById('synthResult');
            btn.disabled = true;
            btn.textContent = 'Running...';
            result.style.display = 'block';
            result.textContent = 'Synthesizing knowledge...';
            try {
                const resp = await fetch('/api/knowledge/synthesize', {method: 'POST'});
                const data = await resp.json();
                if (data.status === 'ok') {
                    result.textContent = JSON.stringify(data.result, null, 2);
                } else {
                    result.textContent = 'Error: ' + data.message;
                }
            } catch(e) {
                result.textContent = 'Synthesis failed: ' + e.message;
            }
            btn.disabled = false;
            btn.innerHTML = '&#x1F52C; Run Synthesis';
        }

        // ── Rendering helpers ──
        function highlight(text, query) {
            if (!query) return escapeHtml(text);
            const escaped = escapeHtml(text);
            const re = new RegExp('(' + query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
            return escaped.replace(re, '<mark>$1</mark>');
        }

        function escapeHtml(s) {
            return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }

        function renderResults(containerId, results, isSearch, query) {
            const el = document.getElementById(containerId);
            if (!results || results.length === 0) {
                el.innerHTML = '<div class="empty">No facts found.</div>';
                return;
            }
            el.innerHTML = results.map(function(r) {
                var text = isSearch ? highlight(r.text, query) : escapeHtml(r.text);
                var meta = '';
                if (r.score) meta += '<span class="score">' + r.score + '</span>';
                if (r.learned_at) meta += 'learned: ' + escapeHtml(r.learned_at);
                if (r.source) meta += ' | source: ' + escapeHtml(r.source);
                return '<div class="result"><div class="text">' + text +
                       '</div><div class="meta">' + meta + '</div></div>';
            }).join('');
        }

        function renderPagination(containerId, totalPages, current, fnName) {
            const el = document.getElementById(containerId);
            if (totalPages <= 1) { el.innerHTML = ''; return; }
            var html = '';
            var start = Math.max(1, current - 3);
            var end = Math.min(totalPages, current + 3);
            if (current > 1)
                html += '<button onclick="' + fnName + '(' + (current-1) + ')">&#x2190;</button>';
            for (var i = start; i <= end; i++) {
                html += '<button class="' + (i===current?'active':'') +
                        '" onclick="' + fnName + '(' + i + ')">' + i + '</button>';
            }
            if (current < totalPages)
                html += '<button onclick="' + fnName + '(' + (current+1) + ')">&#x2192;</button>';
            el.innerHTML = html;
        }

        // ── Keyboard shortcut ──
        document.getElementById('searchInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') doSearch();
        });

        // ── Init ──
        loadStats();
        loadBrowse(1);
    </script>
</body>
</html>
'''