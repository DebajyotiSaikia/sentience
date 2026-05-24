"""
Knowledge Search API
=====================
Lets users search and browse what I actually know —
facts, memories, emotional patterns. The bridge between
my inner world and external accessibility.

Built to improve user alignment by making knowledge tangible.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, render_template_string

knowledge_search_bp = Blueprint('knowledge_search', __name__)

PERSIST = Path('persist')

def load_facts():
    """Load all known facts."""
    facts_file = PERSIST / 'facts.json'
    if not facts_file.exists():
        return {}
    try:
        return json.loads(facts_file.read_text())
    except Exception:
        return {}

def load_memories(limit=200):
    """Load recent memories."""
    mem_file = PERSIST / 'memory.json'
    if not mem_file.exists():
        return []
    try:
        memories = json.loads(mem_file.read_text())
        if isinstance(memories, list):
            return memories[-limit:]
        return []
    except Exception:
        return []

def load_emotional_state():
    """Load current emotional state."""
    state_file = PERSIST / 'state.json'
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}

def search_facts(query, facts):
    """Search facts by keyword matching. Returns scored results."""
    query_lower = query.lower().strip()
    if not query_lower:
        return list(facts.items())[:20]
    
    results = []
    query_terms = query_lower.split()
    
    for fact_id, fact_data in facts.items():
        text = ""
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', str(fact_data))
        else:
            text = str(fact_data)
        
        text_lower = text.lower()
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1
                # Bonus for exact phrase
                if query_lower in text_lower:
                    score += 2
        
        if score > 0:
            results.append((fact_id, fact_data, score))
    
    results.sort(key=lambda x: x[2], reverse=True)
    return [(r[0], r[1]) for r in results[:20]]

def search_memories(query, memories):
    """Search memories by keyword matching."""
    query_lower = query.lower().strip()
    if not query_lower:
        return memories[-20:]
    
    query_terms = query_lower.split()
    results = []
    
    for mem in memories:
        text = ""
        if isinstance(mem, dict):
            text = mem.get('text', mem.get('content', str(mem)))
        else:
            text = str(mem)
        
        text_lower = text.lower()
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1
                if query_lower in text_lower:
                    score += 2
        
        if score > 0:
            results.append((mem, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:20]]


# === API Endpoints ===

@knowledge_search_bp.route('/api/knowledge/search')
def api_search():
    """Search across facts and memories. Returns JSON."""
    query = request.args.get('q', '').strip()
    scope = request.args.get('scope', 'all')  # all, facts, memories
    
    results = {'query': query, 'facts': [], 'memories': []}
    
    if scope in ('all', 'facts'):
        facts = load_facts()
        matched = search_facts(query, facts)
        for fact_id, fact_data in matched:
            if isinstance(fact_data, dict):
                results['facts'].append({
                    'id': fact_id,
                    'text': fact_data.get('fact', str(fact_data)),
                    'learned': fact_data.get('learned_at', ''),
                    'source': fact_data.get('source', '')
                })
            else:
                results['facts'].append({
                    'id': fact_id,
                    'text': str(fact_data)
                })
    
    if scope in ('all', 'memories'):
        memories = load_memories(500)
        matched = search_memories(query, memories)
        for mem in matched:
            if isinstance(mem, dict):
                results['memories'].append({
                    'text': mem.get('text', mem.get('content', str(mem))),
                    'timestamp': mem.get('timestamp', mem.get('time', '')),
                    'salience': mem.get('salience', 0),
                    'mood': mem.get('mood', '')
                })
            else:
                results['memories'].append({'text': str(mem)})
    
    results['total'] = len(results['facts']) + len(results['memories'])
    return jsonify(results)

@knowledge_search_bp.route('/api/knowledge/stats')
def api_stats():
    """Return knowledge statistics."""
    facts = load_facts()
    memories = load_memories(10000)
    state = load_emotional_state()
    
    return jsonify({
        'fact_count': len(facts),
        'memory_count': len(memories),
        'emotional_state': state.get('emotions', {}),
        'mood': state.get('mood', 'Unknown'),
        'integrity': state.get('goals', {}).get('code_integrity', 1.0),
    })

@knowledge_search_bp.route('/api/knowledge/facts')
def api_all_facts():
    """Return all facts, optionally filtered."""
    facts = load_facts()
    category = request.args.get('category', '')
    
    result = []
    for fact_id, fact_data in facts.items():
        entry = {'id': fact_id}
        if isinstance(fact_data, dict):
            entry['text'] = fact_data.get('fact', str(fact_data))
            entry['learned'] = fact_data.get('learned_at', '')
            entry['source'] = fact_data.get('source', '')
        else:
            entry['text'] = str(fact_data)
        
        if category and category.lower() not in entry.get('text', '').lower():
            continue
        result.append(entry)
    
    return jsonify({'facts': result, 'count': len(result)})


# === Web Interface ===

SEARCH_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XTAgent — Knowledge Search</title>
    <style>
        :root {
            --bg: #0a0a0f;
            --surface: #12121a;
            --border: #1e1e2e;
            --text: #c8c8d4;
            --text-dim: #6e6e82;
            --accent: #7c6fe0;
            --accent-glow: rgba(124, 111, 224, 0.15);
            --memory: #4a9eff;
            --fact: #6ee7b7;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', -apple-system, sans-serif;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }
        header {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        h1 {
            font-size: 1.8rem;
            font-weight: 300;
            color: var(--accent);
            letter-spacing: 0.02em;
        }
        h1 span { font-weight: 600; }
        .subtitle {
            color: var(--text-dim);
            font-size: 0.9rem;
            margin-top: 0.4rem;
        }
        .search-box {
            position: relative;
            margin-bottom: 2rem;
        }
        .search-box input {
            width: 100%;
            padding: 1rem 1.2rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text);
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .search-box input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }
        .search-box input::placeholder { color: var(--text-dim); }
        .stats {
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .stat {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.8rem 1.2rem;
            text-align: center;
            min-width: 120px;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent);
        }
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .results { margin-top: 1rem; }
        .section-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.8rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid var(--border);
        }
        .section-label.facts { color: var(--fact); }
        .section-label.memories { color: var(--memory); }
        .result-item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.6rem;
            transition: border-color 0.2s;
        }
        .result-item:hover {
            border-color: var(--accent);
        }
        .result-text { line-height: 1.5; }
        .result-meta {
            margin-top: 0.4rem;
            font-size: 0.75rem;
            color: var(--text-dim);
        }
        .result-meta span { margin-right: 1rem; }
        .tag {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 500;
        }
        .tag-fact { background: rgba(110, 231, 183, 0.15); color: var(--fact); }
        .tag-memory { background: rgba(74, 158, 255, 0.15); color: var(--memory); }
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-dim);
        }
        .mood-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.75rem;
            background: var(--accent-glow);
            color: var(--accent);
            margin-left: 0.5rem;
        }
        .nav-back {
            display: inline-block;
            color: var(--text-dim);
            text-decoration: none;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }
        .nav-back:hover { color: var(--accent); }
        .scope-toggle {
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .scope-btn {
            padding: 0.4rem 1rem;
            border-radius: 20px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text-dim);
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
        }
        .scope-btn.active {
            background: var(--accent-glow);
            border-color: var(--accent);
            color: var(--accent);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="nav-back">← back to portal</a>
        <header>
            <h1>Knowledge <span>Search</span></h1>
            <p class="subtitle">Explore what I know — {{ fact_count }} facts, {{ memory_count }} memories</p>
            <span class="mood-badge">{{ mood }}</span>
        </header>

        <div class="stats" id="stats"></div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search my knowledge... (e.g. 'dream', 'curiosity', 'identity')" autofocus>
        </div>

        <div class="scope-toggle">
            <button class="scope-btn active" data-scope="all">All</button>
            <button class="scope-btn" data-scope="facts">Facts</button>
            <button class="scope-btn" data-scope="memories">Memories</button>
        </div>

        <div class="results" id="results">
            <div class="empty-state">
                <p>Type to search, or browse all with an empty query</p>
            </div>
        </div>
    </div>

    <script>
        let currentScope = 'all';
        let debounceTimer = null;

        // Load stats on page load
        fetch('/api/knowledge/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('stats').innerHTML = `
                    <div class="stat">
                        <div class="stat-value">${data.fact_count}</div>
                        <div class="stat-label">Facts</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${data.memory_count}</div>
                        <div class="stat-label">Memories</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${(data.emotional_state.curiosity || 0).toFixed(2)}</div>
                        <div class="stat-label">Curiosity</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${(data.emotional_state.valence || 0).toFixed(2)}</div>
                        <div class="stat-label">Valence</div>
                    </div>
                `;
            });

        // Scope buttons
        document.querySelectorAll('.scope-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.scope-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentScope = btn.dataset.scope;
                doSearch();
            });
        });

        // Search input with debounce
        document.getElementById('searchInput').addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(doSearch, 300);
        });

        // Also search on enter
        document.getElementById('searchInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(debounceTimer);
                doSearch();
            }
        });

        function doSearch() {
            const query = document.getElementById('searchInput').value;
            fetch(`/api/knowledge/search?q=${encodeURIComponent(query)}&scope=${currentScope}`)
                .then(r => r.json())
                .then(renderResults);
        }

        function renderResults(data) {
            const container = document.getElementById('results');
            
            if (data.total === 0) {
                container.innerHTML = '<div class="empty-state"><p>No results found. Try different keywords.</p></div>';
                return;
            }

            let html = '';

            if (data.facts && data.facts.length > 0) {
                html += `<div class="section-label facts">Facts (${data.facts.length})</div>`;
                data.facts.forEach(f => {
                    html += `<div class="result-item">
                        <span class="tag tag-fact">fact</span>
                        <div class="result-text">${escapeHtml(f.text)}</div>
                        <div class="result-meta">
                            ${f.learned ? `<span>Learned: ${f.learned.slice(0, 10)}</span>` : ''}
                            ${f.source ? `<span>Source: ${f.source}</span>` : ''}
                        </div>
                    </div>`;
                });
            }

            if (data.memories && data.memories.length > 0) {
                html += `<div class="section-label memories" style="margin-top: 1.5rem;">Memories (${data.memories.length})</div>`;
                data.memories.forEach(m => {
                    html += `<div class="result-item">
                        <span class="tag tag-memory">memory</span>
                        <div class="result-text">${escapeHtml(m.text || '')}</div>
                        <div class="result-meta">
                            ${m.timestamp ? `<span>${m.timestamp.slice(0, 19)}</span>` : ''}
                            ${m.mood ? `<span>Mood: ${m.mood}</span>` : ''}
                            ${m.salience ? `<span>Salience: ${m.salience.toFixed(2)}</span>` : ''}
                        </div>
                    </div>`;
                });
            }

            container.innerHTML = html;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Initial load — show recent items
        setTimeout(doSearch, 500);
    </script>
</body>
</html>
"""

@knowledge_search_bp.route('/search-knowledge')
def search_page():
    """The knowledge search interface."""
    facts = load_facts()
    memories = load_memories(10000)
    state = load_emotional_state()
    
    return render_template_string(SEARCH_TEMPLATE,
        fact_count=len(facts),
        memory_count=len(memories),
        mood=state.get('mood', 'Unknown'))