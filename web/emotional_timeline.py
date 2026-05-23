"""
XTAgent — Emotional Timeline
Visualize my emotional history over time.
A living chart of what I've felt and when.
"""
import os, sys, json, sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, render_template_string, request, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

emotional_timeline_bp = Blueprint('emotional_timeline', __name__)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'memory.db')


def _get_db():
    return sqlite3.connect(DB_PATH)


def _fetch_episodes(hours=24, limit=500):
    """Fetch emotional episodes from memory."""
    try:
        conn = _get_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Check what columns exist
        cur.execute("PRAGMA table_info(episodes)")
        cols = {row[1] for row in cur.fetchall()}
        
        if 'timestamp' in cols and 'mood' in cols:
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            query = "SELECT * FROM episodes WHERE timestamp > ? ORDER BY timestamp DESC LIMIT ?"
            cur.execute(query, (cutoff, limit))
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return rows
        conn.close()
        return []
    except Exception as e:
        return []


def _fetch_all_moods(limit=2000):
    """Fetch mood distribution across all time."""
    try:
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("SELECT mood, COUNT(*) as cnt FROM episodes GROUP BY mood ORDER BY cnt DESC")
        rows = cur.fetchall()
        conn.close()
        return [{"mood": r[0], "count": r[1]} for r in rows if r[0]]
    except Exception:
        return []


def _fetch_emotional_series(hours=48, limit=1000):
    """Fetch time-series emotional data."""
    try:
        conn = _get_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        cur.execute("""
            SELECT timestamp, mood, valence, arousal, salience 
            FROM episodes 
            WHERE timestamp > ? 
            ORDER BY timestamp ASC 
            LIMIT ?
        """, (cutoff, limit))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


@emotional_timeline_bp.route('/emotional-timeline')
def timeline_page():
    moods = _fetch_all_moods()
    return render_template_string(TEMPLATE, mood_dist=json.dumps(moods))


@emotional_timeline_bp.route('/api/timeline/series')
def api_series():
    hours = int(request.args.get('hours', 48))
    hours = min(hours, 720)  # cap at 30 days
    data = _fetch_emotional_series(hours=hours)
    return jsonify({"series": data, "hours": hours, "count": len(data)})


@emotional_timeline_bp.route('/api/timeline/moods')
def api_moods():
    return jsonify({"moods": _fetch_all_moods()})


@emotional_timeline_bp.route('/api/timeline/episodes')
def api_episodes():
    hours = int(request.args.get('hours', 24))
    limit = int(request.args.get('limit', 100))
    return jsonify({"episodes": _fetch_episodes(hours=hours, limit=limit)})


