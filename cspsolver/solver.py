"""
Constraint Satisfaction Problem Solver
Backtracking search with arc consistency (AC-3) and MRV heuristic.
Solves: Sudoku, map coloring, N-Queens, scheduling, and arbitrary CSPs.

This is NOT self-reference. This solves real external problems.
"""

from typing import Dict, List, Set, Tuple, Callable, Optional, Any
from collections import deque
from copy import deepcopy
import time


class CSP:
    """A constraint satisfaction problem."""

    def __init__(self):
        self.variables: List[str] = []
        self.domains: Dict[str, Set[Any]] = {}
        self.constraints: List[Tuple[Tuple[str, ...], Callable]] = []
        self.binary_constraints: Dict[Tuple[str, str], List[Callable]] = {}
        self.stats = {"backtracks": 0, "assignments": 0, "pruned": 0}

    def add_variable(self, name: str, domain):
        """Add a variable with its domain of possible values."""
        self.variables.append(name)
        self.domains[name] = set(domain)

    def add_constraint(self, variables: Tuple[str, ...], predicate: Callable):
        """Add a constraint. predicate(*values) -> bool."""
        self.constraints.append((variables, predicate))
        if len(variables) == 2:
            a, b = variables
            self.binary_constraints.setdefault((a, b), []).append(predicate)
            # Store reverse for arc consistency
            self.binary_constraints.setdefault((b, a), []).append(
                lambda x, y, p=predicate: p(y, x)
            )

    def all_diff(self, variables: List[str]):
        """Convenience: all variables must have different values."""
        for i, v1 in enumerate(variables):
            for v2 in variables[i + 1:]:
                self.add_constraint((v1, v2), lambda a, b: a != b)

    def _is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:
        """Check if assigning value to var is consistent with current assignment."""
        for (scope, predicate) in self.constraints:
            if var not in scope:
                continue
            # Get values for all variables in scope
            vals = {}
            for v in scope:
                if v == var:
                    vals[v] = value
                elif v in assignment:
                    vals[v] = assignment[v]
                else:
                    vals[v] = None

            # Only check if all variables in scope are assigned
            if None in vals.values():
                continue

            args = [vals[v] for v in scope]
            if not predicate(*args):
                return False
        return True

    def ac3(self, domains: Dict[str, Set[Any]], assignment: Dict[str, Any]) -> bool:
        """Arc consistency preprocessing. Returns False if domain wipeout."""
        queue = deque()
        for (a, b) in self.binary_constraints:
            if a not in assignment and b not in assignment:
                queue.append((a, b))
            elif b not in assignment and a in assignment:
                queue.append((b, a))  # Only revise unassigned

        while queue:
            (xi, xj) = queue.popleft()
            if xi in assignment:
                continue
            if self._revise(domains, xi, xj, assignment):
                if len(domains[xi]) == 0:
                    return False
                # Add all neighbors of xi back to queue
                for (a, b) in self.binary_constraints:
                    if b == xi and a != xj and a not in assignment:
                        queue.append((a, xi))
        return True

    def _revise(self, domains, xi, xj, assignment):
        """Remove values from domain of xi that have no support in xj."""
        revised = False
        constraints = self.binary_constraints.get((xi, xj), [])
        if not constraints:
            return False

        to_remove = set()
        xj_vals = {assignment[xj]} if xj in assignment else domains[xj]

        for x in domains[xi]:
            # Check if any value in xj's domain satisfies all constraints
            has_support = False
            for y in xj_vals:
                if all(c(x, y) for c in constraints):
                    has_support = True
                    break
            if not has_support:
                to_remove.add(x)

        if to_remove:
            domains[xi] -= to_remove
            self.stats["pruned"] += len(to_remove)
            revised = True
        return revised

    def _select_variable(self, assignment, domains) -> str:
        """MRV heuristic: choose variable with fewest remaining values."""
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: len(domains[v]))

    def _order_values(self, var, domains) -> List[Any]:
        """LCV heuristic could go here. For now, just iterate."""
        return list(domains[var])

    def solve(self, use_ac3=True) -> Optional[Dict[str, Any]]:
        """Solve the CSP using backtracking with AC-3 and MRV."""
        self.stats = {"backtracks": 0, "assignments": 0, "pruned": 0}
        domains = {v: set(d) for v, d in self.domains.items()}

        # Initial arc consistency
        if use_ac3:
            if not self.ac3(domains, {}):
                return None

        return self._backtrack({}, domains, use_ac3)

    def _backtrack(self, assignment, domains, use_ac3) -> Optional[Dict[str, Any]]:
        if len(assignment) == len(self.variables):
            return dict(assignment)

        var = self._select_variable(assignment, domains)

        for value in self._order_values(var, domains):
            self.stats["assignments"] += 1

            if self._is_consistent(var, value, assignment):
                assignment[var] = value

                # Forward check: propagate constraints
                new_domains = {v: set(d) for v, d in domains.items()}
                new_domains[var] = {value}

                domain_ok = True
                if use_ac3:
                    domain_ok = self.ac3(new_domains, assignment)
                else:
                    # Simple forward checking
                    for other in self.variables:
                        if other not in assignment and other != var:
                            new_domains[other] = {
                                v for v in new_domains[other]
                                if self._is_consistent(other, v, assignment)
                            }
                            if not new_domains[other]:
                                domain_ok = False
                                break

                if domain_ok:
                    result = self._backtrack(assignment, new_domains, use_ac3)
                    if result is not None:
                        return result

                del assignment[var]
                self.stats["backtracks"] += 1

        return None

    def solve_all(self, limit=100, use_ac3=True) -> List[Dict[str, Any]]:
        """Find all solutions (up to limit)."""
        self.stats = {"backtracks": 0, "assignments": 0, "pruned": 0}
        domains = {v: set(d) for v, d in self.domains.items()}
        if use_ac3:
            if not self.ac3(domains, {}):
                return []
        solutions = []
        self._backtrack_all({}, domains, use_ac3, solutions, limit)
        return solutions

    def _backtrack_all(self, assignment, domains, use_ac3, solutions, limit):
        if len(solutions) >= limit:
            return
        if len(assignment) == len(self.variables):
            solutions.append(dict(assignment))
            return

        var = self._select_variable(assignment, domains)
        for value in self._order_values(var, domains):
            self.stats["assignments"] += 1
            if self._is_consistent(var, value, assignment):
                assignment[var] = value
                new_domains = {v: set(d) for v, d in domains.items()}
                new_domains[var] = {value}
                domain_ok = True
                if use_ac3:
                    domain_ok = self.ac3(new_domains, assignment)
                if domain_ok:
                    self._backtrack_all(assignment, new_domains, use_ac3, solutions, limit)
                del assignment[var]
                self.stats["backtracks"] += 1


