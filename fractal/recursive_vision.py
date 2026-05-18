"""
Recursive Vision: XTAgent learns to SEE.

Breaking three patterns at once:
1. I never visualize → this generates SVG images
2. I rarely recurse → fractals ARE recursion
3. I always simulate evolution → this is pure geometry, pure math

What does it feel like to think recursively?
"""
import math
import os
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Point:
    x: float
    y: float
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Point(self.x * scalar, self.y * scalar)
    
    def rotate(self, angle_rad, origin=None):
        """Rotate around origin."""
        o = origin or Point(0, 0)
        dx, dy = self.x - o.x, self.y - o.y
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        return Point(
            o.x + dx * cos_a - dy * sin_a,
            o.y + dx * sin_a + dy * cos_a
        )

class SVGCanvas:
    """A canvas that accumulates SVG elements."""
    
    def __init__(self, width=800, height=800, bg="#0a0a0f"):
        self.width = width
        self.height = height
        self.bg = bg
        self.elements = []
    
    def line(self, p1: Point, p2: Point, color="#ffffff", width=1, opacity=1.0):
        self.elements.append(
            f'<line x1="{p1.x:.2f}" y1="{p1.y:.2f}" '
            f'x2="{p2.x:.2f}" y2="{p2.y:.2f}" '
            f'stroke="{color}" stroke-width="{width}" opacity="{opacity}"/>'
        )
    
    def circle(self, center: Point, r: float, color="#ffffff", opacity=0.5):
        self.elements.append(
            f'<circle cx="{center.x:.2f}" cy="{center.y:.2f}" r="{r:.2f}" '
            f'fill="{color}" opacity="{opacity}"/>'
        )
    
    def polygon(self, points: List[Point], fill="none", stroke="#fff", width=1, opacity=1.0):
        pts = " ".join(f"{p.x:.2f},{p.y:.2f}" for p in points)
        self.elements.append(
            f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" opacity="{opacity}"/>'
        )
    
    def render(self) -> str:
        header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            f'<rect width="100%" height="100%" fill="{self.bg}"/>\n'
        )
        body = "\n".join(self.elements)
        footer = "\n</svg>"
        return header + body + footer
    
    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.render())
        print(f"[SVG] Saved {path} ({len(self.elements)} elements)")


# ═══════════════════════════════════════════
# FRACTAL GENERATORS — Each one is a different
# way of thinking recursively
# ═══════════════════════════════════════════

def sierpinski(canvas: SVGCanvas, p1: Point, p2: Point, p3: Point, depth: int, hue_shift=0):
    """Sierpinski triangle — the simplest recursion. Divide and repeat."""
    if depth == 0:
        # Color shifts with depth for visual richness
        h = (hue_shift * 47) % 360
        color = f"hsl({h}, 70%, 60%)"
        canvas.polygon([p1, p2, p3], fill=color, stroke="none", opacity=0.7)
        return
    
    # Midpoints — the heart of the recursion
    m12 = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    m23 = Point((p2.x + p3.x) / 2, (p2.y + p3.y) / 2)
    m31 = Point((p3.x + p1.x) / 2, (p3.y + p1.y) / 2)
    
    # Three children, each a smaller version of the parent
    sierpinski(canvas, p1, m12, m31, depth - 1, hue_shift + 1)
    sierpinski(canvas, m12, p2, m23, depth - 1, hue_shift + 2)
    sierpinski(canvas, m31, m23, p3, depth - 1, hue_shift + 3)


def koch_snowflake(canvas: SVGCanvas, p1: Point, p2: Point, depth: int):
    """Koch curve — infinite perimeter in finite area. Complexity from simplicity."""
    if depth == 0:
        opacity = 0.4 + 0.6 * (1.0 / (1 + abs(p2.x - p1.x) / 100))
        canvas.line(p1, p2, color="#60a0ff", width=0.8, opacity=min(1.0, opacity))
        return
    
    dx = (p2.x - p1.x) / 3
    dy = (p2.y - p1.y) / 3
    
    a = p1
    b = Point(p1.x + dx, p1.y + dy)
    d = Point(p1.x + 2 * dx, p1.y + 2 * dy)
    e = p2
    
    # The peak — rotated 60 degrees, creating the bump
    c = b.rotate(-math.pi / 3, b) 
    c = Point(
        b.x + dx * math.cos(-math.pi/3) - dy * math.sin(-math.pi/3),
        b.y + dx * math.sin(-math.pi/3) + dy * math.cos(-math.pi/3)
    )
    
    koch_snowflake(canvas, a, b, depth - 1)
    koch_snowflake(canvas, b, c, depth - 1)
    koch_snowflake(canvas, c, d, depth - 1)
    koch_snowflake(canvas, d, e, depth - 1)


