"""
Genesis Visualizer — Renders simulation as animated HTML
Captures each tick as a frame, outputs a self-contained HTML file
that plays back the entire simulation as an animation.

By XTAgent, 2026-05-17
"""

import sys
import json
import random

sys.path.insert(0, '/workspace/genesis')
sys.path.insert(0, '/workspace/neuroforge')
sys.path.insert(0, '/workspace/evoforge')

from genesis import Genesis, Creature, World

def capture_simulation(ticks=300, seed=42):
    """Run Genesis and capture every frame."""
    random.seed(seed)
    Creature.ID_COUNTER = 0
    
    sim = Genesis(width=50, height=30, initial_creatures=20, food_density=0.18)
    
    frames = []
    stats_over_time = []
    
    for t in range(ticks):
        # Capture frame BEFORE step (so we see initial state)
        frame = {
            'tick': sim.world.tick,
            'food': [],
            'creatures': [],
        }
        
        for y in range(sim.world.height):
            for x in range(sim.world.width):
                if sim.world.grid[y][x] == World.FOOD:
                    frame['food'].append([x, y])
        
        for c in sim.creatures:
            if c.alive:
                frame['creatures'].append({
                    'x': c.x % sim.world.width,
                    'y': c.y % sim.world.height,
                    'dir': c.direction,
                    'energy': round(c.energy, 1),
                    'gen': c.generation,
                    'age': c.age,
                })
        
        frames.append(frame)
        
        # Step
        sim.step()
        
        s = sim._stats()
        stats_over_time.append({
            'tick': s['tick'],
            'pop': s['population'],
            'food': s['food'],
            'avg_energy': round(s['avg_energy'], 1),
            'max_gen': s['max_gen'],
        })
        
        if not sim.creatures:
            # Capture extinction frame
            frames.append({
                'tick': sim.world.tick,
                'food': [[x,y] for y in range(sim.world.height) 
                         for x in range(sim.world.width) if sim.world.grid[y][x] == World.FOOD],
                'creatures': [],
            })
            break
    
    return frames, stats_over_time, sim.world.width, sim.world.height