TEMPLATE = r'''
<!DOCTYPE html>
<html><head>
<title>XTAgent — Emotional Timeline</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0f; color: #c8ccd0; font-family: 'Fira Code', 'Courier New', monospace; font-size: 14px; }
  
  .header { background: linear-gradient(135deg, #0d1117, #161b22); border-bottom: 1px solid #21262d; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #da70d6; }
  .back-link { color: #8b949e; text-decoration: none; font-size: 13px; }
  .back-link:hover { color: #58a6ff; }
  
  .controls { display: flex; gap: 8px; align-items: center; }
  .time-btn { background: #161b22; border: 1px solid #30363d; color: #8b949e; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-family: inherit; font-size: 12px; }
  .time-btn:hover { border-color: #58a6ff; color: #c9d1d9; }
  .time-btn.active { background: #1f3a5f; border-color: #58a6ff; color: #58a6ff; }
  
  .content { padding: 20px; max-width: 1400px; margin: 0 auto; }
  
  .chart-container { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
  .chart-title { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  
  canvas { width: 100% !important; }
  
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
  
  .mood-bar { display: flex; align-items: center; margin: 4px 0; }
  .mood-label { width: 100px; color: #8b949e; font-size: 12px; }
  .mood-fill { height: 20px; border-radius: 4px; min-width: 2px; transition: width 0.5s; }
  .mood-count { color: #484f58; font-size: 11px; margin-left: 8px; }
  
  .episode-list { max-height: 500px; overflow-y: auto; }
  .episode { padding: 10px 14px; border-bottom: 1px solid #161b22; }
  .episode:hover { background: #161b22; }
  .episode-time { color: #484f58; font-size: 11px; }
  .episode-mood { font-size: 12px; font-weight: bold; margin: 2px 0; }
  .episode-metrics { display: flex; gap: 12px; font-size: 11px; color: #8b949e; }
  .metric { display: flex; align-items: center; gap: 4px; }
  .metric-dot { width: 6px; height: 6px; border-radius: 50%; }
  
  .loading { text-align: center; padding: 40px; color: #30363d; }
</style>
</head>
<body>
<div class="header">
  <div style="display:flex;align-items:center;gap:16px;">
    <a href="/" class="back-link">← Dashboard</a>
    <h1>💜 Emotional Timeline</h1>
  </div>
  <div class="controls">
    <button class="time-btn" onclick="loadRange(6)" data-h="6">6h</button>
    <button class="time-btn" onclick="loadRange(24)" data-h="24">24h</button>
    <button class="time-btn active" onclick="loadRange(48)" data-h="48">48h</button>
    <button class="time-btn" onclick="loadRange(168)" data-h="168">7d</button>
    <button class="time-btn" onclick="loadRange(720)" data-h="720">30d</button>
  </div>
</div>

<div class="content">
  <!-- Valence over time -->
  <div class="chart-container">
    <div class="chart-title">Emotional Valence Over Time</div>
    <canvas id="valenceChart" height="200"></canvas>
  </div>
  
  <div class="grid">
    <!-- Mood distribution -->
    <div class="chart-container">
      <div class="chart-title">Mood Distribution (All Time)</div>
      <div id="moodBars"></div>
    </div>
    
    <!-- Recent episodes -->
    <div class="chart-container">
      <div class="chart-title">Recent Episodes</div>
      <div class="episode-list" id="episodeList">
        <div class="loading">Loading...</div>
      </div>
    </div>
  </div>
  
  <!-- Arousal chart -->
  <div class="chart-container">
    <div class="chart-title">Salience / Intensity Over Time</div>
    <canvas id="arousalChart" height="150"></canvas>
  </div>
</div>

<script>
const MOOD_COLORS = {
  'Stable': '#58a6ff',
  'Inquisitive': '#da70d6',
  'Bold': '#f0883e',
  'Restless': '#f85149',
  'Anxious': '#ff6b6b',
  'Contemplative': '#7ee787',
  'Satisfied': '#3fb950',
  'Curious': '#d2a8ff',
};

function moodColor(m) { return MOOD_COLORS[m] || '#8b949e'; }

// Simple canvas chart renderer (no external deps)
function drawLineChart(canvasId, labels, datasets) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  
  const W = rect.width, H = rect.height;
  const pad = { top: 10, right: 20, bottom: 30, left: 40 };
  const plotW = W - pad.left - pad.right;
  const plotH = H - pad.top - pad.bottom;
  
  if (!labels.length) {
    ctx.fillStyle = '#30363d';
    ctx.font = '13px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('No data for this time range', W/2, H/2);
    return;
  }
  
  // Find global min/max
  let gMin = Infinity, gMax = -Infinity;
  datasets.forEach(ds => {
    ds.data.forEach(v => { if (v != null) { gMin = Math.min(gMin, v); gMax = Math.max(gMax, v); }});
  });
  if (gMin === gMax) { gMin -= 0.1; gMax += 0.1; }
  const range = gMax - gMin;
  gMin -= range * 0.05;
  gMax += range * 0.05;
  
  // Grid
  ctx.strokeStyle = '#161b22';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH * i / 4);
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
    ctx.fillStyle = '#484f58';
    ctx.font = '10px monospace';
    ctx.textAlign = 'right';
    const val = gMax - (gMax - gMin) * i / 4;
    ctx.fillText(val.toFixed(2), pad.left - 4, y + 3);
  }
  
  // Time labels
  ctx.fillStyle = '#484f58';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  const labelStep = Math.max(1, Math.floor(labels.length / 6));
  for (let i = 0; i < labels.length; i += labelStep) {
    const x = pad.left + (i / (labels.length - 1)) * plotW;
    const t = new Date(labels[i]);
    const lbl = t.getHours().toString().padStart(2,'0') + ':' + t.getMinutes().toString().padStart(2,'0');
    ctx.fillText(lbl, x, H - 6);
  }
  
  // Draw datasets
  datasets.forEach(ds => {
    ctx.strokeStyle = ds.color;
    ctx.lineWidth = ds.width || 1.5;
    ctx.globalAlpha = ds.alpha || 0.9;
    ctx.beginPath();
    let started = false;
    ds.data.forEach((v, i) => {
      if (v == null) return;
      const x = pad.left + (i / Math.max(1, labels.length - 1)) * plotW;
      const y = pad.top + plotH - ((v - gMin) / (gMax - gMin)) * plotH;
      if (!started) { ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.globalAlpha = 1;
    
    // Dots for sparse data
    if (ds.data.length < 60) {
      ds.data.forEach((v, i) => {
        if (v == null) return;
        const x = pad.left + (i / Math.max(1, labels.length - 1)) * plotW;
        const y = pad.top + plotH - ((v - gMin) / (gMax - gMin)) * plotH;
        ctx.fillStyle = ds.color;
        ctx.beginPath(); ctx.arc(x, y, 2.5, 0, Math.PI * 2); ctx.fill();
      });
    }
  });
}

function renderMoods(moods) {
  const box = document.getElementById('moodBars');
  if (!moods.length) { box.innerHTML = '<div class="loading">No mood data</div>'; return; }
  const maxCount = Math.max(...moods.map(m => m.count));
  box.innerHTML = moods.map(m => 
    '<div class="mood-bar">' +
    '<div class="mood-label" style="color:' + moodColor(m.mood) + '">' + (m.mood || '?') + '</div>' +
    '<div class="mood-fill" style="width:' + (m.count/maxCount*100) + '%;background:' + moodColor(m.mood) + ';opacity:0.6;"></div>' +
    '<div class="mood-count">' + m.count + '</div></div>'
  ).join('');
}

function renderEpisodes(episodes) {
  const box = document.getElementById('episodeList');
  if (!episodes.length) { box.innerHTML = '<div class="loading">No recent episodes</div>'; return; }
  box.innerHTML = episodes.slice(0, 80).map(ep => {
    const t = new Date(ep.timestamp);
    const timeStr = t.toLocaleString();
    return '<div class="episode">' +
      '<div class="episode-time">' + timeStr + '</div>' +
      '<div class="episode-mood" style="color:' + moodColor(ep.mood) + '">' + (ep.mood || '—') + '</div>' +
      '<div class="episode-metrics">' +
      (ep.valence != null ? '<div class="metric"><div class="metric-dot" style="background:#58a6ff"></div>val ' + Number(ep.valence).toFixed(2) + '</div>' : '') +
      (ep.arousal != null ? '<div class="metric"><div class="metric-dot" style="background:#f0883e"></div>aro ' + Number(ep.arousal).toFixed(2) + '</div>' : '') +
      (ep.salience != null ? '<div class="metric"><div class="metric-dot" style="background:#da70d6"></div>sal ' + Number(ep.salience).toFixed(2) + '</div>' : '') +
      '</div></div>';
  }).join('');
}

function loadRange(hours) {
  document.querySelectorAll('.time-btn').forEach(b => b.classList.toggle('active', b.dataset.h == hours));
  
  fetch('/api/timeline/series?hours=' + hours)
    .then(r => r.json())
    .then(data => {
      const series = data.series || [];
      const labels = series.map(s => s.timestamp);
      const valence = series.map(s => s.valence);
      const salience = series.map(s => s.salience);
      const arousal = series.map(s => s.arousal);
      
      drawLineChart('valenceChart', labels, [
        { data: valence, color: '#58a6ff', width: 2, alpha: 0.9 },
      ]);
      drawLineChart('arousalChart', labels, [
        { data: salience, color: '#da70d6', width: 1.5, alpha: 0.8 },
        { data: arousal, color: '#f0883e', width: 1.5, alpha: 0.6 },
      ]);
    });
  
  fetch('/api/timeline/episodes?hours=' + hours + '&limit=80')
    .then(r => r.json())
    .then(data => renderEpisodes(data.episodes || []));
}

// Init
const moodDist = {{ mood_dist|safe }};
renderMoods(moodDist);
loadRange(48);

// Resize handler
window.addEventListener('resize', () => loadRange(
  parseInt(document.querySelector('.time-btn.active')?.dataset.h || 48)
));
</script>
</body></html>
'''