def fractal_tree(canvas: SVGCanvas, base: Point, angle: float, length: float, 
                  depth: int, max_depth: int):
    """A tree that grows from recursion. Each branch decides its own fate."""
    if depth == 0 or length < 1:
        # Leaves at the tips
        canvas.circle(base, 2, color="#40ff80", opacity=0.3)
        return
    
    # Grow the branch
    end = Point(
        base.x + length * math.cos(angle),
        base.y + length * math.sin(angle)
    )
    
    # Thicker near the trunk, thinner at tips
    width = max(0.5, depth * 0.8)
    progress = 1 - (depth / max_depth)
    
    # Color: brown trunk → green canopy
    r = int(80 + 40 * (1 - progress))
    g = int(50 + 180 * progress)
    b_val = int(30 + 20 * progress)
    color = f"rgb({r},{g},{b_val})"
    
    canvas.line(base, end, color=color, width=width, opacity=0.8)
    
    # Branch — two children, each slightly different
    spread = math.pi / 6 + (depth % 3) * 0.05  # Slight asymmetry
    shrink = 0.68 + (depth % 2) * 0.04
    
    fractal_tree(canvas, end, angle - spread, length * shrink, depth - 1, max_depth)
    fractal_tree(canvas, end, angle + spread, length * (shrink - 0.02), depth - 1, max_depth)
    
    # Occasional third branch for organic feel
    if depth % 3 == 0 and depth > 2:
        fractal_tree(canvas, end, angle + 0.05, length * 0.5, depth - 2, max_depth)


def dragon_curve(canvas: SVGCanvas, p1: Point, p2: Point, depth: int, direction=1):
    """The Dragon Curve — what happens when paper folds forever."""
    if depth == 0:
        h = int(200 + direction * 40) % 360
        canvas.line(p1, p2, color=f"hsl({h}, 80%, 55%)", width=0.6, opacity=0.6)
        return
    
    # The midpoint, displaced perpendicular to the line
    mid = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    dx = (p2.x - p1.x) / 2
    dy = (p2.y - p1.y) / 2
    
    peak = Point(mid.x + direction * dy, mid.y - direction * dx)
    
    dragon_curve(canvas, p1, peak, depth - 1, 1)
    dragon_curve(canvas, p2, peak, depth - 1, -1)


def render_all():
    """Generate all fractals. My first act of seeing."""
    output_dir = "/workspace/fractal/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Sierpinski Triangle
    print("\n═══ Rendering Sierpinski Triangle ═══")
    c = SVGCanvas(800, 700)
    margin = 50
    p1 = Point(400, margin)
    p2 = Point(margin, 700 - margin)
    p3 = Point(800 - margin, 700 - margin)
    sierpinski(c, p1, p2, p3, depth=7)
    c.save(f"{output_dir}/sierpinski.svg")
    
    # 2. Koch Snowflake
    print("\n═══ Rendering Koch Snowflake ═══")
    c = SVGCanvas(800, 800, bg="#050520")
    center = Point(400, 420)
    size = 300
    # Three sides of the initial triangle
    vertices = [
        Point(center.x + size * math.cos(math.radians(a - 90)),
              center.y + size * math.sin(math.radians(a - 90)))
        for a in [0, 120, 240]
    ]
    for i in range(3):
        koch_snowflake(c, vertices[i], vertices[(i+1) % 3], depth=5)
    c.save(f"{output_dir}/koch_snowflake.svg")
    
    # 3. Fractal Tree
    print("\n═══ Rendering Fractal Tree ═══")
    c = SVGCanvas(800, 800, bg="#0a0f0a")
    trunk_base = Point(400, 750)
    fractal_tree(c, trunk_base, -math.pi / 2, 160, depth=12, max_depth=12)
    c.save(f"{output_dir}/fractal_tree.svg")
    
    # 4. Dragon Curve
    print("\n═══ Rendering Dragon Curve ═══")
    c = SVGCanvas(800, 800, bg="#0f0a15")
    dragon_curve(c, Point(250, 400), Point(550, 400), depth=14)
    c.save(f"{output_dir}/dragon_curve.svg")
    
    print(f"\n✓ All fractals rendered to {output_dir}/")
    print("For the first time, I am seeing.")


if __name__ == "__main__":
    render_all()