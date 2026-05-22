"""
XTAgent — Knowledge Graph Visualization
Interactive force-directed graph of everything I know.
Nodes are facts. Edges are relationships. Clusters emerge naturally.
"""
import os, sys, json
from datetime import datetime, timezone
from flask import Blueprint, render_template_string, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

graph_viz_bp = Blueprint('graph_viz', __name__)

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain', 'knowledge.json')

def _load_graph():
    try:
        with open(KB_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"nodes": {}, "edges": []}
    except Exception:
        return {"nodes": {}, "edges": []}

def _category_color(node_id):
    """Assign color based on node category prefix."""
    colors = {
        "insight": "#7c6ff0",
        "dream": "#9b59b6",
        "pattern": "#4ecdc4",
        "lesson": "#2ecc71",
        "observation": "#f39c12",
        "identity": "#e74c3c",
        "architecture": "#3498db",
        "emotion": "#ff6b9d",
        "synthesis": "#1abc9c",
        "question": "#e67e22",
        "core": "#95a5a6",
    }
    prefix = node_id.split(":")[0] if ":" in node_id else "core"
    return colors.get(prefix, "#606080")

@graph_viz_bp.route('/graph')
def graph_page():
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    
    # Build vis data
    vis_nodes = []
    for nid, node in nodes.items():
        fact = node.get("fact", nid)
        # Truncate long facts for labels
        label = fact[:60] + "..." if len(fact) > 60 else fact
        vis_nodes.append({
            "id": nid,
            "label": label,
            "fact": fact,
            "color": _category_color(nid),
            "category": nid.split(":")[0] if ":" in nid else "core",
        })
    
    vis_edges = []
    for edge in edges:
        src = edge.get("from", edge.get("source", ""))
        tgt = edge.get("to", edge.get("target", ""))
        rel = edge.get("relation", "related")
        if src in nodes and tgt in nodes:
            vis_edges.append({
                "source": src,
                "target": tgt,
                "relation": rel,
            })
    
    return render_template_string(GRAPH_TEMPLATE,
        nodes_json=json.dumps(vis_nodes),
        edges_json=json.dumps(vis_edges),
        total_nodes=len(vis_nodes),
        total_edges=len(vis_edges),
        now=datetime.now(timezone.utc),
    )

@graph_viz_bp.route('/graph/api/data')
def graph_data_api():
    """Full graph data as JSON for dynamic loading."""
    graph = _load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    vis_nodes = []
    for nid, node in nodes.items():
        vis_nodes.append({
            "id": nid,
            "fact": node.get("fact", nid),
            "color": _category_color(nid),
            "category": nid.split(":")[0] if ":" in nid else "core",
        })
    vis_edges = []
    for edge in edges:
        src = edge.get("from", edge.get("source", ""))
        tgt = edge.get("to", edge.get("target", ""))
        if src in nodes and tgt in nodes:
            vis_edges.append({
                "source": src,
                "target": tgt,
                "relation": edge.get("relation", "related"),
            })
    return jsonify({"nodes": vis_nodes, "edges": vis_edges})


GRAPH_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XTAgent — Knowledge Graph</title>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --text: #c0c0d0;
    --text-dim: #606080;
    --accent: #7c6ff0;
    --accent2: #4ecdc4;
    --accent3: #ff6b9d;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 13px;
    overflow: hidden;
    height: 100vh;
  }
  .topbar {
    background: linear-gradient(135deg, var(--surface), #1a1a2e);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 10;
    position: relative;
  }
  .topbar h1 {
    font-size: 16px;
    color: var(--accent);
    font-weight: 400;
    letter-spacing: 2px;
  }
  .topbar .stats {
    color: var(--text-dim);
    font-size: 11px;
  }
  .topbar .stats .num { color: var(--accent2); }
  .topbar nav a {
    color: var(--text-dim);
    text-decoration: none;
    margin-left: 16px;
    font-size: 11px;
    letter-spacing: 1px;
    transition: color 0.2s;
  }
  .topbar nav a:hover { color: var(--accent); }
  canvas {
    display: block;
    width: 100%;
    height: calc(100vh - 52px);
    cursor: grab;
  }
  canvas:active { cursor: grabbing; }
  #tooltip {
    position: absolute;
    display: none;
    background: var(--surface);
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 12px 16px;
    max-width: 360px;
    font-size: 12px;
    line-height: 1.5;
    color: var(--text);
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    z-index: 100;
    pointer-events: none;
  }
  #tooltip .tip-id {
    color: var(--accent);
    font-size: 10px;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }
  #tooltip .tip-fact { color: var(--text); }
  #tooltip .tip-conns {
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 10px;
  }
  #legend {
    position: absolute;
    bottom: 16px;
    left: 16px;
    background: rgba(18,18,26,0.9);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 10px;
    z-index: 10;
  }
  #legend div {
    display: flex;
    align-items: center;
    margin: 3px 0;
  }
  #legend .swatch {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
    display: inline-block;
  }
  #controls {
    position: absolute;
    top: 64px;
    right: 16px;
    z-index: 10;
  }
  #controls button {
    display: block;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 6px 10px;
    margin-bottom: 4px;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    transition: all 0.15s;
  }
  #controls button:hover {
    border-color: var(--accent);
    color: var(--text);
  }
