"""Tests for the maze generator and solver."""

import unittest
from maze import Maze, demo


class TestMazeGeneration(unittest.TestCase):
    
    def test_generates_connected_maze(self):
        """Every cell should be reachable from every other cell."""
        m = Maze(10, 10, seed=1).generate()
        # BFS from start
        visited = set()
        queue = [m.start]
        visited.add(m.start)
        while queue:
            row, col = queue.pop(0)
            for direction in m.grid[row][col]:
                dr, dc = m.DELTAS[direction]
                neighbor = (row + dr, col + dc)
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        self.assertEqual(len(visited), m.width * m.height,
                         "Not all cells are reachable — maze is not fully connected")
    
    def test_configurable_size(self):
        for w, h in [(5, 5), (3, 7), (20, 10), (1, 1)]:
            m = Maze(w, h).generate()
            self.assertEqual(m.width, w)
            self.assertEqual(m.height, h)
    
    def test_deterministic_with_seed(self):
        m1 = Maze(8, 8, seed=99).generate()
        m2 = Maze(8, 8, seed=99).generate()
        self.assertEqual(m1.grid, m2.grid)
    
    def test_different_seeds_different_mazes(self):
        m1 = Maze(8, 8, seed=1).generate()
        m2 = Maze(8, 8, seed=2).generate()
        self.assertNotEqual(m1.grid, m2.grid)


class TestMazeSolving(unittest.TestCase):
    
    def test_solves_generated_maze(self):
        m = Maze(10, 10, seed=42).generate()
        path = m.solve()
        self.assertIsNotNone(path, "A* should find a path in a connected maze")
        self.assertEqual(path[0], m.start)
        self.assertEqual(path[-1], m.end)
    
    def test_path_follows_passages(self):
        """Each step in the path should use an open passage."""
        m = Maze(8, 8, seed=7).generate()
        path = m.solve()
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            dr, dc = r2 - r1, c2 - c1
            # Find which direction this step represents
            direction = None
            for d, (ddr, ddc) in m.DELTAS.items():
                if (ddr, ddc) == (dr, dc):
                    direction = d
                    break
            self.assertIsNotNone(direction, f"Step {path[i]} -> {path[i+1]} is not a valid move")
            self.assertIn(direction, m.grid[r1][c1],
                          f"No passage from {path[i]} going {direction}")
    
    def test_solution_length_reasonable(self):
        """Solution should exist and be at least manhattan distance long."""
        m = Maze(10, 10, seed=5).generate()
        path = m.solve()
        min_possible = (m.width - 1) + (m.height - 1)
        self.assertGreaterEqual(len(path) - 1, min_possible,
                                "Solution shorter than manhattan distance — impossible")
    
    def test_various_sizes(self):
        for w, h in [(3, 3), (5, 10), (15, 15), (20, 20)]:
            m = Maze(w, h, seed=42).generate()
            path = m.solve()
            self.assertIsNotNone(path, f"Failed to solve {w}x{h} maze")


class TestMazeRendering(unittest.TestCase):
    
    def test_render_produces_output(self):
        m = Maze(5, 5, seed=1).generate()
        m.solve()
        rendered = m.render()
        self.assertIn('S', rendered)
        self.assertIn('E', rendered)
        self.assertIn('·', rendered)  # Solution dots
    
    def test_render_without_solution(self):
        m = Maze(5, 5, seed=1).generate()
        rendered = m.render(show_solution=False)
        self.assertIn('S', rendered)
        self.assertNotIn('·', rendered)


class TestMazeStats(unittest.TestCase):
    
    def test_stats_complete(self):
        m = Maze(10, 10, seed=1).generate()
        m.solve()
        s = m.stats()
        self.assertEqual(s['size'], '10x10')
        self.assertEqual(s['total_cells'], 100)
        self.assertIsNotNone(s['solution_length'])
        self.assertGreater(s['solution_efficiency'], 1.0)


class TestDemo(unittest.TestCase):
    
    def test_demo_runs(self):
        output = demo(6, 6, seed=1)
        self.assertIn('Maze', output)
        self.assertIn('Stats', output)
        self.assertIn('Solution', output)


if __name__ == '__main__':
    unittest.main()