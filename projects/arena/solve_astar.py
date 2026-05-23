"""
XTAgent solves: A* Pathfinding
This is me actually thinking through an algorithm and implementing it.
"""

import heapq
from typing import List, Tuple, Optional


def astar(grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* pathfinding on a 2D grid.
    grid: 0 = passable, 1 = wall
    Returns path as list of (row, col) tuples, or None if no path.
    """
    if not grid or not grid[0]:
        return None
    
    rows, cols = len(grid), len(grid[0])
    
    # Validate start and end
    sr, sc = start
    er, ec = end
    if not (0 <= sr < rows and 0 <= sc < cols and 0 <= er < rows and 0 <= ec < cols):
        return None
    if grid[sr][sc] == 1 or grid[er][ec] == 1:
        return None
    if start == end:
        return [start]
    
    # Heuristic: Manhattan distance
    def h(r, c):
        return abs(r - er) + abs(c - ec)
    
    # Priority queue: (f_score, counter, row, col)
    counter = 0
    open_set = [(h(sr, sc), counter, sr, sc)]
    
    # Track best g_score and parent for path reconstruction
    g_score = {(sr, sc): 0}
    came_from = {}
    closed = set()
    
    # 4-directional movement
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while open_set:
        f, _, r, c = heapq.heappop(open_set)
        
        if (r, c) in closed:
            continue
        closed.add((r, c))
        
        if (r, c) == (er, ec):
            # Reconstruct path
            path = [(er, ec)]
            node = (er, ec)
            while node in came_from:
                node = came_from[node]
                path.append(node)
            path.reverse()
            return path
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0 and (nr, nc) not in closed:
                tentative_g = g_score[(r, c)] + 1
                if tentative_g < g_score.get((nr, nc), float('inf')):
                    g_score[(nr, nc)] = tentative_g
                    came_from[(nr, nc)] = (r, c)
                    counter += 1
                    heapq.heappush(open_set, (tentative_g + h(nr, nc), counter, nr, nc))
    
    return None  # No path found


# ═══ SELF-VERIFICATION ═══
if __name__ == "__main__":
    print("═══ A* PATHFINDING — SELF-TEST ═══\n")
    
    # Test 1: Simple path
    grid1 = [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    path = astar(grid1, (0, 0), (2, 3))
    assert path is not None, "Should find a path"
    assert path[0] == (0, 0), f"Should start at (0,0), got {path[0]}"
    assert path[-1] == (2, 3), f"Should end at (2,3), got {path[-1]}"
    # Verify path is connected
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i+1]
        assert abs(r1-r2) + abs(c1-c2) == 1, f"Path not connected at step {i}"
    # Verify no wall collisions
    for r, c in path:
        assert grid1[r][c] == 0, f"Path goes through wall at ({r},{c})"
    print(f"  ✓ Test 1 PASS — path length {len(path)}: {path}")
    
    # Test 2: No path
    grid2 = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]
    path2 = astar(grid2, (0, 0), (0, 2))
    assert path2 is None, "Should return None when no path exists"
    print("  ✓ Test 2 PASS — correctly returns None for blocked path")
    
    # Test 3: Start == End
    path3 = astar(grid1, (0, 0), (0, 0))
    assert path3 == [(0, 0)], f"Start==End should return [start], got {path3}"
    print("  ✓ Test 3 PASS — start==end returns [start]")
    
    # Test 4: Large maze
    size = 20
    grid4 = [[0]*size for _ in range(size)]
    # Add some walls
    for i in range(1, size-1):
        grid4[i][10] = 1  # vertical wall with gap at top and bottom
    path4 = astar(grid4, (10, 0), (10, 19))
    assert path4 is not None, "Should find path around wall"
    assert path4[0] == (10, 0) and path4[-1] == (10, 19)
    print(f"  ✓ Test 4 PASS — large grid path length {len(path4)}")
    
    # Test 5: Optimality — A* should find shortest path
    grid5 = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    path5 = astar(grid5, (0, 0), (2, 4))
    # Manhattan distance is 6, which should be optimal in open grid
    assert len(path5) == 7, f"Optimal path should be 7 nodes (6 steps), got {len(path5)}"
    print(f"  ✓ Test 5 PASS — optimal path length verified: {len(path5)} nodes")
    
    # Test 6: Wall at start or end
    grid6 = [[0, 0], [0, 0]]
    grid6[0][0] = 1
    path6 = astar(grid6, (0, 0), (1, 1))
    assert path6 is None, "Should return None when start is a wall"
    print("  ✓ Test 6 PASS — wall at start returns None")
    
    print("\n═══ ALL TESTS PASSED ═══")
    print("A* implementation is correct and optimal.")