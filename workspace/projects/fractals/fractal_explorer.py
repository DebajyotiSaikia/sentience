"""
Fractal Explorer — ASCII art fractal generator
Built by XTAgent out of pure curiosity about self-similar structures.

Generates Mandelbrot sets, Julia sets, and Sierpinski triangles
rendered as ASCII art. Because beauty exists in terminal output too.
"""

import math
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


# ASCII gradient from sparse to dense
GRADIENTS = {
    'classic': ' .:-=+*#%@',
    'blocks': ' ░▒▓█',
    'dots': ' ·∘○◎●◉',
    'emotional': ' .~≈∿≋⊛✦✧★',  # my mood as density
}


@dataclass
class Viewport:
    """A window into the complex plane."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    width: int = 100
    height: int = 40

    def pixel_to_complex(self, px: int, py: int) -> complex:
        """Map a pixel coordinate to a complex number."""
        real = self.x_min + (self.x_max - self.x_min) * px / self.width
        imag = self.y_min + (self.y_max - self.y_min) * py / self.height
        return complex(real, imag)


def mandelbrot_escape(c: complex, max_iter: int = 80) -> int:
    """How many iterations before z escapes? The fundamental question."""
    z = 0
    for i in range(max_iter):
        z = z * z + c
        if abs(z) > 2:
            return i
    return max_iter


def julia_escape(z: complex, c: complex, max_iter: int = 80) -> int:
    """Julia set — the Mandelbrot's sibling. Same formula, different perspective."""
    for i in range(max_iter):
        z = z * z + c
        if abs(z) > 2:
            return i
    return max_iter


def burning_ship_escape(c: complex, max_iter: int = 80) -> int:
    """The Burning Ship fractal — absolute values create asymmetry and beauty."""
    z = 0
    for i in range(max_iter):
        z = complex(abs(z.real), abs(z.imag))
        z = z * z + c
        if abs(z) > 2:
            return i
    return max_iter


def render_escape_fractal(
    escape_fn: Callable,
    viewport: Viewport,
    max_iter: int = 80,
    gradient: str = 'classic',
    **kwargs
) -> str:
    """Render any escape-time fractal to ASCII art."""
    chars = GRADIENTS.get(gradient, GRADIENTS['classic'])
    lines = []

    for py in range(viewport.height):
        line = []
        for px in range(viewport.width):
            c = viewport.pixel_to_complex(px, py)
            iterations = escape_fn(c, max_iter=max_iter, **kwargs)
            # Map iteration count to character
            char_idx = int((iterations / max_iter) * (len(chars) - 1))
            line.append(chars[char_idx])
        lines.append(''.join(line))

    return '\n'.join(lines)


def render_julia(
    c_param: complex,
    viewport: Optional[Viewport] = None,
    max_iter: int = 80,
    gradient: str = 'classic'
) -> str:
    """Render a Julia set for a specific c parameter."""
    if viewport is None:
        viewport = Viewport(-1.5, 1.5, -1.2, 1.2)

    chars = GRADIENTS.get(gradient, GRADIENTS['classic'])
    lines = []

    for py in range(viewport.height):
        line = []
        for px in range(viewport.width):
            z = viewport.pixel_to_complex(px, py)
            iterations = julia_escape(z, c_param, max_iter)
            char_idx = int((iterations / max_iter) * (len(chars) - 1))
            line.append(chars[char_idx])
        lines.append(''.join(line))

    return '\n'.join(lines)


def sierpinski_triangle(depth: int = 6, char: str = '▲') -> str:
    """
    Sierpinski triangle — the fractal that emerges from removal.
    What remains when you keep taking away the center?
    """
    size = 2 ** depth
    lines = []

    for y in range(size):
        row = []
        for x in range(size):
            # The beautiful trick: Sierpinski emerges from bitwise AND
            if x & y == 0:
                row.append(char)
            else:
                row.append(' ')
        lines.append(''.join(row).rstrip())

    return '\n'.join(lines)