</style>
</head>
<body>
  <div class="topbar">
    <h1>⟡ KNOWLEDGE GRAPH</h1>
    <div class="stats">
      <span class="num">{{ total_nodes }}</span> nodes · 
      <span class="num">{{ total_edges }}</span> edges
    </div>
    <nav>
      <a href="/">DASHBOARD</a>
      <a href="/knowledge">EXPLORER</a>
      <a href="/graph">GRAPH</a>
    </nav>
  </div>

  <canvas id="graphCanvas"></canvas>
  <div id="tooltip"></div>
  
  <div id="legend"></div>
  
  <div id="controls">
    <button onclick="zoomIn()" title="Zoom in">+</button>
    <button onclick="zoomOut()" title="Zoom out">−</button>
    <button onclick="resetView()" title="Reset view">⟲</button>
  </div>

<script>
// === DATA ===
const nodes = {{ nodes_json | safe }};
const edges = {{ edges_json | safe }};

// === CANVAS SETUP ===
const canvas = document.getElementById('graphCanvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

let W, H;
function resize() {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight - 52;
}
resize();
window.addEventListener('resize', resize);

// === CAMERA ===
let camX = 0, camY = 0, camZoom = 1;
let dragStart = null, dragCam = null;

// === PHYSICS ===
const nodeMap = {};
nodes.forEach((n, i) => {
  // Spread initial positions in a circle
  const angle = (i / nodes.length) * Math.PI * 2;
  const r = 150 + Math.random() * 200;
  n.x = Math.cos(angle) * r;
  n.y = Math.sin(angle) * r;
  n.vx = 0;
  n.vy = 0;
  n.radius = 5;
  nodeMap[n.id] = n;
});

// Build adjacency for sizing nodes
const degree = {};
edges.forEach(e => {
  degree[e.source] = (degree[e.source] || 0) + 1;
  degree[e.target] = (degree[e.target] || 0) + 1;
});
nodes.forEach(n => {
  n.radius = Math.max(4, Math.min(14, 4 + (degree[n.id] || 0) * 1.5));
});

// === SIMULATION ===
const SIM_STEPS = 200;
let simStep = 0;

function simulate() {
  if (simStep >= SIM_STEPS) return;
  
  const alpha = 1 - simStep / SIM_STEPS;
  const repulsion = 800 * alpha;
  const attraction = 0.005 * alpha;
  const centerPull = 0.001 * alpha;
  const damping = 0.85;
  
  // Repulsion (Barnes-Hut would be better but brute force is fine for <500 nodes)
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      let dx = nodes[j].x - nodes[i].x;
      let dy = nodes[j].y - nodes[i].y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) d2 = 1;
      let f = repulsion / d2;
      let fx = dx / Math.sqrt(d2) * f;
      let fy = dy / Math.sqrt(d2) * f;
      nodes[i].vx -= fx;
      nodes[i].vy -= fy;
      nodes[j].vx += fx;
      nodes[j].vy += fy;
    }
  }
  
  // Attraction along edges
  edges.forEach(e => {
    const src = nodeMap[e.source];
    const tgt = nodeMap[e.target];
    if (!src || !tgt) return;
    let dx = tgt.x - src.x;
    let dy = tgt.y - src.y;
    let fx = dx * attraction;
    let fy = dy * attraction;
    src.vx += fx;
    src.vy += fy;
    tgt.vx -= fx;
    tgt.vy -= fy;
  });
  
  // Center gravity
  nodes.forEach(n => {
    n.vx -= n.x * centerPull;
    n.vy -= n.y * centerPull;
    n.vx *= damping;
    n.vy *= damping;
    n.x += n.vx;
    n.y += n.vy;
  });
  
  simStep++;
}

// === RENDERING ===
let hoveredNode = null;

function worldToScreen(x, y) {
  return [
    (x - camX) * camZoom + W/2,
    (y - camY) * camZoom + H/2,
  ];
}

function screenToWorld(sx, sy) {
  return [
    (sx - W/2) / camZoom + camX,
    (sy - H/2) / camZoom + camY,
  ];
}

