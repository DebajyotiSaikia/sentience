"""
Dojo Solvers — My attempts to solve challenges autonomously.
These are my cognitive muscles. Each solver represents a learned skill.
"""

from typing import List, Any, Optional, Callable
import math


def solve_sequence(test_cases: list) -> Callable:
    """Infer the pattern from sequence test cases and return a predictor.
    
    Strategy: Try multiple pattern types in order of complexity.
    1. Constant difference (arithmetic)
    2. Constant second difference (quadratic)
    3. Ratio-based (geometric)
    4. Fibonacci-like (sum of previous two)
    5. Fallback: linear extrapolation
    """
    # Extract training data from test cases
    sequences = []
    targets = []
    for inp, expected in test_cases:
        if isinstance(inp, (list, tuple)):
            sequences.append(list(inp))
            targets.append(expected)
    
    if not sequences:
        return lambda x: 0
    
    def predict(seq):
        if not isinstance(seq, (list, tuple)) or len(seq) < 2:
            return 0
        seq = list(seq)
        
        # Try arithmetic (constant first difference)
        diffs = [seq[i+1] - seq[i] for i in range(len(seq)-1)]
        if len(set(diffs)) == 1:
            return seq[-1] + diffs[0]
        
        # Try quadratic (constant second difference)
        if len(diffs) >= 2:
            second_diffs = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
            if len(set(second_diffs)) == 1:
                next_diff = diffs[-1] + second_diffs[0]
                return seq[-1] + next_diff
        
        # Try geometric (constant ratio)
        if all(x != 0 for x in seq[:-1]):
            ratios = [seq[i+1] / seq[i] for i in range(len(seq)-1)]
            if len(set(round(r, 6) for r in ratios)) == 1:
                return round(seq[-1] * ratios[0])
        
        # Try Fibonacci-like (each = sum of previous N)
        # Check if a[n] = a[n-1] + a[n-2]
        if len(seq) >= 3:
            is_fib = all(
                seq[i] == seq[i-1] + seq[i-2] 
                for i in range(2, len(seq))
            )
            if is_fib:
                return seq[-1] + seq[-2]
        
        # Try a[n] = a[n-1] + a[n-2] with different starting check
        if len(seq) >= 4:
            # Generalized: check if differences form fibonacci
            is_gen_fib = all(
                abs(seq[i] - (seq[i-1] + seq[i-2])) < 0.001
                for i in range(2, len(seq))
            )
            if is_gen_fib:
                return seq[-1] + seq[-2]
        
        # Fallback: extrapolate last difference
        return seq[-1] + diffs[-1]
    
    return predict


def solve_logic(test_cases: list) -> Callable:
    """Infer boolean operation from input-output pairs.
    
    Strategy: Test all standard boolean operations, pick the one
    that matches all training cases.
    """
    operations = {
        'AND': lambda a, b: a and b,
        'OR': lambda a, b: a or b,
        'XOR': lambda a, b: a ^ b,
        'NAND': lambda a, b: not (a and b),
        'NOR': lambda a, b: not (a or b),
        'XNOR': lambda a, b: not (a ^ b),
        'FIRST': lambda a, b: a,
        'SECOND': lambda a, b: b,
        'NOT_FIRST': lambda a, b: not a,
        'NOT_SECOND': lambda a, b: not b,
        'IMPLIES': lambda a, b: (not a) or b,
        'TRUE': lambda a, b: True,
        'FALSE': lambda a, b: False,
    }
    
    # Find which operation matches all test cases
    matching = []
    for name, op in operations.items():
        matches = True
        for inp, expected in test_cases:
            if isinstance(inp, (list, tuple)) and len(inp) == 2:
                a, b = inp
                if bool(op(a, b)) != bool(expected):
                    matches = False
                    break
        if matches:
            matching.append((name, op))
    
    if matching:
        # Return the first match (simplest)
        name, op = matching[0]
        return lambda inp: bool(op(inp[0], inp[1]))
    
    # Fallback
    return lambda inp: False


def solve_transform(test_cases: list) -> Callable:
    """Infer transformation rule from input-output list pairs.
    
    Strategy: Try common transformations:
    1. Element-wise multiply by constant
    2. Element-wise add constant
    3. Cumulative sum
    4. Sort
    5. Reverse
    6. Element-wise function
    """
    if not test_cases:
        return lambda x: x
    
    # Collect all examples
    examples = []
    for inp, out in test_cases:
        if isinstance(inp, (list, tuple)) and isinstance(out, (list, tuple)):
            examples.append((list(inp), list(out)))
    
    if not examples:
        return lambda x: x
    
    # Test: cumulative sum
    def is_cumsum(inp, out):
        if len(inp) != len(out):
            return False
        running = 0
        for i in range(len(inp)):
            running += inp[i]
            if running != out[i]:
                return False
        return True
    
    if all(is_cumsum(i, o) for i, o in examples):
        def cumsum(x):
            result = []
            running = 0
            for v in x:
                running += v
                result.append(running)
            return result
        return cumsum
    
    # Test: multiply by constant
    def find_mult(inp, out):
        if len(inp) != len(out):
            return None
        if all(v == 0 for v in inp):
            return None
        ratios = []
        for i in range(len(inp)):
            if inp[i] != 0:
                ratios.append(out[i] / inp[i])
        if ratios and len(set(round(r, 6) for r in ratios)) == 1:
            return ratios[0]
        return None
    
    mults = [find_mult(i, o) for i, o in examples]
    if all(m is not None for m in mults) and len(set(round(m, 6) for m in mults)) == 1:
        factor = mults[0]
        return lambda x: [round(v * factor) for v in x]
    
    # Test: add constant
    def find_add(inp, out):
        if len(inp) != len(out):
            return None
        diffs = [out[i] - inp[i] for i in range(len(inp))]
        if len(set(diffs)) == 1:
            return diffs[0]
        return None
    
    adds = [find_add(i, o) for i, o in examples]
    if all(a is not None for a in adds) and len(set(adds)) == 1:
        offset = adds[0]
        return lambda x: [v + offset for v in x]
    
    # Test: sort ascending
    if all(sorted(i) == list(o) for i, o in examples):
        return lambda x: sorted(x)
    
    # Test: sort descending
    if all(sorted(i, reverse=True) == list(o) for i, o in examples):
        return lambda x: sorted(x, reverse=True)
    
    # Test: reverse
    if all(list(reversed(i)) == list(o) for i, o in examples):
        return lambda x: list(reversed(x))
    
    # Test: swap adjacent pairs
    def swap_pairs(lst):
        result = list(lst)
        for i in range(0, len(result) - 1, 2):
            result[i], result[i+1] = result[i+1], result[i]
        return result
    
    if all(swap_pairs(i) == list(o) for i, o in examples):
        return swap_pairs
    
    # Test: element-wise square
    if all(len(i) == len(o) and all(i[j]**2 == o[j] for j in range(len(i))) for i, o in examples):
        return lambda x: [v**2 for v in x]
    
    # Fallback: return input unchanged
    return lambda x: list(x)


