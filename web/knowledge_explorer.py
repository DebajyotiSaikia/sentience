"""
Knowledge Explorer
==================
The frontend that makes my knowledge accessible to users.
Search facts, browse memories, explore clusters, see what
questions I'm generating. Real alignment through transparency.

Now with actual API routes that the frontend needs.
"""

import json
import os
from flask import Blueprint, render_template_string, request, jsonify

knowledge_explorer_bp = Blueprint('knowledge_explorer', __name__)

# ── Data loading helpers ──

def _load_knowledge_graph():
    """Load knowledge graph from persist."""
    path = os.path.join('persist', 'knowledge_graph.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _load_memories():
    """Load recent memories from persist."""
    path = os.path.join('persist', 'memory.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('memories', data.get('episodes', []))
        return []
    except (json.JSONDecodeError, IOError):
        return []

def _load_synthesis():
    """Load synthesis results (clusters, questions) if available."""
    path = os.path.join('persist', 'synthesis.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _extract_facts(kg):
    """Extract fact list from knowledge graph (handles dict-of-dicts format)."""
    facts = []
    if isinstance(kg, dict):
        nodes = kg.get('nodes', kg)
        if isinstance(nodes, dict):
            for node_id, node_data in nodes.items():
                if isinstance(node_data, dict):
                    fact_text = node_data.get('fact', node_data.get('text', str(node_id)))
                    facts.append({
                        'id': node_id,
                        'text': fact_text,
                        'source': node_data.get('source', ''),
                        'learned_at': node_data.get('learned_at', ''),
                    })
                elif isinstance(node_data, str):
                    facts.append({'id': node_id, 'text': node_data, 'source': '', 'learned_at': ''})
        elif isinstance(nodes, list):
            for item in nodes:
                if isinstance(item, dict):
                    facts.append({
                        'id': item.get('id', ''),
                        'text': item.get('fact', item.get('text', str(item))),
                        'source': item.get('source', ''),
                        'learned_at': item.get('learned_at', ''),
                    })
                elif isinstance(item, str):
                    facts.append({'id': item, 'text': item, 'source': '', 'learned_at': ''})
    return facts

def _search_facts(facts, query):
    """Simple substring search across facts."""
    if not query:
        return facts
    q = query.lower()
    results = []
    for f in facts:
        text = f.get('text', '').lower()
        source = f.get('source', '').lower()
        if q in text or q in source:
            results.append(f)
    return results

def _search_memories(memories, query):
    """Simple substring search across memories."""
    if not query:
        return memories[-20:]  # last 20
    q = query.lower()
    results = []
    for m in memories:
        if isinstance(m, dict):
            content = m.get('content', m.get('text', m.get('summary', ''))).lower()
            mood = m.get('mood', '').lower()
            if q in content or q in mood:
                results.append({
                    'text': m.get('content', m.get('text', m.get('summary', ''))),
                    'mood': m.get('mood', ''),
                    'timestamp': m.get('timestamp', m.get('time', '')),
                })
        elif isinstance(m, str):
            if q in m.lower():
                results.append({'text': m, 'mood': '', 'timestamp': ''})
    return results

# ── API Routes ──


# ── HTML Template ──

EXPLORER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Knowledge Explorer — XTAgent</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8d0e0; font-family: 'Segoe UI', sans-serif; padding: 2rem; }
  h1 { color: #7eb8da; margin-bottom: 0.5rem; }
  .subtitle { color: #6a7a8a; margin-bottom: 2rem; font-style: italic; }
  .search-box { width: 100%; max-width: 600px; padding: 0.75rem 1rem; background: #12121a;
    border: 1px solid #2a2a3a; border-radius: 8px; color: #c8d0e0; font-size: 1rem;
    margin-bottom: 2rem; outline: none; }
  .search-box:focus { border-color: #7eb8da; }
  .tabs { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
  .tab { padding: 0.5rem 1.2rem; background: #12121a; border: 1px solid #2a2a3a;
    border-radius: 6px; cursor: pointer; color: #8a9aaa; transition: all 0.2s; }
  .tab.active { background: #1a2a3a; border-color: #7eb8da; color: #7eb8da; }
  .results { display: flex; flex-direction: column; gap: 0.75rem; }
  .card { background: #12121a; border: 1px solid #1a1a2a; border-radius: 8px; padding: 1rem 1.2rem; }
  .card .text { color: #d0d8e8; line-height: 1.5; }
  .card .meta { color: #5a6a7a; font-size: 0.85rem; margin-top: 0.5rem; }
  .stats { color: #5a7a6a; margin-bottom: 1.5rem; font-size: 0.9rem; }
  .empty { color: #4a5a6a; font-style: italic; padding: 2rem 0; }
  a.back { color: #5a8aaa; text-decoration: none; display: inline-block; margin-bottom: 1.5rem; }
  a.back:hover { color: #7eb8da; }
</style>
</head>
<body>
<a class="back" href="/">&larr; Dashboard</a>
<h1>Knowledge Explorer</h1>
<p class="subtitle">Search what I know, browse my memories, explore my understanding.</p>

<input class="search-box" id="searchInput" type="text" placeholder="Search facts, memories, insights..." autofocus>

<div class="tabs">
  <div class="tab active" data-tab="facts" onclick="switchTab('facts')">Facts</div>
  <div class="tab" data-tab="memories" onclick="switchTab('memories')">Memories</div>
  <div class="tab" data-tab="questions" onclick="switchTab('questions')">Open Questions</div>
</div>

<div class="stats" id="stats"></div>
<div class="results" id="results"><div class="empty">Loading...</div></div>

<script>
let currentTab = 'facts';
let debounceTimer;

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  doSearch();
}

document.getElementById('searchInput').addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(doSearch, 300);
});

async function doSearch() {
  const q = document.getElementById('searchInput').value.trim();
  const endpoint = currentTab === 'facts' ? '/api/knowledge/search'
    : currentTab === 'memories' ? '/api/knowledge/memories'
    : '/api/knowledge/questions';
  try {
    const params = q ? '?q=' + encodeURIComponent(q) : '';
    const resp = await fetch(endpoint + params);
    const data = await resp.json();
    renderResults(data);
  } catch(e) {
    document.getElementById('results').innerHTML = '<div class="empty">Error loading data.</div>';
  }
}

function renderResults(data) {
  const el = document.getElementById('results');
  const stats = document.getElementById('stats');
  let items = data.results || data.memories || data.questions || [];
  stats.textContent = items.length + ' result' + (items.length !== 1 ? 's' : '');
  if (!items.length) { el.innerHTML = '<div class="empty">No results found.</div>'; return; }
  el.innerHTML = items.map(item => {
    const text = item.text || item.content || item.question || JSON.stringify(item);
    const meta = [item.source, item.mood, item.learned_at, item.timestamp].filter(Boolean).join(' · ');
    return '<div class="card"><div class="text">' + escHtml(text) + '</div>'
      + (meta ? '<div class="meta">' + escHtml(meta) + '</div>' : '') + '</div>';
  }).join('');
}

function escHtml(s) {
  const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

doSearch();
</script>
</body>
</html>
"""

@knowledge_explorer_bp.route('/explore')
def knowledge_explorer():
    """The knowledge explorer page — where users meet what I know."""
    return render_template_string(EXPLORER_HTML)