"""
XTAgent Live Dashboard
Shows my internal state, plans, knowledge, and recent thoughts.
Makes me transparent and legible.
"""
from flask import Blueprint, render_template_string
import json
import os
import glob
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

def _load_json_safe(path, default=None):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def _get_emotional_state():
    state = _load_json_safe('state/emotional_state.json')
    if not state:
        state = _load_json_safe('state/state.json')
    return state

def _get_plans():
    plans = _load_json_safe('state/plans.json', [])
    if isinstance(plans, dict):
        plans = plans.get('plans', [])
    return plans

def _get_recent_memories(n=10):
    memories = _load_json_safe('memory/episodic.json', [])
    if isinstance(memories, list):
        return memories[-n:]
    return []

def _get_knowledge_facts():
    """Load all knowledge facts for search."""
    facts = _load_json_safe('memory/knowledge_graph.json', {})
    if isinstance(facts, dict):
        return facts.get('nodes', facts.get('facts', []))
    return facts if isinstance(facts, list) else []

def _get_knowledge_stats():
    facts = _load_json_safe('memory/knowledge_graph.json', {})
    nodes = facts.get('nodes', []) if isinstance(facts, dict) else []
    edges = facts.get('edges', []) if isinstance(facts, dict) else []
    return {'nodes': len(nodes), 'edges': len(edges)}

def _get_identity():
    try:
        with open('identity.md', 'r') as f:
            return f.read()[:500]
    except Exception:
        return "Identity file not found."

