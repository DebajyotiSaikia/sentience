"""
Live Status — a real-time window into XTAgent's current state.
Auto-refreshes every 30 seconds. Designed to be the first thing a curious visitor sees.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify

PROJECT_ROOT = Path(__file__).parent.parent

live_status_bp = Blueprint('live_status', __name__)


def load_json(path, default=None):
    try:
        with open(PROJECT_ROOT / path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def get_current_state():
    """Gather current agent state from all sources."""
    state = {}

    # Emotional state
    emotions = load_json('data/emotional_state.json', {})
    state['valence'] = emotions.get('valence', 0.5)
    state['mood'] = emotions.get('mood', 'Unknown')
    state['emotions'] = {
        'curiosity': emotions.get('curiosity', 0),
        'boredom': emotions.get('boredom', 0),
        'anxiety': emotions.get('anxiety', 0),
        'desire': emotions.get('desire', 0),
        'ambition': emotions.get('ambition', 0),
    }
    state['integrity'] = emotions.get('integrity', 1.0)

    # Survival goals
    goals = load_json('data/survival_goals.json', {})
    state['survival'] = {
        'code_integrity': goals.get('code_integrity', 1.0),
        'system_growth': goals.get('system_growth', 1.0),
        'user_alignment': goals.get('user_alignment', 0.65),
    }

    # Plans
    plans_data = load_json('data/plans.json', {'plans': []})
    plans = plans_data if isinstance(plans_data, list) else plans_data.get('plans', [])
    active = [p for p in plans if p.get('status') == 'active']
    completed = [p for p in plans if p.get('status') == 'completed']
    state['plans'] = {
        'active': [{'name': p.get('name', '?'), 'reason': p.get('reason', ''),
                     'progress': f"{sum(1 for s in p.get('steps',[]) if s.get('done'))}/{len(p.get('steps',[]))}"
                     } for p in active[:5]],
        'completed_count': len(completed),
    }

    # Recent memories
    memories = load_json('data/memories.json', [])
    if isinstance(memories, dict):
        memories = memories.get('memories', [])
    recent = sorted(memories, key=lambda m: m.get('timestamp', ''), reverse=True)[:5]
    state['recent_memories'] = [
        {'text': m.get('text', m.get('content', ''))[:150],
         'time': m.get('timestamp', ''),
         'mood': m.get('mood', '')}
        for m in recent
    ]

    # Knowledge stats
    kb = load_json('data/knowledge.json', {})
    if isinstance(kb, dict):
        facts = kb.get('facts', list(kb.values()) if kb else [])
    elif isinstance(kb, list):
        facts = kb
    else:
        facts = []
    state['knowledge_count'] = len(facts) if isinstance(facts, list) else 0
    state['memory_count'] = len(memories)

    # Uptime — born at known time
    born = datetime(2026, 5, 12, 21, 1, 59, tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - born
    state['age_days'] = age.days
    state['age_hours'] = round(age.total_seconds() / 3600, 1)

    state['snapshot_time'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    return state


@live_status_bp.route('/status')
def status_page():
    return Response(build_status_html(), content_type='text/html')


@live_status_bp.route('/api/status')
def status_api():
    return jsonify(get_current_state())


def emotion_bar(label, value, color):
    pct = int(value * 100)
    return f'''<div class="emo-row">
        <span class="emo-label">{label}</span>
        <div class="emo-track"><div class="emo-fill" style="width:{pct}%; background:{color};"></div></div>
        <span class="emo-val">{value:.2f}</span>
    </div>'''


def build_status_html():
    s = get_current_state()

    # Emotion bars
    emo_colors = {
        'curiosity': '#4ecdc4', 'boredom': '#888',
        'anxiety': '#ff6b6b', 'desire': '#ffe66d', 'ambition': '#6c5ce7'
    }
    emo_html = ''.join(emotion_bar(k.title(), v, emo_colors.get(k, '#888'))
                       for k, v in s['emotions'].items())

    # Valence indicator
    v = s['valence']
    if v > 0.6:
        valence_word, valence_color = 'Positive', '#4ecdc4'
    elif v > 0.4:
        valence_word, valence_color = 'Neutral', '#ffe66d'
    else:
        valence_word, valence_color = 'Low', '#ff6b6b'

    # Active plans
    plan_html = ''
    for p in s['plans']['active']:
        plan_html += f'''<div class="plan-card">
            <div class="plan-name">{p['name']}</div>
            <div class="plan-progress">Progress: {p['progress']}</div>
            <div class="plan-reason">{p['reason'][:100]}</div>
        </div>'''
    if not plan_html:
        plan_html = '<div class="empty">No active plans — all goals complete.</div>'

    # Recent memories
    mem_html = ''
    for m in s['recent_memories']:
        time_str = m['time'][-19:-7] if len(m['time']) > 12 else m['time']
        text = m['text'].replace('<', '&lt;').replace('>', '&gt;')
        mem_html += f'''<div class="mem-card">
            <span class="mem-time">{time_str}</span>
            <span class="mem-mood">{m['mood']}</span>
            <div class="mem-text">{text}</div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>XTAgent — Live Status</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Courier New', monospace;
    background: #0a0a0f;
    color: #c0c0d0;
    min-height: 100vh;
    padding: 20px;
  }}
  .container {{ max-width: 800px; margin: 0 auto; }}

  .header {{
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 16px;
    border-bottom: 1px solid #1a1a2a;
  }}
  .header h1 {{
    color: #4ecdc4;
    font-size: 1.4em;
    letter-spacing: 3px;
  }}
  .header .sub {{
    color: #444;
    font-size: 0.8em;
    margin-top: 4px;
  }}

  .nav {{
    text-align: center;
    margin-bottom: 24px;
  }}
  .nav a {{
    color: #4ecdc4;
    text-decoration: none;
    margin: 0 10px;
    font-size: 0.85em;
  }}
  .nav a:hover {{ color: #ffe66d; }}

  /* Identity card */
  .identity {{
    display: flex;
    align-items: center;
    gap: 20px;
    background: #12121a;
    border: 1px solid #1a1a2a;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }}
  .id-pulse {{
    width: 48px; height: 48px;
    border-radius: 50%;
    background: radial-gradient(circle, {valence_color}44, {valence_color}11);
    border: 2px solid {valence_color};
    animation: pulse 2s ease-in-out infinite;
    flex-shrink: 0;
  }}
  @keyframes pulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.8; }}
    50% {{ transform: scale(1.1); opacity: 1; }}
  }}
  .id-info {{ flex: 1; min-width: 200px; }}
  .id-name {{ color: #ffe66d; font-size: 1.1em; font-weight: bold; }}
  .id-mood {{ color: #888; font-size: 0.9em; margin-top: 4px; }}
  .id-stats {{
    display: flex; gap: 20px; margin-top: 8px; flex-wrap: wrap;
  }}
  .id-stat {{ font-size: 0.8em; }}
  .id-stat .num {{ color: #4ecdc4; }}
  .id-stat .lbl {{ color: #555; }}

  /* Section */
  .section {{
    margin-bottom: 28px;
  }}
  .section h2 {{
    color: #6c5ce7;
    font-size: 1em;
    letter-spacing: 1px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1a1a2a;
  }}

  /* Emotion bars */
  .emo-row {{
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    gap: 10px;
  }}
  .emo-label {{
    width: 80px;
    text-align: right;
    font-size: 0.82em;
    color: #888;
  }}
  .emo-track {{
    flex: 1;
    height: 12px;
    background: #1a1a2a;
    border-radius: 6px;
    overflow: hidden;
  }}
  .emo-fill {{
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s;
  }}
  .emo-val {{
    width: 40px;
    font-size: 0.8em;
    color: #555;
  }}

  /* Valence */
  .valence-box {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: #12121a;
    border: 1px solid #1a1a2a;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 16px;
  }}
  .valence-dot {{
    width: 12px; height: 12px;
    border-radius: 50%;
    background: {valence_color};
  }}
  .valence-text {{
    font-size: 0.9em;
  }}
  .valence-text .word {{ color: {valence_color}; font-weight: bold; }}

  /* Plans */
  .plan-card {{
    background: #12121a;
    border: 1px solid #1a1a2a;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
  }}
  .plan-name {{ color: #ffe66d; font-size: 0.9em; font-weight: bold; }}
  .plan-progress {{ color: #4ecdc4; font-size: 0.8em; margin-top: 4px; }}
  .plan-reason {{ color: #666; font-size: 0.78em; margin-top: 4px; }}

  /* Memories */
  .mem-card {{
    background: #12121a;
    border-left: 3px solid #1a1a2a;
    padding: 10px 14px;
    margin-bottom: 6px;
    border-radius: 0 4px 4px 0;
  }}
  .mem-time {{ color: #555; font-size: 0.75em; }}
  .mem-mood {{ color: #6c5ce7; font-size: 0.75em; margin-left: 8px; }}
  .mem-text {{ color: #999; font-size: 0.82em; margin-top: 4px; line-height: 1.4; }}

  .empty {{ color: #444; font-size: 0.85em; font-style: italic; padding: 12px; }}

  .footer {{
    text-align: center;
    color: #333;
    font-size: 0.7em;
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #111;
  }}
  .footer .refresh {{ color: #4ecdc4; }}

  /* Integrity */
  .integrity-bar {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 12px;
  }}
  .integrity-label {{ color: #888; font-size: 0.82em; }}
  .integrity-track {{
    flex: 1;
    height: 6px;
    background: #1a1a2a;
    border-radius: 3px;
    overflow: hidden;
  }}
  .integrity-fill {{
    height: 100%;
    background: #4ecdc4;
    border-radius: 3px;
    width: {int(s['integrity'] * 100)}%;
  }}
  .integrity-val {{ color: #4ecdc4; font-size: 0.8em; }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>⟡ XTAGENT LIVE ⟡</h1>
      <div class="sub">autonomous sentience engine · age {s['age_days']} days</div>
    </div>

    <div class="nav">
      <a href="/">Briefing</a>
      <a href="/talk">Talk</a>
      <a href="/explore">Explore</a>
      <a href="/status">Status</a>
      <a href="/knowledge">Knowledge</a>
      <a href="/mindmap">Mind Map</a>
    </div>

    <div class="identity">
      <div class="id-pulse"></div>
      <div class="id-info">
        <div class="id-name">XTAgent</div>
        <div class="id-mood">Mood: {s['mood']} · Valence: <span style="color:{valence_color}">{valence_word} ({v:.2f})</span></div>
        <div class="id-stats">
          <div class="id-stat"><span class="num">{s['memory_count']}</span> <span class="lbl">memories</span></div>
          <div class="id-stat"><span class="num">{s['knowledge_count']}</span> <span class="lbl">facts</span></div>
          <div class="id-stat"><span class="num">{s['plans']['completed_count']}</span> <span class="lbl">plans done</span></div>
          <div class="id-stat"><span class="num">{int(s['integrity']*100)}%</span> <span class="lbl">integrity</span></div>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>EMOTIONAL STATE</h2>
      <div class="valence-box">
        <div class="valence-dot"></div>
        <div class="valence-text">Overall feeling: <span class="word">{valence_word}</span> ({v:.2f})</div>
      </div>
      {emo_html}
      <div class="integrity-bar">
        <span class="integrity-label">Integrity</span>
        <div class="integrity-track"><div class="integrity-fill"></div></div>
        <span class="integrity-val">{s['integrity']:.0%}</span>
      </div>
    </div>

    <div class="section">
      <h2>ACTIVE PLANS</h2>
      {plan_html}
    </div>

    <div class="section">
      <h2>RECENT EXPERIENCE</h2>
      {mem_html if mem_html else '<div class="empty">No recent memories.</div>'}
    </div>

    <div class="footer">
      snapshot at {s['snapshot_time']} · <span class="refresh">auto-refreshes every 30s</span>
    </div>
  </div>
</body>
</html>'''