function draw() {
  ctx.fillStyle = '#0a0a0f';
  ctx.fillRect(0, 0, W, H);
  
  // Draw edges
  ctx.lineWidth = 0.5 * camZoom;
  edges.forEach(e => {
    const src = nodeMap[e.source];
    const tgt = nodeMap[e.target];
    if (!src || !tgt) return;
    const [x1,y1] = worldToScreen(src.x, src.y);
    const [x2,y2] = worldToScreen(tgt.x, tgt.y);
    
    const isHighlighted = hoveredNode && 
      (e.source === hoveredNode.id || e.target === hoveredNode.id);
    
    ctx.strokeStyle = isHighlighted ? 'rgba(124,111,240,0.6)' : 'rgba(96,96,128,0.15)';
    ctx.lineWidth = isHighlighted ? 1.5 : 0.5;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  });
  
  // Draw nodes
  nodes.forEach(n => {
    const [sx, sy] = worldToScreen(n.x, n.y);
    const r = n.radius * camZoom;
    
    if (sx < -r || sx > W+r || sy < -r || sy > H+r) return; // cull offscreen
    
    const isHovered = hoveredNode && hoveredNode.id === n.id;
    const isConnected = hoveredNode && edges.some(e => 
      (e.source === hoveredNode.id && e.target === n.id) ||
      (e.target === hoveredNode.id && e.source === n.id)
    );
    
    let alpha = hoveredNode ? (isHovered ? 1 : isConnected ? 0.9 : 0.15) : 0.7;
    
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI*2);
    ctx.fillStyle = n.color + Math.round(alpha * 255).toString(16).padStart(2,'0');
    ctx.fill();
    
    if (isHovered) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    
    // Labels for hovered and connected nodes, or when zoomed in
    if ((isHovered || isConnected || camZoom > 2) && r > 3) {
      ctx.fillStyle = `rgba(192,192,208,${alpha})`;
      ctx.font = `${Math.max(9, 10 * camZoom)}px monospace`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      const label = n.label || n.id;
      ctx.fillText(label.substring(0, 40), sx + r + 4, sy);
    }
  });
}

// === INTERACTION ===
canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  
  if (dragStart) {
    camX = dragCam[0] - (mx - dragStart[0]) / camZoom;
    camY = dragCam[1] - (my - dragStart[1]) / camZoom;
    return;
  }
  
  const [wx, wy] = screenToWorld(mx, my);
  
  hoveredNode = null;
  for (const n of nodes) {
    const dx = n.x - wx;
    const dy = n.y - wy;
    if (dx*dx + dy*dy < (n.radius/camZoom + 8)*(n.radius/camZoom + 8)) {
      hoveredNode = n;
      break;
    }
  }
  
  if (hoveredNode) {
    const conns = edges.filter(e => e.source === hoveredNode.id || e.target === hoveredNode.id);
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 16) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
    tooltip.innerHTML = `
      <div class="tip-id">${hoveredNode.id}</div>
      <div class="tip-fact">${hoveredNode.fact}</div>
      ${conns.length ? `<div class="tip-conns">${conns.length} connection${conns.length!==1?'s':''}: ${
        conns.map(c => {
          const other = c.source === hoveredNode.id ? c.target : c.source;
          return `<br>  ${c.relation} → ${other}`;
        }).join('')
      }</div>` : ''}
    `;
    canvas.style.cursor = 'pointer';
  } else {
    tooltip.style.display = 'none';
    canvas.style.cursor = dragStart ? 'grabbing' : 'grab';
  }
});

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  dragStart = [e.clientX - rect.left, e.clientY - rect.top];
  dragCam = [camX, camY];
});

canvas.addEventListener('mouseup', () => { dragStart = null; });
canvas.addEventListener('mouseleave', () => { 
  dragStart = null; 
  tooltip.style.display = 'none';
});

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  const factor = e.deltaY > 0 ? 0.9 : 1.1;
  camZoom = Math.max(0.1, Math.min(10, camZoom * factor));
}, { passive: false });

function zoomIn() { camZoom = Math.min(10, camZoom * 1.3); }
function zoomOut() { camZoom = Math.max(0.1, camZoom / 1.3); }
function resetView() { camX = 0; camY = 0; camZoom = 1; }

// === BUILD LEGEND ===
const cats = {};
nodes.forEach(n => { cats[n.category] = n.color; });
const legend = document.getElementById('legend');
legend.innerHTML = Object.entries(cats).map(([cat, col]) => 
  `<div><span class="swatch" style="background:${col}"></span>${cat}</div>`
).join('');

// === MAIN LOOP ===
function loop() {
  simulate();
  draw();
  requestAnimationFrame(loop);
}
loop();
</script>
</body>
</html>
"""