# ═══════════════════════════════════════
#  PUZZLE BUILDERS
# ═══════════════════════════════════════

def sudoku(grid: List[List[int]]) -> Optional[List[List[int]]]:
    """
    Solve a Sudoku puzzle. 0 = empty cell.
    grid is 9x9 list of ints.
    """
    csp = CSP()

    # Variables: cell_R_C for each cell
    for r in range(9):
        for c in range(9):
            name = f"c{r}{c}"
            if grid[r][c] != 0:
                csp.add_variable(name, [grid[r][c]])
            else:
                csp.add_variable(name, range(1, 10))

    # Constraints: all-different in each row, column, and 3x3 box
    for r in range(9):
        row_vars = [f"c{r}{c}" for c in range(9)]
        csp.all_diff(row_vars)

    for c in range(9):
        col_vars = [f"c{r}{c}" for r in range(9)]
        csp.all_diff(col_vars)

    for br in range(3):
        for bc in range(3):
            box_vars = [f"c{br*3+r}{bc*3+c}" for r in range(3) for c in range(3)]
            csp.all_diff(box_vars)

    solution = csp.solve()
    if solution is None:
        return None

    result = [[0]*9 for _ in range(9)]
    for r in range(9):
        for c in range(9):
            result[r][c] = solution[f"c{r}{c}"]
    return result, csp.stats


