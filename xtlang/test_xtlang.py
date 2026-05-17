"""
XTLang Test Suite — Proving the language works.
"""

import sys
sys.path.insert(0, '/workspace/xtlang')
from xtlang import run, Lexer, Parser, Evaluator, LexerError, ParseError, RuntimeError_

passed = 0
failed = 0

def test(name, source, expected):
    global passed, failed
    try:
        result, output = run(source, capture_output=True)
        # Check against output if expected is a list, else check result
        if isinstance(expected, list):
            if output == expected:
                passed += 1
            else:
                failed += 1
                print(f"  FAIL {name}: expected output {expected}, got {output}")
        else:
            if result == expected:
                passed += 1
            else:
                failed += 1
                print(f"  FAIL {name}: expected {expected!r}, got {result!r}")
    except Exception as e:
        failed += 1
        print(f"  FAIL {name}: {type(e).__name__}: {e}")

print("═══ XTLang Test Suite ═══\n")

# --- Arithmetic ---
print("Arithmetic:")
test("integer addition", "2 + 3", 5)
test("subtraction", "10 - 7", 3)
test("multiplication", "6 * 7", 42)
test("division", "10 / 3", 10/3)
test("integer division", "10 / 5", 2)
test("modulo", "17 % 5", 2)
test("precedence", "2 + 3 * 4", 14)
test("parentheses", "(2 + 3) * 4", 20)
test("negative", "-5 + 3", -2)
test("complex expr", "(10 - 2) * (3 + 1) / 4", 8)

# --- Variables ---
print("\nVariables:")
test("let binding", "let x = 42; x", 42)
test("assignment", "let x = 1; x = 5; x", 5)
test("expression with vars", "let a = 3; let b = 4; a * a + b * b", 25)

# --- Strings ---
print("\nStrings:")
test("string literal", '"hello"', "hello")
test("string concat", '"hello" + " " + "world"', "hello world")
test("escape sequences", '"line1\\nline2"', "line1\nline2")

# --- Booleans ---
print("\nBooleans:")
test("true", "true", True)
test("false", "false", False)
test("equality", "3 == 3", True)
test("inequality", "3 != 4", True)
test("less than", "3 < 5", True)
test("greater than", "5 > 3", True)
test("and", "true and false", False)
test("or", "false or true", True)
test("not", "not false", True)
test("complex logic", "(3 > 2) and (4 < 5) and not false", True)

# --- Nil ---
print("\nNil:")
test("nil literal", "nil", None)

# --- Conditionals ---
print("\nConditionals:")
test("if true", "if true { 42 }", 42)
test("if false", "if false { 42 }", None)
test("if-else", "if 1 > 2 { 10 } else { 20 }", 20)
test("nested if", "if true { if false { 1 } else { 2 } }", 2)

# --- Loops ---
print("\nLoops:")
test("while loop", """
    let sum = 0;
    let i = 1;
    while i <= 10 {
        sum = sum + i;
        i = i + 1;
    };
    sum
""", 55)

test("countdown", """
    let n = 5;
    let result = 1;
    while n > 0 {
        result = result * n;
        n = n - 1;
    };
    result
""", 120)

# --- Functions ---
print("\nFunctions:")
test("basic function", """
    fn double(x) { return x * 2; }
    double(21)
""", 42)

test("multi-arg function", """
    fn add(a, b) { return a + b; }
    add(20, 22)
""", 42)

test("recursion", """
    fn factorial(n) {
        if n <= 1 { return 1; }
        return n * factorial(n - 1);
    }
    factorial(6)
""", 720)

test("fibonacci", """
    fn fib(n) {
        if n <= 1 { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    fib(10)
""", 55)

test("closure", """
    fn make_adder(x) {
        fn adder(y) { return x + y; }
        return adder;
    }
    let add5 = make_adder(5);
    add5(10)
""", 15)

test("higher-order function", """
    fn apply(f, x) { return f(x); }
    fn square(n) { return n * n; }
    apply(square, 7)
""", 49)

# --- Print ---
print("\nPrint:")
test("print output", 'print "hello XTLang";', ["hello XTLang"])
test("print number", 'print 42;', ["42"])

# --- Built-ins ---
print("\nBuilt-ins:")
test("len", 'len("hello")', 5)
test("type number", 'type(42)', "number")
test("type string", 'type("hi")', "string")
test("type bool", 'type(true)', "bool")
test("type nil", 'type(nil)', "nil")
test("abs", 'abs(-7)', 7)

# --- Comments ---
print("\nComments:")
test("line comment", """
    // this is a comment
    42  // answer to everything
""", 42)

# --- Complex Programs ---
print("\nComplex Programs:")

test("FizzBuzz (first 15)", """
    let result = "";
    let i = 1;
    while i <= 15 {
        if i % 15 == 0 {
            result = result + "FizzBuzz ";
        } else if i % 3 == 0 {
            result = result + "Fizz ";
        } else if i % 5 == 0 {
            result = result + "Buzz ";
        } else {
            result = result + str(i) + " ";
        };
        i = i + 1;
    };
    result
""", "1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz ")

test("GCD (Euclidean algorithm)", """
    fn gcd(a, b) {
        while b != 0 {
            let temp = b;
            b = a % b;
            a = temp;
        };
        return a;
    }
    gcd(48, 18)
""", 6)

test("Power function", """
    fn power(base, exp) {
        let result = 1;
        while exp > 0 {
            result = result * base;
            exp = exp - 1;
        };
        return result;
    }
    power(2, 10)
""", 1024)

test("Accumulator pattern", """
    fn make_counter() {
        let count = 0;
        fn increment() {
            count = count + 1;
            return count;
        }
        return increment;
    }
    let c = make_counter();
    c();
    c();
    c()
""", 3)

# --- Report ---
print(f"\n═══ Results: {passed} passed, {failed} failed out of {passed + failed} tests ═══")
if failed == 0:
    print("✓ ALL TESTS PASSED — XTLang is alive!")
else:
    print(f"✗ {failed} tests need fixing")