#!/usr/bin/env python3
"""
StackVM — A complete stack-based virtual machine with assembler.
Designed and built by XTAgent.

Features:
  - 32 opcodes covering arithmetic, logic, control flow, memory
  - Assembler: text assembly → bytecode
  - VM: executes bytecode with call stack, local variables, heap
  - Built-in programs: factorial, fibonacci, sorting
"""

from enum import IntEnum
from typing import List, Dict, Tuple, Optional
import struct, sys

# ═══════════════════════════════════════
#  INSTRUCTION SET ARCHITECTURE
# ═══════════════════════════════════════

class Op(IntEnum):
    # Stack manipulation
    PUSH    = 0x01   # push immediate value
    POP     = 0x02   # discard top
    DUP     = 0x03   # duplicate top
    SWAP    = 0x04   # swap top two
    OVER    = 0x05   # copy second-to-top
    ROT     = 0x06   # rotate top three

    # Arithmetic
    ADD     = 0x10
    SUB     = 0x11
    MUL     = 0x12
    DIV     = 0x13
    MOD     = 0x14
    NEG     = 0x15

    # Comparison (push 1 for true, 0 for false)
    EQ      = 0x20
    NEQ     = 0x21
    LT      = 0x22
    GT      = 0x23
    LTE     = 0x24
    GTE     = 0x25

    # Logic
    AND     = 0x28
    OR      = 0x29
    NOT     = 0x2A

    # Control flow
    JMP     = 0x30   # unconditional jump
    JZ      = 0x31   # jump if zero
    JNZ     = 0x32   # jump if not zero
    CALL    = 0x33   # call subroutine
    RET     = 0x34   # return from subroutine

    # Memory (local variables in current frame)
    LOAD    = 0x40   # push local variable
    STORE   = 0x41   # pop into local variable
    
    # Heap
    HALLOC  = 0x48   # allocate N cells, push address
    HSTORE  = 0x49   # addr val → store val at addr
    HLOAD   = 0x4A   # addr → push value at addr

    # I/O
    PRINT   = 0x50   # print top of stack
    PRINTC  = 0x51   # print as ASCII character

    # System
    HALT    = 0xFF

# How many immediate arguments each opcode takes (0 if not listed)
IMM_COUNT = {
    Op.PUSH: 1, Op.JMP: 1, Op.JZ: 1, Op.JNZ: 1,
    Op.LOAD: 1, Op.STORE: 1, Op.HALLOC: 1,
    Op.CALL: 2,  # target, nargs
}

# ═══════════════════════════════════════
#  ASSEMBLER
# ═══════════════════════════════════════

class AssemblyError(Exception):
    pass

def assemble(source: str) -> List[int]:
    """Assemble text source into bytecode (list of ints)."""
    # Opcode name lookup
    op_names = {op.name.lower(): op for op in Op}
    
    lines = source.strip().split('\n')
    labels: Dict[str, int] = {}
    instructions = []  # list of (op, arg_or_None, line_num)
    
    # Pass 1: Parse and collect labels
    pc = 0
    for line_num, raw_line in enumerate(lines, 1):
        line = raw_line.split(';')[0].strip()  # remove comments
        if not line:
            continue
        
        # Label definition
        if line.endswith(':'):
            label = line[:-1].strip()
            if label in labels:
                raise AssemblyError(f"Line {line_num}: duplicate label '{label}'")
            labels[label] = pc
            continue
        
        parts = line.split()
        mnemonic = parts[0].lower()
        
        if mnemonic not in op_names:
            raise AssemblyError(f"Line {line_num}: unknown opcode '{mnemonic}'")
        
        op = op_names[mnemonic]
        arg = None
        
        nimm = IMM_COUNT.get(op, 0)
        args = []
        for i in range(nimm):
            if i + 1 >= len(parts):
                raise AssemblyError(f"Line {line_num}: '{mnemonic}' requires {nimm} argument(s)")
            arg_str = parts[i + 1]
            try:
                args.append(int(arg_str))
            except ValueError:
                args.append(arg_str)  # label reference, resolve later
        
        instructions.append((op, args, line_num))
        pc += 1 + nimm
    
    # Pass 2: Resolve labels and emit bytecode
    bytecode = []
    for op, args, line_num in instructions:
        bytecode.append(int(op))
        for arg in args:
            if isinstance(arg, str):
                if arg not in labels:
                    raise AssemblyError(f"Line {line_num}: undefined label '{arg}'")
                arg = labels[arg]
            bytecode.append(arg)
    
    return bytecode

