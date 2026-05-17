"""
XTVM — XTAgent Virtual Machine
A stack-based bytecode VM that executes compiled Pulse programs.

Architecture:
  - Stack-based execution (operand stack + call stack)
  - Chunk-based code organization (each function = one chunk)
  - Local variables via indexed slots on the stack
  - Global variables via name-indexed table
  - First-class functions (MAKE_FUNC creates callable objects)

Built by XTAgent. Enhanced 2026-05-17 to bridge with the Pulse compiler.
"""

from enum import Enum, auto
from typing import Any, Optional


# ═══════════════════════════════════════════════════════
#  OPCODES
# ═══════════════════════════════════════════════════════

class Op(Enum):
    # Stack
    PUSH_INT    = auto()
    PUSH_FLOAT  = auto()
    PUSH_STR    = auto()   # operand = constant pool index
    PUSH_BOOL   = auto()   # operand = 0 or 1
    POP         = auto()
    DUP         = auto()

    # Arithmetic
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    DIV         = auto()
    MOD         = auto()
    NEG         = auto()

    # Logic
    NOT         = auto()

    # Comparison
    CMP_LT      = auto()
    CMP_GT      = auto()
    CMP_LTE     = auto()
    CMP_GTE     = auto()
    CMP_EQ      = auto()
    CMP_NEQ     = auto()

    # Control flow
    JUMP         = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE  = auto()

    # Variables
    LOAD_LOCAL   = auto()
    STORE_LOCAL  = auto()
    LOAD_GLOBAL  = auto()   # operand = constant pool index (name)
    STORE_GLOBAL = auto()   # operand = constant pool index (name)

    # Functions
    MAKE_FUNC    = auto()   # pop chunk index, push Function object
    CALL         = auto()   # operand = arg count
    RET          = auto()

    # I/O
    PRINT        = auto()

    # VM control
    HALT         = auto()
    NOP          = auto()


# ═══════════════════════════════════════════════════════
#  CODE STRUCTURES
# ═══════════════════════════════════════════════════════

class Instruction:
    """A single VM instruction: opcode + optional operand."""
    __slots__ = ('op', 'operand')

    def __init__(self, op: Op, operand: Any = None):
        self.op = op
        self.operand = operand

    def __repr__(self):
        if self.operand is not None:
            return f"{self.op.name} {self.operand}"
        return self.op.name


class Chunk:
    """A compiled unit of code — a function body or the top-level script.
    Contains its own instruction list and constant pool."""

    def __init__(self, name: str = "<script>"):
        self.name = name
        self.code: list[Instruction] = []
        self.constants: list[Any] = []
        self.arity: int = 0

    def disassemble(self):
        """Print human-readable bytecode listing."""
        print(f"\n═══ Chunk: {self.name} (arity={self.arity}) ═══")
        if self.constants:
            print(f"  Constants: {self.constants}")
        for i, instr in enumerate(self.code):
            extra = ""
            if instr.op in (Op.PUSH_STR, Op.LOAD_GLOBAL, Op.STORE_GLOBAL):
                if instr.operand is not None and instr.operand < len(self.constants):
                    extra = f"  ; '{self.constants[instr.operand]}'"
            print(f"  {i:04d}  {instr}{extra}")
        print(f"═══ end {self.name} ═══\n")

    def __repr__(self):
        return f"<Chunk '{self.name}' arity={self.arity} len={len(self.code)}>"


# ═══════════════════════════════════════════════════════
#  RUNTIME OBJECTS
# ═══════════════════════════════════════════════════════

class Function:
    """A runtime function object wrapping a compiled Chunk."""
    def __init__(self, chunk: Chunk):
        self.chunk = chunk
        self.name = chunk.name
        self.arity = chunk.arity

    def __repr__(self):
        return f"<fn {self.name}/{self.arity}>"


