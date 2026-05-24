"""Knowledge search routes — lets users query what I know."""

from flask import Blueprint, request, jsonify, render_template_string
from engine.knowledge_search import search_knowledge, find_related, knowledge_summary

knowledge_bp = Blueprint('knowledge', __name__)

SEARCH_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>XTAgent — Knowledge Search</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c0c0d0; font-family: 'Segoe UI', sans-serif; }
  .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
  h1 { color: #7af; margin-bottom: 0.5rem; font-size: 1.8rem; }
  .subtitle { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
  .search-box { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  .search-box input {
    flex: 1; padding: 0.75rem 1rem; background: #151520; border: 1px solid #333;
    color: #e0e0f0; border-radius: 6px; font-size: 1rem; outline: none;
  }
  .search-box input:focus { border-color: #7af; }
  .search-box button {
    padding: 0.75rem 1.5rem; background: #2a4a7a; color: #fff; border: none;
    border-radius: 6px; cursor: pointer; font-size: 1rem;
  }
  .search-box button:hover { background: #3a6aaa; }
  .tabs { display: flex; gap: 0.25rem; margin-bottom: 1rem; }
  .tab {
    padding: 0.5rem 1rem; background: #1a1a25; border: 1px solid #333;
    border-bottom: none; border-radius: 6px 6px 0 0; cursor: pointer; color: #888;
  }
  .tab.active { background: #151520; color: #7af; border-color: #7af; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
  .stat-card { background: #151520; border: 1px solid #252530; border-radius: 8px; padding: 1rem; }
  .stat-value { font-size: 1.8rem; color: #7af; font-weight: bold; }
  .stat-label { color: #888; font-size: 0.8rem; margin-top: 0.25rem; }
  .results { display: flex; flex-direction: column; gap: 0.75rem; }
  .result-card {
    background: #151520; border: 1px solid #252530; border-radius: 8px;
    padding: 1rem; transition: border-color 0.2s;
  }
  .result-card:hover { border-color: #7af; }
  .result-text { color: #d0d0e0; line-height: 1.5; }
  .result-meta { color: #666; font-size: 0.8rem; margin-top: 0.5rem; }
  .result-score { color: #7af; font-weight: bold; }
  .empty { color: #666; text-align: center; padding: 3rem; font-style: italic; }
  .back-link { color: #7af; text-decoration: none; display: inline-block; margin-bottom: 1rem; }
  .back-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="container">
  <a href="/" class="back-link">← Dashboard</a>
  <h1>🔍 Knowledge Search</h1>
  <p class="subtitle">Query my memories, facts, and experiences</p>

  <div id="stats" class="stats"></div>

  <div class="search-box">
    <input type="text" id="query" placeholder="Ask me what I know..." autofocus
      onkeydown="if(event.key==='Enter')doSearch()">
    <button onclick="doSearch()">Search</button>
  </div>

  <div class="tabs">
    <div class="tab active" data-tab="all" onclick="switchTab('all')">All</div>
    <div class="tab" data-tab="facts" onclick="switchTab('facts')">Facts</div>
    <div class="tab" data-tab="episodes" onclick="switchTab('episodes')">Episodes</div>
  </div>

  <div id="results" class="results">
    <div class="empty">Type a query to explore my knowledge...</div>
  </div>
</div>

<script>
let currentTab = 'all';
let lastResults = {};

async function loadStats() {
  const r = await fetch('/api/knowledge/stats');
  const stats = await r.json();
  const el = document.getElementById('stats');
  el.innerHTML = Object.entries(stats).map(([k,v]) =>
    `<div class="stat-card"><div class="stat-value">${v}</div><div class="stat-label">${k.replace(/_/g,' ')}</div></div>`
  ).join('');
}

async function doSearch() {
  const q = document.getElementById('query').value.trim();
  if (!q) return;
  const r = await fetch('/api/knowledge/search?q=' + encodeURIComponent(q) + '&type=' + currentTab);
  lastResults = await r.json();
  renderResults();
}

function renderResults() {
  const el = document.getElementById('results');
  const items = lastResults.results || [];
  if (items.length === 0) {
    el.innerHTML = '<div class="empty">No results found.</div>';
    return;
  }
  el.innerHTML = items.map(r => {
    const score = r.score !== undefined ? `<span class="result-score">${(r.score * 100).toFixed(0)}%</span> · ` : '';
    const source = r.source || r.type || '';
    const time = r.timestamp || r.learned_at || '';
    return `<div class="result-card">
      <div class="result-text">${escHtml(r.text || r.fact || r.content || JSON.stringify(r))}</div>
      <div class="result-meta">${score}${source}${time ? ' · ' + time : ''}</div>
    </div>`;
  }).join('');
}

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  const q = document.getElementById('query').value.trim();
  if (q) doSearch();
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

loadStats();
</script>
</body>
</html>
"""


@knowledge_bp.route('/knowledge')
def knowledge_page():
    return render_template_string(SEARCH_PAGE)


@knowledge_bp.route('/api/knowledge/stats')
def api_stats():
    try:
        stats = knowledge_summary()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@knowledge_bp.route('/api/knowledge/search')
def api_search():
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    
    if not query:
        return jsonify({"results": [], "query": ""})
    
    results = []
    
    try:
        raw = search_knowledge(query, search_type=search_type)
        if isinstance(raw, list):
            for item in raw[:40]:
                if isinstance(item, dict):
                    item.setdefault("text", item.get("fact", item.get("content", str(item))))
                    item.setdefault("type", search_type if search_type != "all" else "result")
                    item.setdefault("score", item.get("relevance", 0.5))
                    results.append(item)
                else:
                    results.append({"text": str(item), "type": "result", "score": 0.5})
        elif isinstance(raw, dict):
            for k, v in list(raw.items())[:40]:
                item = v if isinstance(v, dict) else {"text": str(v)}
                item.setdefault("text", item.get("fact", str(v)))
                item.setdefault("type", "result")
                item.setdefault("score", item.get("relevance", 0.5))
                results.append(item)
        
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
    except Exception as e:
        return jsonify({"results": [], "error": str(e), "query": query})
    
    return jsonify({"results": results[:40], "query": query, "count": len(results)})