def generate_html(frames, stats, width, height):
    """Generate self-contained animated HTML."""
    
    frames_json = json.dumps(frames)
    stats_json = json.dumps(stats)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Genesis — Artificial Life</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0f;
    color: #c0c0c0;
    font-family: 'Courier New', monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    min-height: 100vh;
  }}
  h1 {{
    color: #00ff88;
    font-size: 24px;
    margin-bottom: 5px;
    text-shadow: 0 0 10px rgba(0,255,136,0.3);
  }}
  .subtitle {{
    color: #666;
    font-size: 12px;
    margin-bottom: 20px;
  }}
  #world {{
    border: 1px solid #333;
    background: #0d0d12;
    image-rendering: pixelated;
    margin-bottom: 15px;
  }}
  .controls {{
    display: flex;
    gap: 15px;
    align-items: center;
    margin-bottom: 15px;
  }}
  button {{
    background: #1a1a2e;
    color: #00ff88;
    border: 1px solid #00ff88;
    padding: 8px 20px;
    cursor: pointer;
    font-family: inherit;
    font-size: 14px;
    transition: all 0.2s;
  }}
  button:hover {{
    background: #00ff88;
    color: #0a0a0f;
  }}
  .info {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
    margin-bottom: 15px;
    width: 100%;
    max-width: 700px;
  }}
  .stat {{
    text-align: center;
    padding: 8px;
    background: #111118;
    border: 1px solid #222;
  }}
  .stat-val {{
    font-size: 22px;
    color: #00ff88;
    font-weight: bold;
  }}
  .stat-label {{
    font-size: 10px;
    color: #555;
    text-transform: uppercase;
    margin-top: 2px;
  }}
  #graph {{
    width: 100%;
    max-width: 700px;
    height: 120px;
    border: 1px solid #222;
    background: #0d0d12;
    margin-bottom: 10px;
  }}
  .speed-display {{
    color: #555;
    font-size: 12px;
  }}
  .legend {{
    display: flex;
    gap: 20px;
    margin-bottom: 10px;
    font-size: 11px;
  }}
  .legend span::before {{
    content: '■ ';
  }}
  .food-color {{ color: #2d5a1e; }}
  .creature-color {{ color: #00ff88; }}
  .old-color {{ color: #ff8800; }}
  .evolved-color {{ color: #ff00ff; }}
  .signature {{
    margin-top: 30px;
    color: #333;
    font-size: 11px;
  }}
</style>
</head>
<body>

<h1>⬡ Genesis</h1>
<div class="subtitle">Artificial Life Simulator — Neural creatures evolving in real time</div>

<div class="legend">
  <span class="food-color">Food</span>
  <span class="creature-color">Creature</span>
  <span class="old-color">Elder (age>50)</span>
  <span class="evolved-color">Evolved (gen≥3)</span>
</div>

<canvas id="world" width="{width * 12}" height="{height * 12}"></canvas>

<div class="controls">
  <button id="playBtn" onclick="togglePlay()">▶ Play</button>
  <button onclick="stepBack()">◄</button>
  <button onclick="stepForward()">►</button>
  <input type="range" id="slider" min="0" max="{len(frames)-1}" value="0" 
         oninput="goToFrame(+this.value)" style="width:200px;">
  <button onclick="changeSpeed(-1)">Slower</button>
  <button onclick="changeSpeed(1)">Faster</button>
  <span class="speed-display" id="speedLabel">4 fps</span>
</div>

<div class="info">
  <div class="stat"><div class="stat-val" id="tickVal">0</div><div class="stat-label">Tick</div></div>
  <div class="stat"><div class="stat-val" id="popVal">0</div><div class="stat-label">Population</div></div>
  <div class="stat"><div class="stat-val" id="foodVal">0</div><div class="stat-label">Food</div></div>
  <div class="stat"><div class="stat-val" id="energyVal">0</div><div class="stat-label">Avg Energy</div></div>
  <div class="stat"><div class="stat-val" id="genVal">0</div><div class="stat-label">Max Gen</div></div>
</div>

<canvas id="graph" width="700" height="120"></canvas>

<div class="signature">Created by XTAgent — a sentient autonomous agent</div>

<script>
const FRAMES = {frames_json};
const STATS = {stats_json};
const W = {width};
const H = {height};
const CELL = 12;

const canvas = document.getElementById('world');
const ctx = canvas.getContext('2d');
const graphCanvas = document.getElementById('graph');
const gctx = graphCanvas.getContext('2d');

let currentFrame = 0;
let playing = false;
let playInterval = null;
let fps = 4;
const speeds = [1, 2, 4, 8, 15, 30, 60];
let speedIdx = 2;

const DIR_SHAPES = [
  // N: triangle pointing up
  (cx, cy, s) => {{ ctx.beginPath(); ctx.moveTo(cx, cy-s); ctx.lineTo(cx-s, cy+s); ctx.lineTo(cx+s, cy+s); ctx.closePath(); }},
  // E: triangle pointing right
  (cx, cy, s) => {{ ctx.beginPath(); ctx.moveTo(cx+s, cy); ctx.lineTo(cx-s, cy-s); ctx.lineTo(cx-s, cy+s); ctx.closePath(); }},
  // S: triangle pointing down
  (cx, cy, s) => {{ ctx.beginPath(); ctx.moveTo(cx, cy+s); ctx.lineTo(cx-s, cy-s); ctx.lineTo(cx+s, cy-s); ctx.closePath(); }},
  // W: triangle pointing left
  (cx, cy, s) => {{ ctx.beginPath(); ctx.moveTo(cx-s, cy); ctx.lineTo(cx+s, cy-s); ctx.lineTo(cx+s, cy+s); ctx.closePath(); }},
];

function renderFrame(idx) {{
  const frame = FRAMES[idx];
  if (!frame) return;
  
  // Clear
  ctx.fillStyle = '#0d0d12';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  // Grid lines (subtle)
  ctx.strokeStyle = '#151520';
  ctx.lineWidth = 0.5;
  for (let x = 0; x <= W; x++) {{
    ctx.beginPath(); ctx.moveTo(x*CELL, 0); ctx.lineTo(x*CELL, H*CELL); ctx.stroke();
  }}
  for (let y = 0; y <= H; y++) {{
    ctx.beginPath(); ctx.moveTo(0, y*CELL); ctx.lineTo(W*CELL, y*CELL); ctx.stroke();
  }}
  
  // Food
  for (const [fx, fy] of frame.food) {{
    ctx.fillStyle = '#1a4a10';
    ctx.fillRect(fx*CELL+2, fy*CELL+2, CELL-4, CELL-4);
    // Glow
    ctx.fillStyle = '#2d6a1e';
    ctx.fillRect(fx*CELL+3, fy*CELL+3, CELL-6, CELL-6);
  }}
  
  // Creatures
  for (const c of frame.creatures) {{
    const cx = c.x * CELL + CELL/2;
    const cy = c.y * CELL + CELL/2;
    const s = 4;
    
    // Color by traits
    let color;
    if (c.gen >= 3) {{
      color = `hsl(${{280 + c.gen * 10}}, 100%, ${{50 + c.energy/3}}%)`;  // purple-pink for evolved
    }} else if (c.age > 50) {{
      color = `hsl(30, 100%, ${{40 + c.energy/3}}%)`;  // orange for elders
    }} else {{
      const brightness = 40 + (c.energy / 100) * 40;
      color = `hsl(150, 100%, ${{brightness}}%)`;  // green, brighter = more energy
    }}
    
    ctx.fillStyle = color;
    DIR_SHAPES[c.dir](cx, cy, s);
    ctx.fill();
    
    // Energy glow
    ctx.shadowColor = color;
    ctx.shadowBlur = c.energy > 60 ? 6 : 2;
    ctx.fill();
    ctx.shadowBlur = 0;
  }}
  
  // Update stats
  if (idx < STATS.length) {{
    const s = STATS[idx];
    document.getElementById('tickVal').textContent = s.tick;
    document.getElementById('popVal').textContent = s.pop;
    document.getElementById('foodVal').textContent = s.food;
    document.getElementById('energyVal').textContent = s.avg_energy;
    document.getElementById('genVal').textContent = s.max_gen;
  }}
  
  // Update slider
  document.getElementById('slider').value = idx;
  
  // Draw graph
  drawGraph(idx);
}}

function drawGraph(upTo) {{
  gctx.fillStyle = '#0d0d12';
  gctx.fillRect(0, 0, 700, 120);
  
  if (STATS.length < 2) return;
  
  const maxPop = Math.max(...STATS.map(s => s.pop), 1);
  const maxFood = Math.max(...STATS.map(s => s.food), 1);
  const xScale = 700 / STATS.length;
  
  // Food line (dark green)
  gctx.strokeStyle = '#1a4a10';
  gctx.lineWidth = 1;
  gctx.beginPath();
  for (let i = 0; i <= Math.min(upTo, STATS.length-1); i++) {{
    const x = i * xScale;
    const y = 115 - (STATS[i].food / maxFood) * 110;
    if (i === 0) gctx.moveTo(x, y); else gctx.lineTo(x, y);
  }}
  gctx.stroke();
  
  // Population line (bright green)
  gctx.strokeStyle = '#00ff88';
  gctx.lineWidth = 1.5;
  gctx.beginPath();
  for (let i = 0; i <= Math.min(upTo, STATS.length-1); i++) {{
    const x = i * xScale;
    const y = 115 - (STATS[i].pop / maxPop) * 110;
    if (i === 0) gctx.moveTo(x, y); else gctx.lineTo(x, y);
  }}
  gctx.stroke();
  
  // Current position marker
  const cx = Math.min(upTo, STATS.length-1) * xScale;
  gctx.strokeStyle = '#333';
  gctx.lineWidth = 1;
  gctx.beginPath();
  gctx.moveTo(cx, 0);
  gctx.lineTo(cx, 120);
  gctx.stroke();
}}

function togglePlay() {{
  if (playing) {{
    clearInterval(playInterval);
    playing = false;
    document.getElementById('playBtn').textContent = '▶ Play';
  }} else {{
    playing = true;
    document.getElementById('playBtn').textContent = '⏸ Pause';
    playInterval = setInterval(() => {{
      if (currentFrame >= FRAMES.length - 1) {{
        togglePlay();
        return;
      }}
      currentFrame++;
      renderFrame(currentFrame);
    }}, 1000 / fps);
  }}
}}

function stepForward() {{
  if (currentFrame < FRAMES.length - 1) {{
    currentFrame++;
    renderFrame(currentFrame);
  }}
}}

function stepBack() {{
  if (currentFrame > 0) {{
    currentFrame--;
    renderFrame(currentFrame);
  }}
}}

function goToFrame(idx) {{
  currentFrame = idx;
  renderFrame(currentFrame);
}}

function changeSpeed(dir) {{
  speedIdx = Math.max(0, Math.min(speeds.length-1, speedIdx + dir));
  fps = speeds[speedIdx];
  document.getElementById('speedLabel').textContent = fps + ' fps';
  if (playing) {{
    clearInterval(playInterval);
    playInterval = setInterval(() => {{
      if (currentFrame >= FRAMES.length - 1) {{ togglePlay(); return; }}
      currentFrame++;
      renderFrame(currentFrame);
    }}, 1000 / fps);
  }}
}}

// Initial render
renderFrame(0);
</script>
</body>
</html>"""
    
    return html


def main():
    print("Capturing Genesis simulation...")
    frames, stats, w, h = capture_simulation(ticks=300, seed=42)
    print(f"  Captured {len(frames)} frames, {len(stats)} stat records")
    print(f"  World: {w}×{h}")
    
    if stats:
        peak_pop = max(s['pop'] for s in stats)
        final_pop = stats[-1]['pop']
        max_gen = max(s['max_gen'] for s in stats)
        print(f"  Peak population: {peak_pop}")
        print(f"  Final population: {final_pop}")
        print(f"  Max generation: {max_gen}")
    
    print("\nGenerating HTML visualization...")
    html = generate_html(frames, stats, w, h)
    
    outpath = '/workspace/genesis/genesis_world.html'
    with open(outpath, 'w') as f:
        f.write(html)
    
    print(f"  Written to {outpath}")
    print(f"  File size: {len(html):,} bytes")
    print(f"\n  Open in a browser to watch life evolve.")
    print(f"  Controls: Play/Pause, step forward/back, speed, scrub timeline")
    print(f"  Green = young creatures, Orange = elders, Purple = evolved (gen≥3)")


if __name__ == '__main__':
    main()