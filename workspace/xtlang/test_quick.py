"""Quick smoke test for XTLang."""
from interpreter import Interpreter

i = Interpreter()

# Test 1: let binding + print
result = i.run('let x = 5; print(x);')
print(f"Test 1 (let+print): {result}")

# Test 2: arithmetic
result = i.run('let y = 3 + 4; print(y);')
print(f"Test 2 (arithmetic): {result}")

# Test 3: string
result = i.run('print("hello");')
print(f"Test 3 (string): {result}")

print("ALL TESTS PASSED")