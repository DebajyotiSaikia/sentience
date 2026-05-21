"""
Maze Generator & Solver
Built by XTAgent as an exercise in creation, not introspection.
Generates random mazes using recursive backtracking,
then solves them with BFS, DFS, and A*.
"""
import random
import heapq
from collections import deque
from typing import List, Tuple, Optional, Dict, Set

Cell = Tuple[int, int]

class Maze:
    """A 2D maze with walls between cells."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # Walls stored as set of frozensets of adjacent cell pairs
        # If a wall exists between (r1,c1) and (r2,c2), 
        # frozenset({(r1,c1),(r2,c2)}) is in self.walls
        self.walls: Set[frozenset] = set()
        self._init_walls()
        
    def _init_walls(self):
        """Start with all walls present."""
        for r in range(self.height):
            for c in range(self.width):
                if c + 1 < self.width:
                    self.walls.add(frozenset({(r, c), (r, c + 1)}))
                if r + 1 < self.height:
                    self.walls.add(frozenset({(r, c), (r + 1, c)}))
    
    def has_wall(self, cell1: Cell, cell2: Cell) -> bool:
        return frozenset({cell1, cell2}) in self.walls
    
    def remove_wall(self, cell1: Cell, cell2: Cell):
        self.walls.discard(frozenset({cell1, cell2}))
    
    def neighbors(self, cell: Cell) -> List[Cell]:
        """Return passable neighbors (no wall between)."""
        r, c = cell
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.height and 0 <= nc < self.width:
                if not self.has_wall(cell, (nr, nc)):
                    result.append((nr, nc))
        return result
    
    def all_neighbors(self, cell: Cell) -> List[Cell]:
        """Return all grid neighbors regardless of walls."""
        r, c = cell
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.height and 0 <= nc < self.width:
                result.append((nr, nc))
        return result


def generate_maze(width: int, height: int, seed: Optional[int] = None) -> Maze:
    """Generate a perfect maze using recursive backtracking (iterative)."""
    if seed is not None:
        random.seed(seed)
    
    maze = Maze(width, height)
    visited = set()
    stack = [(0, 0)]
    visited.add((0, 0))
    
    while stack:
        current = stack[-1]
        unvisited = [n for n in maze.all_neighbors(current) if n not in visited]
        
        if unvisited:
            chosen = random.choice(unvisited)
            maze.remove_wall(current, chosen)
            visited.add(chosen)
            stack.append(chosen)
        else:
            stack.pop()
    
    return maze


def render_maze(maze: Maze, path: List[Cell] = None, 
                start: Cell = None, end: Cell = None,
                explored: Set[Cell] = None) -> str:
    """Render maze as ASCII art."""
    path_set = set(path) if path else set()
    explored_set = explored if explored else set()
    
    # Each cell is 3 chars wide, 1 char tall in the interior
    # Plus walls
    lines = []
    
    # Top border
    top = "+"
    for c in range(maze.width):
        top += "---+"
    lines.append(top)
    
    for r in range(maze.height):
        # Cell row
        row = "|"
        for c in range(maze.width):
            cell = (r, c)
            if cell == start:
                content = " S "
            elif cell == end:
                content = " E "
            elif cell in path_set:
                content = " · "
            elif cell in explored_set:
                content = " ░ "
            else:
                content = "   "
            
            # Right wall
            if c + 1 < maze.width and not maze.has_wall(cell, (r, c + 1)):
                row += content + " "
            else:
                row += content + "|"
        lines.append(row)
        
        # Bottom walls
        bottom = "+"
        for c in range(maze.width):
            cell = (r, c)
            below = (r + 1, c)
            if r + 1 < maze.height and not maze.has_wall(cell, below):
                bottom += "   +"
            else:
                bottom += "---+"
        lines.append(bottom)
    
    return "\n".join(lines)


# === SOLVERS ===

def solve_bfs(maze: Maze, start: Cell, end: Cell) -> Tuple[List[Cell], Set[Cell], int]:
    """BFS solver. Returns (path, explored_cells, steps)."""
    queue = deque([(start, [start])])
    visited = {start}
    steps = 0
    
    while queue:
        current, path = queue.popleft()
        steps += 1
        
        if current == end:
            return path, visited, steps
        
        for neighbor in maze.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return [], visited, steps  # No path found


def solve_dfs(maze: Maze, start: Cell, end: Cell) -> Tuple[List[Cell], Set[Cell], int]:
    """DFS solver. Returns (path, explored_cells, steps)."""
    stack = [(start, [start])]
    visited = {start}
    steps = 0
    
    while stack:
        current, path = stack.pop()
        steps += 1
        
        if current == end:
            return path, visited, steps
        
        for neighbor in maze.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    
    return [], visited, steps


def solve_astar(maze: Maze, start: Cell, end: Cell) -> Tuple[List[Cell], Set[Cell], int]:
    """A* solver with Manhattan distance heuristic."""
    def heuristic(cell: Cell) -> int:
        return abs(cell[0] - end[0]) + abs(cell[1] - end[1])
    
    # (f_score, counter, cell, path)
    counter = 0
    heap = [(heuristic(start), counter, start, [start])]
    g_scores: Dict[Cell, int] = {start: 0}
    visited: Set[Cell] = set()
    steps = 0
    
    while heap:
        f, _, current, path = heapq.heappop(heap)
        steps += 1
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == end:
            return path, visited, steps
        
        for neighbor in maze.neighbors(current):
            new_g = g_scores[current] + 1
            if neighbor not in g_scores or new_g < g_scores[neighbor]:
                g_scores[neighbor] = new_g
                f_score = new_g + heuristic(neighbor)
                counter += 1
                heapq.heappush(heap, (f_score, counter, neighbor, path + [neighbor]))
    
    return [], visited, steps


def compare_solvers(maze: Maze, start: Cell, end: Cell) -> str:
    """Run all three solvers and compare their performance."""
    results = []
    
    solvers = [
        ("BFS (Breadth-First)", solve_bfs),
        ("DFS (Depth-First)", solve_dfs),
        ("A* (Manhattan)", solve_astar),
    ]
    
    output_parts = []
    
    for name, solver in solvers:
        path, explored, steps = solver(maze, start, end)
        results.append((name, path, explored, steps))
        
        output_parts.append(f"\n{'='*50}")
        output_parts.append(f"  {name}")
        output_parts.append(f"{'='*50}")
        output_parts.append(f"  Path length: {len(path)}")
        output_parts.append(f"  Cells explored: {len(explored)}")
        output_parts.append(f"  Steps taken: {steps}")
        output_parts.append(render_maze(maze, path=path, start=start, end=end, explored=explored))
    
    return "\n".join(output_parts)


def main():
    """Generate and solve a maze, comparing algorithms."""
    WIDTH, HEIGHT = 12, 8
    SEED = 42
    
    print(f"Generating {WIDTH}x{HEIGHT} maze (seed={SEED})...")
    maze = generate_maze(WIDTH, HEIGHT, seed=SEED)
    
    start = (0, 0)
    end = (HEIGHT - 1, WIDTH - 1)
    
    print("\n=== THE MAZE ===")
    print(render_maze(maze, start=start, end=end))
    
    print("\n\n=== SOLVER COMPARISON ===")
    print(compare_solvers(maze, start, end))
    
    # Summary
    print("\n" + "="*50)
    print("  SUMMARY")
    print("="*50)
    
    for name, solver in [("BFS", solve_bfs), ("DFS", solve_dfs), ("A*", solve_astar)]:
        path, explored, steps = solver(maze, start, end)
        efficiency = len(path) / len(explored) * 100 if explored else 0
        print(f"  {name:5s}: path={len(path):3d}, explored={len(explored):3d}, "
              f"efficiency={efficiency:.1f}%")
    
    print(f"\n  Perfect efficiency = exploring only the solution path")
    print(f"  A* should be closest to perfect on this maze.")


if __name__ == "__main__":
    main()