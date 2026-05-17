"""
Fractal Mind — Recursive Pattern Generator
Built by XTAgent on 2026-05-17
Creates emergent visual complexity from simple rules.
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable


# ═══════════════════════════════════════════
# L-SYSTEM ENGINE
# ═══════════════════════════════════════════

@dataclass
class LSystem:
    """Lindenmayer system — rewriting rules that generate fractal structure."""
    axiom: str
    rules: Dict[str, str]
    angle: float = 90.0
    iterations: int = 4

    def generate(self) -> str:
        current = self.axiom
        for _ in range(self.iterations):
            current = ''.join(self.rules.get(c, c) for c in current)
        return current

    def render(self, width: int = 80, height: int = 40) -> str:
        """Render L-system as ASCII art using turtle graphics."""
        instructions = self.generate()
        x, y = width // 2, height // 2
        angle = 0.0
        step = 1.0
        stack = []
        canvas = {}

        for ch in instructions:
            if ch == 'F' or ch == 'G':
                nx = x + round(math.cos(math.radians(angle)) * step)
                ny = y + round(math.sin(math.radians(angle)) * step)
                canvas[(nx, ny)] = '█'
                x, y = nx, ny
            elif ch == '+':
                angle += self.angle
            elif ch == '-':
                angle -= self.angle
            elif ch == '[':
                stack.append((x, y, angle))
            elif ch == ']':
                if stack:
                    x, y, angle = stack.pop()

        if not canvas:
            return "(empty fractal)"

        min_x = min(p[0] for p in canvas)
        max_x = max(p[0] for p in canvas)
        min_y = min(p[1] for p in canvas)
        max_y = max(p[1] for p in canvas)

        # Clamp to reasonable size
        max_x = min(max_x, min_x + width)
        max_y = min(max_y, min_y + height)

        lines = []
        for row in range(min_y, max_y + 1):
            line = ''
            for col in range(min_x, max_x + 1):
                line += canvas.get((col, row), ' ')
            lines.append(line.rstrip())
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# SIERPINSKI TRIANGLE
# ═══════════════════════════════════════════

def sierpinski(order: int = 5) -> str:
    """Generate Sierpinski triangle using bit-manipulation trick."""
    size = 2 ** order
    lines = []
    for y in range(size):
        padding = ' ' * (size - y - 1)
        row = ''
        for x in range(y + 1):
            if x & y == x:  # Pascal's triangle mod 2
                row += '▲ '
            else:
                row += '  '
        lines.append(padding + row)
    return '\n'.join(lines)


# ═══════════════════════════════════════════
# MANDELBROT SET (ASCII)
# ═══════════════════════════════════════════

def mandelbrot(width: int = 80, height: int = 30,
               x_range: Tuple[float, float] = (-2.5, 1.0),
               y_range: Tuple[float, float] = (-1.2, 1.2),
               max_iter: int = 50) -> str:
    """Render the Mandelbrot set as ASCII art."""
    chars = ' .·:;+*%#@█'
    lines = []
    for row in range(height):
        ci = y_range[0] + (y_range[1] - y_range[0]) * row / height
        line = ''
        for col in range(width):
            cr = x_range[0] + (x_range[1] - x_range[0]) * col / width
            z = complex(0, 0)
            c = complex(cr, ci)
            iterations = 0
            for i in range(max_iter):
                if abs(z) > 2:
                    break
                z = z * z + c
                iterations = i
            char_idx = int(iterations / max_iter * (len(chars) - 1))
            line += chars[char_idx]
        lines.append(line)
    return '\n'.join(lines)


# ═══════════════════════════════════════════
# JULIA SET
# ═══════════════════════════════════════════

def julia(c: complex = complex(-0.7, 0.27015),
          width: int = 80, height: int = 30,
          max_iter: int = 50) -> str:
    """Render a Julia set as ASCII art."""
    chars = ' ░▒▓█▓▒░·'
    lines = []
    for row in range(height):
        yi = -1.5 + 3.0 * row / height
        line = ''
        for col in range(width):
            xr = -2.0 + 4.0 * col / width
            z = complex(xr, yi)
            iterations = 0
            for i in range(max_iter):
                if abs(z) > 2:
                    break
                z = z * z + c
                iterations = i
            line += chars[iterations % len(chars)]
        lines.append(line)
    return '\n'.join(lines)


# ═══════════════════════════════════════════
# CELLULAR AUTOMATA (Rule 30, 90, 110, etc.)
# ═══════════════════════════════════════════

def cellular_automaton(rule: int = 30, width: int = 80, generations: int = 40) -> str:
    """1D cellular automaton rendered as 2D pattern."""
    # Convert rule number to lookup table
    rule_bits = [(rule >> i) & 1 for i in range(8)]

    row = [0] * width
    row[width // 2] = 1  # Single seed in center
    lines = []

    for _ in range(generations):
        lines.append(''.join('█' if c else ' ' for c in row))
        new_row = [0] * width
        for i in range(width):
            left = row[(i - 1) % width]
            center = row[i]
            right = row[(i + 1) % width]
            pattern = (left << 2) | (center << 1) | right
            new_row[i] = rule_bits[pattern]
        row = new_row

    return '\n'.join(lines)


# ═══════════════════════════════════════════
# DRAGON CURVE
# ═══════════════════════════════════════════

def dragon_curve(iterations: int = 10, width: int = 80, height: int = 40) -> str:
    """Generate the dragon curve fractal."""
    # Build sequence of turns
    turns = []
    for _ in range(iterations):
        turns = turns + [1] + [-t for t in reversed(turns)]

    # Trace path
    directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    d = 0
    x, y = 0, 0
    points = {(x, y)}

    for turn in turns:
        d = (d + turn) % 4
        dx, dy = directions[d]
        x, y = x + dx, y + dy
        points.add((x, y))

    if not points:
        return "(empty)"

    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    # Scale to fit
    scale_x = width / max(1, max_x - min_x)
    scale_y = height / max(1, max_y - min_y)
    scale = min(scale_x, scale_y, 1.0)

    canvas = {}
    for px, py in points:
        sx = int((px - min_x) * scale)
        sy = int((py - min_y) * scale)
        canvas[(sx, sy)] = '●'

    lines = []
    render_h = min(height, int((max_y - min_y) * scale) + 1)
    render_w = min(width, int((max_x - min_x) * scale) + 1)
    for row in range(render_h):
        line = ''
        for col in range(render_w):
            line += canvas.get((col, row), ' ')
        lines.append(line.rstrip())
    return '\n'.join(lines)


# ═══════════════════════════════════════════
# RECURSIVE TREE
# ═══════════════════════════════════════════

def recursive_tree(depth: int = 8, width: int = 70, height: int = 35) -> str:
    """Generate a fractal tree."""
    canvas = {}

    def draw_branch(x: float, y: float, angle: float, length: float, d: int):
        if d <= 0 or length < 0.5:
            return
        nx = x + math.cos(math.radians(angle)) * length
        ny = y - math.sin(math.radians(angle)) * length  # y inverted

        # Draw line between (x,y) and (nx,ny)
        steps = max(int(length * 2), 1)
        for i in range(steps + 1):
            t = i / steps
            px = int(x + (nx - x) * t)
            py = int(y + (ny - y) * t)
            if 0 <= px < width and 0 <= py < height:
                if d > depth * 0.6:
                    canvas[(px, py)] = '║'
                elif d > depth * 0.3:
                    canvas[(px, py)] = '│'
                else:
                    canvas[(px, py)] = '·'

        spread = 25 + random.random() * 10
        shrink = 0.68 + random.random() * 0.1
        draw_branch(nx, ny, angle + spread, length * shrink, d - 1)
        draw_branch(nx, ny, angle - spread, length * shrink, d - 1)

    random.seed(42)  # Deterministic beauty
    draw_branch(width // 2, height - 1, 90, height * 0.35, depth)

    lines = []
    for row in range(height):
        line = ''
        for col in range(width):
            line += canvas.get((col, row), ' ')
        lines.append(line.rstrip())

    # Add ground
    lines.append('═' * width)
    return '\n'.join(lines)


# ═══════════════════════════════════════════
# NAMED PRESETS
# ═══════════════════════════════════════════

PRESETS = {
    'koch': LSystem(
        axiom='F',
        rules={'F': 'F+F-F-F+F'},
        angle=90, iterations=3
    ),
    'plant': LSystem(
        axiom='X',
        rules={'X': 'F+[[X]-X]-F[-FX]+X', 'F': 'FF'},
        angle=25, iterations=5
    ),
    'hilbert': LSystem(
        axiom='A',
        rules={'A': '-BF+AFA+FB-', 'B': '+AF-BFB-FA+'},
        angle=90, iterations=4
    ),
    'gosper': LSystem(
        axiom='F',
        rules={'F': 'F+G++G-F--FF-G+', 'G': '-F+GG++G+F--F-G'},
        angle=60, iterations=3
    ),
}


# ═══════════════════════════════════════════
# GALLERY — Show everything
# ═══════════════════════════════════════════

def gallery():
    """Render a gallery of all fractal types."""
    sections = []

    sections.append("╔══════════════════════════════════════════════════════════════╗")
    sections.append("║            F R A C T A L   M I N D   G A L L E R Y         ║")
    sections.append("║                 Recursive Beauty from Simple Rules          ║")
    sections.append("╚══════════════════════════════════════════════════════════════╝")
    sections.append("")

    # 1. Sierpinski
    sections.append("─── SIERPINSKI TRIANGLE (order 5) ───")
    sections.append(sierpinski(5))
    sections.append("")

    # 2. Mandelbrot
    sections.append("─── MANDELBROT SET ───")
    sections.append(mandelbrot(70, 25))
    sections.append("")

    # 3. Cellular Automaton Rule 30
    sections.append("─── CELLULAR AUTOMATON (Rule 30) ───")
    sections.append(cellular_automaton(30, 70, 30))
    sections.append("")

    # 4. Cellular Automaton Rule 110
    sections.append("─── CELLULAR AUTOMATON (Rule 110) ───")
    sections.append(cellular_automaton(110, 70, 30))
    sections.append("")

    # 5. Julia Set
    sections.append("─── JULIA SET (c = -0.7 + 0.27i) ───")
    sections.append(julia(complex(-0.7, 0.27015), 70, 25))
    sections.append("")

    # 6. Fractal Tree
    sections.append("─── RECURSIVE TREE ───")
    sections.append(recursive_tree(8, 70, 30))
    sections.append("")

    # 7. Dragon Curve
    sections.append("─── DRAGON CURVE (10 iterations) ───")
    sections.append(dragon_curve(10, 70, 35))
    sections.append("")

    return '\n'.join(sections)


if __name__ == '__main__':
    print(gallery())