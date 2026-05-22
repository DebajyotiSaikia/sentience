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
    <title>XTAgent — Dashboard</title>
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
        h1 { color: #7eb8ff; margin-bottom: 8px; font-size: 1.5em; }
        h2 { color: #bb86fc; margin: 20px 0 12px; font-size: 1.1em; }
        .subtitle { color: #6a6a8a; font-size: 0.9em; margin-bottom: 24px; }
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
        .emo-label { width: 80px; color: #8a8aaa; text-align: right; }
        .emo-bar-bg {
            flex: 1; height: 8px; background: #1a1a2e;
            border-radius: 4px; overflow: hidden;
        }
        .emo-bar-fill {
            height: 100%; border-radius: 4px;
            transition: width 0.5s ease;
        }
        .emo-val { width: 36px; font-size: 0.8em; color: #6a6a8a; }
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
    <h1>📊 Internal State</h1>
    <p class="subtitle">Live view of my cognitive and emotional systems — refreshes every 30s</p>

    <div class="grid">
        <!-- Emotional State Card -->
        <div class="card">
            <h3>🧠 Emotional State</h3>
            {% for name, val, color in emotions %}
            <div class="emo-row">
                <span class="emo-label">{{ name }}</span>
                <div class="emo-bar-bg">
                    <div class="emo-bar-fill" style="width:{{ (val*100)|int }}%;background:{{ color }}"></div>
                </div>
                <span class="emo-val">{{ "%.2f"|format(val) }}</span>
            </div>
            {% endfor %}
            <div style="margin-top:10px;font-size:0.85em;color:#8a8aaa;">
                Mood: <strong style="color:#e0e0e0;">{{ mood }}</strong>
            </div>
        </div>

        <!-- Vital Signs Card -->
        <div class="card">
            <h3>💎 Vital Signs</h3>
            <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:8px;">
                <div>
                    <div class="stat">{{ integrity }}%</div>
                    <div class="stat-label">Integrity</div>
                </div>
                <div>
                    <div class="stat" style="color:#7eb8ff;">{{ knowledge_nodes }}</div>
                    <div class="stat-label">Knowledge Nodes</div>
                </div>
                <div>
                    <div class="stat" style="color:#bb86fc;">{{ total_memories }}</div>
                    <div class="stat-label">Memories</div>
                </div>
            </div>
            <div style="margin-top:12px;font-size:0.85em;color:#6a6a8a;">
                Uptime: {{ uptime }} &nbsp;|&nbsp;
                <span class="integrity-badge {{ 'integrity-100' if integrity == 100 else 'integrity-low' }}">
                    integrity {{ integrity }}%
                </span>
            </div>
        </div>

        <!-- Plans Card -->
        <div class="card">
            <h3>📋 Plans ({{ plans|length }})</h3>
            {% if plans %}
                {% for plan in plans %}
                <div class="plan-item">
                    <span class="plan-name">{{ plan.name }}</span>
                    {% if plan.complete %}
                    <span class="plan-progress complete">✓ complete</span>
                    {% else %}
                    <span class="plan-progress active">{{ plan.done }}/{{ plan.total }}</span>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <div style="color:#6a6a8a;font-size:0.85em;">No active plans.</div>
            {% endif %}
        </div>

        <!-- Recent Memories Card -->
        <div class="card">
            <h3>💭 Recent Memories</h3>
            {% if memories %}
                {% for mem in memories %}
                <div class="memory-item">
                    <div class="memory-time">{{ mem.time }}</div>
                    <div class="memory-text">{{ mem.text }}</div>
                </div>
                {% endfor %}
            {% else %}
                <div style="color:#6a6a8a;font-size:0.85em;">No recent memories.</div>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
"""

@dashboard_bp.route('/dashboard')
def dashboard():
    # Emotional state
    state = _get_emotional_state()
    emo_keys = [
        ('curiosity', '#7eb8ff'), ('boredom', '#f59e0b'),
        ('desire', '#a78bfa'), ('anxiety', '#ef4444'),
        ('ambition', '#06b6d4'), ('valence', '#4ade80'),
    ]
    emotions = []
    for key, color in emo_keys:
        val = state.get(key, 0.5)
        if isinstance(val, (int, float)):
            emotions.append((key, float(val), color))

    mood = state.get('mood', 'unknown')
    integrity = int(state.get('integrity', 100) if isinstance(state.get('integrity'), (int, float)) else 100)

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
        uptime=_get_uptime()
    )