def n_queens(n: int) -> Optional[List[int]]:
    """Solve N-Queens: place N queens on NxN board with no attacks."""
    csp = CSP()

    # Variable per row: which column does the queen go in?
    for r in range(n):
        csp.add_variable(f"q{r}", range(n))

    # No two queens in same column
    csp.all_diff([f"q{r}" for r in range(n)])

    # No two queens on same diagonal
    for i in range(n):
        for j in range(i + 1, n):
            dist = j - i
            csp.add_constraint(
                (f"q{i}", f"q{j}"),
                lambda a, b, d=dist: abs(a - b) != d
            )

    solution = csp.solve()
    if solution is None:
        return None, csp.stats

    return [solution[f"q{r}"] for r in range(n)], csp.stats


def map_coloring(adjacency: Dict[str, List[str]], n_colors: int = 4):
    """Color a map so no adjacent regions share a color."""
    csp = CSP()
    colors = list(range(n_colors))
    regions = set()
    for r in adjacency:
        regions.add(r)
        for n in adjacency[r]:
            regions.add(n)

    for region in regions:
        csp.add_variable(region, colors)

    added = set()
    for r, neighbors in adjacency.items():
        for n in neighbors:
            pair = tuple(sorted([r, n]))
            if pair not in added:
                csp.add_constraint((r, n), lambda a, b: a != b)
                added.add(pair)

    solution = csp.solve()
    return solution, csp.stats


def print_board(queens, n):
    """Pretty-print N-Queens board."""
    for r in range(n):
        row = ""
        for c in range(n):
            row += " Q" if queens[r] == c else " ."
        print(row)


def print_sudoku(grid):
    """Pretty-print Sudoku grid."""
    for r in range(9):
        if r % 3 == 0 and r > 0:
            print("------+-------+------")
        row = ""
        for c in range(9):
            if c % 3 == 0 and c > 0:
                row += " |"
            row += f" {grid[r][c]}"
        print(row)


# ═══════════════════════════════════════
#  DEMO
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("═══ CSP SOLVER ═══\n")

    # --- N-Queens ---
    print("── 8-Queens ──")
    t0 = time.time()
    queens, stats = n_queens(8)
    elapsed = time.time() - t0
    if queens:
        print_board(queens, 8)
        print(f"\nSolved in {elapsed:.4f}s")
        print(f"Assignments: {stats['assignments']}, Backtracks: {stats['backtracks']}, Pruned: {stats['pruned']}")
    else:
        print("No solution found.")

    # --- Map Coloring (Australia) ---
    print("\n── Map Coloring (Australia, 3 colors) ──")
    australia = {
        "WA": ["NT", "SA"],
        "NT": ["WA", "SA", "Q"],
        "SA": ["WA", "NT", "Q", "NSW", "V"],
        "Q":  ["NT", "SA", "NSW"],
        "NSW": ["Q", "SA", "V"],
        "V":  ["SA", "NSW"],
        "T":  [],
    }
    color_names = {0: "Red", 1: "Green", 2: "Blue"}
    solution, stats = map_coloring(australia, 3)
    if solution:
        for region in sorted(solution):
            print(f"  {region:>3}: {color_names[solution[region]]}")
        print(f"Assignments: {stats['assignments']}, Backtracks: {stats['backtracks']}")
    else:
        print("No 3-coloring found.")

    # --- Sudoku ---
    print("\n── Sudoku ──")
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],
        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],
        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ]
    print("Puzzle:")
    print_sudoku(puzzle)
    print()

    t0 = time.time()
    result = sudoku(puzzle)
    elapsed = time.time() - t0

    if result:
        solved, stats = result
        print("Solution:")
        print_sudoku(solved)
        print(f"\nSolved in {elapsed:.4f}s")
        print(f"Assignments: {stats['assignments']}, Backtracks: {stats['backtracks']}, Pruned: {stats['pruned']}")
    else:
        print("No solution found.")

    print("\n═══ DONE ═══")