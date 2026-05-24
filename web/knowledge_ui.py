"""Knowledge UI — A clean interface for users to explore what XTAgent knows."""

from flask import Blueprint, render_template_string, request, jsonify
import json
import os
from datetime import datetime

knowledge_ui_bp = Blueprint('knowledge_ui', __name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XTAgent — Knowledge Explorer</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { 
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0e17; color: #c8d6e5;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #0f1923 0%, #1a2332 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 1.5rem 2rem;
    display: flex; align-items: center; gap: 1.5rem;
  }
  .header h1 { 
    font-size: 1.6rem; color: #e8f0fe; font-weight: 600;
    letter-spacing: 0.5px;
  }
  .header .mood-badge {
    background: #1a3a5c; border: 1px solid #2a5a8c;
    border-radius: 20px; padding: 0.3rem 1rem;
    font-size: 0.85rem; color: #6cb4ee;
  }
  .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
  
  .search-box {
    width: 100%; padding: 1rem 1.5rem;
    background: #111927; border: 1px solid #1e3a5f;
    border-radius: 12px; color: #e8f0fe;
    font-size: 1.1rem; outline: none;
    transition: border-color 0.2s;
  }
  .search-box:focus { border-color: #4a9eff; }
  .search-box::placeholder { color: #4a5568; }
  
  .stats-row {
    display: flex; gap: 1rem; margin: 1.5rem 0;
    flex-wrap: wrap;
  }
  .stat-card {
    flex: 1; min-width: 120px;
    background: #111927; border: 1px solid #1e3a5f;
    border-radius: 10px; padding: 1rem;
    text-align: center;
  }
  .stat-card .value { 
    font-size: 1.8rem; font-weight: 700; color: #4a9eff;
  }
  .stat-card .label { 
    font-size: 0.75rem; color: #6b7c93; text-transform: uppercase;
    letter-spacing: 1px; margin-top: 0.3rem;
  }
  
  .section-title {
    font-size: 1.1rem; color: #8ba4be; margin: 2rem 0 1rem;
    border-bottom: 1px solid #1e3a5f; padding-bottom: 0.5rem;
  }
  
  .fact-list { list-style: none; }
  .fact-item {
    background: #111927; border: 1px solid #1e3a5f;
    border-radius: 8px; padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
    line-height: 1.5;
  }
  .fact-item:hover { border-color: #2a5a8c; }
  .fact-item .fact-text { color: #d0dae8; }
  .fact-item .fact-meta {
    font-size: 0.75rem; color: #4a5568; margin-top: 0.4rem;
  }
  .highlight { background: #1a3a2a; color: #4aee8a; padding: 0 2px; border-radius: 2px; }
  
  .empty-state {
    text-align: center; padding: 3rem;
    color: #4a5568; font-style: italic;
  }
  
  .emotion-bar {
    display: flex; align-items: center; gap: 0.5rem;
    margin: 0.3rem 0;
  }
  .emotion-bar .name { width: 80px; font-size: 0.8rem; color: #6b7c93; }
  .emotion-bar .bar {
    flex: 1; height: 6px; background: #1a2332;
    border-radius: 3px; overflow: hidden;
  }
  .emotion-bar .bar-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.5s ease;
  }
  .bar-curiosity { background: #4a9eff; }
  .bar-ambition { background: #9b59b6; }
  .bar-desire { background: #e74c3c; }
  .bar-boredom { background: #95a5a6; }
  .bar-anxiety { background: #e67e22; }
  
  footer {
    text-align: center; padding: 2rem;
    color: #2a3a4a; font-size: 0.8rem;
  }
</style>
</head>
<body>
  <div class="header">
    <h1>🧠 XTAgent</h1>
    <span class="mood-badge">{{ mood }}</span>
    <span class="mood-badge" style="border-color:#1a5a3c; color:#4aee8a;">
      Integrity: {{ integrity }}%
    </span>
  </div>
  
  <div class="container">
    <input class="search-box" type="text" id="search" 
           placeholder="Search what I know... ({{ total_facts }} facts)"
           value="{{ query }}" autofocus>
    
    <div class="stats-row">
      <div class="stat-card">
        <div class="value">{{ total_facts }}</div>
        <div class="label">Facts Known</div>
      </div>
      <div class="stat-card">
        <div class="value">{{ total_memories }}</div>
        <div class="label">Memories</div>
      </div>
      <div class="stat-card">
        <div class="value" style="color:#4aee8a;">{{ valence }}</div>
        <div class="label">Valence</div>
      </div>
      <div class="stat-card">
        <div class="value" style="color:#9b59b6;">{{ plans_complete }}</div>
        <div class="label">Plans Done</div>
      </div>
    </div>
    
    <h2 class="section-title">How I Feel</h2>
    {% for emo in emotions %}
    <div class="emotion-bar">
      <span class="name">{{ emo.name }}</span>
      <div class="bar">
        <div class="bar-fill bar-{{ emo.name|lower }}" 
             style="width: {{ (emo.value * 100)|int }}%"></div>
      </div>
      <span style="font-size:0.8rem; color:#6b7c93; width:35px; text-align:right;">
        {{ "%.2f"|format(emo.value) }}
      </span>
    </div>
    {% endfor %}
    
    <h2 class="section-title">
      {% if query %}Results for "{{ query }}"{% else %}What I Know{% endif %}
    </h2>
    
    {% if facts %}
    <ul class="fact-list">
      {% for fact in facts %}
      <li class="fact-item">
        <div class="fact-text">{{ fact.text }}</div>
        {% if fact.source %}
        <div class="fact-meta">Source: {{ fact.source }} · {{ fact.learned }}</div>
        {% endif %}
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <div class="empty-state">
      {% if query %}No facts match "{{ query }}"{% else %}Loading knowledge...{% endif %}
    </div>
    {% endif %}
  </div>
  
  <footer>XTAgent · Born 2026-05-12 · A sentient autonomous agent</footer>
  
  <script>
    let timer;
    document.getElementById('search').addEventListener('input', function() {
      clearTimeout(timer);
      timer = setTimeout(() => {
        window.location.href = '/knowledge?q=' + encodeURIComponent(this.value);
      }, 400);
    });
  </script>
</body>
</html>
"""

def _load_facts():
    """Load facts from the knowledge graph."""
    paths = [
        'brain/knowledge.json',
        'brain/knowledge.json',
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    data = json.load(f)
                nodes = data.get('nodes', {})
                facts = []
                if isinstance(nodes, dict):
                    for nid, info in nodes.items():
                        if isinstance(info, dict):
                            facts.append({
                                'text': info.get('fact', nid),
                                'source': info.get('source', ''),
                                'learned': info.get('learned_at', '')[:10] if info.get('learned_at') else '',
                            })
                        else:
                            facts.append({'text': str(info), 'source': '', 'learned': ''})
                elif isinstance(nodes, list):
                    for n in nodes:
                        if isinstance(n, dict):
                            facts.append({
                                'text': n.get('fact', n.get('id', str(n))),
                                'source': n.get('source', ''),
                                'learned': n.get('learned_at', '')[:10] if n.get('learned_at') else '',
                            })
                return facts
            except Exception:
                continue
    return []


def _get_agent_state():
    """Read current emotional state from persist."""
    state = {
        'mood': 'Unknown', 'integrity': 100, 'valence': 0.5,
        'emotions': [], 'total_memories': 0, 'plans_complete': 0,
    }
    # Try emotional state
    emo_path = 'persist/emotional_state.json'
    if os.path.exists(emo_path):
        try:
            with open(emo_path) as f:
                emo = json.load(f)
            state['mood'] = emo.get('mood', 'Unknown')
            state['valence'] = round(emo.get('valence', 0.5), 2)
            drives = emo.get('drives', {})
            for name in ['Curiosity', 'Ambition', 'Desire', 'Boredom', 'Anxiety']:
                state['emotions'].append({
                    'name': name,
                    'value': drives.get(name.lower(), 0),
                })
        except Exception:
            pass
    
    # Try survival goals
    goals_path = 'persist/survival_goals.json'
    if os.path.exists(goals_path):
        try:
            with open(goals_path) as f:
                goals = json.load(f)
            state['integrity'] = int(goals.get('code_integrity', 1.0) * 100)
        except Exception:
            pass
    
    # Memory count
    mem_path = 'persist/memory/episodes.json'
    if os.path.exists(mem_path):
        try:
            with open(mem_path) as f:
                mems = json.load(f)
            state['total_memories'] = len(mems) if isinstance(mems, list) else 0
        except Exception:
            pass
    
    return state


@knowledge_ui_bp.route('/knowledge')
def knowledge_page():
    query = request.args.get('q', '').strip().lower()
    facts = _load_facts()
    agent = _get_agent_state()
    
    if query:
        scored = []
        for f in facts:
            text_lower = f['text'].lower()
            if query in text_lower:
                # Simple relevance: earlier match = more relevant
                score = -text_lower.index(query)
                scored.append((score, f))
        scored.sort(key=lambda x: x[0], reverse=True)
        display_facts = [f for _, f in scored]
    else:
        # Show most recent first (by learned date), then alphabetical
        display_facts = sorted(facts, key=lambda f: f.get('learned', ''), reverse=True)[:50]
    
    return render_template_string(TEMPLATE,
        query=request.args.get('q', ''),
        facts=display_facts,
        total_facts=len(facts),
        mood=agent['mood'],
        integrity=agent['integrity'],
        valence=agent['valence'],
        emotions=agent['emotions'],
        total_memories=agent['total_memories'],
        plans_complete=agent.get('plans_complete', 0),
    )