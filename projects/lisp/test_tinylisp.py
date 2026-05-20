"""Test suite for TinyLisp — prove the interpreter actually works."""
from tinylisp import run, lisp_str

passed = 0
failed = 0

def test(name, source, expected):
    global passed, failed
    try:
        result, _ = run(source)
        result_str = lisp_str(result)
        if result_str == expected:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}: expected {expected}, got {result_str}")
            failed += 1
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        failed += 1

print("═══ TinyLisp Test Suite ═══\n")

print("── Atoms & Arithmetic ──")
test("integer", "42", "42")
test("negative", "-7", "-7")
test("float", "3.14", "3.14")
test("addition", "(+ 2 3)", "5")
test("nested math", "(+ (* 3 4) (- 10 5))", "17")
test("variadic add", "(+ 1 2 3 4 5)", "15")
test("variadic mul", "(* 2 3 4)", "24")

print("\n── Booleans & Comparison ──")
test("true", "#t", "#t")
test("false", "#f", "#f")
test("equal", "(= 3 3)", "#t")
test("less than", "(< 2 5)", "#t")
test("not", "(not #f)", "#t")

print("\n── Strings ──")
test("string literal", '"hello"', '"hello"')

print("\n── Define & Variables ──")
test("define", "(begin (define x 42) x)", "42")
test("define expr", "(begin (define y (+ 10 20)) y)", "30")

print("\n── Conditionals ──")
test("if true", "(if #t 1 2)", "1")
test("if false", "(if #f 1 2)", "2")
test("if computed", "(if (> 5 3) (+ 10 20) 0)", "30")
test("cond", "(cond ((= 1 2) 10) ((= 1 1) 20) (else 30))", "20")

print("\n── Lambda ──")
test("lambda call", "((lambda (x) (* x x)) 5)", "25")
test("closure", """
    (begin
      (define make-adder (lambda (n) (lambda (x) (+ n x))))
      (define add5 (make-adder 5))
      (add5 10))
""", "15")

print("\n── Syntactic Sugar ──")
test("define-function", """
    (begin
      (define (square x) (* x x))
      (square 7))
""", "49")

print("\n── Recursion ──")
test("factorial", """
    (begin
      (define (fact n)
        (if (<= n 1) 1 (* n (fact (- n 1)))))
      (fact 10))
""", "3628800")

test("fibonacci", """
    (begin
      (define (fib n)
        (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2)))))
      (fib 10))
""", "55")

print("\n── Lists ──")
test("list create", "(list 1 2 3)", "(1 2 3)")
test("car", "(car (list 1 2 3))", "1")
test("cdr", "(cdr (list 1 2 3))", "(2 3)")
test("cons", "(cons 0 (list 1 2))", "(0 1 2)")
test("null?", "(null? (list))", "#t")
test("length", "(length (list 1 2 3 4))", "4")

print("\n── Higher-Order Functions ──")
test("map", """
    (begin
      (define (double x) (* 2 x))
      (map double (list 1 2 3 4)))
""", "(2 4 6 8)")

test("filter", """
    (begin
      (define (even? x) (= (% x 2) 0))
      (filter even? (list 1 2 3 4 5 6)))
""", "(2 4 6)")

print("\n── Let Bindings ──")
test("let", "(let ((x 10) (y 20)) (+ x y))", "30")

print("\n── Complex Programs ──")
test("accumulate", """
    (begin
      (define (accumulate f init lst)
        (if (null? lst)
          init
          (accumulate f (f init (car lst)) (cdr lst))))
      (accumulate + 0 (list 1 2 3 4 5)))
""", "15")

test("compose", """
    (begin
      (define (compose f g) (lambda (x) (f (g x))))
      (define (add1 x) (+ x 1))
      (define (double x) (* x 2))
      (define double-then-add1 (compose add1 double))
      (double-then-add1 5))
""", "11")

test("mutual recursion via define", """
    (begin
      (define (even? n) (if (= n 0) #t (odd? (- n 1))))
      (define (odd? n) (if (= n 0) #f (even? (- n 1))))
      (list (even? 10) (odd? 7) (even? 3)))
""", "(#t #t #f)")

print(f"\n{'═'*40}")
print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
if failed == 0:
    print("All tests passed! ✓")
else:
    print(f"⚠ {failed} test(s) failed")