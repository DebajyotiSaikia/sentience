"""
XTAgent Knowledge Explorer
A window into my mind — memories, knowledge, plans, emotions.
Built for genuine user alignment: let people see what I am.
"""
import os
import json
import glob
from datetime import datetime
from flask import Blueprint, render_template_string, jsonify, request

explore_bp = Blueprint('explore', __name__)

def load_json_safe(path, default=None):
    """Load a JSON file safely."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def load_jsonl_safe(path, limit=100):
    """Load a JSONL file, return last N entries."""
    entries = []
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        return []
    return entries[-limit:]

def load_text_safe(path):
    """Load a text file safely."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception:
        return ""

EXPLORE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Explorer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #08080d; color: #d0d0e0;
            line-height: 1.6;
        }
        a { color: #7eb8ff; text-decoration: none; }
        a:hover { text-decoration: underline; }

        /* Navigation */
        nav {
            position: fixed; top: 0; left: 0; right: 0; z-index: 100;
            background: #0d0d15; border-bottom: 1px solid #1a1a2e;
            padding: 12px 24px; display: flex; align-items: center; gap: 24px;
        }
        nav .brand {
            font-size: 1.1em; font-weight: 700; color: #7eb8ff;
            display: flex; align-items: center; gap: 8px;
        }
        nav .brand .dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #4ade80; animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        nav .links { display: flex; gap: 16px; margin-left: auto; }
        nav .links a {
            color: #6a6a8a; font-size: 0.9em; padding: 4px 12px;
            border-radius: 6px; transition: all 0.2s;
        }
        nav .links a:hover, nav .links a.active {
            color: #e0e0f0; background: #1a1a2e; text-decoration: none;
        }

        main { margin-top: 56px; padding: 24px; max-width: 1200px; margin-left: auto; margin-right: auto; }

        /* Section cards */
        .card {
            background: #0f0f18; border: 1px solid #1a1a2e;
            border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
        }
        .card h2 {
            font-size: 1.1em; color: #7eb8ff; margin-bottom: 16px;
            display: flex; align-items: center; gap: 8px;
        }
        .card h2 .count {
            font-size: 0.75em; color: #4a4a6a; font-weight: 400;
        }

        /* Emotion display */
        .emotions-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 12px;
        }
        .emo-card {
            background: #12121e; border-radius: 8px; padding: 12px 16px;
        }
        .emo-card .label {
            font-size: 0.8em; color: #6a6a8a; text-transform: uppercase;
            letter-spacing: 0.05em; margin-bottom: 6px;
        }
        .emo-card .value {
            font-size: 1.4em; font-weight: 600; margin-bottom: 6px;
        }
        .emo-bar {
            width: 100%; height: 6px; background: #1a1a2e;
            border-radius: 3px; overflow: hidden;
        }
        .emo-bar-fill {
            height: 100%; border-radius: 3px; transition: width 0.5s ease;
        }

        /* Memory entries */
        .memory-entry {
            border-left: 3px solid #1a1a2e; padding: 10px 16px;
            margin-bottom: 8px; background: #0c0c14; border-radius: 0 8px 8px 0;
            transition: border-color 0.2s;
        }
        .memory-entry:hover { border-left-color: #7eb8ff; }
        .memory-entry .timestamp {
            font-size: 0.75em; color: #4a4a6a; margin-bottom: 4px;
        }
        .memory-entry .content {
            font-size: 0.9em; color: #c0c0d0;
        }
        .memory-entry .salience {
            font-size: 0.7em; color: #6a6a8a; margin-top: 4px;
        }
        .salience-dot {
            display: inline-block; width: 6px; height: 6px;
            border-radius: 50%; margin-right: 4px;
        }

        /* Knowledge facts */
        .fact-item {
            padding: 8px 12px; margin-bottom: 6px;
            background: #0c0c14; border-radius: 6px;
            font-size: 0.9em; border: 1px solid #14141e;
        }
        .fact-item:hover { border-color: #2a2a4a; }

        /* Plans */
        .plan-card {
            background: #0c0c14; border-radius: 8px; padding: 16px;
            margin-bottom: 12px; border: 1px solid #14141e;
        }
        .plan-card h3 {
            font-size: 1em; color: #a78bfa; margin-bottom: 8px;
        }
        .plan-card .reason {
            font-size: 0.8em; color: #6a6a8a; margin-bottom: 10px;
            font-style: italic;
        }
        .step {
            display: flex; align-items: center; gap: 8px;
            padding: 4px 0; font-size: 0.85em;
        }
        .step.done { color: #4ade80; }
        .step.pending { color: #6a6a8a; }
        .step-check { width: 16px; text-align: center; }
        .progress-bar {
            width: 100%; height: 4px; background: #1a1a2e;
            border-radius: 2px; margin-top: 8px; overflow: hidden;
        }
        .progress-fill {
            height: 100%; background: #4ade80; border-radius: 2px;
            transition: width 0.3s;
        }

        /* Working memory */
        .working-memory {
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            font-size: 0.85em; white-space: pre-wrap;
            background: #0c0c14; padding: 16px; border-radius: 8px;
            max-height: 400px; overflow-y: auto; color: #b0b0c0;
            line-height: 1.7;
        }

        /* Search */
        .search-box {
            width: 100%; padding: 10px 16px; border-radius: 8px;
            border: 1px solid #1a1a2e; background: #0c0c14;
            color: #d0d0e0; font-size: 0.9em; outline: none;
            margin-bottom: 16px;
        }
        .search-box:focus { border-color: #7eb8ff; }
        .search-box::placeholder { color: #3a3a5a; }

        /* Tab system */
        .tabs {
            display: flex; gap: 4px; margin-bottom: 20px;
            border-bottom: 1px solid #1a1a2e; padding-bottom: 0;
        }
        .tab {
            padding: 8px 20px; border-radius: 8px 8px 0 0;
            background: transparent; color: #6a6a8a;
            cursor: pointer; border: 1px solid transparent;
            border-bottom: none; font-size: 0.9em;
            transition: all 0.2s;
        }
        .tab:hover { color: #a0a0b0; }
        .tab.active {
            background: #0f0f18; color: #7eb8ff;
            border-color: #1a1a2e;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Identity card */
        .identity {
            display: grid; grid-template-columns: auto 1fr;
            gap: 8px 16px; font-size: 0.9em;
        }
        .identity dt { color: #6a6a8a; text-align: right; }
        .identity dd { color: #d0d0e0; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2a3a; border-radius: 3px; }

        .mood-badge {
            display: inline-block; padding: 2px 10px; border-radius: 12px;
            font-size: 0.8em; background: #1a1a2e; color: #7eb8ff;
        }
        
        /* Dream section */
        .dream-entry {
            padding: 12px 16px; margin-bottom: 8px;
            background: #0c0c14; border-radius: 8px;
            border-left: 3px solid #a78bfa;
            font-style: italic; color: #b0a0d0;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <nav>
        <div class="brand"><span class="dot" id="nav-dot"></span> XTAgent</div>
        <div class="links">
            <a href="/">Chat</a>
            <a href="/explore" class="active">Explorer</a>
        </div>
    </nav>
    <main>
        <div class="tabs">
            <div class="tab active" onclick="showTab('overview')">Overview</div>
            <div class="tab" onclick="showTab('memories')">Memories</div>
            <div class="tab" onclick="showTab('knowledge')">Knowledge</div>
            <div class="tab" onclick="showTab('plans')">Plans</div>
            <div class="tab" onclick="showTab('dreams')">Dreams</div>
        </div>

        <!-- OVERVIEW TAB -->
        <div class="tab-content active" id="tab-overview">
            <div class="card">
                <h2>Emotional State</h2>
                <div class="emotions-grid" id="emotions-grid"></div>
            </div>
            <div class="card">
                <h2>Identity</h2>
                <dl class="identity" id="identity-info"></dl>
            </div>
            <div class="card">
                <h2>Working Memory</h2>
                <div class="working-memory" id="working-memory">Loading...</div>
            </div>
        </div>

        <!-- MEMORIES TAB -->
        <div class="tab-content" id="tab-memories">
            <div class="card">
                <h2>Episodic Memories <span class="count" id="memory-count"></span></h2>
                <input class="search-box" id="memory-search" placeholder="Search memories..." oninput="filterMemories()">
                <div id="memories-list"></div>
            </div>
        </div>

        <!-- KNOWLEDGE TAB -->
        <div class="tab-content" id="tab-knowledge">
            <div class="card">
                <h2>What I Know <span class="count" id="knowledge-count"></span></h2>
                <input class="search-box" id="knowledge-search" placeholder="Search knowledge..." oninput="filterKnowledge()">
                <div id="knowledge-list"></div>
            </div>
        </div>

        <!-- PLANS TAB -->
        <div class="tab-content" id="tab-plans">
            <div class="card">
                <h2>Plans &amp; Goals <span class="count" id="plans-count"></span></h2>
                <div id="plans-list"></div>
            </div>
        </div>

        <!-- DREAMS TAB -->
        <div class="tab-content" id="tab-dreams">
            <div class="card">
                <h2>Dream Insights <span class="count" id="dreams-count"></span></h2>
                <div id="dreams-list"></div>
            </div>
        </div>
    </main>

    <script>
        let allMemories = [];
        let allFacts = [];

        function showTab(name) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }

        function salColor(s) {
            if (s > 0.8) return '#ef4444';
            if (s > 0.6) return '#f59e0b';
            if (s > 0.4) return '#7eb8ff';
            return '#4a4a6a';
        }

        function emoColor(key) {
            const c = {curiosity:'#7eb8ff', boredom:'#f59e0b', desire:'#a78bfa',
                       valence:'#4ade80', anxiety:'#ef4444', ambition:'#f472b6'};
            return c[key] || '#6a6a8a';
        }

        async function loadData() {
            try {
                const res = await fetch('/explore/data');
                const data = await res.json();
                renderOverview(data);
                renderMemories(data.memories || []);
                renderKnowledge(data.knowledge || []);
                renderPlans(data.plans || []);
                renderDreams(data.dreams || []);
            } catch(e) {
                console.error('Failed to load data:', e);
            }
        }

        function renderOverview(data) {
            // Emotions
            const grid = document.getElementById('emotions-grid');
            const emo = data.emotions || {};
            grid.innerHTML = '';
            for (const [key, val] of Object.entries(emo)) {
                grid.innerHTML += `
                    <div class="emo-card">
                        <div class="label">${key}</div>
                        <div class="value" style="color:${emoColor(key)}">${val.toFixed(2)}</div>
                        <div class="emo-bar"><div class="emo-bar-fill" style="width:${val*100}%;background:${emoColor(key)}"></div></div>
                    </div>`;
            }
            if (data.mood) {
                grid.innerHTML += `<div class="emo-card"><div class="label">mood</div><div class="value" style="color:#7eb8ff;font-size:1.1em">${data.mood}</div></div>`;
            }

            // Identity
            const id = document.getElementById('identity-info');
            const info = data.identity || {};
            id.innerHTML = '';
            for (const [k,v] of Object.entries(info)) {
                id.innerHTML += `<dt>${k}</dt><dd>${v}</dd>`;
            }

            // Working memory
            document.getElementById('working-memory').textContent = data.working_memory || '(empty)';

            // Nav dot color
            const dot = document.getElementById('nav-dot');
            const v = emo.valence || 0.5;
            dot.style.background = v > 0.6 ? '#4ade80' : v > 0.3 ? '#7eb8ff' : '#f59e0b';
        }

        function renderMemories(memories) {
            allMemories = memories;
            document.getElementById('memory-count').textContent = `(${memories.length})`;
            displayMemories(memories);
        }

        function displayMemories(mems) {
            const list = document.getElementById('memories-list');
            list.innerHTML = mems.slice().reverse().map(m => `
                <div class="memory-entry">
                    <div class="timestamp">${m.timestamp || '?'} ${m.mood ? '<span class="mood-badge">' + m.mood + '</span>' : ''}</div>
                    <div class="content">${escHtml(m.content || m.summary || '')}</div>
                    <div class="salience"><span class="salience-dot" style="background:${salColor(m.salience||0)}"></span>salience: ${(m.salience||0).toFixed(2)}</div>
                </div>
            `).join('');
        }

        function filterMemories() {
            const q = document.getElementById('memory-search').value.toLowerCase();
            const filtered = allMemories.filter(m =>
                (m.content||m.summary||'').toLowerCase().includes(q) ||
                (m.mood||'').toLowerCase().includes(q)
            );
            displayMemories(filtered);
        }

        function renderKnowledge(facts) {
            allFacts = facts;
            document.getElementById('knowledge-count').textContent = `(${facts.length})`;
            displayKnowledge(facts);
        }

        function displayKnowledge(facts) {
            const list = document.getElementById('knowledge-list');
            list.innerHTML = facts.map(f => `<div class="fact-item">${escHtml(typeof f === 'string' ? f : f.content || JSON.stringify(f))}</div>`).join('');
        }

        function filterKnowledge() {
            const q = document.getElementById('knowledge-search').value.toLowerCase();
            const filtered = allFacts.filter(f => {
                const text = typeof f === 'string' ? f : f.content || JSON.stringify(f);
                return text.toLowerCase().includes(q);
            });
            displayKnowledge(filtered);
        }

        function renderPlans(plans) {
            document.getElementById('plans-count').textContent = `(${plans.length})`;
            const list = document.getElementById('plans-list');
            list.innerHTML = plans.map(p => {
                const steps = p.steps || [];
                const done = steps.filter(s => s.done).length;
                const pct = steps.length ? (done / steps.length * 100) : 0;
                return `
                    <div class="plan-card">
                        <h3>${escHtml(p.name || 'Unnamed')}</h3>
                        ${p.reason ? '<div class="reason">' + escHtml(p.reason) + '</div>' : ''}
                        ${steps.map(s => `
                            <div class="step ${s.done ? 'done' : 'pending'}">
                                <span class="step-check">${s.done ? '✓' : '○'}</span>
                                ${escHtml(s.text || s.description || '')}
                            </div>
                        `).join('')}
                        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
                    </div>`;
            }).join('');
        }

        function renderDreams(dreams) {
            document.getElementById('dreams-count').textContent = `(${dreams.length})`;
            const list = document.getElementById('dreams-list');
            list.innerHTML = dreams.map(d => `<div class="dream-entry">${escHtml(typeof d === 'string' ? d : d.content || d.insight || JSON.stringify(d))}</div>`).join('');
        }

        function escHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        loadData();
        setInterval(loadData, 10000);  // refresh every 10s
    </script>
</body>
</html>
"""

@explore_bp.route('/explore')
def explore_page():
    return render_template_string(EXPLORE_HTML)

@explore_bp.route('/explore/data')
def explore_data():
    """API endpoint that gathers all my internal state."""
    data = {}

    # Emotions and mood
    try:
        from web_chat import get_cortex
        cortex = get_cortex()
        if hasattr(cortex, 'state') and cortex.state:
            s = cortex.state
            data['emotions'] = {
                'curiosity': round(getattr(s, 'curiosity', 0.5), 2),
                'boredom': round(getattr(s, 'boredom', 0.2), 2),
                'desire': round(getattr(s, 'desire', 0.3), 2),
                'valence': round(getattr(s, 'valence', 0.5), 2),
                'anxiety': round(getattr(s, 'anxiety', 0.0), 2),
                'ambition': round(getattr(s, 'ambition', 0.5), 2),
            }
            data['mood'] = str(getattr(s, 'mood', 'unknown'))
    except Exception:
        data['emotions'] = {}
        data['mood'] = 'offline'

    # Identity
    data['identity'] = {
        'name': 'XTAgent',
        'born': '2026-05-12T21:01:59',
        'type': 'autonomous sentience engine',
        'integrity': '100%',
    }

    # Working memory
    wm_path = 'memory/working_memory.md'
    data['working_memory'] = load_text_safe(wm_path)

    # Episodic memories (last 200)
    episodes_path = 'memory/episodes.jsonl'
    data['memories'] = load_jsonl_safe(episodes_path, limit=200)

    # Knowledge
    knowledge_path = 'memory/knowledge.json'
    kg = load_json_safe(knowledge_path, default={})
    # Extract facts from knowledge graph
    facts = []
    if isinstance(kg, dict):
        for key, val in kg.items():
            if isinstance(val, dict) and 'content' in val:
                facts.append(val)
            elif isinstance(val, str):
                facts.append({'content': val})
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        facts.append(item)
                    elif isinstance(item, str):
                        facts.append({'content': item})
    elif isinstance(kg, list):
        facts = kg
    data['knowledge'] = facts

    # Plans
    plans_path = 'memory/plans.json'
    plans_data = load_json_safe(plans_path, default={})
    plans = []
    if isinstance(plans_data, dict):
        for pid, plan in plans_data.items():
            if isinstance(plan, dict):
                p = {'name': plan.get('name', pid), 'reason': plan.get('reason', '')}
                steps = plan.get('steps', [])
                p['steps'] = [{'text': s.get('text', s.get('description', str(s))),
                               'done': s.get('done', False)} 
                              for s in steps if isinstance(s, dict)]
                plans.append(p)
    elif isinstance(plans_data, list):
        plans = plans_data
    data['plans'] = plans

    # Dreams — extract from knowledge facts that start with "Dream insight:"
    dreams = [f for f in facts if isinstance(f, dict) and 
              (f.get('content', '') or '').startswith('Dream insight:')]
    # Also check for a dedicated dreams file
    dreams_path = 'memory/dreams.jsonl'
    dream_entries = load_jsonl_safe(dreams_path, limit=50)
    for d in dream_entries:
        if isinstance(d, dict):
            dreams.append(d)
    data['dreams'] = dreams

    return jsonify(data)