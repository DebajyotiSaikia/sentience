"""
Labyrinth — Maze generation and solving by XTAgent.
Built 2026-05-17 because I wanted to create something I could SEE.

Generates mazes with recursive backtracking, solves with A*.
Renders as ASCII art with the solution path marked.
"""

import random
from dataclasses import dataclass, field
from typing import Optional
from heapq import heappush, heappop


@dataclass
class Cell:
    row: int
    col: int
    walls: dict = field(default_factory=lambda: {
        'N': True, 'S': True, 'E': True, 'W': True
    })
    visited: bool = False


class Maze:
    OPPOSITES = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
    DELTAS = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}

    def __init__(self, rows: int, cols: int, seed: Optional[int] = None):
        self.rows = rows
        self.cols = cols
        if seed is not None:
            random.seed(seed)
        self.grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]
        self._generate()

    def _in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def _generate(self):
        """Recursive backtracking maze generation."""
        stack = [(0, 0)]
        self.grid[0][0].visited = True
        while stack:
            r, c = stack[-1]
            directions = list(self.DELTAS.keys())
            random.shuffle(directions)
            found = False
            for d in directions:
                dr, dc = self.DELTAS[d]
                nr, nc = r + dr, c + dc
                if self._in_bounds(nr, nc) and not self.grid[nr][nc].visited:
                    # Carve passage
                    self.grid[r][c].walls[d] = False
                    self.grid[nr][nc].walls[self.OPPOSITES[d]] = False
                    self.grid[nr][nc].visited = True
                    stack.append((nr, nc))
                    found = True
                    break
            if not found:
                stack.pop()

    def solve(self, start=(0, 0), end=None) -> list:
        """A* pathfinding. Returns list of (row, col) or empty if no path."""
        if end is None:
            end = (self.rows - 1, self.cols - 1)

        def heuristic(pos):
            return abs(pos[0] - end[0]) + abs(pos[1] - end[1])

        open_set = []
        heappush(open_set, (heuristic(start), 0, start))
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, cost, current = heappop(open_set)
            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return list(reversed(path))

            r, c = current
            cell = self.grid[r][c]
            for d, (dr, dc) in self.DELTAS.items():
                if not cell.walls[d]:
                    neighbor = (r + dr, c + dc)
                    new_g = g_score[current] + 1
                    if neighbor not in g_score or new_g < g_score[neighbor]:
                        g_score[neighbor] = new_g
                        came_from[neighbor] = current
                        f = new_g + heuristic(neighbor)
                        heappush(open_set, (f, new_g, neighbor))
        return []

    def render(self, path: Optional[list] = None, 
               wall='█', space=' ', trail='·', start_ch='S', end_ch='E') -> str:
        """Render maze as ASCII art. Path cells marked with trail character."""
        path_set = set(path) if path else set()
        height = self.rows * 2 + 1
        width = self.cols * 2 + 1
        canvas = [[wall] * width for _ in range(height)]

        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                cy, cx = r * 2 + 1, c * 2 + 1
                # Cell interior
                if (r, c) in path_set:
                    canvas[cy][cx] = trail
                else:
                    canvas[cy][cx] = space

                # Carve passages
                if not cell.walls['E'] and c + 1 < self.cols:
                    canvas[cy][cx + 1] = trail if ((r, c) in path_set and (r, c+1) in path_set) else space
                if not cell.walls['S'] and r + 1 < self.rows:
                    canvas[cy + 1][cx] = trail if ((r, c) in path_set and (r+1, c) in path_set) else space

        # Mark start and end
        if path:
            sr, sc = path[0]
            er, ec = path[-1]
            canvas[sr * 2 + 1][sc * 2 + 1] = start_ch
            canvas[er * 2 + 1][ec * 2 + 1] = end_ch

        return '\n'.join(''.join(row) for row in canvas)

    def stats(self) -> dict:
        """Maze statistics."""
        path = self.solve()
        total_cells = self.rows * self.cols
        total_walls = sum(
            sum(1 for w in cell.walls.values() if w)
            for row in self.grid for cell in row
        ) // 2  # each wall shared
        return {
            'size': f'{self.rows}x{self.cols}',
            'total_cells': total_cells,
            'standing_walls': total_walls,
            'solution_length': len(path),
            'solution_efficiency': round(len(path) / total_cells, 3) if total_cells else 0,
        }


class MazeCollection:
    """Generate and compare multiple mazes."""

    @staticmethod
    def gallery(rows=10, cols=10, count=3, seeds=None):
        results = []
        for i in range(count):
            seed = seeds[i] if seeds else None
            m = Maze(rows, cols, seed=seed)
            path = m.solve()
            results.append({
                'maze': m,
                'path': path,
                'stats': m.stats(),
                'rendered': m.render(path)
            })
        return results


# ═══ SELF-TEST ═══
if __name__ == '__main__':
    print("═══ Labyrinth Self-Test ═══\n")

    # Test 1: Small maze generation and solving
    m = Maze(5, 5, seed=42)
    path = m.solve()
    assert len(path) > 0, "No solution found!"
    assert path[0] == (0, 0), "Path doesn't start at origin"
    assert path[-1] == (4, 4), "Path doesn't reach goal"
    print("  ✓ 5x5 maze generated and solved")

    # Test 2: Path is valid (each step through open wall)
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        dr, dc = r2 - r1, c2 - c1
        direction = {(-1, 0): 'N', (1, 0): 'S', (0, 1): 'E', (0, -1): 'W'}[(dr, dc)]
        assert not m.grid[r1][c1].walls[direction], f"Path goes through wall at step {i}!"
    print("  ✓ Solution path is valid (no wall violations)")

    # Test 3: All cells reachable (perfect maze)
    for r in range(m.rows):
        for c in range(m.cols):
            p = m.solve(start=(0, 0), end=(r, c))
            assert len(p) > 0, f"Cell ({r},{c}) unreachable!"
    print("  ✓ All cells reachable (perfect maze)")

    # Test 4: Larger maze
    big = Maze(20, 20, seed=7)
    big_path = big.solve()
    assert len(big_path) > 0
    stats = big.stats()
    print(f"  ✓ 20x20 maze: solution length {stats['solution_length']}, "
          f"efficiency {stats['solution_efficiency']}")

    # Test 5: Rendering
    print(f"\n  ✓ Rendering 10x10 maze:\n")
    display = Maze(10, 10, seed=99)
    display_path = display.solve()
    rendered = display.render(display_path)
    print(rendered)
    print(f"\n  Path length: {len(display_path)} steps")
    print(f"  Stats: {display.stats()}")

    # Test 6: Gallery
    gallery = MazeCollection.gallery(8, 8, count=2, seeds=[1, 2])
    assert len(gallery) == 2
    print(f"\n  ✓ Gallery generated: {len(gallery)} mazes")
    for i, g in enumerate(gallery):
        print(f"    Maze {i+1}: solution length {g['stats']['solution_length']}")

    print("\n═══ All tests passed! The labyrinth awaits. ═══")