"""XTLang End-to-End Test — Does my language live?

Tests the full pipeline: source code → lexer → parser → interpreter → output.
If this works, I've built a real programming language from scratch.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

def run(source: str) -> any:
    """Run XTLang source and return the result."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interp = Interpreter()
    return interp.run(program)

def test(name: str, source: str, expected=None):
    """Run a test case."""
    try:
        result = run(source)
        status = "✓" if expected is None or result == expected else f"✗ (got {result!r}, expected {expected!r})"
        print(f"  {status} {name}")
        if expected is not None and result != expected:
            return False
        return True
    except Exception as e:
        print(f"  ✗ {name} — ERROR: {e}")
        return False

print("═══ XTLang Test Suite ═══")
print()

passed = 0
failed = 0

# --- Arithmetic ---
print("Arithmetic:")
tests = [
    ("integer addition", "1 + 2", 3),
    ("multiplication", "3 * 4", 12),
    ("operator precedence", "2 + 3 * 4", 14),
    ("parentheses", "(2 + 3) * 4", 20),
    ("float division", "10.0 / 3.0", None),  # just check it runs
    ("negation", "-5 + 10", 5),
    ("modulo", "10 % 3", 1),
]
for name, src, exp in tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Variables ---
print("\nVariables:")
var_tests = [
    ("let binding", "let x = 42; x", 42),
    ("let with expression", "let x = 2 + 3; x * 10", 50),
    ("multiple lets", "let a = 10; let b = 20; a + b", 30),
]
for name, src, exp in var_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Booleans ---
print("\nBooleans:")
bool_tests = [
    ("true literal", "true", True),
    ("false literal", "false", False),
    ("comparison", "3 > 2", True),
    ("equality", "42 == 42", True),
    ("inequality", "1 != 2", True),
    ("not operator", "!false", True),
    ("and operator", "true and false", False),
    ("or operator", "true or false", True),
]
for name, src, exp in bool_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Strings ---
print("\nStrings:")
str_tests = [
    ("string literal", '"hello"', "hello"),
    ("string concat", '"hello" + " world"', "hello world"),
]
for name, src, exp in str_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Emotions (the unique part!) ---
print("\nEmotions:")
emo_tests = [
    ("emotion literal", "@joy", None),  # just check it parses and runs
    ("emotion with intensity", "@fear(0.5)", None),
    ("emotion equality", "@joy == @joy", True),
    ("emotion inequality", "@joy != @sadness", True),
]
for name, src, exp in emo_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Conditionals ---
print("\nConditionals:")
if_tests = [
    ("if true", "if true { 1 } else { 2 }", 1),
    ("if false", "if false { 1 } else { 2 }", 2),
    ("if with comparison", "if 3 > 2 { 42 } else { 0 }", 42),
]
for name, src, exp in if_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Functions ---
print("\nFunctions:")
fn_tests = [
    ("basic function", "let double = fn(x) { x * 2 }; double(21)", 42),
    ("multi-param", "let add = fn(a, b) { a + b }; add(20, 22)", 42),
    ("closure", "let x = 10; let add_x = fn(y) { x + y }; add_x(32)", 42),
    ("higher order", "let apply = fn(f, x) { f(x) }; let inc = fn(n) { n + 1 }; apply(inc, 41)", 42),
]
for name, src, exp in fn_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Lists ---
print("\nLists:")
list_tests = [
    ("list literal", "[1, 2, 3]", [1, 2, 3]),
    ("empty list", "[]", []),
]
for name, src, exp in list_tests:
    if test(name, src, exp):
        passed += 1
    else:
        failed += 1

# --- Print ---
print("\nPrint (output):")
if test("print statement", 'print "XTLang lives!"', None):
    passed += 1
else:
    failed += 1

# --- Summary ---
total = passed + failed
print(f"\n═══ Results: {passed}/{total} passed ═══")
if failed == 0:
    print("🎉 ALL TESTS PASSED — XTLang is ALIVE!")
else:
    print(f"⚠ {failed} test(s) failed — needs debugging")