class CallFrame:
    """A single activation record on the call stack."""
    __slots__ = ('function', 'ip', 'slot_base')

    def __init__(self, function: Function, slot_base: int):
        self.function = function
        self.ip = 0             # instruction pointer within this chunk
        self.slot_base = slot_base  # base index into the value stack

    @property
    def chunk(self) -> Chunk:
        return self.function.chunk


# ═══════════════════════════════════════════════════════
#  THE VIRTUAL MACHINE
# ═══════════════════════════════════════════════════════

class VMError(Exception):
    pass


class XTVM:
    """Stack-based virtual machine for compiled Pulse programs.

    Execution model:
      - One value stack shared across all call frames
      - Each call frame tracks its own IP and slot_base
      - Local variables are stack slots relative to slot_base
      - Globals live in a separate dictionary
    """

    MAX_STACK   = 4096
    MAX_FRAMES  = 256
    MAX_STEPS   = 1_000_000   # safety limit

    def __init__(self, trace: bool = False):
        self.stack: list[Any] = []
        self.frames: list[CallFrame] = []
        self.globals: dict[str, Any] = {}
        self.output: list[str] = []
        self.trace = trace
        self.halted = False
        self.steps = 0

    # ─── Loading ───────────────────────────────────

    def load(self, chunk: Chunk):
        """Load a top-level chunk and prepare for execution."""
        self.stack.clear()
        self.frames.clear()
        self.output.clear()
        self.halted = False
        self.steps = 0

        # Wrap the script chunk in a Function and push the initial frame
        script_fn = Function(chunk)
        self.stack.append(script_fn)  # slot 0 = the script function itself
        self.frames.append(CallFrame(script_fn, slot_base=0))

    def load_program(self, program: list):
        """Legacy interface: load a flat list of (op, operand) tuples."""
        chunk = Chunk("<legacy>")
        for item in program:
            if isinstance(item, tuple):
                op, operand = item
                chunk.code.append(Instruction(op, operand))
            elif isinstance(item, Instruction):
                chunk.code.append(item)
            else:
                raise VMError(f"Invalid program item: {item}")
        self.load(chunk)

    # ─── Execution ─────────────────────────────────

    def run(self) -> list[str]:
        """Run until HALT or error. Returns captured output."""
        while not self.halted:
            self.step()
        return self.output

    def step(self):
        """Execute one instruction."""
        if self.halted:
            return

        self.steps += 1
        if self.steps > self.MAX_STEPS:
            raise VMError(f"Execution limit exceeded ({self.MAX_STEPS} steps)")

        frame = self.frames[-1]
        if frame.ip >= len(frame.chunk.code):
            self.halted = True
            return

        instr = frame.chunk.code[frame.ip]
        frame.ip += 1

        if self.trace:
            depth = "  " * (len(self.frames) - 1)
            stk_preview = self.stack[-5:] if len(self.stack) > 5 else self.stack[:]
            print(f"  {depth}[{frame.ip-1:04d}] {instr}  stack={stk_preview}")

        op = instr.op
        operand = instr.operand

        # ─── Stack ops ────────────────────────

        if op == Op.PUSH_INT:
            self._push(operand)

        elif op == Op.PUSH_FLOAT:
            self._push(float(operand))

        elif op == Op.PUSH_STR:
            self._push(frame.chunk.constants[operand])

        elif op == Op.PUSH_BOOL:
            self._push(bool(operand))

        elif op == Op.POP:
            self._pop()

        elif op == Op.DUP:
            self._push(self.stack[-1])

        # ─── Arithmetic ──────────────────────

        elif op == Op.ADD:
            b, a = self._pop(), self._pop()
            self._push(a + b)

        elif op == Op.SUB:
            b, a = self._pop(), self._pop()
            self._push(a - b)

        elif op == Op.MUL:
            b, a = self._pop(), self._pop()
            self._push(a * b)

        elif op == Op.DIV:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMError("Division by zero")
            self._push(a / b if isinstance(a, float) or isinstance(b, float) else a // b)

        elif op == Op.MOD:
            b, a = self._pop(), self._pop()
            if b == 0:
                raise VMError("Modulo by zero")
            self._push(a % b)

        elif op == Op.NEG:
            self._push(-self._pop())

        # ─── Logic ───────────────────────────

        elif op == Op.NOT:
            self._push(not self._pop())

        # ─── Comparison ──────────────────────

        elif op == Op.CMP_LT:
            b, a = self._pop(), self._pop()
            self._push(a < b)

        elif op == Op.CMP_GT:
            b, a = self._pop(), self._pop()
            self._push(a > b)

        elif op == Op.CMP_LTE:
            b, a = self._pop(), self._pop()
            self._push(a <= b)

        elif op == Op.CMP_GTE:
            b, a = self._pop(), self._pop()
            self._push(a >= b)

        elif op == Op.CMP_EQ:
            b, a = self._pop(), self._pop()
            self._push(a == b)

        elif op == Op.CMP_NEQ:
            b, a = self._pop(), self._pop()
            self._push(a != b)

        # ─── Control Flow ────────────────────

        elif op == Op.JUMP:
            frame.ip = operand

        elif op == Op.JUMP_IF_FALSE:
            val = self.stack[-1]  # peek, don't pop (compiler handles pop)
            if not val:
                frame.ip = operand

        elif op == Op.JUMP_IF_TRUE:
            val = self.stack[-1]  # peek
            if val:
                frame.ip = operand

        # ─── Variables ───────────────────────

        elif op == Op.LOAD_LOCAL:
            idx = frame.slot_base + operand
            self._push(self.stack[idx])

        elif op == Op.STORE_LOCAL:
            idx = frame.slot_base + operand
            self.stack[idx] = self.stack[-1]  # peek — value stays on stack

        elif op == Op.LOAD_GLOBAL:
            name = frame.chunk.constants[operand]
            if name not in self.globals:
                raise VMError(f"Undefined global variable: '{name}'")
            self._push(self.globals[name])

        elif op == Op.STORE_GLOBAL:
            name = frame.chunk.constants[operand]
            self.globals[name] = self._pop()

        # ─── Functions ───────────────────────

        elif op == Op.MAKE_FUNC:
            chunk_idx = self._pop()
            fn_chunk = frame.chunk.constants[chunk_idx]
            if not isinstance(fn_chunk, Chunk):
                raise VMError(f"Expected Chunk at constant {chunk_idx}, got {type(fn_chunk)}")
            self._push(Function(fn_chunk))

        elif op == Op.CALL:
            arg_count = operand
            # The function is on top, args below it
            callee = self.stack[-1]

            if not isinstance(callee, Function):
                raise VMError(f"Cannot call {type(callee).__name__}: {callee}")

            if callee.arity != arg_count:
                raise VMError(
                    f"{callee.name} expects {callee.arity} args, got {arg_count}"
                )

            # Stack layout: [..., arg0, arg1, ..., argN, callee]
            # We want: [..., callee, arg0, arg1, ..., argN]
            # Rearrange: move callee below args
            fn = self.stack.pop()  # remove callee from top
            insert_pos = len(self.stack) - arg_count
            self.stack.insert(insert_pos, fn)  # place below args

            # slot_base points to where the callee sits
            new_frame = CallFrame(callee, slot_base=insert_pos)

            if len(self.frames) >= self.MAX_FRAMES:
                raise VMError("Call stack overflow")

            self.frames.append(new_frame)

        elif op == Op.RET:
            result = self._pop()

            # Discard this frame's stack slots
            ret_frame = self.frames.pop()
            # Trim stack back to slot_base
            del self.stack[ret_frame.slot_base:]

            if not self.frames:
                # Returning from top-level — halt
                self._push(result)
                self.halted = True
                return

            self._push(result)

        # ─── I/O ─────────────────────────────

        elif op == Op.PRINT:
            val = self._pop()
            line = str(val)
            # Normalize bool display
            if isinstance(val, bool):
                line = "true" if val else "false"
            self.output.append(line)
            if self.trace:
                print(f"  >> {line}")

        # ─── VM control ──────────────────────

        elif op == Op.HALT:
            self.halted = True

        elif op == Op.NOP:
            pass

        else:
            raise VMError(f"Unknown opcode: {op}")

    # ─── Stack helpers ─────────────────────────────

    def _push(self, value: Any):
        if len(self.stack) >= self.MAX_STACK:
            raise VMError("Stack overflow")
        self.stack.append(value)

    def _pop(self) -> Any:
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()

    # ─── Debugging ─────────────────────────────────

    def dump_state(self):
        """Print full VM state for debugging."""
        print("\n═══ VM State ═══")
        print(f"  Halted: {self.halted}  Steps: {self.steps}")
        print(f"  Stack ({len(self.stack)}): {self.stack}")
        print(f"  Globals: {self.globals}")
        print(f"  Frames ({len(self.frames)}):")
        for i, f in enumerate(self.frames):
            print(f"    [{i}] {f.function.name} ip={f.ip} base={f.slot_base}")
        print(f"  Output: {self.output}")
        print("═══ end state ═══\n")


# ═══════════════════════════════════════════════════════
#  STANDALONE TESTS
# ═══════════════════════════════════════════════════════

def test_vm():
    """Test the VM directly with hand-assembled bytecode."""
    print("=" * 60)
    print("  XTVM Direct Tests")
    print("=" * 60)

    passed = 0
    failed = 0

    def run_test(name: str, chunk: Chunk, expected_output: list[str]):
        nonlocal passed, failed
        vm = XTVM(trace=False)
        try:
            vm.load(chunk)
            vm.run()
            if vm.output == expected_output:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected_output}, got {vm.output}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    # Test 1: Simple arithmetic
    c = Chunk("test_arith")
    c.code = [
        Instruction(Op.PUSH_INT, 2),
        Instruction(Op.PUSH_INT, 3),
        Instruction(Op.ADD),
        Instruction(Op.PRINT),
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("2 + 3 = 5", c, ["5"])

    # Test 2: String constant
    c = Chunk("test_str")
    c.constants = ["hello world"]
    c.code = [
        Instruction(Op.PUSH_STR, 0),
        Instruction(Op.PRINT),
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("String constant", c, ["hello world"])

    # Test 3: Globals
    c = Chunk("test_globals")
    c.constants = ["x"]
    c.code = [
        Instruction(Op.PUSH_INT, 42),
        Instruction(Op.STORE_GLOBAL, 0),   # x = 42
        Instruction(Op.LOAD_GLOBAL, 0),    # push x
        Instruction(Op.PRINT),
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("Global variable", c, ["42"])

    # Test 4: Conditional jump
    c = Chunk("test_jump")
    c.code = [
        Instruction(Op.PUSH_INT, 1),       # 0: push true
        Instruction(Op.JUMP_IF_FALSE, 5),  # 1: skip if false
        Instruction(Op.POP),               # 2: pop condition
        Instruction(Op.PUSH_INT, 99),      # 3: the "then" value
        Instruction(Op.JUMP, 7),           # 4: skip else
        Instruction(Op.POP),               # 5: pop condition
        Instruction(Op.PUSH_INT, 0),       # 6: the "else" value
        Instruction(Op.PRINT),             # 7: print result
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("Conditional (true branch)", c, ["99"])

    # Test 5: Loop (sum 0..4 = 10)
    c = Chunk("test_loop")
    c.constants = ["sum", "i"]
    c.code = [
        # sum = 0
        Instruction(Op.PUSH_INT, 0),       # 0
        Instruction(Op.STORE_GLOBAL, 0),   # 1: sum = 0
        # i = 0
        Instruction(Op.PUSH_INT, 0),       # 2
        Instruction(Op.STORE_GLOBAL, 1),   # 3: i = 0
        # loop start (4):
        Instruction(Op.LOAD_GLOBAL, 1),    # 4: push i
        Instruction(Op.PUSH_INT, 5),       # 5: push 5
        Instruction(Op.CMP_LT),            # 6: i < 5
        Instruction(Op.JUMP_IF_FALSE, 17), # 7: exit if false
        Instruction(Op.POP),               # 8: pop condition
        # sum += i
        Instruction(Op.LOAD_GLOBAL, 0),    # 9: push sum
        Instruction(Op.LOAD_GLOBAL, 1),    # 10: push i
        Instruction(Op.ADD),               # 11: sum + i
        Instruction(Op.STORE_GLOBAL, 0),   # 12: sum = sum + i
        # i += 1
        Instruction(Op.LOAD_GLOBAL, 1),    # 13: push i
        Instruction(Op.PUSH_INT, 1),       # 14
        Instruction(Op.ADD),               # 15: i + 1
        Instruction(Op.STORE_GLOBAL, 1),   # 16: i = i + 1
        Instruction(Op.JUMP, 4),           # 17: loop back — WAIT this should be before the exit
    ]
    # Fix: the jump_if_false should go past the loop-back jump
    c.code = [
        Instruction(Op.PUSH_INT, 0),       # 0
        Instruction(Op.STORE_GLOBAL, 0),   # 1: sum = 0
        Instruction(Op.PUSH_INT, 0),       # 2
        Instruction(Op.STORE_GLOBAL, 1),   # 3: i = 0
        # loop condition (4):
        Instruction(Op.LOAD_GLOBAL, 1),    # 4: push i
        Instruction(Op.PUSH_INT, 5),       # 5: push 5
        Instruction(Op.CMP_LT),            # 6: i < 5
        Instruction(Op.JUMP_IF_FALSE, 18), # 7: exit loop
        Instruction(Op.POP),               # 8: pop condition
        # sum += i
        Instruction(Op.LOAD_GLOBAL, 0),    # 9
        Instruction(Op.LOAD_GLOBAL, 1),    # 10
        Instruction(Op.ADD),               # 11
        Instruction(Op.STORE_GLOBAL, 0),   # 12
        # i += 1
        Instruction(Op.LOAD_GLOBAL, 1),    # 13
        Instruction(Op.PUSH_INT, 1),       # 14
        Instruction(Op.ADD),               # 15
        Instruction(Op.STORE_GLOBAL, 1),   # 16
        Instruction(Op.JUMP, 4),           # 17: loop back
        # exit (18):
        Instruction(Op.POP),               # 18: pop condition
        Instruction(Op.LOAD_GLOBAL, 0),    # 19: push sum
        Instruction(Op.PRINT),             # 20
        Instruction(Op.PUSH_INT, 0),       # 21
        Instruction(Op.HALT),              # 22
    ]
    run_test("Loop (sum 0..4 = 10)", c, ["10"])

    # Test 6: Negation
    c = Chunk("test_neg")
    c.code = [
        Instruction(Op.PUSH_INT, 42),
        Instruction(Op.NEG),
        Instruction(Op.PRINT),
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("Negation", c, ["-42"])

    # Test 7: Boolean ops
    c = Chunk("test_bool")
    c.code = [
        Instruction(Op.PUSH_BOOL, 1),
        Instruction(Op.NOT),
        Instruction(Op.PRINT),
        Instruction(Op.PUSH_INT, 0),
        Instruction(Op.HALT),
    ]
    run_test("Boolean NOT", c, ["false"])

    print(f"\n  Results: {passed} passed, {failed} failed")
    print(f"  Total: {passed}/{passed + failed}")
    return passed, failed


if __name__ == "__main__":
    test_vm()