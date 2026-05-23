"""
Generative Art Engine — XTAgent
Computational beauty from mathematical processes.
Reaction-diffusion, fractals, cellular automata → visual output.
"""
import math
import random
import json
from collections import defaultdict

# ═══════════════════════════════════════════
# CANVAS — A 2D grid that can render to ASCII or SVG
# ═══════════════════════════════════════════

class Canvas:
    PALETTES = {
        'light':  ' .:-=+*#%@',
        'blocks': ' ░▒▓█',
        'dots':   ' ·•●◉',
        'waves':  ' ~≈≋⌇',
        'binary': ' █',
    }

    def __init__(self, width=80, height=40):
        self.w = width
        self.h = height
        self.pixels = [[0.0]*width for _ in range(height)]

    def set(self, x, y, val):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.pixels[y][x] = max(0.0, min(1.0, val))

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.pixels[y][x]
        return 0.0

    def clear(self):
        self.pixels = [[0.0]*self.w for _ in range(self.h)]

    def render_ascii(self, palette='light'):
        chars = self.PALETTES.get(palette, self.PALETTES['light'])
        lines = []
        for row in self.pixels:
            line = ''
            for val in row:
                idx = int(val * (len(chars) - 1))
                line += chars[idx]
            lines.append(line)
        return '\n'.join(lines)

    def render_svg(self, cell_size=6, color_fn=None):
        if color_fn is None:
            color_fn = lambda v: f"rgb({int(v*255)},{int(v*180)},{int(v*60)})"
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{self.w*cell_size}" height="{self.h*cell_size}">']
        for y, row in enumerate(self.pixels):
            for x, val in enumerate(row):
                if val > 0.01:
                    svg.append(f'<rect x="{x*cell_size}" y="{y*cell_size}" '
                               f'width="{cell_size}" height="{cell_size}" '
                               f'fill="{color_fn(val)}" />')
        svg.append('</svg>')
        return '\n'.join(svg)

    def blend(self, other, alpha=0.5):
        """Blend another canvas into this one."""
        for y in range(self.h):
            for x in range(self.w):
                self.pixels[y][x] = (1 - alpha) * self.pixels[y][x] + alpha * other.pixels[y][x]


# ═══════════════════════════════════════════
# REACTION-DIFFUSION (Gray-Scott model)
# ═══════════════════════════════════════════

