"""Test the optimized solver on basic cases, then Sudoku."""
import sys
sys.path.insert(0, '/workspace/sat')

from solver2 import SATSolverV2

def test_basic():
    print("═══ Basic Tests ═══")
    
    # Trivial SAT
    s = SATSolverV2(1, [[1]])
    r = s.solve()
    assert r is not None and r[1] == True
    print("✓ trivial_sat")
    
    # Trivial UNSAT
    s = SATSolverV2(1, [[1], [-1]])
    r = s.solve()
    assert r is None
    print("✓ trivial_unsat")
    
    # Two clause
    s = SATSolverV2(2, [[1, 2], [-1, 2]])
    r = s.solve()
    assert r is not None and r[2] == True
    print("✓ two_clause")
    
    # Pigeonhole 3-2 (UNSAT)
    clauses = []
    for i in range(3):
        clauses.append([i*2+1, i*2+2])
    for j in range(1, 3):
        for i1 in range(3):
            for i2 in range(i1+1, 3):
                clauses.append([-(i1*2+j), -(i2*2+j)])
    s = SATSolverV2(6, clauses)
    r = s.solve()
    assert r is None
    print("✓ pigeonhole_3_2 (UNSAT)")

    # Random 3-SAT
    import random
    random.seed(42)
    n, m = 20, 80
    clauses = []
    for _ in range(m):
        vs = random.sample(range(1, n+1), 3)
        clause = [v if random.random() > 0.5 else -v for v in vs]
        clauses.append(clause)
    s = SATSolverV2(n, clauses)
    r = s.solve()
    if r is not None:
        for clause in clauses:
            assert any((l > 0) == r.get(abs(l), True) for l in clause)
    print(f"✓ random_3sat ({'SAT' if r else 'UNSAT'})")

def test_sudoku():
    print("\n═══ Sudoku Test ═══")
    from sudoku import encode_sudoku, decode_solution, print_grid, verify_solution
    
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
    
    print("Puzzle:")
    print_grid(moderate_puzzle)
    
    num_vars, clauses = encode_sudoku(moderate_puzzle)
    print(f"\nEncoded: {num_vars} variables, {len(clauses)} clauses")
    
    # Use v2 solver instead of the imported one
    solver = SATSolverV2(num_vars, clauses)
    result = solver.solve()
    
    if result is not None:
        solution = decode_solution(result)
        valid = verify_solution(solution)
        print(f"\nValid: {valid}")
        print("\nSolution:")
        print_grid(solution)
        if not valid:
            print("⚠ INVALID — bug in solver")
    else:
        print("\nUNSAT — this shouldn't happen for a valid Sudoku")

if __name__ == '__main__':
    test_basic()
    test_sudoku()