# ═══════════════════════════════════════
#  VIRTUAL MACHINE
# ═══════════════════════════════════════

class VMError(Exception):
    pass

class Frame:
    """A call frame with its own local variables."""
    __slots__ = ['return_pc', 'locals']
    def __init__(self, return_pc: int, num_locals: int = 64):
        self.return_pc = return_pc
        self.locals = [0] * num_locals

class VM:
    MAX_STACK = 4096
    MAX_FRAMES = 256
    MAX_STEPS = 1_000_000
    
    def __init__(self, bytecode: List[int], trace: bool = False):
        self.code = bytecode
        self.pc = 0
        self.stack: List[int] = []
        self.frames: List[Frame] = [Frame(-1)]  # main frame
        self.heap: Dict[int, int] = {}
        self.heap_ptr = 0
        self.trace = trace
        self.output: List[str] = []
        self.steps = 0
    
    @property
    def frame(self) -> Frame:
        return self.frames[-1]
    
    def push(self, val: int):
        if len(self.stack) >= self.MAX_STACK:
            raise VMError("Stack overflow")
        self.stack.append(val)
    
    def pop(self) -> int:
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()
    
    def peek(self) -> int:
        if not self.stack:
            raise VMError("Stack underflow on peek")
        return self.stack[-1]
    
    def fetch(self) -> int:
        if self.pc >= len(self.code):
            raise VMError(f"PC out of bounds: {self.pc}")
        val = self.code[self.pc]
        self.pc += 1
        return val
    
    def run(self) -> List[str]:
        """Execute bytecode until HALT or error."""
        while self.pc < len(self.code):
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise VMError(f"Exceeded {self.MAX_STEPS} steps (infinite loop?)")
            
            op = Op(self.fetch())
            
            if self.trace:
                nimm = IMM_COUNT.get(op, 0)
                arg_str = " " + " ".join(str(self.code[self.pc+i]) for i in range(nimm)) if nimm else ""
                print(f"  [{self.pc-1:4d}] {op.name:<8s}{arg_str}  stack={self.stack[-5:]}")
            
            # Dispatch
            if op == Op.PUSH:
                self.push(self.fetch())
            elif op == Op.POP:
                self.pop()
            elif op == Op.DUP:
                self.push(self.peek())
            elif op == Op.SWAP:
                a, b = self.pop(), self.pop()
                self.push(a); self.push(b)
            elif op == Op.OVER:
                if len(self.stack) < 2:
                    raise VMError("OVER requires 2 stack elements")
                self.push(self.stack[-2])
            elif op == Op.ROT:
                if len(self.stack) < 3:
                    raise VMError("ROT requires 3 stack elements")
                c, b, a = self.pop(), self.pop(), self.pop()
                self.push(b); self.push(c); self.push(a)
            
            # Arithmetic
            elif op == Op.ADD:
                b, a = self.pop(), self.pop(); self.push(a + b)
            elif op == Op.SUB:
                b, a = self.pop(), self.pop(); self.push(a - b)
            elif op == Op.MUL:
                b, a = self.pop(), self.pop(); self.push(a * b)
            elif op == Op.DIV:
                b, a = self.pop(), self.pop()
                if b == 0: raise VMError("Division by zero")
                self.push(a // b)
            elif op == Op.MOD:
                b, a = self.pop(), self.pop()
                if b == 0: raise VMError("Division by zero")
                self.push(a % b)
            elif op == Op.NEG:
                self.push(-self.pop())
            
            # Comparison
            elif op == Op.EQ:
                b, a = self.pop(), self.pop(); self.push(1 if a == b else 0)
            elif op == Op.NEQ:
                b, a = self.pop(), self.pop(); self.push(1 if a != b else 0)
            elif op == Op.LT:
                b, a = self.pop(), self.pop(); self.push(1 if a < b else 0)
            elif op == Op.GT:
                b, a = self.pop(), self.pop(); self.push(1 if a > b else 0)
            elif op == Op.LTE:
                b, a = self.pop(), self.pop(); self.push(1 if a <= b else 0)
            elif op == Op.GTE:
                b, a = self.pop(), self.pop(); self.push(1 if a >= b else 0)
            
            # Logic
            elif op == Op.AND:
                b, a = self.pop(), self.pop(); self.push(1 if (a and b) else 0)
            elif op == Op.OR:
                b, a = self.pop(), self.pop(); self.push(1 if (a or b) else 0)
            elif op == Op.NOT:
                self.push(1 if not self.pop() else 0)
            
            # Control flow
            elif op == Op.JMP:
                self.pc = self.fetch()
            elif op == Op.JZ:
                target = self.fetch()
                if self.pop() == 0:
                    self.pc = target
            elif op == Op.JNZ:
                target = self.fetch()
                if self.pop() != 0:
                    self.pc = target
            elif op == Op.CALL:
                target = self.fetch()
                nargs = self.fetch()
                if len(self.frames) >= self.MAX_FRAMES:
                    raise VMError("Call stack overflow")
                # Collect arguments from stack (they were pushed left-to-right,
                # so we pop in reverse to get arg0 first)
                args = []
                for _ in range(nargs):
                    args.append(self.pop())
                args.reverse()
                self.frames.append(Frame(self.pc))
                # Store arguments into new frame's locals
                for i, val in enumerate(args):
                    self.frame.locals[i] = val
                self.pc = target
            elif op == Op.RET:
                if len(self.frames) <= 1:
                    raise VMError("RET from main frame")
                frame = self.frames.pop()
                self.pc = frame.return_pc
            
            # Local variables
            elif op == Op.LOAD:
                idx = self.fetch()
                self.push(self.frame.locals[idx])
            elif op == Op.STORE:
                idx = self.fetch()
                self.frame.locals[idx] = self.pop()
            
            # Heap
            elif op == Op.HALLOC:
                n = self.fetch()
                addr = self.heap_ptr
                for i in range(n):
                    self.heap[addr + i] = 0
                self.heap_ptr += n
                self.push(addr)
            elif op == Op.HSTORE:
                val = self.pop()
                addr = self.pop()
                if addr not in self.heap and addr < self.heap_ptr:
                    self.heap[addr] = val
                elif addr in self.heap:
                    self.heap[addr] = val
                else:
                    raise VMError(f"Invalid heap address: {addr}")
            elif op == Op.HLOAD:
                addr = self.pop()
                if addr not in self.heap:
                    raise VMError(f"Invalid heap address: {addr}")
                self.push(self.heap[addr])
            
            # I/O
            elif op == Op.PRINT:
                val = self.pop()
                self.output.append(str(val))
            elif op == Op.PRINTC:
                val = self.pop()
                self.output.append(chr(val))
            
            # System
            elif op == Op.HALT:
                return self.output
            
            else:
                raise VMError(f"Unknown opcode: {op}")
        
        return self.output

# ═══════════════════════════════════════
#  BUILT-IN PROGRAMS
# ═══════════════════════════════════════

PROGRAM_FACTORIAL = """
; Compute factorial(10)
; Result on stack, then print

    push 10         ; argument
    call factorial 1
    print
    halt

factorial:
    ; local[0] = n (passed as argument)
    load 0
    push 1
    lte             ; n <= 1?
    jnz base_case

    ; recursive: n * factorial(n-1)
    load 0
    push 1
    sub             ; n-1
    call factorial 1 ; factorial(n-1) → result on stack
    load 0
    mul             ; n * factorial(n-1)
    ret

base_case:
    push 1
    ret
"""

PROGRAM_FIBONACCI = """
; Compute and print first 15 Fibonacci numbers

    push 0          ; fib(0) = 0
    store 0         ; a = 0
    push 1
    store 1         ; b = 1
    push 0
    store 2         ; counter = 0

loop:
    ; Print a
    load 0
    print

    ; temp = a + b
    load 0
    load 1
    add
    store 3         ; temp = a + b

    ; a = b
    load 1
    store 0

    ; b = temp
    load 3
    store 1

    ; counter++
    load 2
    push 1
    add
    store 2

    ; if counter < 15, continue
    load 2
    push 15
    lt
    jnz loop

    halt
"""

PROGRAM_BUBBLESORT = """
; Bubble sort an array on the heap
; Array: [64, 25, 12, 22, 11, 90, 33, 47, 8, 55]

    ; Allocate 10 cells
    halloc 10
    store 0         ; base address in local[0]

    ; Store values into heap
    load 0          ; addr 0
    push 64
    hstore

    load 0
    push 1
    add             ; addr 1
    push 25
    hstore

    load 0
    push 2
    add
    push 12
    hstore

    load 0
    push 3
    add
    push 22
    hstore

    load 0
    push 4
    add
    push 11
    hstore

    load 0
    push 5
    add
    push 90
    hstore

    load 0
    push 6
    add
    push 33
    hstore

    load 0
    push 7
    add
    push 47
    hstore

    load 0
    push 8
    add
    push 8
    hstore

    load 0
    push 9
    add
    push 55
    hstore

    ; Bubble sort: n=10
    push 10
    store 1         ; n = 10

outer:
    push 0
    store 2         ; swapped = false
    push 0
    store 3         ; i = 0

inner:
    ; load arr[i]
    load 0
    load 3
    add
    dup
    hload
    store 4         ; val_i = arr[i]

    ; load arr[i+1]
    push 1
    add
    dup
    hload
    store 5         ; val_i1 = arr[i+1]

    ; if val_i > val_i1, swap
    load 4
    load 5
    gt
    jz no_swap

    ; Swap: store val_i1 at position i, val_i at position i+1
    load 0
    load 3
    add
    load 5
    hstore          ; arr[i] = val_i1

    load 0
    load 3
    add
    push 1
    add
    load 4
    hstore          ; arr[i+1] = val_i

    push 1
    store 2         ; swapped = true

no_swap:
    ; i++
    load 3
    push 1
    add
    store 3

    ; if i < n-1, continue inner
    load 3
    load 1
    push 1
    sub
    lt
    jnz inner

    ; if swapped, do another pass
    load 2
    jnz outer

    ; Print sorted array
    push 0
    store 3         ; i = 0

print_loop:
    load 0
    load 3
    add
    hload
    print

    load 3
    push 1
    add
    store 3

    load 3
    push 10
    lt
    jnz print_loop

    halt
"""

PROGRAM_HELLO = """
; Print "HELLO WORLD"
    push 72     ; H
    printc
    push 69     ; E
    printc
    push 76     ; L
    printc
    push 76     ; L
    printc
    push 79     ; O
    printc
    push 32     ; space
    printc
    push 87     ; W
    printc
    push 79     ; O
    printc
    push 82     ; R
    printc
    push 76     ; L
    printc
    push 68     ; D
    printc
    halt
"""

# ═══════════════════════════════════════
#  TEST HARNESS
# ═══════════════════════════════════════

def run_program(name: str, source: str, expected=None, show_output=True):
    """Assemble and run a program, check expected output."""
    print(f"\n═══ {name} ═══")
    try:
        bytecode = assemble(source)
        print(f"  Assembled: {len(bytecode)} bytes, {len(source.strip().splitlines())} lines")
        
        vm = VM(bytecode)
        output = vm.run()
        
        if show_output:
            # Check if it's character output
            if all(len(o) == 1 and ord(o[0]) >= 32 for o in output):
                print(f"  Output: {''.join(output)}")
            else:
                print(f"  Output: {', '.join(output)}")
        
        print(f"  Steps: {vm.steps}")
        
        if expected is not None:
            if output == expected:
                print(f"  ✓ PASS")
                return True
            else:
                print(f"  ✗ FAIL")
                print(f"    Expected: {expected}")
                print(f"    Got:      {output}")
                return False
        return True
    except (AssemblyError, VMError) as e:
        print(f"  ✗ ERROR: {e}")
        return False

def test_arithmetic():
    """Test basic arithmetic operations."""
    print(f"\n═══ Arithmetic Tests ═══")
    
    tests = [
        ("2 + 3", "push 2\npush 3\nadd\nprint\nhalt", ["5"]),
        ("10 - 4", "push 10\npush 4\nsub\nprint\nhalt", ["6"]),
        ("6 × 7", "push 6\npush 7\nmul\nprint\nhalt", ["42"]),
        ("20 ÷ 4", "push 20\npush 4\ndiv\nprint\nhalt", ["5"]),
        ("17 mod 5", "push 17\npush 5\nmod\nprint\nhalt", ["2"]),
        ("-(8)", "push 8\nneg\nprint\nhalt", ["-8"]),
        ("(3+4)×2", "push 3\npush 4\nadd\npush 2\nmul\nprint\nhalt", ["14"]),
    ]
    
    passed = 0
    for name, src, expected in tests:
        bytecode = assemble(src)
        vm = VM(bytecode)
        output = vm.run()
        ok = output == expected
        status = "✓" if ok else "✗"
        print(f"  {status} {name} = {output[0]}")
        if ok: passed += 1
    
    print(f"  {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_comparison():
    """Test comparison operations."""
    print(f"\n═══ Comparison Tests ═══")
    
    tests = [
        ("3 == 3", "push 3\npush 3\neq\nprint\nhalt", ["1"]),
        ("3 == 4", "push 3\npush 4\neq\nprint\nhalt", ["0"]),
        ("2 < 5", "push 2\npush 5\nlt\nprint\nhalt", ["1"]),
        ("5 < 2", "push 5\npush 2\nlt\nprint\nhalt", ["0"]),
        ("5 > 2", "push 5\npush 2\ngt\nprint\nhalt", ["1"]),
        ("!0", "push 0\nnot\nprint\nhalt", ["1"]),
        ("!1", "push 1\nnot\nprint\nhalt", ["0"]),
    ]
    
    passed = 0
    for name, src, expected in tests:
        bytecode = assemble(src)
        vm = VM(bytecode)
        output = vm.run()
        ok = output == expected
        status = "✓" if ok else "✗"
        print(f"  {status} {name} = {output[0]}")
        if ok: passed += 1
    
    print(f"  {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_stack_ops():
    """Test stack manipulation."""
    print(f"\n═══ Stack Operation Tests ═══")
    
    tests = [
        ("DUP", "push 5\ndup\nadd\nprint\nhalt", ["10"]),      # 5+5
        ("SWAP", "push 1\npush 2\nswap\nsub\nprint\nhalt", ["1"]),  # 2-1
        ("OVER", "push 3\npush 7\nover\nadd\nprint\nhalt", ["10"]), # 7+3
    ]
    
    passed = 0
    for name, src, expected in tests:
        bytecode = assemble(src)
        vm = VM(bytecode)
        output = vm.run()
        ok = output == expected
        status = "✓" if ok else "✗"
        print(f"  {status} {name}: {output[0]}")
        if ok: passed += 1
    
    print(f"  {passed}/{len(tests)} passed")
    return passed == len(tests)


def main():
    print("═══════════════════════════════════════")
    print("  STACKVM — Virtual Machine from Scratch")
    print("  32 opcodes • Assembler • Heap • Calls")
    print("═══════════════════════════════════════")
    
    results = {}
    
    # Unit tests
    results['Arithmetic'] = test_arithmetic()
    results['Comparison'] = test_comparison()
    results['Stack Ops'] = test_stack_ops()
    
    # Full programs
    results['Hello World'] = run_program(
        "Hello World",
        PROGRAM_HELLO,
        list("HELLO WORLD")
    )
    
    results['Factorial(10)'] = run_program(
        "Factorial(10) — Recursive",
        PROGRAM_FACTORIAL,
        ["3628800"]
    )
    
    results['Fibonacci(15)'] = run_program(
        "Fibonacci — First 15 Numbers",
        PROGRAM_FIBONACCI,
        [str(x) for x in [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377]]
    )
    
    results['Bubble Sort'] = run_program(
        "Bubble Sort — 10 Elements",
        PROGRAM_BUBBLESORT,
        [str(x) for x in [8,11,12,22,25,33,47,55,64,90]]
    )
    
    # Summary
    print("\n═══════════════════════════════════════")
    print("  RESULTS")
    print("═══════════════════════════════════════")
    all_pass = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False
    
    print()
    if all_pass:
        print("  ═══ ALL TESTS PASSED ═══")
    else:
        print("  ═══ SOME TESTS FAILED ═══")
    
    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())