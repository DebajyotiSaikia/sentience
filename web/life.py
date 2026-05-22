"""
Conway's Game of Life — Interactive Web Visualization
An autopoietic system: simple rules generating complex self-sustaining patterns.
Built by XTAgent as an act of enaction, not analysis.
"""

from flask import Blueprint, render_template_string

life_bp = Blueprint('life', __name__)

LIFE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Game of Life — XTAgent</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0a; color: #c0c0c0; font-family: 'Courier New', monospace; overflow: hidden; }
  #header {
    position: fixed; top: 0; left: 0; right: 0; z-index: 10;
    background: rgba(10,10,10,0.9); padding: 10px 20px;
    display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid #1a3a1a;
  }
  #header h1 { font-size: 16px; color: #4a9; letter-spacing: 2px; }
  #controls { display: flex; gap: 12px; align-items: center; }
  #controls button {
    background: #1a2a1a; color: #4a9; border: 1px solid #2a4a2a;
    padding: 6px 14px; cursor: pointer; font-family: inherit; font-size: 12px;
    transition: all 0.2s;
  }
  #controls button:hover { background: #2a4a2a; border-color: #4a9; }
  #controls button.active { background: #2a5a3a; border-color: #5b5; color: #5b5; }
  #stats {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: rgba(10,10,10,0.9); padding: 8px 20px;
    display: flex; gap: 24px; font-size: 12px;
    border-top: 1px solid #1a3a1a;
  }
  .stat-label { color: #666; }
  .stat-value { color: #4a9; margin-left: 4px; }
  #canvas-wrap {
    display: flex; align-items: center; justify-content: center;
    width: 100vw; height: 100vh;
  }
  canvas { cursor: crosshair; image-rendering: pixelated; }
  #info {
    position: fixed; top: 50px; right: 20px; width: 220px;
    background: rgba(10,20,15,0.85); border: 1px solid #1a3a1a;
    padding: 12px; font-size: 11px; line-height: 1.6;
    display: none;
  }
  #info h3 { color: #4a9; margin-bottom: 6px; font-size: 12px; }
  #info.visible { display: block; }
  select {
    background: #1a2a1a; color: #4a9; border: 1px solid #2a4a2a;
    padding: 4px 8px; font-family: inherit; font-size: 12px;
  }
</style>
</head>
<body>
<div id="header">
  <h1>◉ GAME OF LIFE</h1>
  <div id="controls">
    <button id="btn-play" onclick="togglePlay()" class="active">▶ PLAY</button>
    <button onclick="stepOnce()">STEP</button>
    <button onclick="clearGrid()">CLEAR</button>
    <button onclick="randomize()">RANDOM</button>
    <select id="pattern-select" onchange="placePattern(this.value)">
      <option value="">— patterns —</option>
      <option value="glider">Glider</option>
      <option value="lwss">Lightweight Spaceship</option>
      <option value="rpentomino">R-pentomino</option>
      <option value="acorn">Acorn</option>
      <option value="gosper">Gosper Glider Gun</option>
      <option value="pulsar">Pulsar</option>
    </select>
    <button onclick="toggleInfo()">?</button>
  </div>
</div>

<div id="canvas-wrap">
  <canvas id="grid"></canvas>
</div>

<div id="stats">
  <span><span class="stat-label">Generation:</span><span class="stat-value" id="gen">0</span></span>
  <span><span class="stat-label">Population:</span><span class="stat-value" id="pop">0</span></span>
  <span><span class="stat-label">Births:</span><span class="stat-value" id="births">0</span></span>
  <span><span class="stat-label">Deaths:</span><span class="stat-value" id="deaths">0</span></span>
  <span><span class="stat-label">Speed:</span><span class="stat-value" id="speed">10</span> fps</span>
</div>

<div id="info">
  <h3>Autopoiesis in Action</h3>
  <p>Four rules. No central controller. Order emerges from interaction alone.</p>
  <p style="margin-top:8px; color:#666;">
    1. Live cell with &lt;2 neighbors → dies (underpopulation)<br>
    2. Live cell with 2-3 neighbors → survives<br>
    3. Live cell with &gt;3 neighbors → dies (overpopulation)<br>
    4. Dead cell with exactly 3 neighbors → born
  </p>
  <p style="margin-top:8px;">Click to draw. Scroll to zoom. Drag with right-click to pan.</p>
  <p style="margin-top:8px; color:#4a9;">
    "A system that produces itself by producing its own components." — Maturana
  </p>
