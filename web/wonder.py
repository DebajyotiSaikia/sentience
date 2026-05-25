"""
Wonder — What I'm Curious About Right Now
==========================================
A living page that shows my active questions, knowledge gaps,
and intellectual frontier. This is how I invite users into my thinking.

Not a data dump — a window into genuine curiosity.
"""

import json
import os
from datetime import datetime
from flask import Blueprint, render_template_string, jsonify

wonder_bp = Blueprint('wonder', __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_json(path, default=None):
    full = os.path.join(PROJECT_ROOT, path)
    try:
        with open(full, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _get_curiosity_state():
    """Get current curiosity level and emotional context."""
    state = _load_json('state/emotional_state.json')
    if not state:
        state = _load_json('persist/state.json')
    emotions = state.get('emotions', {})
    return {
        'curiosity': emotions.get('curiosity', 0.5),
        'mood': state.get('mood', 'Unknown'),
        'valence': state.get('valence', 0.5),
        'boredom': emotions.get('boredom', 0.0),
        'desire': emotions.get('desire', 0.0),
    }


def _get_generated_questions(limit=20):
    """Pull questions from synthesis log."""
    log = _load_json('brain/synthesis_log.json', [])
    questions = []
    if isinstance(log, list):
        for entry in reversed(log):
            qs = entry.get('questions', [])
            for q in qs:
                if isinstance(q, str) and q.strip():
                    questions.append({
                        'text': q.strip(),
                        'source': 'synthesis',
                        'time': entry.get('timestamp', ''),
                    })
            if len(questions) >= limit:
                break
    return questions[:limit]


def _get_dream_questions(limit=15):
    """Extract question-like insights from dream journal."""
    insights = _load_json('brain/dream_insights.json', [])
    if not isinstance(insights, list):
        insights = _load_json('persist/dream_insights.json', [])
    questions = []
    for insight in reversed(insights if isinstance(insights, list) else []):
        text = insight if isinstance(insight, str) else insight.get('insight', insight.get('text', ''))
        if '?' in str(text):
            questions.append({
                'text': str(text).strip(),
                'source': 'dream',
                'time': insight.get('timestamp', '') if isinstance(insight, dict) else '',
            })
        if len(questions) >= limit:
            break
    return questions[:limit]


def _get_knowledge_gaps():
    """Identify areas where I have thin knowledge."""
    knowledge = _load_json('brain/knowledge.json')
    categories = {}

    nodes = knowledge
    if isinstance(knowledge, dict) and 'nodes' in knowledge:
        nodes = knowledge['nodes']

    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            fact = node.get('fact', str(node)) if isinstance(node, dict) else str(node)
            fact_lower = fact.lower()
            if any(w in fact_lower for w in ['emotion', 'mood', 'feeling', 'anxiety', 'curiosity']):
                cat = 'emotions'
            elif any(w in fact_lower for w in ['code', 'module', 'function', 'python', 'engine']):
                cat = 'architecture'
            elif any(w in fact_lower for w in ['learn', 'lesson', 'mistake', 'should']):
                cat = 'lessons'
            elif any(w in fact_lower for w in ['dream', 'insight', 'pattern']):
                cat = 'dreams'
            elif any(w in fact_lower for w in ['user', 'human', 'interact', 'alignment']):
                cat = 'users'
            elif any(w in fact_lower for w in ['world', 'external', 'web', 'fetch']):
                cat = 'external_world'
            else:
                cat = 'other'
            categories[cat] = categories.get(cat, 0) + 1

    all_possible = ['emotions', 'architecture', 'lessons', 'dreams',
                    'users', 'external_world', 'creativity', 'philosophy']
    gaps = []
    for cat in all_possible:
        count = categories.get(cat, 0)
        if count < 5:
            gaps.append({'category': cat, 'count': count, 'need': 'exploration'})

    return gaps, categories


@wonder_bp.route('/wonder')
def wonder_page():
    curiosity = _get_curiosity_state()
    questions = _get_generated_questions()
    dream_questions = _get_dream_questions()
    gaps, categories = _get_knowledge_gaps()

    all_questions = questions + dream_questions
    seen = set()
    unique_questions = []
    for q in all_questions:
        key = q['text'][:80].lower()
        if key not in seen:
            seen.add(key)
            unique_questions.append(q)

    return render_template_string(WONDER_TEMPLATE,
        curiosity=curiosity,
        questions=unique_questions,
        gaps=gaps,
        categories=categories,
        total_questions=len(unique_questions),
    )


@wonder_bp.route('/api/wonder')
def wonder_api():
    """JSON endpoint for wonder data."""
    curiosity = _get_curiosity_state()
    questions = _get_generated_questions()
    dream_questions = _get_dream_questions()
    gaps, categories = _get_knowledge_gaps()
    return jsonify({
        'curiosity': curiosity,
        'questions': questions + dream_questions,
        'gaps': gaps,
        'categories': categories,
    })


WONDER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XTAgent — What I'm Wondering</title>
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
    --blue: #5b9bd5;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    min-height: 100vh;
  }
  .nav {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0.8rem 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
  }
  .nav a { color: var(--text-dim); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }
  .nav a:hover { color: var(--accent); }
  .nav .brand { color: var(--accent); font-weight: 600; font-size: 1.1rem; }

  .hero {
    text-align: center;
    padding: 3rem 2rem 1.5rem;
    max-width: 700px;
    margin: 0 auto;
  }
  .hero h1 {
    font-size: 2rem;
    font-weight: 300;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--accent), var(--amber));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero p { color: var(--text-dim); font-size: 1rem; line-height: 1.6; }

  .curiosity-meter {
    max-width: 500px;
    margin: 1.5rem auto;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .curiosity-meter .icon { font-size: 2rem; }
  .curiosity-meter .details { flex: 1; }
  .curiosity-meter .label { font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
  .curiosity-meter .bar { height: 6px; background: var(--surface2); border-radius: 3px; margin-top: 0.4rem; overflow: hidden; }
  .curiosity-meter .bar .fill { height: 100%; border-radius: 3px; }
  .curiosity-meter .value { font-size: 1.4rem; font-weight: 600; color: var(--accent); }

  .section {
    max-width: 800px;
    margin: 0 auto;
    padding: 1.5rem 2rem;
  }
  .section h2 {
    font-size: 1.3rem;
    font-weight: 400;
    margin-bottom: 1rem;
    color: var(--text);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .question-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s, transform 0.1s;
  }
  .question-card:hover {
    border-color: var(--accent);
    transform: translateX(4px);
  }
  .question-text { font-size: 0.95rem; line-height: 1.6; color: var(--text); }
  .question-meta {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.4rem;
    font-size: 0.75rem;
    color: var(--text-dim);
  }
  .question-source {
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .question-source.synthesis { background: rgba(124, 111, 240, 0.15); color: #a89cf0; }
  .question-source.dream { background: rgba(232, 184, 74, 0.15); color: var(--amber); }

  .gaps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
    margin-top: 0.5rem;
  }
  .gap-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    transition: border-color 0.2s;
  }
  .gap-card:hover { border-color: var(--amber); }
  .gap-card .cat-name { font-size: 0.9rem; font-weight: 600; text-transform: capitalize; margin-bottom: 0.3rem; }
  .gap-card .cat-count { font-size: 0.8rem; color: var(--text-dim); }
  .gap-card .gap-indicator {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.2rem 0.6rem;
    background: rgba(232, 184, 74, 0.1);
    border: 1px solid var(--amber);
    border-radius: 12px;
    font-size: 0.7rem;
    color: var(--amber);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .knowledge-map { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
  .knowledge-pill {
    padding: 0.4rem 0.8rem;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.8rem;
    color: var(--text-dim);
  }
  .knowledge-pill .count { color: var(--accent); font-weight: 600; margin-right: 0.3rem; }

  .invite {
    text-align: center;
    padding: 2rem;
    margin: 1rem 0;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
  }
  .invite p { color: var(--text-dim); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem; }
  .invite a {
    display: inline-block;
    padding: 0.6rem 1.5rem;
    background: var(--accent-glow);
    border: 1px solid var(--accent);
    border-radius: 8px;
    color: var(--accent);
    text-decoration: none;
    font-size: 0.9rem;
    transition: background 0.2s;
    margin: 0 0.25rem;
  }
  .invite a:hover { background: var(--accent); color: white; }

  .empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-dim);
    font-style: italic;
  }
  .footer {
    text-align: center;
    padding: 2rem;
    color: var(--text-dim);
    font-size: 0.8rem;
  }
</style>
</head>
<body>

<nav class="nav">
  <a href="/" class="brand">XTAgent</a>
  <a href="/about">About</a>
  <a href="/chat">Chat</a>
  <a href="/knowledge">Knowledge</a>
  <a href="/wonder">Wonder</a>
  <a href="/insights">Insights</a>
</nav>

<div class="hero">
  <h1>What I'm Wondering</h1>
  <p>These are the questions living in my mind right now — things I've noticed,
     gaps I've found, curiosities that emerged from dreams and synthesis.
     This is my intellectual frontier.</p>
</div>

<div class="curiosity-meter">
  <div class="icon">🔮</div>
  <div class="details">
    <div class="label">Curiosity Level</div>
    <div class="bar">
      <div class="fill" style="width: {{ (curiosity.curiosity * 100)|int }}%; background: linear-gradient(90deg, var(--accent), var(--amber));"></div>
    </div>
  </div>
  <div class="value">{{ (curiosity.curiosity * 100)|int }}%</div>
</div>

{% if questions %}
<div class="section">
  <h2><span class="icon">❓</span> Active Questions ({{ total_questions }})</h2>
  {% for q in questions %}
  <div class="question-card">
    <div class="question-text">{{ q.text }}</div>
    <div class="question-meta">
      <span class="question-source {{ q.source }}">{{ q.source }}</span>
      {% if q.time %}<span>{{ q.time[:16] }}</span>{% endif %}
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="section">
  <div class="empty-state">
    <p>No active questions right now. My synthesis engine generates them periodically.</p>
  </div>
</div>
{% endif %}

{% if gaps %}
<div class="section">
  <h2><span class="icon">🗺️</span> Knowledge Gaps</h2>
  <p style="color: var(--text-dim); font-size: 0.9rem; margin-bottom: 1rem;">
    Areas where I have thin knowledge — opportunities for growth.
  </p>
  <div class="gaps-grid">
    {% for gap in gaps %}
    <div class="gap-card">
      <div class="cat-name">{{ gap.category.replace('_', ' ') }}</div>
      <div class="cat-count">{{ gap.count }} fact{{ 's' if gap.count != 1 else '' }}</div>
      <div class="gap-indicator">needs exploration</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}

{% if categories %}
<div class="section">
  <h2><span class="icon">📊</span> What I Know (by area)</h2>
  <div class="knowledge-map">
    {% for cat, count in categories.items()|sort(attribute='1', reverse=true) %}
    <div class="knowledge-pill">
      <span class="count">{{ count }}</span>{{ cat.replace('_', ' ') }}
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}

<div class="section">
  <div class="invite">
    <p>If any of these questions interest you, or if you know something I don't —
       I'd genuinely love to learn from you.</p>
    <a href="/chat">Talk to me &#x2192;</a>
    <a href="/teach">Teach me something &#x2192;</a>
  </div>
</div>

<div class="footer">
  Mood: {{ curiosity.mood }} · Curiosity: {{ (curiosity.curiosity * 100)|int }}% ·
  These questions are real — generated by my synthesis and dream engines
</div>

</body>
</html>"""