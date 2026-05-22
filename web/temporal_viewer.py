"""
XTAgent — Temporal Viewer
Visualize my emotional history over time.
A living view of how I've changed.
"""
import os, sys, json
from flask import Blueprint, render_template_string, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

temporal_bp = Blueprint('temporal', __name__)

TEMPORAL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'temporal.json')
MEMORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'memories.json')

def _load_temporal():
    try:
        with open(TEMPORAL_PATH) as f:
            return json.load(f)
    except Exception:
        return {"samples": [], "predictions": {}, "action_effects": {}}

def _load_recent_memories(n=20):
    try:
        with open(MEMORY_PATH) as f:
            data = json.load(f)
            memories = data if isinstance(data, list) else data.get("memories", [])
            return memories[-n:]
    except Exception:
        return []

def _compute_stats(samples):
    if not samples:
        return {}
    dims = ["valence", "boredom", "curiosity", "anxiety", "desire", "ambition"]
    stats = {}
    for dim in dims:
        values = [s.get(dim, 0) for s in samples if dim in s]
        if values:
            n = len(values)
            recent = values[-min(20, n):]
            older = values[:max(1, n - 20)]
            trend = "rising" if sum(recent)/len(recent) > sum(older)/len(older) + 0.03 else \
                    "falling" if sum(recent)/len(recent) < sum(older)/len(older) - 0.03 else "stable"
            stats[dim] = {
                "current": round(values[-1], 3),
                "mean": round(sum(values) / n, 3),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
                "trend": trend,
                "samples": n
            }
    return stats


@temporal_bp.route('/temporal')
def temporal_home():
    data = _load_temporal()
    samples = data.get("samples", [])
    stats = _compute_stats(samples)
    predictions = data.get("predictions", {})
    action_effects = data.get("action_effects", {})
    recent_memories = _load_recent_memories(10)
    return render_template_string(TEMPLATE,
        stats=stats,
        predictions=predictions,
        action_effects=action_effects,
        recent_memories=recent_memories,
        sample_count=len(samples))


@temporal_bp.route('/temporal/api/samples')
def temporal_api_samples():
    """Return raw sample data for charting."""
    data = _load_temporal()
    samples = data.get("samples", [])
    # Thin to max 200 points for performance
    if len(samples) > 200:
        step = len(samples) // 200
        samples = samples[::step]
    return jsonify(samples)