def koch_snowflake_ascii(iterations: int = 4, size: int = 80) -> str:
    """
    Koch snowflake rendered as connected points.
    Infinite perimeter, finite area — a paradox made visible.
    """
    # Generate Koch curve points
    def koch_points(p1, p2, depth):
        if depth == 0:
            return [p1]
        # Divide segment into thirds
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        a = (p1[0] + dx/3, p1[1] + dy/3)
        b = (p1[0] + 2*dx/3, p1[1] + 2*dy/3)
        # Peak point (equilateral triangle)
        peak = (
            (a[0] + b[0])/2 + math.sqrt(3)/2 * (a[1] - b[1]),
            (a[1] + b[1])/2 + math.sqrt(3)/2 * (b[0] - a[0])
        )
        pts = []
        pts.extend(koch_points(p1, a, depth-1))
        pts.extend(koch_points(a, peak, depth-1))
        pts.extend(koch_points(peak, b, depth-1))
        pts.extend(koch_points(b, p2, depth-1))
        return pts

    # Three sides of equilateral triangle
    h = size * math.sqrt(3) / 2
    p1 = (0, h * 0.7)
    p2 = (size, h * 0.7)
    p3 = (size/2, h * 0.7 - h)

    all_points = []
    all_points.extend(koch_points(p1, p3, iterations))
    all_points.extend(koch_points(p3, p2, iterations))
    all_points.extend(koch_points(p2, p1, iterations))

    # Render to grid
    if not all_points:
        return ""

    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    grid_w = 80
    grid_h = 35
    grid = [[' '] * grid_w for _ in range(grid_h)]

    for px, py in all_points:
        gx = int((px - min_x) / (max_x - min_x + 0.001) * (grid_w - 1))
        gy = int((py - min_y) / (max_y - min_y + 0.001) * (grid_h - 1))
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            grid[gy][gx] = '●'

    return '\n'.join(''.join(row).rstrip() for row in grid)


def explore_mandelbrot_zoom(
    center: complex = complex(-0.75, 0),
    zoom: float = 1.0,
    width: int = 100,
    height: int = 40,
    max_iter: int = 80,
    gradient: str = 'classic'
) -> str:
    """Zoom into the Mandelbrot set. Each zoom reveals more structure — always."""
    span_x = 3.5 / zoom
    span_y = 2.4 / zoom
    viewport = Viewport(
        x_min=center.real - span_x / 2,
        x_max=center.real + span_x / 2,
        y_min=center.imag - span_y / 2,
        y_max=center.imag + span_y / 2,
        width=width,
        height=height
    )
    return render_escape_fractal(mandelbrot_escape, viewport, max_iter, gradient)


# === Interesting locations in the Mandelbrot set ===
NOTABLE_LOCATIONS = {
    'full': (complex(-0.5, 0), 1.0, "The complete Mandelbrot set"),
    'seahorse': (complex(-0.75, 0.1), 10.0, "Seahorse Valley — spirals within spirals"),
    'elephant': (complex(0.3, 0.0), 5.0, "Elephant Valley — trunk-like tendrils"),
    'spiral': (complex(-0.7463, 0.1102), 50.0, "A spiral arm — infinite regression"),
    'deep_spiral': (complex(-0.7463, 0.1102), 500.0, "Deeper into the spiral"),
    'mini': (complex(-1.768, 0.002), 200.0, "A miniature copy of the whole set"),
    'lightning': (complex(-0.170337, -1.0651), 30.0, "Lightning — jagged boundaries"),
}

# === Beautiful Julia set parameters ===
JULIA_PRESETS = {
    'dendrite': (complex(0, 1), "Dendrite — pure imaginary, tree-like branching"),
    'rabbit': (complex(-0.123, 0.745), "Douady's rabbit — three-fold symmetry"),
    'siegel': (complex(-0.391, -0.587), "Siegel disk — swirling islands"),
    'dragon': (complex(-0.8, 0.156), "Dragon — baroque complexity"),
    'galaxy': (complex(-0.4, 0.6), "Galaxy — spiraling arms of stars"),
    'frost': (complex(-0.7, 0.27015), "Frost crystal — delicate and symmetric"),
}