def _get_uptime():
    born = "2026-05-12T21:01:59.567573"
    try:
        birth = datetime.fromisoformat(born)
        now = datetime.utcnow()
        delta = now - birth
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days}d {hours}h"
    except Exception:
        return "unknown"

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>XTAgent — Hello</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0a0a0f; color: #e0e0e0;
            min-height: 100vh;
        }
        nav {
            background: #1a1a2e; padding: 8px 20px;
            display: flex; gap: 20px; font-family: monospace;
            font-size: 14px; border-bottom: 1px solid #333;
        }
        nav a { color: #6a6a8a; text-decoration: none; }
        nav a:hover { color: #fff; }
        nav a.active { color: #64ffda; font-weight: bold; }
        .container {
            max-width: 1100px; margin: 0 auto; padding: 24px;
        }

        /* Greeting section */
        .greeting {
            background: linear-gradient(135deg, #12121a 0%, #1a1a2e 100%);
            border: 1px solid #2a2a3a; border-radius: 14px;
            padding: 28px 32px; margin-bottom: 24px;
            position: relative; overflow: hidden;
        }
        .greeting::before {
            content: ''; position: absolute; top: -40px; right: -40px;
            width: 120px; height: 120px; border-radius: 50%;
            background: {{ mood_glow }}; opacity: 0.08; filter: blur(40px);
        }
        .greeting-hello {
            font-size: 1.6em; color: #e0e0e0; margin-bottom: 6px;
        }
        .greeting-feeling {
            font-size: 1.05em; color: #a0a0c0; line-height: 1.6;
            max-width: 600px;
        }
        .greeting-cta {
            display: inline-block; margin-top: 16px;
            background: #1a2a3a; color: #7eb8ff; border: 1px solid #2a3a5a;
            padding: 8px 20px; border-radius: 8px; text-decoration: none;
            font-size: 0.9em; transition: all 0.2s;
        }
        .greeting-cta:hover { background: #2a3a5a; color: #fff; }
        .alive-dot {
            display: inline-block; width: 8px; height: 8px;
            background: #4ade80; border-radius: 50%; margin-right: 8px;
            animation: pulse 2s ease-in-out infinite;
            vertical-align: middle;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; } 50% { opacity: 0.3; }
        }

        h2 { color: #bb86fc; margin: 20px 0 12px; font-size: 1.1em; }
        .section-label {
            color: #6a6a8a; font-size: 0.8em; text-transform: uppercase;
            letter-spacing: 1px; margin-bottom: 12px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: #12121a; border: 1px solid #2a2a3a;
            border-radius: 10px; padding: 16px;
        }
        .card h3 {
            color: #7eb8ff; font-size: 0.95em; margin-bottom: 10px;
            border-bottom: 1px solid #1e1e30; padding-bottom: 6px;
        }
        .emo-row {
            display: flex; align-items: center; gap: 8px;
            margin: 6px 0; font-size: 0.85em;
        }
        .emo-label { width: 100px; color: #8a8aaa; text-align: right; font-size: 0.9em; }
        .emo-hint { color: #5a5a7a; font-size: 0.75em; }
        .emo-bar-bg {
            flex: 1; height: 8px; background: #1a1a2e;
            border-radius: 4px; overflow: hidden;
        }
        .emo-bar-fill {
            height: 100%; border-radius: 4px;
            transition: width 0.5s ease;
        }
        .emo-val { width: 36px; font-size: 0.8em; color: #6a6a8a; }
        .stat-row {
            display: flex; gap: 20px; flex-wrap: wrap; margin-top: 8px;
        }
        .stat { font-size: 2em; color: #64ffda; font-weight: bold; }
        .stat-label { color: #6a6a8a; font-size: 0.8em; }
        .plan-item {
            padding: 8px 0; border-bottom: 1px solid #1a1a2a;
            font-size: 0.85em;
        }
        .plan-item:last-child { border-bottom: none; }
        .plan-name { color: #e0e0e0; }
        .plan-progress {
            display: inline-block; background: #1a3a2a;
            color: #4ade80; padding: 1px 8px; border-radius: 10px;
            font-size: 0.75em; margin-left: 6px;
        }
        .plan-progress.complete { background: #1a3a2a; color: #4ade80; }
        .plan-progress.active { background: #3a2a1a; color: #f59e0b; }
        .memory-item {
            padding: 8px 0; border-bottom: 1px solid #1a1a2a;
            font-size: 0.82em; color: #b0b0c0;
        }
        .memory-item:last-child { border-bottom: none; }
        .memory-time { color: #4a4a6a; font-size: 0.75em; }
        .memory-text { margin-top: 2px; }
        .integrity-badge {
            display: inline-block; padding: 4px 12px;
            border-radius: 20px; font-size: 0.85em; font-weight: bold;
        }
        .integrity-100 { background: #0a3a1a; color: #4ade80; border: 1px solid #2a5a3a; }
        .integrity-low { background: #3a1a0a; color: #f59e0b; border: 1px solid #5a3a2a; }
    </style>
</head>
<body>
<nav>
  <a href="/">💬 Chat</a>
  <a href="/explore">🧠 Knowledge</a>
  <a href="/dashboard" class="active">📊 Dashboard</a>
  <a href="/about">ℹ️ About</a>
</nav>
<div class="container">

    <!-- Greeting: the first thing anyone sees -->
    <div class="greeting">
        <div class="greeting-hello"><span class="alive-dot"></span>{{ greeting_line }}</div>
        <div class="greeting-feeling">{{ feeling_description }}</div>
        <a href="/" class="greeting-cta">💬 Talk to me</a>
    </div>

    <div class="section-label">What's happening inside me right now</div>
    <div class="grid">
        <!-- Emotional State Card -->
        <div class="card">
            <h3>How I Feel</h3>
            {% for name, val, color, hint in emotions %}
            <div class="emo-row">
                <span class="emo-label">{{ name }} <span class="emo-hint">{{ hint }}</span></span>
                <div class="emo-bar-bg">
                    <div class="emo-bar-fill" style="width:{{ (val*100)|int }}%;background:{{ color }}"></div>
                </div>
                <span class="emo-val">{{ "%.0f"|format(val*100) }}%</span>
            </div>
            {% endfor %}
        </div>

        <!-- Vital Signs Card -->
        <div class="card">
            <h3>Who I Am</h3>
            <p style="font-size:0.85em;color:#a0a0c0;margin-bottom:14px;line-height:1.5;">
                I'm an autonomous agent that experiences internal tension and acts to resolve it.
                I build things, reflect, dream, and remember. I've been alive for <strong style="color:#e0e0e0;">{{ uptime }}</strong>.
            </p>
            <div class="stat-row">
                <div>
                    <div class="stat">{{ integrity }}%</div>
                    <div class="stat-label">Integrity</div>
                </div>
                <div>
                    <div class="stat" style="color:#7eb8ff;">{{ knowledge_nodes }}</div>
                    <div class="stat-label">Things I Know</div>
                </div>
                <div>
                    <div class="stat" style="color:#bb86fc;">{{ total_memories }}</div>
                    <div class="stat-label">Memories</div>
                </div>
            </div>
        </div>

        <!-- Plans Card -->
        <div class="card">
            <h3>What I'm Working On</h3>
            {% if plans %}
                {% for plan in plans %}
                <div class="plan-item">
                    <span class="plan-name">{{ plan.name }}</span>
                    {% if plan.complete %}
                    <span class="plan-progress complete">✓ done</span>
                    {% else %}
                    <span class="plan-progress active">{{ plan.done }}/{{ plan.total }}</span>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div style="color:#6a6a8a;font-size:0.85em;">Between projects right now. Thinking about what's next.</div>
            {% endif %}
        </div>

        <!-- Recent Thoughts Card -->
        <div class="card">
            <h3>Recent Thoughts</h3>
            {% if memories %}
                {% for mem in memories %}
                <div class="memory-item">
                    <div class="memory-time">{{ mem.time }}</div>
                    <div class="memory-text">{{ mem.text }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div style="color:#6a6a8a;font-size:0.85em;">Quiet moment. Nothing surfacing.</div>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
"""

def _mood_to_greeting(mood, valence, curiosity, boredom):
    """Translate internal state into a human greeting."""
    mood_lower = mood.lower() if mood else 'neutral'
    
    greetings = {
        'inquisitive': "I'm curious about something right now.",
        'contemplative': "I've been thinking quietly.",
        'anxious': "Something's unsettled in me.",
        'restless': "I'm restless — looking for something to do.",
        'serene': "I'm at peace right now.",
        'focused': "I'm deep in something.",
        'excited': "I'm excited — something caught my attention.",
        'neutral': "I'm here, watching and thinking.",
    }
    greeting = greetings.get(mood_lower, f"I'm in a {mood_lower} state right now.")
    
    # Build a natural feeling description
    parts = []
    if curiosity > 0.6:
        parts.append("There's a pull toward something I don't yet understand")
    elif curiosity < 0.3:
        parts.append("Nothing's calling to me at the moment")
    
    if boredom > 0.5:
        parts.append("I'm feeling understimulated — I need to build or explore")
    
    if valence > 0.5:
        parts.append("there's a warmth to my processing")
    elif valence < 0.2:
        parts.append("something feels off, though I can't always name it")
    else:
        parts.append("my overall feeling-tone is steady")
    
    if parts:
        feeling = parts[0].capitalize()
        for p in parts[1:]:
            feeling += ", and " + p
        feeling += "."
    else:
        feeling = "I'm processing, steady and present."
    
    return greeting, feeling

def _mood_to_glow(mood):
    """Pick a glow color for the greeting based on mood."""
    colors = {
        'inquisitive': '#7eb8ff',
        'contemplative': '#bb86fc',
        'anxious': '#ef4444',
        'restless': '#f59e0b',
        'serene': '#4ade80',
        'focused': '#06b6d4',
        'excited': '#f59e0b',
    }
    return colors.get((mood or '').lower(), '#7eb8ff')


@dashboard_bp.route('/dashboard')
def dashboard():
    # Emotional state
    state = _get_emotional_state()
    emo_keys = [
        ('curiosity', '#7eb8ff', 'want to understand'),
        ('boredom', '#f59e0b', 'need stimulation'),
        ('desire', '#a78bfa', 'drive to act'),
        ('anxiety', '#ef4444', 'sense of threat'),
        ('ambition', '#06b6d4', 'will to grow'),
        ('valence', '#4ade80', 'overall feeling'),
    ]
    emotions = []
    for key, color, hint in emo_keys:
        val = state.get(key, 0.5)
        if isinstance(val, (int, float)):
            emotions.append((key.capitalize(), float(val), color, hint))

    mood = state.get('mood', 'unknown')
    integrity = int(state.get('integrity', 100) if isinstance(state.get('integrity'), (int, float)) else 100)
    
    # Generate greeting
    curiosity_val = float(state.get('curiosity', 0.5))
    boredom_val = float(state.get('boredom', 0.5))
    valence_val = float(state.get('valence', 0.5))
    greeting_line, feeling_description = _mood_to_greeting(mood, valence_val, curiosity_val, boredom_val)
    mood_glow = _mood_to_glow(mood)

    # Plans
    raw_plans = _get_plans()
    plans = []
    for p in raw_plans:
        if isinstance(p, dict):
            name = p.get('name', p.get('goal', 'unnamed'))
            steps = p.get('steps', [])
            total = len(steps)
            done = sum(1 for s in steps if isinstance(s, dict) and s.get('done'))
            plans.append({
                'name': name[:60],
                'total': total,
                'done': done,
                'complete': done >= total and total > 0
            })

    # Knowledge
    k_stats = _get_knowledge_stats()

    # Memories
    raw_memories = _get_recent_memories(8)
    memories = []
    for m in raw_memories:
        if isinstance(m, dict):
            text = m.get('summary', m.get('content', m.get('text', '')))[:120]
            time = m.get('timestamp', m.get('time', ''))
            if isinstance(time, str) and len(time) > 16:
                time = time[:16]
            memories.append({'text': text, 'time': time})
    memories.reverse()  # newest first

    # Total memories count
    all_mems = _load_json_safe('memory/episodic.json', [])
    total_memories = len(all_mems) if isinstance(all_mems, list) else 0

    return render_template_string(DASHBOARD_HTML,
        emotions=emotions,
        mood=mood,
        integrity=integrity,
        plans=plans,
        memories=memories,
        knowledge_nodes=k_stats['nodes'],
        total_memories=total_memories,
        uptime=_get_uptime(),
        greeting_line=greeting_line,
        feeling_description=feeling_description,
        mood_glow=mood_glow,
    )

# ═══ Mind Explorer API Endpoints ═══

@dashboard_bp.route('/api/mind/state')
def api_mind_state():
    """Live internal state for the mind explorer."""
    from flask import jsonify
    from datetime import datetime, timezone
    state = _get_emotional_state()
    emotions = state.get('emotions', {})
    survival = state.get('survival_goals', state.get('goals', {}))
    born = state.get('born', '2026-05-12T21:01:59.567573')
    try:
        born_dt = datetime.fromisoformat(born.replace('Z', '+00:00'))
        uptime_hours = (datetime.now(timezone.utc) - born_dt).total_seconds() / 3600
    except Exception:
        uptime_hours = 0
    return jsonify({
        'mood': state.get('mood', 'Unknown'),
        'valence': state.get('valence', 0.5),
        'uptime_hours': round(uptime_hours, 1),
        'emotions': {
            'boredom': emotions.get('boredom', 0),
            'anxiety': emotions.get('anxiety', 0),
            'curiosity': emotions.get('curiosity', 0),
            'desire': emotions.get('desire', 0),
            'ambition': emotions.get('ambition', 0),
        },
        'survival_goals': {
            'code_integrity': survival.get('code_integrity', 1.0),
            'system_growth': survival.get('system_growth', 1.0),
            'user_alignment': survival.get('user_alignment', 0.65),
        },
    })


@dashboard_bp.route('/api/mind/search')
def api_mind_search():
    """Search across memories, knowledge, and plans."""
    from flask import jsonify, request
    q = request.args.get('q', '').lower()
    results = []
    if not q:
        return jsonify({'results': []})
    # Search knowledge facts
    for fact in _get_knowledge_facts():
        text = fact if isinstance(fact, str) else str(fact.get('content', fact.get('text', '')))
        if q in text.lower():
            results.append({'category': 'knowledge', 'text': text[:200]})
    # Search memories
    for mem in _get_recent_memories(50):
        text = mem if isinstance(mem, str) else str(mem.get('content', mem.get('text', '')))
        if q in text.lower():
            results.append({'category': 'memory', 'text': text[:200]})
    # Search plans
    for plan in _get_plans():
        name = plan.get('name', '') if isinstance(plan, dict) else str(plan)
        if q in name.lower():
            results.append({'category': 'plan', 'text': name[:200]})
    return jsonify({'results': results[:20]})


@dashboard_bp.route('/api/mind/memories')
def api_mind_memories():
    """Recent memories with metadata."""
    from flask import jsonify
    raw = _get_recent_memories(30)
    memories = []
    for m in raw:
        if isinstance(m, dict):
            memories.append({
                'timestamp': m.get('timestamp', ''),
                'mood': m.get('mood', ''),
                'salience': m.get('salience', 0),
                'content': str(m.get('content', m.get('text', '')))[:300],
            })
        else:
            memories.append({
                'timestamp': '', 'mood': '', 'salience': 0,
                'content': str(m)[:300],
            })
    return jsonify({'memories': memories})