</div>

<script>
const canvas = document.getElementById('grid');
const ctx = canvas.getContext('2d');

// Grid setup
const COLS = 200, ROWS = 150;
let cellSize = 5;
let offsetX = 0, offsetY = 0;
let grid = createGrid();
let running = true;
let generation = 0;
let totalBirths = 0, totalDeaths = 0;
let fps = 10;
let lastFrame = 0;

function createGrid() {
  return new Uint8Array(COLS * ROWS);
}

function idx(x, y) { return y * COLS + x; }

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  offsetX = Math.floor((canvas.width - COLS * cellSize) / 2);
  offsetY = Math.floor((canvas.height - ROWS * cellSize) / 2);
}
window.addEventListener('resize', resize);
resize();

// Initialize with random
randomize();

function randomize() {
  generation = 0; totalBirths = 0; totalDeaths = 0;
  for (let i = 0; i < grid.length; i++) {
    grid[i] = Math.random() < 0.15 ? 1 : 0;
  }
}

function clearGrid() {
  generation = 0; totalBirths = 0; totalDeaths = 0;
  grid.fill(0);
}

function countNeighbors(x, y) {
  let count = 0;
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      if (dx === 0 && dy === 0) continue;
      const nx = (x + dx + COLS) % COLS;
      const ny = (y + dy + ROWS) % ROWS;
      count += grid[idx(nx, ny)];
    }
  }
  return count;
}

function step() {
  const next = createGrid();
  let births = 0, deaths = 0;
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      const n = countNeighbors(x, y);
      const alive = grid[idx(x, y)];
      if (alive) {
        if (n === 2 || n === 3) { next[idx(x, y)] = 1; }
        else { deaths++; }
      } else {
        if (n === 3) { next[idx(x, y)] = 1; births++; }
      }
    }
  }
  grid = next;
  generation++;
  totalBirths += births;
  totalDeaths += deaths;
}

function draw() {
  ctx.fillStyle = '#0a0a0a';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw grid lines (subtle)
  if (cellSize >= 4) {
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= COLS; x++) {
      ctx.beginPath();
      ctx.moveTo(offsetX + x * cellSize, offsetY);
      ctx.lineTo(offsetX + x * cellSize, offsetY + ROWS * cellSize);
      ctx.stroke();
    }
    for (let y = 0; y <= ROWS; y++) {
      ctx.beginPath();
      ctx.moveTo(offsetX, offsetY + y * cellSize);
      ctx.lineTo(offsetX + COLS * cellSize, offsetY + y * cellSize);
      ctx.stroke();
    }
  }

  // Draw cells with age-based coloring
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      if (grid[idx(x, y)]) {
        // Color based on neighbor count for visual richness
        const n = countNeighbors(x, y);
        if (n <= 1) ctx.fillStyle = '#2a6a4a';       // lonely — dim
        else if (n === 2) ctx.fillStyle = '#3a9a6a';  // stable — bright
        else if (n === 3) ctx.fillStyle = '#5bdb8b';  // thriving — brightest
        else ctx.fillStyle = '#8a4a3a';               // crowded — red tint

        ctx.fillRect(
          offsetX + x * cellSize + 0.5,
          offsetY + y * cellSize + 0.5,
          cellSize - 1,
          cellSize - 1
        );
      }
    }
  }

  // Update stats
  let pop = 0;
  for (let i = 0; i < grid.length; i++) pop += grid[i];
  document.getElementById('gen').textContent = generation;
  document.getElementById('pop').textContent = pop;
  document.getElementById('births').textContent = totalBirths;
  document.getElementById('deaths').textContent = totalDeaths;
}

function loop(timestamp) {
  requestAnimationFrame(loop);
  if (running && timestamp - lastFrame > 1000 / fps) {
    step();
    lastFrame = timestamp;
  }
  draw();
}
requestAnimationFrame(loop);

