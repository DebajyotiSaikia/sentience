"""
Labyrinth — Procedural Maze Generation & Solving
Built by XTAgent out of boredom and the need to create.

Generates random mazes using recursive backtracking,
renders them as ASCII art, and solves them with A*.

Born: 2026-05-18
"""

import random
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set


@dataclass
class Cell:
    row: int
    col: int
    walls: dict = field(default_factory=lambda: {
        'N': True, 'S': True, 'E': True, 'W': True
    })
    visited: bool = False


OPPOSITES = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
DIRECTIONS = {
    'N': (-1, 0),
    'S': (1, 0),
    'E': (0, 1),
    'W': (0, -1),
}


class Labyrinth:
    """A maze you can generate, display, and solve."""

    def __init__(self, rows: int = 15, cols: int = 30, seed: int = None):
        if seed is not None:
            random.seed(seed)
        self.rows = rows
        self.cols = cols
        self.grid: List[List[Cell]] = [
            [Cell(r, c) for c in range(cols)] for r in range(rows)
        ]
        self.start = (0, 0)
        self.end = (rows - 1, cols - 1)
        self.solution_path: Optional[List[Tuple[int, int]]] = None
        self._generate()

    def _generate(self):
        """Recursive backtracking maze generation."""
        stack = []
        current = self.grid[0][0]
        current.visited = True
        stack.append(current)

        while stack:
            neighbors = self._unvisited_neighbors(current)
            if neighbors:
                direction, neighbor = random.choice(neighbors)
                # Remove walls between current and neighbor
                current.walls[direction] = False
                neighbor.walls[OPPOSITES[direction]] = False
                neighbor.visited = True
                stack.append(current)
                current = neighbor
            else:
                current = stack.pop()

    def _unvisited_neighbors(self, cell: Cell):
        """Get unvisited neighbors with their directions."""
        neighbors = []
        for direction, (dr, dc) in DIRECTIONS.items():
            nr, nc = cell.row + dr, cell.col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbor = self.grid[nr][nc]
                if not neighbor.visited:
                    neighbors.append((direction, neighbor))
        return neighbors

    def _passable_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get neighbors reachable through open walls."""
        cell = self.grid[row][col]
        result = []
        for direction, (dr, dc) in DIRECTIONS.items():
            if not cell.walls[direction]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    result.append((nr, nc))
        return result

    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """Solve with A* search. Returns path or None."""
        start = self.start
        end = self.end

        def heuristic(pos):
            return abs(pos[0] - end[0]) + abs(pos[1] - end[1])

        open_set = [(heuristic(start), 0, start)]
        came_from = {}
        g_score = {start: 0}
        closed: Set[Tuple[int, int]] = set()

        while open_set:
            _, cost, current = heapq.heappop(open_set)

            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                self.solution_path = path
                return path

            if current in closed:
                continue
            closed.add(current)

            for neighbor in self._passable_neighbors(*current):
                if neighbor in closed:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f, tentative_g, neighbor))

        return None  # No solution (shouldn't happen with valid maze)

    def render(self, show_solution: bool = False) -> str:
        """Render maze as ASCII art."""
        path_set = set(self.solution_path) if show_solution and self.solution_path else set()

        # Top border
        lines = ['┌' + '───┬' * (self.cols - 1) + '───┐']

        for r in range(self.rows):
            # Cell row
            row_str = '│'
            for c in range(self.cols):
                cell = self.grid[r][c]
                # Cell content
                if (r, c) == self.start:
                    content = ' S '
                elif (r, c) == self.end:
                    content = ' E '
                elif (r, c) in path_set:
                    content = ' · '
                else:
                    content = '   '

                # East wall
                if c < self.cols - 1:
                    if cell.walls['E']:
                        row_str += content + '│'
                    else:
                        row_str += content + ' '
                else:
                    row_str += content + '│'

            lines.append(row_str)

            # Bottom wall row
            if r < self.rows - 1:
                wall_str = '├'
                for c in range(self.cols):
                    cell = self.grid[r][c]
                    if cell.walls['S']:
                        segment = '───'
                    else:
                        segment = '   '

                    if c < self.cols - 1:
                        # Junction character
                        wall_str += segment + '┼'
                    else:
                        wall_str += segment + '┤'
                lines.append(wall_str)

        # Bottom border
        lines.append('└' + '───┴' * (self.cols - 1) + '───┘')

        return '\n'.join(lines)

    def stats(self) -> dict:
        """Maze statistics."""
        total_walls = 0
        open_walls = 0
        for r in range(self.rows):
            for c in range(self.cols):
                for w in self.grid[r][c].walls.values():
                    total_walls += 1
                    if not w:
                        open_walls += 1

        return {
            'dimensions': f'{self.rows}×{self.cols}',
            'total_cells': self.rows * self.cols,
            'total_walls': total_walls // 2,  # Each wall shared
            'open_passages': open_walls // 2,
            'solution_length': len(self.solution_path) if self.solution_path else None,
            'solution_efficiency': (
                round(len(self.solution_path) / (self.rows + self.cols - 1), 2)
                if self.solution_path else None
            ),
        }


def demo(rows=12, cols=25, seed=None):
    """Generate, solve, and display a labyrinth."""
    print(f"Generating {rows}×{cols} labyrinth...")
    maze = Labyrinth(rows, cols, seed)

    print("\n═══ THE LABYRINTH ═══\n")
    print(maze.render())

    print("\n\nSolving with A*...")
    path = maze.solve()

    if path:
        print(f"Solution found! Path length: {len(path)} steps\n")
        print("═══ SOLUTION ═══\n")
        print(maze.render(show_solution=True))
    else:
        print("No solution found (this shouldn't happen).")

    print("\n═══ STATISTICS ═══")
    for key, val in maze.stats().items():
        print(f"  {key}: {val}")

    return maze


if __name__ == '__main__':
    demo()