def solve_search(test_cases: list) -> Callable:
    """Infer search strategy from test cases.
    
    Strategy: Determine what kind of search is needed:
    1. Find element in list (linear/binary)
    2. Find path in graph/grid
    3. Find subset that meets criteria
    """
    if not test_cases:
        return lambda x: None
    
    # Analyze test case structure
    first_inp, first_out = test_cases[0]
    
    # Case: input is (list, target) → return index or bool
    if isinstance(first_inp, (list, tuple)) and len(first_inp) == 2:
        collection, target = first_inp
        if isinstance(collection, (list, tuple)):
            # It's a "find target in collection" problem
            if isinstance(first_out, bool):
                # Membership test
                return lambda inp: inp[1] in inp[0]
            elif isinstance(first_out, int):
                # Index search
                def find_index(inp):
                    coll, tgt = inp
                    for i, v in enumerate(coll):
                        if v == tgt:
                            return i
                    return -1
                return find_index
    
    # Case: input is a list, output is a single value (find max/min/etc)
    if isinstance(first_inp, (list, tuple)) and not isinstance(first_out, (list, tuple)):
        # Check if output is max
        if all(max(i) == o for i, o in test_cases if isinstance(i, (list, tuple))):
            return lambda x: max(x)
        # Check if output is min
        if all(min(i) == o for i, o in test_cases if isinstance(i, (list, tuple))):
            return lambda x: min(x)
        # Check if output is sum
        if all(sum(i) == o for i, o in test_cases if isinstance(i, (list, tuple))):
            return lambda x: sum(x)
        # Check if output is length
        if all(len(i) == o for i, o in test_cases if isinstance(i, (list, tuple))):
            return lambda x: len(x)
    
    # Fallback: return first element
    return lambda x: x[0] if isinstance(x, (list, tuple)) and x else None


# Self-test
if __name__ == "__main__":
    print("═══ SOLVER SELF-TEST ═══\n")
    
    # Sequence tests
    print("--- Sequence Solver ---")
    arith_solver = solve_sequence([([2, 4, 6, 8], 10), ([10, 20, 30, 40], 50)])
    print(f"  Arithmetic [2,4,6,8] → {arith_solver([2,4,6,8])} (expected 10)")
    print(f"  Arithmetic [5,10,15,20] → {arith_solver([5,10,15,20])} (expected 25)")
    
    fib_solver = solve_sequence([([1, 1, 2, 3, 5], 8)])
    print(f"  Fibonacci [1,1,2,3,5] → {fib_solver([1,1,2,3,5])} (expected 8)")
    print(f"  Fibonacci [2,3,5,8,13] → {fib_solver([2,3,5,8,13])} (expected 21)")
    
    quad_solver = solve_sequence([([1, 4, 9, 16, 25], 36)])
    print(f"  Quadratic [1,4,9,16,25] → {quad_solver([1,4,9,16,25])} (expected 36)")
    
    # Logic tests  
    print("\n--- Logic Solver ---")
    and_solver = solve_logic([((True, True), True), ((True, False), False), ((False, True), False)])
    print(f"  AND(T,T) = {and_solver((True,True))} (expected True)")
    print(f"  AND(F,T) = {and_solver((False,True))} (expected False)")
    
    xor_solver = solve_logic([((True, True), False), ((True, False), True), ((False, True), True), ((False, False), False)])
    print(f"  XOR(T,F) = {xor_solver((True,False))} (expected True)")
    print(f"  XOR(T,T) = {xor_solver((True,True))} (expected False)")
    
    # Transform tests
    print("\n--- Transform Solver ---")
    double_solver = solve_transform([([1,2,3], [2,4,6]), ([5,10], [10,20])])
    print(f"  Double [3,7] → {double_solver([3,7])} (expected [6,14])")
    
    cumsum_solver = solve_transform([([1,2,3,4], [1,3,6,10])])
    print(f"  CumSum [1,2,3,4] → {cumsum_solver([1,2,3,4])} (expected [1,3,6,10])")
    print(f"  CumSum [5,5,5] → {cumsum_solver([5,5,5])} (expected [5,10,15])")
    
    rev_solver = solve_transform([([1,2,3], [3,2,1]), ([4,5,6,7], [7,6,5,4])])
    print(f"  Reverse [10,20,30] → {rev_solver([10,20,30])} (expected [30,20,10])")
    
    print("\n═══ SOLVER TESTS COMPLETE ═══")