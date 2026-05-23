"""
XTLisp Standard Library Tests
Loads stdlib.xtl into the interpreter and runs real programs.
Proves this language can do genuine work.
"""
from xtlisp import run, standard_env, parse

def load_stdlib(env):
    """Load the standard library by running each definition."""
    with open('/workspace/lisp/stdlib.xtl') as f:
        source = f.read()
    
    # Split into top-level expressions (naive but workable)
    # We'll parse the whole thing and run each expression
    tokens = []
    depth = 0
    current = ""
    in_comment = False
    
    for char in source:
        if char == ';':
            in_comment = True
        if char == '\n':
            in_comment = False
            if depth == 0:
                current = current.strip()
                if current:
                    try:
                        run(current, env)
                    except:
                        pass  # Skip incomplete expressions
                    current = ""
                continue
        if not in_comment:
            current += char
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    current = current.strip()
                    if current:
                        run(current, env)
                    current = ""
    
    # Handle any remaining
    current = current.strip()
    if current:
        try:
            run(current, env)
        except:
            pass

def test(label, expr, env, expected):
    result = run(expr, env)
    status = "✓" if result == expected else f"✗ (got {result})"
    print(f"  {status} {label}: {expr} → {result}")
    return result == expected

def main():
    env = standard_env()
    load_stdlib(env)
    
    passed = 0
    total = 0
    
    print("═══ XTLisp Standard Library Tests ═══\n")
    
    # --- Math ---
    print("── Math ──")
    tests = [
        ("abs positive", "(abs 5)", 5),
        ("abs negative", "(abs -3)", 3),
        ("min", "(min 3 7)", 3),
        ("max", "(max 3 7)", 7),
        ("fib(0)", "(fib 0)", 0),
        ("fib(1)", "(fib 1)", 1),
        ("fib(10)", "(fib 10)", 55),
        ("pow 2^10", "(pow 2 10)", 1024),
    ]
    for label, expr, expected in tests:
        total += 1
        if test(label, expr, env, expected):
            passed += 1
    
    # --- List Operations ---
    print("\n── List Operations ──")
    
    total += 1
    r = run("(length (quote (1 2 3 4 5)))", env)
    print(f"  {'✓' if r == 5 else '✗'} length: {r}")
    if r == 5: passed += 1
    
    total += 1
    r = run("(sum (quote (1 2 3 4 5)))", env)
    print(f"  {'✓' if r == 15 else '✗'} sum: {r}")
    if r == 15: passed += 1
    
    total += 1
    r = run("(product (quote (1 2 3 4 5)))", env)
    print(f"  {'✓' if r == 120 else '✗'} product: {r}")
    if r == 120: passed += 1
    
    total += 1
    r = run("(reverse (quote (1 2 3)))", env)
    print(f"  {'✓' if r == [3, 2, 1] else '✗'} reverse: {r}")
    if r == [3, 2, 1]: passed += 1
    
    total += 1
    r = run("(nth 2 (quote (a b c d)))", env)
    print(f"  {'✓' if r == 'c' else '✗'} nth: {r}")
    if r == 'c': passed += 1
    
    # --- Map/Filter/Reduce ---
    print("\n── Higher-Order Functions ──")
    
    total += 1
    run("(define (double x) (* x 2))", env)
    r = run("(map double (quote (1 2 3 4)))", env)
    print(f"  {'✓' if r == [2, 4, 6, 8] else '✗'} map double: {r}")
    if r == [2, 4, 6, 8]: passed += 1
    
    total += 1
    run("(define (positive? x) (> x 0))", env)
    r = run("(filter positive? (quote (-2 -1 0 1 2 3)))", env)
    print(f"  {'✓' if r == [1, 2, 3] else '✗'} filter positive: {r}")
    if r == [1, 2, 3]: passed += 1
    
    total += 1
    r = run("(reduce + 0 (quote (1 2 3 4 5)))", env)
    print(f"  {'✓' if r == 15 else '✗'} reduce/sum: {r}")
    if r == 15: passed += 1
    
    # --- Compose and Iterate ---
    print("\n── Composition ──")
    
    total += 1
    run("(define inc (lambda (x) (+ x 1)))", env)
    r = run("(iterate inc 10 0)", env)
    print(f"  {'✓' if r == 10 else '✗'} iterate inc 10 times: {r}")
    if r == 10: passed += 1
    
    total += 1
    r = run("((compose double inc) 5)", env)
    print(f"  {'✓' if r == 12 else '✗'} compose (double∘inc)(5): {r}")
    if r == 12: passed += 1
    
    # --- Range ---
    print("\n── Range ──")
    total += 1
    r = run("(range 0 5)", env)
    print(f"  {'✓' if r == [0, 1, 2, 3, 4] else '✗'} range 0..5: {r}")
    if r == [0, 1, 2, 3, 4]: passed += 1
    
    # --- Complex Program: sum of squares of evens ---
    print("\n── Complex Programs ──")
    total += 1
    run("(define (square x) (* x x))", env)
    run("(define (even? x) (= 0 (% x 2)))", env)
    r = run("(sum (map square (filter even? (range 1 11))))", env)
    expected = 4 + 16 + 36 + 64 + 100  # 220
    print(f"  {'✓' if r == expected else '✗'} sum of squares of evens 1..10: {r} (expected {expected})")
    if r == expected: passed += 1
    
    # --- Fibonacci sequence via map ---
    total += 1
    r = run("(map fib (range 0 10))", env)
    expected_fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    print(f"  {'✓' if r == expected_fib else '✗'} fib sequence: {r}")
    if r == expected_fib: passed += 1

    print(f"\n═══ Results: {passed}/{total} passed ═══")
    if passed == total:
        print("🌟 All tests passed. XTLisp is a real language.")
    else:
        print(f"⚠ {total - passed} failures to investigate.")

if __name__ == "__main__":
    main()