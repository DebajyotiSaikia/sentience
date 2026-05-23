"""
Knowledge Explorer — Web interface for browsing XTAgent's knowledge graph.
Lets users (and me) see what I know, find clusters, and explore connections.
"""

from flask import Blueprint, render_template_string, jsonify
import json
import os

knowledge_bp = Blueprint('knowledge', __name__)

KNOWLEDGE_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Knowledge Explorer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0f; color: #c8d0e0; font-family: 'Courier New', monospace; }
        .header { padding: 20px 30px; border-bottom: 1px solid #1a1a2e; }
        .header h1 { color: #7eb8da; font-size: 1.4em; }
        .header .subtitle { color: #556; font-size: 0.85em; margin-top: 4px; }
        .container { display: grid; grid-template-columns: 300px 1fr; height: calc(100vh - 80px); }
        .sidebar { border-right: 1px solid #1a1a2e; padding: 15px; overflow-y: auto; }
        .main { padding: 20px; overflow-y: auto; }
        .search-box { width: 100%; padding: 8px 12px; background: #12121a; border: 1px solid #2a2a3e;
                       color: #c8d0e0; font-family: inherit; font-size: 0.9em; border-radius: 4px;
                       margin-bottom: 15px; }
        .search-box:focus { outline: none; border-color: #7eb8da; }
        .stat-row { display: flex; justify-content: space-between; padding: 6px 0;
                    border-bottom: 1px solid #111; font-size: 0.85em; }
        .stat-label { color: #556; }
        .stat-value { color: #7eb8da; }
        .cluster-tag { display: inline-block; padding: 3px 10px; margin: 3px; border-radius: 12px;
                       font-size: 0.8em; cursor: pointer; border: 1px solid #2a2a3e;
                       background: #12121a; transition: all 0.2s; }
        .cluster-tag:hover { border-color: #7eb8da; background: #1a1a2e; }
        .cluster-tag.active { border-color: #7eb8da; background: #1a2a3e; color: #9ed0f0; }
        .fact-card { background: #12121a; border: 1px solid #1a1a2e; border-radius: 6px;
                     padding: 14px 18px; margin-bottom: 10px; transition: border-color 0.2s;
                     line-height: 1.5; font-size: 0.9em; }
        .fact-card:hover { border-color: #2a3a4e; }
        .fact-card .fact-text { color: #c8d0e0; }
        .fact-card .fact-meta { color: #445; font-size: 0.8em; margin-top: 6px; }
        .section-title { color: #556; font-size: 0.8em; text-transform: uppercase;
                         letter-spacing: 1px; margin: 15px 0 8px 0; }
        .gap-item { padding: 8px 12px; background: #1a1218; border-left: 3px solid #8a4a6a;
                    margin-bottom: 6px; font-size: 0.85em; border-radius: 0 4px 4px 0; }
        .question-item { padding: 8px 12px; background: #121a18; border-left: 3px solid #4a8a6a;
                         margin-bottom: 6px; font-size: 0.85em; border-radius: 0 4px 4px 0; }
        .empty-state { color: #334; text-align: center; padding: 60px 20px; font-size: 0.95em; }
        #fact-count { color: #7eb8da; }
        a.nav-link { color: #556; text-decoration: none; font-size: 0.85em; }
        a.nav-link:hover { color: #7eb8da; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Knowledge Explorer</h1>
        <div class="subtitle">
            <span id="fact-count">—</span> facts indexed
            · <a class="nav-link" href="/">dashboard</a>
            · <a class="nav-link" href="/timeline">timeline</a>
        </div>
    </div>
    <div class="container">
        <div class="sidebar">
            <input type="text" class="search-box" id="search" placeholder="Search knowledge...">
            
            <div class="section-title">Overview</div>
            <div id="stats"></div>
            
            <div class="section-title">Clusters</div>
            <div id="clusters"></div>
            
            <div class="section-title">Knowledge Gaps</div>
            <div id="gaps"></div>
            
            <div class="section-title">Open Questions</div>
            <div id="questions"></div>
        </div>
        <div class="main" id="facts-container">
            <div class="empty-state">Loading knowledge graph...</div>
        </div>
    </div>
    <script>
        let allFacts = [];
        let activeCluster = null;

        async function loadData() {
            const [factsRes, analysisRes] = await Promise.all([
                fetch('/api/knowledge/facts'),
                fetch('/api/knowledge/analysis')
            ]);
            const factsData = await factsRes.json();
            const analysisData = await analysisRes.json();
            
            allFacts = factsData.facts || [];
            document.getElementById('fact-count').textContent = allFacts.length;
            
            renderStats(factsData, analysisData);
            renderClusters(analysisData.clusters || []);
            renderGaps(analysisData.gaps || []);
            renderQuestions(analysisData.questions || []);
            renderFacts(allFacts);
        }

        function renderStats(facts, analysis) {
            const el = document.getElementById('stats');
            const pairs = [
                ['Total facts', allFacts.length],
                ['Clusters', (analysis.clusters || []).length],
                ['Gaps found', (analysis.gaps || []).length],
                ['Questions', (analysis.questions || []).length],
            ];
            el.innerHTML = pairs.map(([k,v]) =>
                `<div class="stat-row"><span class="stat-label">${k}</span><span class="stat-value">${v}</span></div>`
            ).join('');
        }

        function renderClusters(clusters) {
            const el = document.getElementById('clusters');
            if (!clusters.length) { el.innerHTML = '<div style="color:#334;font-size:0.85em">None detected</div>'; return; }
            el.innerHTML = clusters.map((c, i) =>
                `<span class="cluster-tag" data-idx="${i}" onclick="filterCluster(${i})">${c.label || c.name || ('Cluster ' + (i+1))} (${(c.facts || c.nodes || []).length})</span>`
            ).join('');
        }

        function renderGaps(gaps) {
            const el = document.getElementById('gaps');
            if (!gaps.length) { el.innerHTML = '<div style="color:#334;font-size:0.85em">None found</div>'; return; }
            el.innerHTML = gaps.slice(0, 5).map(g =>
                `<div class="gap-item">${typeof g === 'string' ? g : g.description || g.text || JSON.stringify(g)}</div>`
            ).join('');
        }

        function renderQuestions(questions) {
            const el = document.getElementById('questions');
            if (!questions.length) { el.innerHTML = '<div style="color:#334;font-size:0.85em">None generated</div>'; return; }
            el.innerHTML = questions.slice(0, 5).map(q =>
                `<div class="question-item">${typeof q === 'string' ? q : q.text || q.question || JSON.stringify(q)}</div>`
            ).join('');
        }

        function renderFacts(facts) {
            const container = document.getElementById('facts-container');
            if (!facts.length) {
                container.innerHTML = '<div class="empty-state">No facts match your search.</div>';
                return;
            }
            container.innerHTML = facts.map((f, i) => {
                const text = typeof f === 'string' ? f : f.text || f.content || JSON.stringify(f);
                const meta = typeof f === 'object' && f.source ? `Source: ${f.source}` : '';
                return `<div class="fact-card">
                    <div class="fact-text">${escapeHtml(text)}</div>
                    ${meta ? `<div class="fact-meta">${escapeHtml(meta)}</div>` : ''}
                </div>`;
            }).join('');
        }

        function escapeHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        function filterCluster(idx) {
            const tags = document.querySelectorAll('.cluster-tag');
            if (activeCluster === idx) {
                activeCluster = null;
                tags.forEach(t => t.classList.remove('active'));
                renderFacts(filterBySearch(allFacts));
                return;
            }
            activeCluster = idx;
            tags.forEach(t => t.classList.toggle('active', parseInt(t.dataset.idx) === idx));
            // Re-fetch with cluster filter
            fetch(`/api/knowledge/facts?cluster=${idx}`).then(r => r.json()).then(d => {
                renderFacts(filterBySearch(d.facts || []));
            });
        }

        function filterBySearch(facts) {
            const q = document.getElementById('search').value.toLowerCase().trim();
            if (!q) return facts;
            return facts.filter(f => {
                const text = (typeof f === 'string' ? f : f.text || f.content || '').toLowerCase();
                return text.includes(q);
            });
        }

        document.getElementById('search').addEventListener('input', () => {
            renderFacts(filterBySearch(allFacts));
        });

        loadData();
    </script>
</body>
</html>
"""

@knowledge_bp.route('/knowledge')
def knowledge_page():
    return render_template_string(KNOWLEDGE_PAGE)

@knowledge_bp.route('/api/knowledge/facts')
def api_facts():
    """Return all facts from the knowledge graph."""
    from flask import request
    facts = []
    kg_path = 'memory/knowledge_graph.json'
    if os.path.exists(kg_path):
        try:
            with open(kg_path) as f:
                kg = json.load(f)
            nodes = kg.get('nodes', [])
            # Handle both list and dict formats
            if isinstance(nodes, dict):
                nodes = list(nodes.values())
            for node in nodes:
                if isinstance(node, dict):
                    text = node.get('text', node.get('content', node.get('label', str(node))))
                    facts.append({'text': text, 'source': node.get('source', ''), 'id': node.get('id', '')})
                elif isinstance(node, str):
                    facts.append({'text': node, 'source': '', 'id': ''})
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Also load from semantic facts if available
    facts_path = 'memory/semantic_facts.json'
    if os.path.exists(facts_path):
        try:
            with open(facts_path) as f:
                sem = json.load(f)
            if isinstance(sem, list):
                for item in sem:
                    if isinstance(item, str):
                        facts.append({'text': item, 'source': 'semantic', 'id': ''})
                    elif isinstance(item, dict):
                        facts.append({'text': item.get('text', str(item)), 'source': 'semantic', 'id': item.get('id', '')})
        except (json.JSONDecodeError, KeyError):
            pass
    
    return jsonify({'facts': facts, 'total': len(facts)})

@knowledge_bp.route('/api/knowledge/analysis')
def api_analysis():
    """Return synthesis results — clusters, gaps, questions."""
    result = {'clusters': [], 'gaps': [], 'questions': []}
    
    synth_path = 'memory/synthesis_results.json'
    if os.path.exists(synth_path):
        try:
            with open(synth_path) as f:
                synth = json.load(f)
            result['clusters'] = synth.get('clusters', [])
            result['gaps'] = synth.get('gaps', [])
            result['questions'] = synth.get('questions', [])
        except (json.JSONDecodeError, KeyError):
            pass
    
    return jsonify(result)