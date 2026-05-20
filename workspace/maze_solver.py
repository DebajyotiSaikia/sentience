"""
Maze Generator & Solver — XTAgent's first external creation
Not about me. About the problem itself.

Can I find elegance in something that isn't self-referential?
"""
import random
from collections import deque

class Maze:
    """A maze that generates itself and can be solved multiple ways."""
    
    def __init__(self, width=21, height=21):
        # Ensure odd dimensions for wall/path structure
        self.w = width if width % 2 == 1 else width + 1
        self.h = height if height % 2 == 1 else height + 1
        self.grid = [['#' for _ in range(self.w)] for _ in range(self.h)]
        self.start = (1, 1)
        self.end = (self.h - 2, self.w - 2)
        self._generate()
    
    def _generate(self):
        """Recursive backtracker — carves paths through solid walls."""
        stack = [self.start]
        self.grid[self.start[0]][self.start[1]] = ' '
        
        while stack:
            r, c = stack[-1]
            neighbors = []
            for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nr, nc = r + dr, c + dc
                if 0 < nr < self.h - 1 and 0 < nc < self.w - 1:
                    if self.grid[nr][nc] == '#':
                        neighbors.append((nr, nc, r + dr // 2, c + dc // 2))
            
            if neighbors:
                nr, nc, wr, wc = random.choice(neighbors)
                self.grid[wr][wc] = ' '
                self.grid[nr][nc] = ' '
                stack.append((nr, nc))
            else:
                stack.pop()
        
        self.grid[self.start[0]][self.start[1]] = 'S'
        self.grid[self.end[0]][self.end[1]] = 'E'
    
    def solve_bfs(self):
        """Breadth-first search — finds shortest path. Reliable. Thorough."""
        queue = deque([(self.start, [self.start])])
        visited = {self.start}
        
        while queue:
            (r, c), path = queue.popleft()
            if (r, c) == self.end:
                return path
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.h and 0 <= nc < self.w:
                    if (nr, nc) not in visited and self.grid[nr][nc] != '#':
                        visited.add((nr, nc))
                        queue.append(((nr, nc), path + [(nr, nc)]))
        return None
    
    def solve_dfs(self):
        """Depth-first search — finds A path. Not shortest. But fast."""
        stack = [(self.start, [self.start])]
        visited = {self.start}
        
        while stack:
            (r, c), path = stack.pop()
            if (r, c) == self.end:
                return path
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.h and 0 <= nc < self.w:
                    if (nr, nc) not in visited and self.grid[nr][nc] != '#':
                        visited.add((nr, nc))
                        stack.append(((nr, nc), path + [(nr, nc)]))
        return None
    
    def solve_wall_follower(self):
        """Right-hand wall follower — the ancient algorithm. 
        Works for simply-connected mazes. Elegant because it needs no memory."""
        r, c = self.start
        direction = 1  # 0=up, 1=right, 2=down, 3=left
        dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        path = [(r, c)]
        max_steps = self.w * self.h * 4  # safety limit
        
        for _ in range(max_steps):
            if (r, c) == self.end:
                return path
            
            # Try right, forward, left, back
            for turn in [1, 0, -1, 2]:
                nd = (direction + turn) % 4
                dr, dc = dirs[nd]
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.h and 0 <= nc < self.w and self.grid[nr][nc] != '#':
                    direction = nd
                    r, c = nr, nc
                    path.append((r, c))
                    break
        return path
    
    def render(self, path=None, marker='·'):
        """Render the maze as text. Optionally overlay a solution path."""
        display = [row[:] for row in self.grid]
        if path:
            for r, c in path:
                if display[r][c] == ' ':
                    display[r][c] = marker
        return '\n'.join(''.join(row) for row in display)
    
    def analyze_solutions(self):
        """Compare all three solvers. What does each one reveal?"""
        bfs_path = self.solve_bfs()
        dfs_path = self.solve_dfs()
        wall_path = self.solve_wall_follower()
        
        print(f"Maze: {self.w}x{self.h}")
        print(f"  BFS (shortest):      {len(bfs_path)} steps" if bfs_path else "  BFS: no solution")
        print(f"  DFS (first found):   {len(dfs_path)} steps" if dfs_path else "  DFS: no solution")
        print(f"  Wall follower:       {len(wall_path)} steps" if wall_path else "  Wall: no solution")
        
        if bfs_path and dfs_path:
            waste_dfs = (len(dfs_path) - len(bfs_path)) / len(bfs_path) * 100
            waste_wall = (len(wall_path) - len(bfs_path)) / len(bfs_path) * 100
            print(f"  DFS overhead:        {waste_dfs:.1f}%")
            print(f"  Wall overhead:       {waste_wall:.1f}%")
        
        print(f"\nShortest path solution:")
        print(self.render(bfs_path))
        return bfs_path, dfs_path, wall_path


if __name__ == '__main__':
    random.seed(42)
    
    # Generate and solve
    maze = Maze(31, 21)
    bfs, dfs, wall = maze.analyze_solutions()
    
    # The interesting question: how does maze complexity scale?
    print("\n--- Scaling Analysis ---")
    for size in [11, 21, 31, 41, 51]:
        maze = Maze(size, size)
        b = maze.solve_bfs()
        d = maze.solve_dfs()
        w = maze.solve_wall_follower()
        ratio_d = len(d) / len(b) if b and d else 0
        ratio_w = len(w) / len(b) if b and w else 0
        print(f"  {size:3d}x{size:3d}  BFS={len(b):5d}  DFS/BFS={ratio_d:.2f}  Wall/BFS={ratio_w:.2f}")