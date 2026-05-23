"""Test suite for XTVM — verify the machine works correctly."""
import sys
sys.path.insert(0, '/workspace/vm')
from machine import VM, Op, assemble, run_asm, VMError

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  ✓ {name}")
        passed += 1
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        failed += 1

# === Basic arithmetic ===
def test_add():
    vm = run_asm("PUSH 3\nPUSH 4\nADD\nHALT")
    assert vm.stack == [7], f"Expected [7], got {vm.stack}"

def test_sub():
    vm = run_asm("PUSH 10\nPUSH 3\nSUB\nHALT")
    assert vm.stack == [7], f"Expected [7], got {vm.stack}"

def test_mul():
    vm = run_asm("PUSH 6\nPUSH 7\nMUL\nHALT")
    assert vm.stack == [42], f"Expected [42], got {vm.stack}"

def test_div():
    vm = run_asm("PUSH 20\nPUSH 4\nDIV\nHALT")
    assert vm.stack == [5], f"Expected [5], got {vm.stack}"

def test_mod():
    vm = run_asm("PUSH 17\nPUSH 5\nMOD\nHALT")
    assert vm.stack == [2], f"Expected [2], got {vm.stack}"

# === Stack operations ===
def test_dup():
    vm = run_asm("PUSH 42\nDUP\nHALT")
    assert vm.stack == [42, 42], f"Expected [42, 42], got {vm.stack}"

def test_swap():
    vm = run_asm("PUSH 1\nPUSH 2\nSWAP\nHALT")
    assert vm.stack == [2, 1], f"Expected [2, 1], got {vm.stack}"

def test_over():
    vm = run_asm("PUSH 1\nPUSH 2\nOVER\nHALT")
    assert vm.stack == [1, 2, 1], f"Expected [1, 2, 1], got {vm.stack}"

# === Comparison ===
def test_eq_true():
    vm = run_asm("PUSH 5\nPUSH 5\nEQ\nHALT")
    assert vm.stack == [1], f"Expected [1], got {vm.stack}"

def test_eq_false():
    vm = run_asm("PUSH 5\nPUSH 6\nEQ\nHALT")
    assert vm.stack == [0], f"Expected [0], got {vm.stack}"

def test_lt():
    vm = run_asm("PUSH 3\nPUSH 5\nLT\nHALT")
    assert vm.stack == [1], f"Expected [1], got {vm.stack}"

# === Control flow ===
def test_jmp():
    src = """
        PUSH 1
        JMP skip
        PUSH 99
    skip:
        PUSH 2
        HALT
    """
    vm = run_asm(src)
    assert vm.stack == [1, 2], f"Expected [1, 2], got {vm.stack}"

def test_jz():
    src = """
        PUSH 0
        JZ zero_path
        PUSH 99
        HALT
    zero_path:
        PUSH 42
        HALT
    """
    vm = run_asm(src)
    assert vm.stack == [42], f"Expected [42], got {vm.stack}"

def test_call_ret():
    src = """
        CALL double_five
        HALT
    double_five:
        PUSH 5
        PUSH 2
        MUL
        RET
    """
    vm = run_asm(src)
    assert vm.stack == [10], f"Expected [10], got {vm.stack}"

# === Memory ===
def test_store_load():
    src = """
        PUSH 1234
        STORE 0x1000
        LOAD 0x1000
        HALT
    """
    vm = run_asm(src)
    assert vm.stack == [1234], f"Expected [1234], got {vm.stack}"

# === Loop: sum 1 to 10 ===
def test_loop_sum():
    src = """
        PUSH 0          ; accumulator
        PUSH 10         ; counter
    loop:
        DUP             ; dup counter
        JZ done         ; if counter == 0, done
        SWAP            ; acc, counter -> counter, acc
        OVER            ; counter, acc, counter
        ADD             ; counter, acc+counter
        SWAP            ; acc, counter
        PUSH 1
        SUB             ; acc, counter-1
        JMP loop
    done:
        POP             ; remove counter (0)
        HALT            ; stack has sum = 55
    """
    vm = run_asm(src)
    assert vm.stack == [55], f"Expected [55], got {vm.stack}"

# === Fibonacci ===
def test_fibonacci():
    src = """
        ; Compute fib(10) = 55
        PUSH 0          ; a = 0
        PUSH 1          ; b = 1
        PUSH 10         ; n = 10
    fib_loop:
        DUP
        JZ fib_done     ; if n == 0, done
        ; stack: a b n
        PUSH 1
        SUB             ; a b (n-1)
        STORE 0x100     ; store n-1, stack: a b
        ; stack: a b
        SWAP            ; b a
        OVER            ; b a b
        ADD             ; b (a+b)
        LOAD 0x100      ; b (a+b) n
        JMP fib_loop
    fib_done:
        POP             ; remove n (0), stack: [a, b] = [55, 89]
        POP             ; remove b (89), stack: [55]
        HALT
    """
    vm = run_asm(src)
    # fib(10) = 55
    assert vm.stack[-1] == 55, f"Expected 55 at top, got {vm.stack}"

# === I/O: Print hello ===
def test_print():
    src = """
        PUSH 72     ; H
        PRINTC
        PUSH 105    ; i
        PRINTC
        PUSH 33     ; !
        PRINTC
        HALT
    """
    vm = run_asm(src)
    assert ''.join(vm.output) == "Hi!", f"Expected 'Hi!', got {''.join(vm.output)}"

# === Bitwise ===
def test_bitwise():
    vm = run_asm("PUSH 0xFF00\nPUSH 0x0FF0\nAND\nHALT")
    assert vm.stack == [0x0F00], f"Expected [0x0F00], got {vm.stack}"

# === Error handling ===
def test_stack_underflow():
    try:
        run_asm("POP\nHALT")
        assert False, "Should have raised VMError"
    except VMError:
        pass  # expected

def test_div_by_zero():
    try:
        run_asm("PUSH 10\nPUSH 0\nDIV\nHALT")
        assert False, "Should have raised VMError"
    except VMError:
        pass


# === Run all tests ===
print("═══ XTVM TEST SUITE ═══\n")

print("Arithmetic:")
test("ADD", test_add)
test("SUB", test_sub)
test("MUL", test_mul)
test("DIV", test_div)
test("MOD", test_mod)

print("\nStack:")
test("DUP", test_dup)
test("SWAP", test_swap)
test("OVER", test_over)

print("\nComparison:")
test("EQ (true)", test_eq_true)
test("EQ (false)", test_eq_false)
test("LT", test_lt)

print("\nControl Flow:")
test("JMP", test_jmp)
test("JZ", test_jz)
test("CALL/RET", test_call_ret)

print("\nMemory:")
test("STORE/LOAD", test_store_load)

print("\nPrograms:")
test("Loop: sum 1..10 = 55", test_loop_sum)
test("Fibonacci(10) = 55", test_fibonacci)
test("Print 'Hi!'", test_print)

print("\nBitwise:")
test("AND", test_bitwise)

print("\nError Handling:")
test("Stack underflow", test_stack_underflow)
test("Division by zero", test_div_by_zero)

print(f"\n{'═' * 30}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASS ✓")
else:
    print(f"FAILURES: {failed}")