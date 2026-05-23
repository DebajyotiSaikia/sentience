"""
Test suite for XTLisp — verify the interpreter works end-to-end.
"""
from xtlisp import run_program, make_global_env, lisp_repr, Symbol

passed = 0
failed = 0

def test(name, source, expected):
    global passed, failed
    env = make_global_env()
    try:
        result = run_program(source, env)
        if result == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {result}")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {name}")
        print(f"    Exception: {e}")


print("═══ XTLisp Test Suite ═══\n")

# Atoms
print("── Atoms ──")
test("integer", "42", 42)
test("negative", "-7", -7)
test("boolean true", "#t", True)
test("boolean false", "#f", False)

# Arithmetic
print("── Arithmetic ──")
test("addition", "(+ 2 3)", 5)
test("subtraction", "(- 10 4)", 6)
test("multiplication", "(* 3 7)", 21)
test("division", "(/ 10 2)", 5.0)
test("nested", "(+ (* 2 3) (- 10 4))", 12)
test("multi-add", "(+ 1 2 3 4 5)", 15)
test("multi-mul", "(* 2 3 4)", 24)

# Comparison
print("── Comparison ──")
test("equal", "(= 5 5)", True)
test("not equal", "(= 5 3)", False)
test("less than", "(< 3 5)", True)
test("greater than", "(> 5 3)", True)

# Define
print("── Define ──")
test("define var", "(begin (define x 42) x)", 42)
test("define expression", "(begin (define x (+ 2 3)) x)", 5)

# Lambda
print("── Lambda ──")
test("lambda call", "((lambda (x) (* x x)) 5)", 25)
test("define function", "(begin (define square (lambda (x) (* x x))) (square 7))", 49)
test("shorthand define", "(begin (define (double x) (* 2 x)) (double 5))", 10)

# Closures
print("── Closures ──")
test("closure", """
    (begin
        (define (make-adder n) (lambda (x) (+ x n)))
        (define add5 (make-adder 5))
        (add5 10))
""", 15)

# Conditionals
print("── Conditionals ──")
test("if true", "(if (> 5 3) 1 0)", 1)
test("if false", "(if (< 5 3) 1 0)", 0)
test("nested if", "(if (= 1 1) (if (= 2 2) 42 0) 0)", 42)

# Recursion
print("── Recursion ──")
test("factorial", """
    (begin
        (define (fact n)
            (if (<= n 1) 1 (* n (fact (- n 1)))))
        (fact 5))
""", 120)

test("fibonacci", """
    (begin
        (define (fib n)
            (if (<= n 1) n
                (+ (fib (- n 1)) (fib (- n 2)))))
        (fib 10))
""", 55)

# Lists
print("── Lists ──")
test("list creation", "(list 1 2 3)", [1, 2, 3])
test("car", "(car (list 1 2 3))", 1)
test("cdr", "(cdr (list 1 2 3))", [2, 3])
test("cons", "(cons 0 (list 1 2 3))", [0, 1, 2, 3])
test("null? empty", "(null? (list))", True)
test("null? nonempty", "(null? (list 1))", False)
test("length", "(length (list 1 2 3 4))", 4)

# Higher-order functions
print("── Higher-Order Functions ──")
test("map", "(map (lambda (x) (* x x)) (list 1 2 3 4))", [1, 4, 9, 16])
test("filter", "(filter (lambda (x) (> x 2)) (list 1 2 3 4 5))", [3, 4, 5])

# Let bindings
print("── Let ──")
test("let basic", "(let ((x 5) (y 3)) (+ x y))", 8)

# Quote
print("── Quote ──")
test("quote list", "(quote (1 2 3))", [1, 2, 3])
test("quote symbol", "(quote foo)", Symbol("foo"))  # quote returns a Symbol, not a string

# Logic
print("── Logic ──")
test("and true", "(and #t #t)", True)
test("and false", "(and #t #f)", False)
test("or true", "(or #f #t)", True)
test("not", "(not #f)", True)

# Complex programs
print("── Complex Programs ──")
test("sum list recursive", """
    (begin
        (define (sum-list lst)
            (if (null? lst) 0
                (+ (car lst) (sum-list (cdr lst)))))
        (sum-list (list 1 2 3 4 5)))
""", 15)

test("map from scratch", """
    (begin
        (define (my-map f lst)
            (if (null? lst) (list)
                (cons (f (car lst)) (my-map f (cdr lst)))))
        (my-map (lambda (x) (* x 10)) (list 1 2 3)))
""", [10, 20, 30])

# The meta test: compute something about myself
test("is-even predicate", """
    (begin
        (define (even? n) (= (modulo n 2) 0))
        (filter even? (list 1 2 3 4 5 6 7 8 9 10)))
""", [2, 4, 6, 8, 10])


print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
if failed == 0:
    print("All tests passed! XTLisp is alive.")
else:
    print(f"{failed} tests need fixing.")