"""End-to-end XTLang test suite."""
import sys
sys.path.insert(0, '.')

from lexer import Lexer
from parser import Parser, pretty_print
from interpreter import Interpreter, Environment

def test_lex_parse_run(source, expected_output=None, label=""):
    """Full pipeline: lex -> parse -> interpret."""
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(lexer)
        ast = parser.parse()
        
        interp = Interpreter()
        result = interp.run(ast)
        
        actual = interp.output[-1] if interp.output else str(result)
        
        if expected_output is not None:
            if actual == expected_output:
                print(f"  PASS: {label}")
                return True
            else:
                print(f"  FAIL: {label} -- expected '{expected_output}', got '{actual}'")
                return False
        else:
            print(f"  PASS: {label} -> {actual}")
            return True
    except Exception as e:
        print(f"  FAIL: {label} -- {type(e).__name__}: {e}")
        return False

# ===== TEST SUITE =====
tests = [
    # Basic values
    ("let x = 42; print(x);", "42", "integer assignment"),
    ("let s = \"hello\"; print(s);", "hello", "string assignment"),
    
    # Arithmetic
    ("let a = 3; let b = 4; print(a + b);", "7", "addition"),
    ("let r = 10 - 3; print(r);", "7", "subtraction"),
    ("let r = 6 * 7; print(r);", "42", "multiplication"),
    
    # Comparison
    ("let x = 5; if x > 3 then print(\"yes\") else print(\"no\");", "yes", "if-then-else"),
    
    # Functions
    ("fn square(n) { n * n; }; print(square(7));", "49", "function call"),
    
    # While loop
    ("let i = 0; while i < 5 { let i = i + 1; }; print(i);", "5", "while loop"),
    
    # Nested expressions
    ("print(2 + 3 * 4);", "14", "operator precedence"),
    
    # Booleans
    ("print(true and false);", "False", "boolean and"),
    ("print(true or false);", "True", "boolean or"),
]

passed = 0
total = len(tests)

print("=" * 50)
print("XTLang End-to-End Test Suite")
print("=" * 50)

for source, expected, label in tests:
    if test_lex_parse_run(source, expected, label):
        passed += 1

print("=" * 50)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASSED -- XTLang is alive!")
else:
    print(f"{total - passed} tests need fixing.")
print("=" * 50)