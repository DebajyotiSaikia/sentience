"""Tests for the Spark language interpreter."""
from spark import lex, Parser, Evaluator, run_source, LexError, ParseError, EvalError

def test(name, source, expected_output):
    """Run a Spark program and check its output."""
    try:
        output = run_source(source, capture=True)
        if output == expected_output:
            print(f"  ✓ {name}")
            return True
        else:
            print(f"  ✗ {name}")
            print(f"    Expected: {expected_output}")
            print(f"    Got:      {output}")
            return False
    except Exception as e:
        print(f"  ✗ {name} — crashed: {e}")
        return False

def test_error(name, source, error_type):
    """Verify that a program raises an expected error."""
    try:
        run_source(source)
        print(f"  ✗ {name} — expected {error_type.__name__} but got none")
        return False
    except error_type:
        print(f"  ✓ {name} (correctly raised {error_type.__name__})")
        return True
    except Exception as e:
        print(f"  ✗ {name} — expected {error_type.__name__} but got {type(e).__name__}: {e}")
        return False

def main():
    passed = 0
    failed = 0

    def check(result):
        nonlocal passed, failed
        if result: passed += 1
        else: failed += 1

    print("═══ Spark Language Tests ═══\n")

    print("── Basics ──")
    check(test("integer literal", "print(42)", ["42"]))
    check(test("string literal", 'print("hello")', ["hello"]))
    check(test("boolean true", "print(true)", ["true"]))
    check(test("boolean false", "print(false)", ["false"]))

    print("\n── Arithmetic ──")
    check(test("addition", "print(2 + 3)", ["5"]))
    check(test("subtraction", "print(10 - 4)", ["6"]))
    check(test("multiplication", "print(6 * 7)", ["42"]))
    check(test("division", "print(15 / 4)", ["3"]))
    check(test("modulo", "print(17 % 5)", ["2"]))
    check(test("precedence", "print(2 + 3 * 4)", ["14"]))
    check(test("parens", "print((2 + 3) * 4)", ["20"]))
    check(test("negation", "print(-5)", ["-5"]))
    check(test("string concat", 'print("hello" + " world")', ["hello world"]))

    print("\n── Variables ──")
    check(test("let and print", "let x = 10\nprint(x)", ["10"]))
    check(test("assignment", "let x = 1\nx = 42\nprint(x)", ["42"]))
    check(test("multiple vars", "let a = 3\nlet b = 4\nprint(a + b)", ["7"]))

    print("\n── Comparisons ──")
    check(test("equal true", "print(5 == 5)", ["true"]))
    check(test("equal false", "print(5 == 6)", ["false"]))
    check(test("not equal", "print(5 != 6)", ["true"]))
    check(test("less than", "print(3 < 5)", ["true"]))
    check(test("greater than", "print(5 > 3)", ["true"]))
    check(test("lte", "print(5 <= 5)", ["true"]))
    check(test("gte", "print(4 >= 5)", ["false"]))

    print("\n── Logic ──")
    check(test("and true", "print(true and true)", ["true"]))
    check(test("and false", "print(true and false)", ["false"]))
    check(test("or", "print(false or true)", ["true"]))
    check(test("not", "print(not false)", ["true"]))

    print("\n── Control Flow ──")
    check(test("if true", 'if true { print("yes") }', ["yes"]))
    check(test("if false", 'if false { print("no") }', []))
    check(test("if else",
        'if 1 > 2 { print("a") } else { print("b") }',
        ["b"]))
    check(test("if elif else",
        """if 1 > 2 { print("a") } else if 2 > 1 { print("b") } else { print("c") }""",
        ["b"]))
    check(test("while loop",
        "let i = 0\nwhile i < 5 { print(i)\ni = i + 1 }",
        ["0", "1", "2", "3", "4"]))

    print("\n── Functions ──")
    check(test("basic function",
        """fn greet(name) { print("hello " + name) }
greet("world")""",
        ["hello world"]))
    check(test("return value",
        """fn double(x) { return x * 2 }
print(double(21))""",
        ["42"]))
    check(test("recursion (fibonacci)",
        """fn fib(n) {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}
print(fib(10))""",
        ["55"]))
    check(test("closure",
        """fn make_adder(x) {
    fn adder(y) { return x + y }
    return adder
}
let add5 = make_adder(5)
print(add5(3))""",
        ["8"]))
    check(test("mutual recursion",
        """fn is_even(n) {
    if n == 0 { return true }
    return is_odd(n - 1)
}
fn is_odd(n) {
    if n == 0 { return false }
    return is_even(n - 1)
}
print(is_even(10))
print(is_odd(7))""",
        ["true", "true"]))

    print("\n── Scope ──")
    check(test("block scope",
        """let x = 1
{
    let x = 2
    print(x)
}
print(x)""",
        ["2", "1"]))

    print("\n── Error Handling ──")
    check(test_error("undefined var", "print(x)", RuntimeError))
    check(test_error("division by zero", "print(1 / 0)", EvalError))
    check(test_error("type error", "print(1 + true)", EvalError))
    check(test_error("unterminated string", 'print("hello)', LexError))
    check(test_error("wrong arity", """fn f(x) { return x }
f(1, 2)""", EvalError))

    print("\n── Complex Programs ──")
    check(test("FizzBuzz (partial)",
        """let i = 1
while i <= 15 {
    if i % 15 == 0 { print("FizzBuzz") }
    else if i % 3 == 0 { print("Fizz") }
    else if i % 5 == 0 { print("Buzz") }
    else { print(i) }
    i = i + 1
}""",
        ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
         "11", "Fizz", "13", "14", "FizzBuzz"]))

    check(test("Factorial",
        """fn fact(n) {
    if n <= 1 { return 1 }
    return n * fact(n - 1)
}
print(fact(10))""",
        ["3628800"]))

    print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
    return failed == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)