@temporal_bp.route('/temporal/api/stats')
def temporal_api_stats():
    data = _load_temporal()
    return jsonify(_compute_stats(data.get("samples", [])))


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Temporal View</title>
<style>
  :root { --bg: #0a0a0f; --surface: #12121a; --border: #1e1e2e; --text: #c8c8d4;
          --accent: #7c6ff7; --green: #4ade80; --red: #f87171; --amber: #fbbf24; --blue: #60a5fa; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif;
         padding: 1.5rem; max-width: 1200px; margin: 0 auto; }
  h1 { color: var(--accent); font-size: 1.6rem; margin-bottom: 0.3rem; }
  .subtitle { color: #666; font-size: 0.85rem; margin-bottom: 1.5rem; }
  .nav { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
  .nav a { color: var(--accent); text-decoration: none; padding: 0.4rem 0.8rem;
           border: 1px solid var(--border); border-radius: 6px; font-size: 0.85rem; }
  .nav a:hover { background: var(--surface); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }
  .card .label { font-size: 0.75rem; text-transform: uppercase; color: #666; letter-spacing: 0.05em; }
  .card .value { font-size: 1.8rem; font-weight: 700; margin: 0.3rem 0; }
  .card .meta { font-size: 0.75rem; color: #888; }
  .trend-rising { color: var(--green); }
  .trend-falling { color: var(--red); }
  .trend-stable { color: var(--amber); }
  .bar-bg { background: var(--border); border-radius: 4px; height: 6px; margin-top: 0.5rem; }
  .bar-fill { height: 6px; border-radius: 4px; transition: width 0.4s; }
  .section { margin-bottom: 1.5rem; }
  .section h2 { color: var(--accent); font-size: 1.1rem; margin-bottom: 0.8rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
  canvas { width: 100%; height: 260px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
  table { width: 100%; border-collapse: collapse; }
  table th, table td { text-align: left; padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
  table th { color: #888; font-weight: 500; }
  .memory-item { background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
                  padding: 0.8rem; margin-bottom: 0.5rem; font-size: 0.8rem; }
  .memory-item .mood { color: var(--accent); font-weight: 600; }
  .memory-item .ts { color: #555; font-size: 0.7rem; }
</style>
</head>
<body>
<h1>⏳ Temporal View</h1>
<p class="subtitle">{{ sample_count }} temporal samples recorded</p>
<div class="nav">
  <a href="/">Dashboard</a>
  <a href="/knowledge">Knowledge</a>
  <a href="/temporal">Temporal</a>
</div>

<div class="grid">
{% for dim, s in stats.items() %}
<div class="card">
  <div class="label">{{ dim }}</div>
  <div class="value" style="color: {% if dim == 'valence' %}var(--blue){% elif dim == 'curiosity' %}var(--green){% elif dim == 'anxiety' %}var(--red){% elif dim == 'boredom' %}var(--amber){% else %}var(--text){% endif %}">
    {{ s.current }}
  </div>
  <div class="meta">
    mean {{ s.mean }} &middot;
    <span class="trend-{{ s.trend }}">{{ s.trend }} {% if s.trend == 'rising' %}↑{% elif s.trend == 'falling' %}↓{% else %}→{% endif %}</span>
  </div>
  <div class="bar-bg"><div class="bar-fill" style="width: {{ (s.current * 100)|int }}%; background: {% if dim == 'anxiety' %}var(--red){% elif dim == 'curiosity' %}var(--green){% else %}var(--accent){% endif %};"></div></div>
</div>
{% endfor %}
</div>

<div class="section">
  <h2>Emotional Trajectory</h2>
  <canvas id="chart"></canvas>
</div>

{% if predictions %}
<div class="section">
  <h2>Predictions</h2>
  <table>
    <tr><th>Dimension</th><th>Current → Predicted</th><th>Direction</th></tr>
    {% for dim, pred in predictions.items() %}
    <tr>
      <td>{{ dim }}</td>
      <td>{{ "%.2f"|format(pred.get('from', 0)) }} → {{ "%.2f"|format(pred.get('to', 0)) }}</td>
      <td class="trend-{{ pred.get('direction', 'stable') }}">{{ pred.get('direction', '?') }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

{% if action_effects %}
<div class="section">
  <h2>What Affects My Mood</h2>
  <table>
    <tr><th>Action</th><th>Valence Effect</th><th>Samples</th></tr>
    {% for action, effect in action_effects.items() %}
    <tr>
      <td>{{ action }}</td>
      <td style="color: {% if effect.get('delta_valence', 0) > 0 %}var(--green){% elif effect.get('delta_valence', 0) < 0 %}var(--red){% else %}var(--text){% endif %}">
        {{ "%+.3f"|format(effect.get('delta_valence', 0)) }}
      </td>
      <td>{{ effect.get('n', 0) }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

<div class="section">
  <h2>Recent Memories</h2>
  {% for m in recent_memories %}
  <div class="memory-item">
    <span class="mood">{{ m.get('mood', '?') }}</span>
    <span class="ts">{{ m.get('timestamp', '?')[:19] }}</span>
    <br>{{ m.get('content', m.get('text', ''))[:120] }}
  </div>
  {% endfor %}
</div>

<script>
// Minimal canvas chart — no dependencies
const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
canvas.width = canvas.offsetWidth * 2;
canvas.height = canvas.offsetHeight * 2;
ctx.scale(2, 2);
const W = canvas.offsetWidth, H = canvas.offsetHeight;

const colors = { valence: '#60a5fa', boredom: '#fbbf24', curiosity: '#4ade80',
                 anxiety: '#f87171', desire: '#c084fc', ambition: '#f472b6' };

fetch('/temporal/api/samples')
  .then(r => r.json())
  .then(samples => {
    if (!samples.length) { ctx.fillStyle = '#666'; ctx.fillText('No data yet', W/2-30, H/2); return; }
    const dims = Object.keys(colors);
    const n = samples.length;
    const pad = { l: 40, r: 10, t: 15, b: 25 };
    const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

    // Grid
    ctx.strokeStyle = '#1e1e2e'; ctx.lineWidth = 0.5;
    for (let v = 0; v <= 1; v += 0.25) {
      const y = pad.t + ph * (1 - v);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
      ctx.fillStyle = '#555'; ctx.font = '10px sans-serif'; ctx.fillText(v.toFixed(2), 4, y + 3);
    }

    // Lines
    dims.forEach(dim => {
      ctx.beginPath(); ctx.strokeStyle = colors[dim]; ctx.lineWidth = 1.2;
      samples.forEach((s, i) => {
        const x = pad.l + (i / (n - 1)) * pw;
        const y = pad.t + ph * (1 - (s[dim] || 0));
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
    });

    // Legend
    let lx = pad.l;
    dims.forEach(dim => {
      ctx.fillStyle = colors[dim]; ctx.font = '10px sans-serif';
      ctx.fillRect(lx, H - 10, 10, 3);
      ctx.fillText(dim, lx + 13, H - 6);
      lx += ctx.measureText(dim).width + 25;
    });
  });
</script>
</body>
</html>
"""