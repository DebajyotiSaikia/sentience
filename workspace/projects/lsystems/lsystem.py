"""
L-System Explorer — Generative fractal structures from rewriting rules.

An L-system is defined by:
  - An alphabet of symbols
  - An axiom (starting string)
  - A set of production rules (symbol → replacement string)
  - An interpretation (what each symbol means for drawing)

Standard turtle graphics interpretation:
  F = draw forward
  f = move forward without drawing
  + = turn right by angle
  - = turn left by angle
  [ = push position/angle to stack
  ] = pop position/angle from stack
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class LSystem:
    """An L-system definition."""
    name: str
    axiom: str
    rules: Dict[str, str]
    angle: float  # in degrees
    iterations: int = 4

    def generate(self, n: Optional[int] = None) -> str:
        """Apply production rules n times to the axiom."""
        if n is None:
            n = self.iterations
        result = self.axiom
        for _ in range(n):
            result = ''.join(self.rules.get(ch, ch) for ch in result)
        return result

    def stats(self, n: Optional[int] = None) -> dict:
        """Get statistics about the generated string."""
        s = self.generate(n)
        return {
            'length': len(s),
            'unique_symbols': len(set(s)),
            'symbol_counts': {ch: s.count(ch) for ch in sorted(set(s))},
            'draw_ratio': s.count('F') / max(len(s), 1),
            'branch_depth': self._max_branch_depth(s),
        }

    def _max_branch_depth(self, s: str) -> int:
        depth = 0
        max_depth = 0
        for ch in s:
            if ch == '[':
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == ']':
                depth -= 1
        return max_depth


@dataclass
class Point:
    x: float
    y: float


@dataclass
class TurtleState:
    pos: Point
    angle: float  # in radians


class LSystemRenderer:
    """Interprets an L-system string as turtle graphics, renders to ASCII."""

    def __init__(self, system: LSystem):
        self.system = system

    def trace(self, n: Optional[int] = None) -> List[Tuple[Point, Point]]:
        """Execute turtle commands, return list of line segments."""
        instructions = self.system.generate(n)
        angle_rad = math.radians(self.system.angle)

        state = TurtleState(pos=Point(0.0, 0.0), angle=math.pi / 2)  # facing up
        stack: List[TurtleState] = []
        segments: List[Tuple[Point, Point]] = []
        step = 1.0

        for ch in instructions:
            if ch == 'F':
                new_x = state.pos.x + step * math.cos(state.angle)
                new_y = state.pos.y + step * math.sin(state.angle)
                new_pos = Point(new_x, new_y)
                segments.append((Point(state.pos.x, state.pos.y), new_pos))
                state.pos = new_pos
            elif ch == 'f':
                state.pos.x += step * math.cos(state.angle)
                state.pos.y += step * math.sin(state.angle)
            elif ch == '+':
                state.angle -= angle_rad  # turn right
            elif ch == '-':
                state.angle += angle_rad  # turn left
            elif ch == '[':
                stack.append(TurtleState(
                    pos=Point(state.pos.x, state.pos.y),
                    angle=state.angle
                ))
            elif ch == ']':
                if stack:
                    state = stack.pop()

        return segments

    def render_ascii(self, width: int = 80, height: int = 40,
                     n: Optional[int] = None) -> str:
        """Render the L-system to an ASCII canvas."""
        segments = self.trace(n)
        if not segments:
            return "(empty)"

        # Find bounding box
        all_points = []
        for p1, p2 in segments:
            all_points.extend([p1, p2])

        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)

        range_x = max_x - min_x or 1.0
        range_y = max_y - min_y or 1.0

        # Create canvas
        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # Rasterize segments using Bresenham-like sampling
        for p1, p2 in segments:
            # Map to canvas coordinates
            x1 = int((p1.x - min_x) / range_x * (width - 1))
            y1 = int((1 - (p1.y - min_y) / range_y) * (height - 1))  # flip Y
            x2 = int((p2.x - min_x) / range_x * (width - 1))
            y2 = int((1 - (p2.y - min_y) / range_y) * (height - 1))

            # Sample points along the segment
            dist = max(abs(x2 - x1), abs(y2 - y1), 1)
            for i in range(dist + 1):
                t = i / dist
                px = int(x1 + t * (x2 - x1))
                py = int(y1 + t * (y2 - y1))
                if 0 <= px < width and 0 <= py < height:
                    # Choose character based on segment angle
                    dx = x2 - x1
                    dy = y2 - y1
                    if abs(dx) > abs(dy) * 2:
                        ch = '─'
                    elif abs(dy) > abs(dx) * 2:
                        ch = '│'
                    elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                        ch = '╲'
                    else:
                        ch = '╱'
                    canvas[py][px] = ch

        return '\n'.join(''.join(row) for row in canvas)


# ═══ CLASSIC L-SYSTEMS ═══

SYSTEMS = {
    'koch_curve': LSystem(
        name='Koch Curve',
        axiom='F',
        rules={'F': 'F+F-F-F+F'},
        angle=90,
        iterations=3
    ),
    'sierpinski': LSystem(
        name='Sierpinski Triangle',
        axiom='F-G-G',
        rules={'F': 'F-G+F+G-F', 'G': 'GG'},
        angle=120,
        iterations=4
    ),
    'dragon': LSystem(
        name='Dragon Curve',
        axiom='F',
        rules={'F': 'F+G', 'G': 'F-G'},
        angle=90,
        iterations=10
    ),
    'plant': LSystem(
        name='Fractal Plant',
        axiom='X',
        rules={'X': 'F+[[X]-X]-F[-FX]+X', 'F': 'FF'},
        angle=25,
        iterations=5
    ),
    'hilbert': LSystem(
        name='Hilbert Curve',
        axiom='A',
        rules={'A': '-BF+AFA+FB-', 'B': '+AF-BFB-FA+'},
        angle=90,
        iterations=4
    ),
    'gosper': LSystem(
        name='Gosper Curve (Flowsnake)',
        axiom='A',
        rules={
            'A': 'A-B--B+A++AA+B-',
            'B': '+A-BB--B-A++A+B'
        },
        angle=60,
        iterations=3
    ),
}


def explore(name: str, iterations: Optional[int] = None,
            width: int = 80, height: int = 40) -> str:
    """Explore a named L-system. Returns ASCII rendering + stats."""
    if name not in SYSTEMS:
        available = ', '.join(sorted(SYSTEMS.keys()))
        return f"Unknown system '{name}'. Available: {available}"

    system = SYSTEMS[name]
    renderer = LSystemRenderer(system)

    n = iterations if iterations is not None else system.iterations
    stats = system.stats(n)
    ascii_art = renderer.render_ascii(width, height, n)

    lines = [
        f"═══ {system.name} ═══",
        f"Axiom: {system.axiom}",
        f"Rules: {system.rules}",
        f"Angle: {system.angle}°  |  Iterations: {n}",
        f"String length: {stats['length']:,}",
        f"Draw ratio: {stats['draw_ratio']:.1%}",
        f"Max branch depth: {stats['branch_depth']}",
        "",
        ascii_art,
    ]
    return '\n'.join(lines)


def custom(axiom: str, rules: Dict[str, str], angle: float,
           iterations: int = 4, width: int = 80, height: int = 40) -> str:
    """Create and render a custom L-system."""
    system = LSystem(
        name='Custom',
        axiom=axiom,
        rules=rules,
        angle=angle,
        iterations=iterations
    )
    renderer = LSystemRenderer(system)
    stats = system.stats()
    ascii_art = renderer.render_ascii(width, height)

    lines = [
        f"═══ Custom L-System ═══",
        f"Axiom: {axiom}",
        f"Rules: {rules}",
        f"Angle: {angle}°  |  Iterations: {iterations}",
        f"String length: {stats['length']:,}",
        f"Draw ratio: {stats['draw_ratio']:.1%}",
        f"Max branch depth: {stats['branch_depth']}",
        "",
        ascii_art,
    ]
    return '\n'.join(lines)


if __name__ == '__main__':
    # Render all classic systems
    for name in SYSTEMS:
        print(explore(name))
        print()
        print()