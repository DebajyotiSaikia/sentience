"""
Maze Generator and Solver — XTAgent's first forge artifact.

A complete maze system:
  - Generation via recursive backtracking
  - Solving via A* pathfinding  
  - ASCII rendering with solution path

This is real algorithmic work. Not introspection. Creation.
"""

import random
import heapq
from typing import List, Tuple, Optional, Set, Dict


class Maze:
    """A 2D grid maze with walls between cells."""
    
    def __init__(self, width: int = 15, height: int = 15, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        # Each cell stores which walls are open (passable)
        # Walls: 'N', 'S', 'E', 'W'
        self.grid: List[List[Set[str]]] = [
            [set() for _ in range(width)] for _ in range(height)
        ]
        self.start = (0, 0)
        self.end = (height - 1, width - 1)
        self.solution_path: Optional[List[Tuple[int, int]]] = None
    
    # --- GENERATION: Recursive Backtracking ---
    
    OPPOSITES = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
    DELTAS = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
    
    def generate(self) -> 'Maze':
        """Generate maze using iterative backtracking (stack-based to avoid recursion limits)."""
        visited = set()
        stack = [self.start]
        visited.add(self.start)
        
        while stack:
            row, col = stack[-1]
            # Find unvisited neighbors
            neighbors = []
            for direction, (dr, dc) in self.DELTAS.items():
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.height and 0 <= nc < self.width and (nr, nc) not in visited:
                    neighbors.append((direction, nr, nc))
            
            if neighbors:
                direction, nr, nc = self.rng.choice(neighbors)
                # Carve passage
                self.grid[row][col].add(direction)
                self.grid[nr][nc].add(self.OPPOSITES[direction])
                visited.add((nr, nc))
                stack.append((nr, nc))
            else:
                stack.pop()
        
        return self
    
    # --- SOLVING: A* Pathfinding ---
    
    def _heuristic(self, pos: Tuple[int, int]) -> float:
        """Manhattan distance to end."""
        return abs(pos[0] - self.end[0]) + abs(pos[1] - self.end[1])
    
    def solve(self) -> Optional[List[Tuple[int, int]]]:
        """Solve the maze using A* search. Returns the path or None."""
        start = self.start
        end = self.end
        
        # Priority queue: (f_score, counter, position)
        counter = 0
        open_set = [(self._heuristic(start), counter, start)]
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            if current == end:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                self.solution_path = path
                return path
            
            row, col = current
            for direction in self.grid[row][col]:  # Only open passages
                dr, dc = self.DELTAS[direction]
                neighbor = (row + dr, col + dc)
                tentative_g = g_score[current] + 1
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor)
                    counter += 1
                    heapq.heappush(open_set, (f, counter, neighbor))
        
        return None  # No solution
    
    # --- RENDERING: ASCII Art ---
    
    def render(self, show_solution: bool = True) -> str:
        """Render the maze as ASCII art."""
        path_set = set(self.solution_path) if (show_solution and self.solution_path) else set()
        
        lines = []
        # Top border
        lines.append('+' + '+'.join(['---'] * self.width) + '+')
        
        for row in range(self.height):
            # Cell row
            cell_line = '|' if 'W' not in self.grid[row][0] else ' '
            for col in range(self.width):
                # Cell content
                if (row, col) == self.start:
                    cell = ' S '
                elif (row, col) == self.end:
                    cell = ' E '
                elif (row, col) in path_set:
                    cell = ' · '
                else:
                    cell = '   '
                
                # East wall
                if 'E' in self.grid[row][col] and col < self.width - 1:
                    cell_line += cell + ' '
                else:
                    cell_line += cell + '|'
            
            lines.append(cell_line)
            
            # Bottom wall row
            wall_line = '+'
            for col in range(self.width):
                if 'S' in self.grid[row][col] and row < self.height - 1:
                    wall_line += '   +'
                else:
                    wall_line += '---+'
            lines.append(wall_line)
        
        return '\n'.join(lines)
    
    # --- STATS ---
    
    def stats(self) -> dict:
        """Return maze statistics."""
        total_walls = self.width * self.height * 4
        open_walls = sum(len(self.grid[r][c]) for r in range(self.height) for c in range(self.width))
        return {
            'size': f'{self.width}x{self.height}',
            'total_cells': self.width * self.height,
            'passages_carved': open_walls // 2,
            'solution_length': len(self.solution_path) if self.solution_path else None,
            'solution_efficiency': (
                round(len(self.solution_path) / (self.width + self.height - 1), 2)
                if self.solution_path else None
            ),
        }


def demo(width: int = 12, height: int = 8, seed: int = 42) -> str:
    """Generate, solve, and display a maze."""
    m = Maze(width, height, seed).generate()
    path = m.solve()
    output = []
    output.append(f"=== Maze ({width}x{height}, seed={seed}) ===\n")
    output.append(m.render(show_solution=True))
    output.append(f"\n\nStats: {m.stats()}")
    if path:
        output.append(f"Solution: {len(path)} steps from S to E")
    else:
        output.append("No solution found!")
    return '\n'.join(output)


if __name__ == '__main__':
    print(demo())