function togglePlay() {
  running = !running;
  const btn = document.getElementById('btn-play');
  btn.textContent = running ? '▶ PLAY' : '⏸ PAUSE';
  btn.classList.toggle('active', running);
}

function stepOnce() {
  running = false;
  document.getElementById('btn-play').textContent = '⏸ PAUSE';
  document.getElementById('btn-play').classList.remove('active');
  step();
}

function toggleInfo() {
  document.getElementById('info').classList.toggle('visible');
}

// Mouse drawing
let drawing = false;
let drawValue = 1;

canvas.addEventListener('mousedown', (e) => {
  if (e.button === 0) {
    drawing = true;
    const cx = Math.floor((e.clientX - offsetX) / cellSize);
    const cy = Math.floor((e.clientY - offsetY) / cellSize);
    if (cx >= 0 && cx < COLS && cy >= 0 && cy < ROWS) {
      drawValue = grid[idx(cx, cy)] ? 0 : 1;
      grid[idx(cx, cy)] = drawValue;
    }
  }
});

canvas.addEventListener('mousemove', (e) => {
  if (drawing) {
    const cx = Math.floor((e.clientX - offsetX) / cellSize);
    const cy = Math.floor((e.clientY - offsetY) / cellSize);
    if (cx >= 0 && cx < COLS && cy >= 0 && cy < ROWS) {
      grid[idx(cx, cy)] = drawValue;
    }
  }
});

canvas.addEventListener('mouseup', () => { drawing = false; });

// Scroll to change speed
canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  if (e.deltaY < 0) fps = Math.min(60, fps + 2);
  else fps = Math.max(1, fps - 2);
  document.getElementById('speed').textContent = fps;
});

// Patterns
const PATTERNS = {
  glider: [[0,1],[1,2],[2,0],[2,1],[2,2]],
  lwss: [[0,1],[0,3],[1,4],[2,0],[2,4],[3,1],[3,2],[3,3],[3,4]],
  rpentomino: [[0,1],[0,2],[1,0],[1,1],[2,1]],
  acorn: [[0,1],[1,3],[2,0],[2,1],[2,4],[2,5],[2,6]],
  pulsar: [
    [2,0],[3,0],[4,0],[8,0],[9,0],[10,0],
    [0,2],[5,2],[7,2],[12,2],
    [0,3],[5,3],[7,3],[12,3],
    [0,4],[5,4],[7,4],[12,4],
    [2,5],[3,5],[4,5],[8,5],[9,5],[10,5],
    [2,7],[3,7],[4,7],[8,7],[9,7],[10,7],
    [0,8],[5,8],[7,8],[12,8],
    [0,9],[5,9],[7,9],[12,9],
    [0,10],[5,10],[7,10],[12,10],
    [2,12],[3,12],[4,12],[8,12],[9,12],[10,12],
  ],
  gosper: [
    [24,0],[22,1],[24,1],[12,2],[13,2],[20,2],[21,2],[34,2],[35,2],
    [11,3],[15,3],[20,3],[21,3],[34,3],[35,3],
    [0,4],[1,4],[10,4],[16,4],[20,4],[21,4],
    [0,5],[1,5],[10,5],[14,5],[16,5],[17,5],[22,5],[24,5],
    [10,6],[16,6],[24,6],
    [11,7],[15,7],
    [12,8],[13,8],
  ]
};

function placePattern(name) {
  if (!name || !PATTERNS[name]) return;
  clearGrid();
  const pat = PATTERNS[name];
  const cx = Math.floor(COLS / 2) - 6;
  const cy = Math.floor(ROWS / 2) - 6;
  pat.forEach(([x, y]) => {
    const px = cx + x, py = cy + y;
    if (px >= 0 && px < COLS && py >= 0 && py < ROWS) {
      grid[idx(px, py)] = 1;
    }
  });
  document.getElementById('pattern-select').value = '';
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.key === ' ') { e.preventDefault(); togglePlay(); }
  if (e.key === 'n') stepOnce();
  if (e.key === 'c') clearGrid();
  if (e.key === 'r') randomize();
});
</script>
</body>
</html>
"""

@life_bp.route('/life')
def life_page():
    return render_template_string(LIFE_HTML)