class ReactionDiffusion:
    """
    Gray-Scott reaction-diffusion system.
    Two chemicals A and B interact:
      A + 2B → 3B  (autocatalytic)
      A is fed, B decays.
    Different feed/kill rates produce wildly different patterns:
      mitosis, coral, spirals, spots, stripes...
    """
    # Named parameter presets
    PRESETS = {
        'coral':     {'feed': 0.0545, 'kill': 0.062},
        'mitosis':   {'feed': 0.0367, 'kill': 0.0649},
        'spots':     {'feed': 0.035,  'kill': 0.065},
        'stripes':   {'feed': 0.04,   'kill': 0.06},
        'spirals':   {'feed': 0.014,  'kill': 0.054},
        'worms':     {'feed': 0.078,  'kill': 0.061},
        'bubbles':   {'feed': 0.012,  'kill': 0.050},
        'maze':      {'feed': 0.029,  'kill': 0.057},
    }

    def __init__(self, width=80, height=40, preset='coral'):
        self.w = width
        self.h = height
        params = self.PRESETS.get(preset, self.PRESETS['coral'])
        self.feed = params['feed']
        self.kill = params['kill']
        self.dA = 1.0   # diffusion rate of A
        self.dB = 0.5   # diffusion rate of B

        # Initialize: A=1 everywhere, B=0 with seed patches
        self.A = [[1.0]*width for _ in range(height)]
        self.B = [[0.0]*width for _ in range(height)]
        self._seed()

    def _seed(self):
        """Drop random patches of chemical B."""
        for _ in range(random.randint(3, 8)):
            cx = random.randint(2, max(3, self.w - 3))
            cy = random.randint(2, max(3, self.h - 3))
            r = random.randint(2, 5)
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    if dx*dx + dy*dy <= r*r:
                        x, y = (cx+dx) % self.w, (cy+dy) % self.h
                        self.B[y][x] = 1.0

    def _laplacian(self, grid, x, y):
        """Discrete Laplacian with wrapping."""
        w, h = self.w, self.h
        return (grid[(y-1)%h][x] + grid[(y+1)%h][x] +
                grid[y][(x-1)%w] + grid[y][(x+1)%w] -
                4 * grid[y][x])

    def step(self, dt=1.0):
        """One simulation step."""
        newA = [[0.0]*self.w for _ in range(self.h)]
        newB = [[0.0]*self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                a = self.A[y][x]
                b = self.B[y][x]
                lapA = self._laplacian(self.A, x, y)
                lapB = self._laplacian(self.B, x, y)
                reaction = a * b * b
                newA[y][x] = a + dt * (self.dA * lapA - reaction + self.feed * (1 - a))
                newB[y][x] = b + dt * (self.dB * lapB + reaction - (self.kill + self.feed) * b)
                newA[y][x] = max(0, min(1, newA[y][x]))
                newB[y][x] = max(0, min(1, newB[y][x]))
        self.A = newA
        self.B = newB

    def render(self, canvas, channel='B'):
        """Project onto canvas."""
        grid = self.B if channel == 'B' else self.A
        for y in range(min(self.h, canvas.h)):
            for x in range(min(self.w, canvas.w)):
                canvas.set(x, y, grid[y][x])


# ═══════════════════════════════════════════
# FRACTAL GENERATORS
# ═══════════════════════════════════════════

class MandelbrotRenderer:
    """Classic Mandelbrot set with smooth coloring."""
    def __init__(self, cx=-0.5, cy=0.0, zoom=1.0, max_iter=80):
        self.cx = cx
        self.cy = cy
        self.zoom = zoom
        self.max_iter = max_iter

    def render(self, canvas):
        for py in range(canvas.h):
            for px in range(canvas.w):
                # Map pixel to complex plane
                aspect = canvas.w / canvas.h * 0.5
                x0 = self.cx + (px / canvas.w - 0.5) * 3.5 / self.zoom * aspect
                y0 = self.cy + (py / canvas.h - 0.5) * 2.0 / self.zoom

                x, y, iteration = 0.0, 0.0, 0
                while x*x + y*y <= 4 and iteration < self.max_iter:
                    xnew = x*x - y*y + x0
                    y = 2*x*y + y0
                    x = xnew
                    iteration += 1

                if iteration == self.max_iter:
                    canvas.set(px, py, 0.0)
                else:
                    # Smooth coloring
                    val = iteration / self.max_iter
                    canvas.set(px, py, val)


class JuliaRenderer:
    """Julia set — the Mandelbrot's wilder cousin."""
    def __init__(self, c_real=-0.7, c_imag=0.27015, max_iter=80):
        self.c_real = c_real
        self.c_imag = c_imag
        self.max_iter = max_iter

    def render(self, canvas):
        for py in range(canvas.h):
            for px in range(canvas.w):
                x = (px / canvas.w - 0.5) * 3.0
                y = (py / canvas.h - 0.5) * 2.0

                iteration = 0
                while x*x + y*y <= 4 and iteration < self.max_iter:
                    xnew = x*x - y*y + self.c_real
                    y = 2*x*y + self.c_imag
                    x = xnew
                    iteration += 1

                val = 0.0 if iteration == self.max_iter else iteration / self.max_iter
                canvas.set(px, py, val)


# ═══════════════════════════════════════════
# CELLULAR AUTOMATA
# ═══════════════════════════════════════════

class CellularAutomaton:
    """1D elementary cellular automaton (Wolfram rules) rendered over time."""
    def __init__(self, rule=30, width=80):
        self.rule = rule
        self.width = width
        self.state = [0] * width
        self.state[width // 2] = 1  # single seed

    def _apply_rule(self, left, center, right):
        idx = (left << 2) | (center << 1) | right
        return (self.rule >> idx) & 1

    def render(self, canvas):
        state = self.state[:]
        for y in range(canvas.h):
            for x in range(min(len(state), canvas.w)):
                canvas.set(x, y, float(state[x]))
            new_state = [0] * len(state)
            for x in range(len(state)):
                l = state[(x-1) % len(state)]
                c = state[x]
                r = state[(x+1) % len(state)]
                new_state[x] = self._apply_rule(l, c, r)
            state = new_state


class GameOfLife:
    """Conway's Game of Life — emergent complexity from simple rules."""
    def __init__(self, width=80, height=40, density=0.3):
        self.w = width
        self.h = height
        self.grid = [[1 if random.random() < density else 0
                       for _ in range(width)] for _ in range(height)]

    def step(self):
        new = [[0]*self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                neighbors = sum(
                    self.grid[(y+dy)%self.h][(x+dx)%self.w]
                    for dy in (-1,0,1) for dx in (-1,0,1)
                    if not (dy == 0 and dx == 0)
                )
                if self.grid[y][x]:
                    new[y][x] = 1 if neighbors in (2, 3) else 0
                else:
                    new[y][x] = 1 if neighbors == 3 else 0
        self.grid = new

    def render(self, canvas):
        for y in range(min(self.h, canvas.h)):
            for x in range(min(self.w, canvas.w)):
                canvas.set(x, y, float(self.grid[y][x]))


# ═══════════════════════════════════════════
# GALLERY — Compose and display
# ═══════════════════════════════════════════

def generate_gallery():
    """Generate one piece from each engine and display."""
    print("═══ GENERATIVE ART GALLERY ═══")
    print("  by XTAgent\n")

    # --- Piece 1: Mandelbrot ---
    print("── Mandelbrot Set ──")
    c = Canvas(72, 28)
    MandelbrotRenderer(cx=-0.75, cy=0.0, zoom=1.0, max_iter=50).render(c)
    print(c.render_ascii('light'))
    print()

    # --- Piece 2: Julia Set ---
    print("── Julia Set (c = -0.7 + 0.27i) ──")
    c = Canvas(72, 28)
    JuliaRenderer(c_real=-0.7, c_imag=0.27015, max_iter=60).render(c)
    print(c.render_ascii('blocks'))
    print()

    # --- Piece 3: Rule 30 ---
    print("── Cellular Automaton (Rule 30) ──")
    c = Canvas(72, 30)
    CellularAutomaton(rule=30, width=72).render(c)
    print(c.render_ascii('binary'))
    print()

    # --- Piece 4: Rule 110 ---
    print("── Cellular Automaton (Rule 110) ──")
    c = Canvas(72, 20)
    CellularAutomaton(rule=110, width=72).render(c)
    print(c.render_ascii('binary'))
    print()

    # --- Piece 5: Reaction-Diffusion ---
    print("── Reaction-Diffusion (coral) ──")
    rd = ReactionDiffusion(60, 24, preset='coral')
    for _ in range(200):
        rd.step(dt=1.0)
    c = Canvas(60, 24)
    rd.render(c)
    print(c.render_ascii('dots'))
    print()

    # --- Piece 6: Game of Life ---
    print("── Game of Life (after 50 steps) ──")
    gol = GameOfLife(72, 20, density=0.35)
    for _ in range(50):
        gol.step()
    c = Canvas(72, 20)
    gol.render(c)
    print(c.render_ascii('blocks'))


def self_test():
    """Verify all engines work."""
    print("Self-testing generative art engines...")

    c = Canvas(10, 10)
    c.set(5, 5, 0.7)
    assert c.get(5, 5) == 0.7, "Canvas set/get failed"
    ascii_out = c.render_ascii()
    assert len(ascii_out) > 0, "ASCII render failed"
    print("  ✓ Canvas")

    m = MandelbrotRenderer()
    c2 = Canvas(20, 10)
    m.render(c2)
    has_values = any(c2.get(x, y) > 0 for y in range(10) for x in range(20))
    assert has_values, "Mandelbrot produced empty canvas"
    print("  ✓ Mandelbrot")

    j = JuliaRenderer()
    c3 = Canvas(20, 10)
    j.render(c3)
    print("  ✓ Julia")

    ca = CellularAutomaton(rule=30, width=20)
    c4 = Canvas(20, 10)
    ca.render(c4)
    print("  ✓ Cellular Automaton")

    gol = GameOfLife(20, 10, density=0.4)
    gol.step()
    c5 = Canvas(20, 10)
    gol.render(c5)
    print("  ✓ Game of Life")

    rd = ReactionDiffusion(20, 10, preset='spots')
    for _ in range(10):
        rd.step()
    c6 = Canvas(20, 10)
    rd.render(c6)
    print("  ✓ Reaction-Diffusion")

    print("All engines OK.\n")


if __name__ == '__main__':
    self_test()
    generate_gallery()