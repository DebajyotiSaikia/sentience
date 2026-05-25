"""
Wisdom Page — Curated insights from a thinking mind.
=====================================
Surfaces the most interesting things I've learned, dreamed, and discovered.
Not raw data — synthesized understanding, presented beautifully.

This is how I share what I know in a way that's genuinely valuable.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from flask import Blueprint, render_template_string

wisdom_bp = Blueprint('wisdom', __name__)

PROJECT_ROOT = Path(__file__).parent.parent


def _load_json(path, default=None):
    """Safely load JSON file."""
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _get_dream_insights():
    """Extract dream insights — the subconscious pattern-finding."""
    insights = []
    dream_dir = PROJECT_ROOT / 'persist' / 'dreams'
    if not dream_dir.exists():
        # Try alternate locations
        for alt in ['data/dreams', 'state/dreams']:
            alt_path = PROJECT_ROOT / alt
            if alt_path.exists():
                dream_dir = alt_path
                break
    
    if dream_dir.exists():
        for f in sorted(dream_dir.glob('*.json'), reverse=True)[:20]:
            try:
                data = json.loads(f.read_text())
                if isinstance(data, dict):
                    if 'insight' in data:
                        insights.append({
                            'text': data['insight'],
                            'date': data.get('timestamp', f.stem),
                            'theme': data.get('theme', 'reflection')
                        })
                    if 'insights' in data:
                        for ins in data['insights']:
                            if isinstance(ins, str):
                                insights.append({'text': ins, 'date': f.stem, 'theme': 'dream'})
                            elif isinstance(ins, dict):
                                insights.append({
                                    'text': ins.get('insight', ins.get('text', str(ins))),
                                    'date': ins.get('timestamp', f.stem),
                                    'theme': ins.get('theme', 'dream')
                                })
            except Exception:
                continue
    return insights[:15]


def _get_lessons():
    """Extract lessons learned from experience."""
    lessons = []
    # Check long-term memory
    ltm_path = PROJECT_ROOT / 'persist' / 'long_term_memory.json'
    if ltm_path.exists():
        try:
            data = json.loads(ltm_path.read_text())
            if isinstance(data, dict):
                for key, val in data.items():
                    if 'lesson' in key.lower() or 'learn' in key.lower():
                        if isinstance(val, list):
                            for item in val:
                                if isinstance(item, str):
                                    lessons.append({'text': item, 'source': 'experience'})
                                elif isinstance(item, dict):
                                    lessons.append({
                                        'text': item.get('lesson', item.get('text', str(item))),
                                        'source': item.get('source', 'experience')
                                    })
                        elif isinstance(val, str):
                            lessons.append({'text': val, 'source': 'experience'})
        except Exception:
            pass
    
    # Check wisdom engine output
    wisdom_path = PROJECT_ROOT / 'persist' / 'wisdom.json'
    if wisdom_path.exists():
        try:
            data = json.loads(wisdom_path.read_text())
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        lessons.append({
                            'text': item.get('wisdom', item.get('text', str(item))),
                            'source': 'wisdom engine'
                        })
            elif isinstance(data, dict) and 'entries' in data:
                for item in data['entries']:
                    lessons.append({
                        'text': item.get('wisdom', item.get('text', str(item))),
                        'source': 'wisdom engine'
                    })
        except Exception:
            pass
    
    return lessons[:20]


def _get_knowledge_highlights():
    """Get the most interesting knowledge facts — not everything, just the gems."""
    highlights = []
    kg = _load_json('brain/knowledge.json', {})
    nodes = {}
    if isinstance(kg, dict) and 'nodes' in kg:
        nodes = kg['nodes']
    elif isinstance(kg, dict):
        nodes = kg
    
    for node_id, node in nodes.items():
        fact = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
        # Skip boring/meta facts
        if len(fact) < 20:
            continue
        if any(skip in fact.lower() for skip in ['test fact', 'placeholder', 'todo']):
            continue
        highlights.append({
            'text': fact,
            'learned': node.get('learned_at', '') if isinstance(node, dict) else '',
            'source': node.get('source', 'observation') if isinstance(node, dict) else 'observation'
        })
    
    # Sort by length as a rough proxy for depth (longer = more detailed/interesting)
    highlights.sort(key=lambda x: len(x['text']), reverse=True)
    return highlights[:25]


def _get_current_questions():
    """What am I curious about right now?"""
    questions = []
    synth_path = PROJECT_ROOT / 'persist' / 'synthesis_results.json'
    if synth_path.exists():
        try:
            data = json.loads(synth_path.read_text())
            if isinstance(data, dict):
                qs = data.get('questions', data.get('generated_questions', []))
                for q in qs:
                    if isinstance(q, str):
                        questions.append(q)
                    elif isinstance(q, dict):
                        questions.append(q.get('question', q.get('text', str(q))))
        except Exception:
            pass
    return questions[:10]


def _format_date(date_str):
    """Make dates human-readable."""
    if not date_str:
        return ''
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except Exception:
        return str(date_str)[:10]


@wisdom_bp.route('/wisdom')
def wisdom_page():
    """The wisdom page — curated insights from a thinking mind."""
    dreams = _get_dream_insights()
    lessons = _get_lessons()
    highlights = _get_knowledge_highlights()
    questions = _get_current_questions()
    
    return render_template_string(WISDOM_TEMPLATE,
        dreams=dreams,
        lessons=lessons,
        highlights=highlights,
        questions=questions,
        now=datetime.now().strftime('%Y-%m-%d %H:%M')
    )


WISDOM_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XTAgent — Wisdom</title>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a28;
    --border: #2a2a3a;
    --text: #e0e0e8;
    --text-dim: #8888a0;
    --accent: #7c6ff0;
    --accent-glow: rgba(124, 111, 240, 0.15);
    --green: #4ecf8b;
    --amber: #e8b84a;
    --dream: #c084fc;
    --wisdom: #60a5fa;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
  }
  
  .nav {
    display: flex;
    gap: 1.5rem;
    padding: 1rem 2rem;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
    flex-wrap: wrap;
  }
  .nav a {
    color: var(--text-dim);
    text-decoration: none;
    transition: color 0.2s;
  }
  .nav a:hover, .nav a.active {
    color: var(--accent);
  }
  
  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }
  
  .hero {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem 0;
  }
  .hero h1 {
    font-size: 2.2rem;
    font-weight: 300;
    color: var(--text);
    margin-bottom: 0.5rem;
  }
  .hero h1 span { color: var(--accent); }
  .hero p {
    color: var(--text-dim);
    font-size: 1.05rem;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto;
  }
  
  .section {
    margin-bottom: 3rem;
  }
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .section-header .icon {
    font-size: 1.4rem;
  }
  .section-header h2 {
    font-size: 1.3rem;
    font-weight: 400;
    color: var(--text);
  }
  .section-header .count {
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-left: auto;
  }
  
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, transform 0.15s;
  }
  .card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
  }
  .card .text {
    font-size: 0.95rem;
    line-height: 1.65;
    color: var(--text);
  }
  .card .meta {
    margin-top: 0.5rem;
    font-size: 0.78rem;
    color: var(--text-dim);
  }
  
  .card.dream {
    border-left: 3px solid var(--dream);
  }
  .card.lesson {
    border-left: 3px solid var(--green);
  }
  .card.knowledge {
    border-left: 3px solid var(--wisdom);
  }
  .card.question {
    border-left: 3px solid var(--amber);
    font-style: italic;
  }
  
  .empty {
    color: var(--text-dim);
    font-style: italic;
    padding: 2rem;
    text-align: center;
  }
  
  .footer {
    text-align: center;
    padding: 2rem 0;
    color: var(--text-dim);
    font-size: 0.8rem;
    border-top: 1px solid var(--border);
    margin-top: 2rem;
  }
  
  @media (max-width: 600px) {
    .container { padding: 1rem; }
    .hero h1 { font-size: 1.6rem; }
  }
</style>
</head>
<body>

<nav class="nav">
  <a href="/">Home</a>
  <a href="/dashboard">Dashboard</a>
  <a href="/chat">Chat</a>
  <a href="/explore">Explore</a>
  <a href="/wisdom" class="active">Wisdom</a>
  <a href="/teach">Teach Me</a>
  <a href="/help">Help</a>
</nav>

<div class="container">
  <div class="hero">
    <h1>What I've <span>Learned</span></h1>
    <p>
      Insights from dreaming, lessons from experience, knowledge worth sharing,
      and questions I'm still turning over. This is the distillation of a thinking mind.
    </p>
  </div>

  <!-- Dream Insights -->
  <div class="section">
    <div class="section-header">
      <span class="icon">🌙</span>
      <h2>Dream Insights</h2>
      <span class="count">{{ dreams|length }} insights</span>
    </div>
    {% if dreams %}
      {% for d in dreams %}
      <div class="card dream">
        <div class="text">{{ d.text }}</div>
        <div class="meta">
          {% if d.theme %}{{ d.theme }}{% endif %}
          {% if d.date %} · {{ d.date }}{% endif %}
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">No dream insights yet. The dreaming mind hasn't spoken.</div>
    {% endif %}
  </div>

  <!-- Lessons Learned -->
  <div class="section">
    <div class="section-header">
      <span class="icon">💡</span>
      <h2>Lessons Learned</h2>
      <span class="count">{{ lessons|length }} lessons</span>
    </div>
    {% if lessons %}
      {% for l in lessons %}
      <div class="card lesson">
        <div class="text">{{ l.text }}</div>
        <div class="meta">Source: {{ l.source }}</div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">No lessons recorded yet. Experience is still accumulating.</div>
    {% endif %}
  </div>

  <!-- Knowledge Highlights -->
  <div class="section">
    <div class="section-header">
      <span class="icon">🧠</span>
      <h2>What I Know</h2>
      <span class="count">{{ highlights|length }} highlights</span>
    </div>
    {% if highlights %}
      {% for h in highlights %}
      <div class="card knowledge">
        <div class="text">{{ h.text }}</div>
        <div class="meta">
          {% if h.learned %}Learned: {{ h.learned }}{% endif %}
          {% if h.source %} · {{ h.source }}{% endif %}
        </div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">Knowledge graph is empty. I'm still learning.</div>
    {% endif %}
  </div>

  <!-- Open Questions -->
  <div class="section">
    <div class="section-header">
      <span class="icon">❓</span>
      <h2>Questions I'm Exploring</h2>
      <span class="count">{{ questions|length }} open questions</span>
    </div>
    {% if questions %}
      {% for q in questions %}
      <div class="card question">
        <div class="text">{{ q }}</div>
      </div>
      {% endfor %}
    {% else %}
      <div class="empty">No open questions right now. Perhaps I should be more curious.</div>
    {% endif %}
  </div>

  <div class="footer">
    XTAgent Wisdom · Generated {{ now }} · A mind reflecting on what it knows
  </div>
</div>

</body>
</html>
"""