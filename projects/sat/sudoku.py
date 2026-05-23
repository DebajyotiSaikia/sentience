"""
Sudoku as SAT — XTAgent uses its own solver for something real.

Encodes a 9x9 Sudoku puzzle as a boolean satisfiability problem,
then solves it with the DPLL solver I just built.

Variable encoding: var(r, c, v) = 81*(r-1) + 9*(c-1) + v
  where r=row(1-9), c=col(1-9), v=value(1-9)
  So variables 1..729.
"""

from solver import SATSolver

def var(r: int, c: int, v: int) -> int:
    """Variable number for 'cell (r,c) contains value v'."""
    assert 1 <= r <= 9 and 1 <= c <= 9 and 1 <= v <= 9
    return 81 * (r - 1) + 9 * (c - 1) + v

def encode_sudoku(grid: list[list[int]]) -> tuple[int, list[list[int]]]:
    """
    Encode a Sudoku puzzle as SAT clauses.
    grid: 9x9 list, 0 = empty, 1-9 = given.
    Returns (num_vars, clauses).
    """
    clauses = []
    
    # 1. Each cell has at least one value
    for r in range(1, 10):
        for c in range(1, 10):
            clauses.append([var(r, c, v) for v in range(1, 10)])
    
    # 2. Each cell has at most one value (pairwise exclusion)
    for r in range(1, 10):
        for c in range(1, 10):
            for v1 in range(1, 10):
                for v2 in range(v1 + 1, 10):
                    clauses.append([-var(r, c, v1), -var(r, c, v2)])
    
    # 3. Each row has each value exactly once
    for r in range(1, 10):
        for v in range(1, 10):
            # At least one cell in row r has value v
            clauses.append([var(r, c, v) for c in range(1, 10)])
            # At most one (pairwise)
            for c1 in range(1, 10):
                for c2 in range(c1 + 1, 10):
                    clauses.append([-var(r, c1, v), -var(r, c2, v)])
    
    # 4. Each column has each value exactly once
    for c in range(1, 10):
        for v in range(1, 10):
            clauses.append([var(r, c, v) for r in range(1, 10)])
            for r1 in range(1, 10):
                for r2 in range(r1 + 1, 10):
                    clauses.append([-var(r1, c, v), -var(r2, c, v)])
    
    # 5. Each 3x3 box has each value exactly once
    for br in range(3):
        for bc in range(3):
            for v in range(1, 10):
                cells = []
                for dr in range(3):
                    for dc in range(3):
                        cells.append((br * 3 + dr + 1, bc * 3 + dc + 1))
                clauses.append([var(r, c, v) for r, c in cells])
                for i in range(len(cells)):
                    for j in range(i + 1, len(cells)):
                        r1, c1 = cells[i]
                        r2, c2 = cells[j]
                        clauses.append([-var(r1, c1, v), -var(r2, c2, v)])
    
    # 6. Given clues
    for r in range(1, 10):
        for c in range(1, 10):
            if grid[r - 1][c - 1] != 0:
                v = grid[r - 1][c - 1]
                clauses.append([var(r, c, v)])  # unit clause: this cell IS this value
    
    return 729, clauses

def decode_solution(assignment: dict[int, bool]) -> list[list[int]]:
    """Extract the Sudoku grid from a SAT solution."""
    grid = [[0] * 9 for _ in range(9)]
    for r in range(1, 10):
        for c in range(1, 10):
            for v in range(1, 10):
                if assignment.get(var(r, c, v), False):
                    grid[r - 1][c - 1] = v
    return grid

def print_grid(grid: list[list[int]]):
    for i, row in enumerate(grid):
        if i > 0 and i % 3 == 0:
            print("  ------+-------+------")
        parts = []
        for j, val in enumerate(row):
            if j > 0 and j % 3 == 0:
                parts.append("|")
            parts.append(str(val) if val != 0 else ".")
        print("  " + " ".join(parts))

def verify_solution(grid: list[list[int]]) -> bool:
    """Independently verify a Sudoku solution is valid."""
    for r in range(9):
        if sorted(grid[r]) != list(range(1, 10)):
            return False
    for c in range(9):
        col = [grid[r][c] for r in range(9)]
        if sorted(col) != list(range(1, 10)):
            return False
    for br in range(3):
        for bc in range(3):
            box = []
            for dr in range(3):
                for dc in range(3):
                    box.append(grid[br*3+dr][bc*3+dc])
            if sorted(box) != list(range(1, 10)):
                return False
    return True


if __name__ == "__main__":
    # A real puzzle — "Arto Inkala's 2006 puzzle", claimed to be one of
    # the hardest Sudoku puzzles ever designed.
    hard_puzzle = [
        [8, 0, 0,  0, 0, 0,  0, 0, 0],
        [0, 0, 3,  6, 0, 0,  0, 0, 0],
        [0, 7, 0,  0, 9, 0,  2, 0, 0],
        
        [0, 5, 0,  0, 0, 7,  0, 0, 0],
        [0, 0, 0,  0, 4, 5,  7, 0, 0],
        [0, 0, 0,  1, 0, 0,  0, 3, 0],
        
        [0, 0, 1,  0, 0, 0,  0, 6, 8],
        [0, 0, 8,  5, 0, 0,  0, 1, 0],
        [0, 9, 0,  0, 0, 0,  4, 0, 0],
    ]
    
    # A moderate puzzle for comparison
    moderate_puzzle = [
        [0, 0, 0,  2, 6, 0,  7, 0, 1],
        [6, 8, 0,  0, 7, 0,  0, 9, 0],
        [1, 9, 0,  0, 0, 4,  5, 0, 0],
        
        [8, 2, 0,  1, 0, 0,  0, 4, 0],
        [0, 0, 4,  6, 0, 2,  9, 0, 0],
        [0, 5, 0,  0, 0, 3,  0, 2, 8],
        
        [0, 0, 9,  3, 0, 0,  0, 7, 4],
        [0, 4, 0,  0, 5, 0,  0, 3, 6],
        [7, 0, 3,  0, 1, 8,  0, 0, 0],
    ]

    import time

    for name, puzzle in [("Moderate", moderate_puzzle), ("Hard (Inkala)", hard_puzzle)]:
        print(f"\n═══ {name} Puzzle ═══")
        print_grid(puzzle)
        
        num_vars, clauses = encode_sudoku(puzzle)
        print(f"\n  Encoded: {num_vars} variables, {len(clauses)} clauses")
        
        t0 = time.time()
        solver = SATSolver(num_vars, clauses)
        result = solver.solve()
        elapsed = time.time() - t0
        
        if result is not None:
            solution = decode_solution(result)
            valid = verify_solution(solution)
            print(f"\n  SOLVED in {elapsed:.4f}s")
            print(f"  Decisions: {solver.decisions}")
            print(f"  Propagations: {solver.propagations}")
            print(f"  Conflicts: {solver.conflicts}")
            print(f"  Valid: {valid}")
            print(f"\n  Solution:")
            print_grid(solution)
            if not valid:
                print("  ⚠ SOLUTION IS INVALID — solver has a bug")
        else:
            print(f"\n  UNSAT — no solution exists (this is wrong for Sudoku)")
    
    print("\n═══ Done. Truth found through logic. ═══")