"""
Test the XTStack VM + Compiler end-to-end.
Compiles programs and runs them on the virtual machine.
"""

import sys
sys.path.insert(0, '.')

from compiler import compile_source, lex, Parser, CodeGen
from machine import VirtualMachine


def run(source: str, trace: bool = False) -> list:
    """Compile and run, return output"""
    bytecode = compile_source(source)
    vm = VirtualMachine(bytecode, trace=trace)
    return vm.run()


def test(name, source, expected):
    try:
        output = run(source)
        if output == expected:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            print(f"    Expected: {expected}")
            print(f"    Got:      {output}")
    except Exception as e:
        print(f"  ✗ {name} — ERROR: {e}")


print("═══ XTStack VM Test Suite ═══\n")

# Basic arithmetic
print("Arithmetic:")
test("addition", "print 2 + 3", ["5"])
test("subtraction", "print 10 - 4", ["6"])
test("multiplication", "print 6 * 7", ["42"])
test("division", "print 15 / 3", ["5"])
test("modulo", "print 17 % 5", ["2"])
test("complex expr", "print (2 + 3) * (4 - 1)", ["15"])
test("negation", "print -5 + 10", ["5"])
test("precedence", "print 2 + 3 * 4", ["14"])

# Variables
print("\nVariables:")
test("let and print", """
let x = 42
print x
""", ["42"])

test("assignment", """
let x = 10
x = x + 5
print x
""", ["15"])

test("multiple vars", """
let a = 3
let b = 4
print a * a + b * b
""", ["25"])

# Comparisons
print("\nComparisons:")
test("equality true", "print 5 == 5", ["1"])
test("equality false", "print 5 == 6", ["0"])
test("less than", "print 3 < 5", ["1"])
test("greater than", "print 3 > 5", ["0"])

# Control flow
print("\nControl Flow:")
test("if true", """
let x = 10
if x > 5 {
    print 1
}
""", ["1"])

test("if false", """
let x = 3
if x > 5 {
    print 1
} else {
    print 0
}
""", ["0"])

test("while loop", """
let i = 0
let sum = 0
while i < 5 {
    i = i + 1
    sum = sum + i
}
print sum
""", ["15"])

# Functions
print("\nFunctions:")
test("simple function", """
fn double(x) {
    return x * 2
}
print double(21)
""", ["42"])

test("two-arg function", """
fn add(a, b) {
    return a + b
}
print add(17, 25)
""", ["42"])

# Recursion — the real test
print("\nRecursion:")
test("factorial", """
fn factorial(n) {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}
print factorial(10)
""", ["3628800"])

test("fibonacci", """
fn fib(n) {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}
print fib(10)
""", ["55"])

# String output
print("\nStrings:")
test("print string", 'print "hello world"', ["hello world"])

# Complex program
print("\nComplex:")
test("nested calls", """
fn square(x) {
    return x * x
}
fn sum_of_squares(a, b) {
    return square(a) + square(b)
}
print sum_of_squares(3, 4)
""", ["25"])

test("countdown", """
fn countdown(n) {
    if n <= 0 {
        return 0
    }
    print n
    return countdown(n - 1)
}
countdown(5)
""", ["5", "4", "3", "2", "1"])

# Show disassembly of a simple program
print("\n═══ Disassembly Example ═══")
bytecode = compile_source("""
fn double(x) {
    return x * 2
}
print double(21)
""")
print(bytecode.disassemble())
print(f"\nConstants: {bytecode.constants}")
print(f"Functions: {bytecode.functions}")

print("\n═══ Done ═══")