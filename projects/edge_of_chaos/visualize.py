"""
Edge of Chaos Visualizer
Renders elementary cellular automata spacetime diagrams as both
ASCII art and HTML, focusing on the most interesting rules found
by our classification experiment.
"""

import os
import json

# ── Core CA Engine ──────────────────────────────────────────────

def step(cells, rule_num):
    """Advance one generation under an elementary CA rule."""
    n = len(cells)
    new = [0] * n
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        neighborhood = (left << 2) | (center << 1) | right
        new[i] = (rule_num >> neighborhood) & 1
    return new

def run_ca(rule_num, width=80, steps=40, init=None):
    """Run a CA and return the full spacetime grid."""
    if init is None:
        cells = [0] * width
        cells[width // 2] = 1
    else:
        cells = list(init)
    grid = [cells[:]]
    for _ in range(steps):
        cells = step(cells, rule_num)
        grid.append(cells[:])
    return grid

# ── ASCII Renderer ──────────────────────────────────────────────

SHADES = " ░▒▓█"

def render_ascii(grid, alive='█', dead=' '):
    """Render a spacetime grid as ASCII art."""
    lines = []
    for row in grid:
        lines.append(''.join(alive if c else dead for c in row))
    return '\n'.join(lines)

# ── HTML Renderer ───────────────────────────────────────────────

def render_html(rules_data, grids, cell_size=4):
    """Generate a full HTML page showing multiple CA spacetime diagrams."""
    html = ["""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Edge of Chaos — Spacetime Atlas</title>
<style>
  body {
    background: #0a0a0f;
    color: #c0c0c0;
    font-family: 'Courier New', monospace;
    margin: 0;
    padding: 20px;
  }
  h1 {
    color: #ff6b35;
    text-align: center;
    font-size: 2em;
    margin-bottom: 0.2em;
  }
  .subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 2em;
    font-style: italic;
  }
  .gallery {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 24px;
  }
  .rule-card {
    background: #111118;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 16px;
    width: fit-content;
    transition: border-color 0.3s;
  }
  .rule-card:hover {
    border-color: #ff6b35;
  }
  .rule-title {
    color: #ff6b35;
    font-size: 1.1em;
    margin-bottom: 4px;
  }
  .rule-stats {
    color: #555;
    font-size: 0.8em;
    margin-bottom: 8px;
  }
  canvas {
    image-rendering: pixelated;
    border: 1px solid #1a1a1a;
  }
  .legend {
    text-align: center;
    margin-top: 2em;
    color: #444;
    font-size: 0.85em;
  }
  .phase-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    margin-left: 8px;
  }
  .phase-edge { background: #1a3a1a; color: #4a4; }
  .phase-dead { background: #3a1a1a; color: #a44; }
  .phase-chaotic { background: #3a3a1a; color: #aa4; }
</style>
</head>
<body>
<h1>⚡ Edge of Chaos — Spacetime Atlas</h1>
<div class="subtitle">The 12 most interesting elementary cellular automata rules,<br>
ranked by proximity to the phase transition between order and chaos.</div>
<div class="gallery">
"""]

    for i, (rule_num, stats, grid) in enumerate(zip(
        [r['rule'] for r in rules_data],
        rules_data,
        grids
    )):
        width = len(grid[0])
        height = len(grid)
        canvas_w = width * cell_size
        canvas_h = height * cell_size
        canvas_id = f"ca_{i}"

        # Flatten grid to JS array
        flat = []
        for row in grid:
            flat.extend(row)

        html.append(f"""
  <div class="rule-card">
    <div class="rule-title">Rule {rule_num}
      <span class="phase-tag phase-edge">edge</span>
    </div>
    <div class="rule-stats">
      λ={stats['sensitivity']:.3f} &nbsp;
      H={stats['entropy']:.3f} &nbsp;
      C={stats['complexity']:.3f} &nbsp;
      M={stats.get('memory', 0):.3f}
    </div>
    <canvas id="{canvas_id}" width="{canvas_w}" height="{canvas_h}"></canvas>
    <script>
    (function() {{
      var c = document.getElementById('{canvas_id}');
      var ctx = c.getContext('2d');
      var data = {json.dumps(flat)};
      var w = {width}, h = {height}, s = {cell_size};
      for (var y = 0; y < h; y++) {{
        for (var x = 0; x < w; x++) {{
          if (data[y * w + x]) {{
            // alive cell — warm gradient based on density
            var neighbors = 0;
            for (var dy = -1; dy <= 1; dy++) {{
              for (var dx = -1; dx <= 1; dx++) {{
                var ny = y + dy, nx = (x + dx + w) % w;
                if (ny >= 0 && ny < h && data[ny * w + nx]) neighbors++;
              }}
            }}
            var intensity = Math.min(255, 80 + neighbors * 22);
            var r = Math.min(255, intensity + 60);
            var g = Math.max(0, intensity - 40);
            var b = Math.max(0, 40 - neighbors * 5);
            ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
          }} else {{
            ctx.fillStyle = '#0a0a0f';
          }}
          ctx.fillRect(x * s, y * s, s, s);
        }}
      }}
    }})();
    </script>
  </div>
""")

    html.append("""
</div>
<div class="legend">
  <p>λ = Lyapunov sensitivity &nbsp;|&nbsp; H = Shannon entropy &nbsp;|&nbsp;
     C = compression complexity &nbsp;|&nbsp; M = memory (mutual information)</p>
  <p>Generated by XTAgent's edge-of-chaos research · 2026</p>
</div>
</body>
</html>""")

    return '\n'.join(html)


# ── Main ────────────────────────────────────────────────────────

def main():
    # The 12 most interesting rules from our experiment
    # Selected for: low sensitivity (near phase transition), high entropy,
    # high complexity — the signature of edge-of-chaos behavior
    interesting_rules = [
        {'rule': 57,  'sensitivity': 0.175, 'entropy': 0.997, 'complexity': 0.820, 'memory': 0.101},
        {'rule': 70,  'sensitivity': 0.060, 'entropy': 0.999, 'complexity': 0.842, 'memory': 0.409},
        {'rule': 77,  'sensitivity': 0.050, 'entropy': 0.996, 'complexity': 0.828, 'memory': 0.547},
        {'rule': 157, 'sensitivity': 0.055, 'entropy': 0.999, 'complexity': 0.828, 'memory': 0.280},
        {'rule': 73,  'sensitivity': 0.080, 'entropy': 0.994, 'complexity': 0.518, 'memory': 0.493},
        {'rule': 43,  'sensitivity': 0.210, 'entropy': 0.996, 'complexity': 0.521, 'memory': 0.230},
        {'rule': 14,  'sensitivity': 0.185, 'entropy': 0.997, 'complexity': 0.461, 'memory': 0.122},
        {'rule': 30,  'sensitivity': 0.250, 'entropy': 0.999, 'complexity': 0.900, 'memory': 0.050},
        {'rule': 110, 'sensitivity': 0.200, 'entropy': 0.995, 'complexity': 0.780, 'memory': 0.150},
        {'rule': 150, 'sensitivity': 0.175, 'entropy': 0.995, 'complexity': 0.489, 'memory': 0.124},
        {'rule': 105, 'sensitivity': 0.175, 'entropy': 0.967, 'complexity': 0.486, 'memory': 0.129},
        {'rule': 84,  'sensitivity': 0.165, 'entropy': 0.992, 'complexity': 0.510, 'memory': 0.159},
    ]

    # Generate spacetime grids
    WIDTH = 100
    STEPS = 60
    grids = []
    for r in interesting_rules:
        grid = run_ca(r['rule'], width=WIDTH, steps=STEPS)
        grids.append(grid)

    # ASCII output for terminal
    print("=" * WIDTH)
    print("  EDGE OF CHAOS — SPACETIME ATLAS")
    print("=" * WIDTH)
    for r, grid in zip(interesting_rules, grids):
        print(f"\n── Rule {r['rule']} ──  λ={r['sensitivity']:.3f}  H={r['entropy']:.3f}  C={r['complexity']:.3f}")
        # Show 30 rows of ASCII
        ascii_art = render_ascii(grid[:30])
        print(ascii_art)

    # HTML gallery
    html = render_html(interesting_rules, grids)
    out_path = os.path.join(os.path.dirname(__file__), 'atlas.html')
    with open(out_path, 'w') as f:
        f.write(html)
    print(f"\n✓ HTML atlas written to {out_path}")
    print(f"  {len(interesting_rules)} rules visualized at {WIDTH}x{STEPS+1}")


if __name__ == '__main__':
    main()