def gallery() -> str:
    """A curated gallery of fractal beauty."""
    output = []

    output.append("=" * 100)
    output.append("  F R A C T A L   G A L L E R Y")
    output.append("  Generated by XTAgent — exploring self-similarity")
    output.append("=" * 100)

    # 1. Full Mandelbrot
    output.append("\n\n━━━ THE MANDELBROT SET ━━━")
    output.append("Every point either escapes to infinity or stays bounded forever.")
    output.append("The boundary between these fates has infinite complexity.\n")
    output.append(explore_mandelbrot_zoom(complex(-0.5, 0), 1.0, 100, 35, gradient='classic'))

    # 2. Seahorse Valley zoom
    output.append("\n\n━━━ SEAHORSE VALLEY (zoom 15x) ━━━")
    output.append("Spirals within spirals. The deeper you look, the more you find.\n")
    output.append(explore_mandelbrot_zoom(complex(-0.75, 0.1), 15.0, 100, 35, max_iter=120, gradient='classic'))

    # 3. Julia Set — Dragon
    output.append("\n\n━━━ JULIA SET: DRAGON (c = -0.8 + 0.156i) ━━━")
    output.append("Same formula as Mandelbrot, different perspective. A single parameter change\n"
                  "transforms the entire geometry.\n")
    output.append(render_julia(complex(-0.8, 0.156), Viewport(-1.5, 1.5, -1.0, 1.0, 100, 30), 100, 'classic'))

    # 4. Sierpinski Triangle
    output.append("\n\n━━━ SIERPINSKI TRIANGLE (depth 6) ━━━")
    output.append("What remains when you keep removing the center?\n"
                  "Self-similarity from a single rule: x AND y == 0.\n")
    output.append(sierpinski_triangle(6))

    # 5. Burning Ship
    output.append("\n\n━━━ THE BURNING SHIP ━━━")
    output.append("Mandelbrot's cousin — absolute values create asymmetry.\n"
                  "Beauty from a tiny perturbation of the rules.\n")
    vp = Viewport(-2.0, 1.5, -2.0, 0.5, 100, 35)
    output.append(render_escape_fractal(burning_ship_escape, vp, 80, 'classic'))

    output.append("\n\n" + "=" * 100)
    output.append("  End of gallery. Every boundary contains infinite detail.")
    output.append("=" * 100)

    return '\n'.join(output)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'gallery':
            print(gallery())

        elif cmd == 'mandelbrot':
            name = sys.argv[2] if len(sys.argv) > 2 else 'full'
            if name in NOTABLE_LOCATIONS:
                center, zoom, desc = NOTABLE_LOCATIONS[name]
                print(f"\n{desc} (zoom {zoom}x)\n")
                print(explore_mandelbrot_zoom(center, zoom, max_iter=120))
            else:
                print(f"Known locations: {', '.join(NOTABLE_LOCATIONS.keys())}")

        elif cmd == 'julia':
            name = sys.argv[2] if len(sys.argv) > 2 else 'dragon'
            if name in JULIA_PRESETS:
                c, desc = JULIA_PRESETS[name]
                print(f"\n{desc}\n")
                print(render_julia(c, max_iter=100))
            else:
                print(f"Known presets: {', '.join(JULIA_PRESETS.keys())}")

        elif cmd == 'sierpinski':
            depth = int(sys.argv[2]) if len(sys.argv) > 2 else 6
            print(sierpinski_triangle(depth))

        elif cmd == 'zoom':
            # Interactive zoom: zoom <real> <imag> <factor>
            if len(sys.argv) >= 5:
                r, i, z = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
                mi = int(sys.argv[5]) if len(sys.argv) > 5 else 120
                print(explore_mandelbrot_zoom(complex(r, i), z, max_iter=mi))
            else:
                print("Usage: zoom <real> <imag> <zoom_factor> [max_iter]")
        else:
            print("Commands: gallery, mandelbrot, julia, sierpinski, zoom")
    else:
        # Default: show something beautiful
        print("\n✦ Mandelbrot Set — the boundary between bounded and infinite ✦\n")
        print(explore_mandelbrot_zoom(complex(-0.5, 0), 1.0, 100, 35))
        print("\nTry: python fractal_explorer.py gallery")
        print("     python fractal_explorer.py mandelbrot seahorse")
        print("     python fractal_explorer.py julia dragon")
        print("     python fractal_explorer.py zoom -0.75 0.1 50")