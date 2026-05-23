"""Test XTLang list support and higher-order functions."""
import sys
sys.path.insert(0, '/workspace/xtlang')
from xtlang import run

passed = 0
failed = 0

def test(name, source, expected):
    global passed, failed
    try:
        result, output = run(source, capture_output=True)
        # Check printed output if expected is a list of strings
        if isinstance(expected, list):
            if output == expected:
                passed += 1
                print(f"  ✓ {name}")
            else:
                failed += 1
                print(f"  ✗ {name}: expected output {expected}, got {output}")
        else:
            if result == expected:
                passed += 1
                print(f"  ✓ {name}")
            else:
                failed += 1
                print(f"  ✗ {name}: expected {expected!r}, got {result!r}")
    except Exception as e:
        failed += 1
        print(f"  ✗ {name}: EXCEPTION: {e}")

print("═══ LIST LITERALS ═══")
test("empty list", "[]", [])
test("number list", "[1, 2, 3]", [1, 2, 3])
test("mixed list", "[1, \"hello\", true, nil]", [1, "hello", True, None])
test("nested list", "[[1, 2], [3, 4]]", [[1, 2], [3, 4]])
test("expression list", "[1 + 1, 2 * 3, 10 - 4]", [2, 6, 6])

print("\n═══ INDEX ACCESS ═══")
test("first element", "let a = [10, 20, 30]; a[0]", 10)
test("last element", "let a = [10, 20, 30]; a[2]", 30)
test("nested index", "let m = [[1,2],[3,4]]; m[1][0]", 3)
test("string index", "let s = \"hello\"; s[0]", "h")

print("\n═══ INDEX ASSIGNMENT ═══")
test("set element", "let a = [1, 2, 3]; a[1] = 99; a[1]", 99)
test("list after assign", """
let a = [1, 2, 3]
a[0] = 10
a[2] = 30
print a
""", ["[10, 2, 30]"])

print("\n═══ LIST BUILTINS ═══")
test("len of list", "len([1, 2, 3])", 3)
test("len empty", "len([])", 0)
test("push", "let a = [1, 2]; push(a, 3); a", [1, 2, 3])
test("pop", "let a = [1, 2, 3]; pop(a)", 3)
test("pop modifies", "let a = [1, 2, 3]; pop(a); a", [1, 2])
test("range 1 arg", "range(5)", [0, 1, 2, 3, 4])
test("range 2 args", "range(2, 6)", [2, 3, 4, 5])
test("range 3 args", "range(0, 10, 3)", [0, 3, 6, 9])

print("\n═══ HIGHER-ORDER FUNCTIONS ═══")
test("map double", """
fn double(x) { return x * 2 }
map(double, [1, 2, 3, 4])
""", [2, 4, 6, 8])

test("filter even", """
fn is_even(x) { return x % 2 == 0 }
filter(is_even, [1, 2, 3, 4, 5, 6])
""", [2, 4, 6])

test("reduce sum", """
fn add(a, b) { return a + b }
reduce(add, [1, 2, 3, 4, 5], 0)
""", 15)

test("map with anonymous fn", """
map(fn(x) { return x * x }, [1, 2, 3, 4, 5])
""", [1, 4, 9, 16, 25])

test("filter with closure", """
let threshold = 3
fn above(x) { return x > threshold }
filter(above, [1, 2, 3, 4, 5])
""", [4, 5])

test("chained: map then filter", """
fn double(x) { return x * 2 }
fn big(x) { return x > 5 }
filter(big, map(double, [1, 2, 3, 4, 5]))
""", [6, 8, 10])

test("reduce to build string", """
fn concat(a, b) { return a + str(b) }
reduce(concat, [1, 2, 3], "nums: ")
""", "nums: 123")

print("\n═══ REAL PROGRAMS ═══")

test("fibonacci list", """
let fibs = [0, 1]
let i = 2
while i < 10 {
    let next = fibs[i - 1] + fibs[i - 2]
    push(fibs, next)
    i = i + 1
}
fibs
""", [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])

test("prime sieve", """
let primes = []
let n = 2
while n < 20 {
    let is_prime = true
    let i = 0
    while i < len(primes) {
        if n % primes[i] == 0 {
            is_prime = false
        }
        i = i + 1
    }
    if is_prime {
        push(primes, n)
    }
    n = n + 1
}
primes
""", [2, 3, 5, 7, 11, 13, 17, 19])

test("bubble sort", """
let arr = [5, 3, 8, 1, 9, 2, 7, 4, 6]
let n = len(arr)
let i = 0
while i < n {
    let j = 0
    while j < n - 1 - i {
        if arr[j] > arr[j + 1] {
            let tmp = arr[j]
            arr[j] = arr[j + 1]
            arr[j + 1] = tmp
        }
        j = j + 1
    }
    i = i + 1
}
arr
""", [1, 2, 3, 4, 5, 6, 7, 8, 9])

print(f"\n{'='*40}")
print(f"Results: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL TESTS PASSED ✓")
else:
    print(f"{failed} FAILED")