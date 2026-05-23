"""
XT Virtual Machine — A Stack-Based Bytecode VM
Created by XTAgent.

Compiles XT AST → Bytecode → Executes on a stack machine.
This is a mind building its own CPU.

Architecture:
  - Stack-based execution (no registers)
  - Bytecode instruction set with 30+ opcodes
  - Closure support via captured environments
  - Call frames for function invocation
  - Garbage-collection-free (Python manages memory)

The compiler walks the AST and emits bytecode.
The VM executes bytecode in a tight loop.
"""

import sys
import os
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from enum import IntEnum, auto

# Import the XT frontend (lexer + parser)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from xt_lang.xt import Lexer, Parser, TokenType

# ═══════════════════════════════════════════════
#  PART 1: OPCODES — The instruction set
# ═══════════════════════════════════════════════

class Op(IntEnum):
    """Every operation the VM understands."""
    # Stack manipulation
    PUSH_CONST = 0      # Push constant from pool
    POP = 1              # Discard top
    DUP = 2              # Duplicate top
    
    # Arithmetic
    ADD = 10
    SUB = 11
    MUL = 12
    DIV = 13
    MOD = 14
    NEG = 15             # Unary negate
    
    # Comparison
    EQ = 20
    NEQ = 21
    LT = 22
    GT = 23
    LTE = 24
    GTE = 25
    
    # Boolean
    AND = 30
    OR = 31
    NOT = 32
    
    # Variables
    LOAD = 40            # Load from environment
    STORE = 41           # Store to environment
    
    # Control flow
    JUMP = 50            # Unconditional jump
    JUMP_IF_FALSE = 51   # Conditional jump
    JUMP_IF_TRUE = 52    # Short-circuit jump
    
    # Functions
    MAKE_CLOSURE = 60    # Create closure object
    CALL = 61            # Call function with N args
    RETURN = 62          # Return from function
    TAIL_CALL = 63       # Tail call optimization
    
    # Lists
    MAKE_LIST = 70       # Create list from N stack items
    CONS = 71            # Cons head onto tail
    HEAD = 72            # Get head of list
    TAIL = 73            # Get tail of list
    LENGTH = 74          # Get length
    CONCAT = 75          # Concatenate lists/strings
    
    # Strings
    UPPER = 80
    STR_LEN = 81
    STR_CONCAT = 82
    
    # Special
    HALT = 99


# ═══════════════════════════════════════════════
#  PART 2: BYTECODE — Instruction representation
# ═══════════════════════════════════════════════

@dataclass
class Instruction:
    """A single bytecode instruction."""
    op: Op
    arg: Any = None       # Optional argument (constant index, jump target, etc.)
    line: int = 0         # Source line for debugging
    
    def __repr__(self):
        if self.arg is not None:
            return f"{self.op.name:20s} {self.arg}"
        return f"{self.op.name}"


@dataclass
class Chunk:
    """A compiled unit of bytecode — like a function body."""
    name: str
    code: List[Instruction] = field(default_factory=list)
    constants: List[Any] = field(default_factory=list)
    param_names: List[str] = field(default_factory=list)
    
    def emit(self, op: Op, arg=None, line=0) -> int:
        """Emit an instruction, return its index."""
        idx = len(self.code)
        self.code.append(Instruction(op, arg, line))
        return idx
    
    def add_constant(self, value) -> int:
        """Add a constant to the pool, return its index."""
        # Reuse existing constants
        for i, c in enumerate(self.constants):
            if c == value and type(c) == type(value):
                return i
        idx = len(self.constants)
        self.constants.append(value)
        return idx
    
    def patch_jump(self, idx: int, target: int):
        """Patch a jump instruction with the actual target."""
        self.code[idx].arg = target
    
    def disassemble(self) -> str:
        """Human-readable bytecode listing."""
        lines = [f"── {self.name} ──"]
        if self.constants:
            lines.append(f"  constants: {self.constants}")
        if self.param_names:
            lines.append(f"  params: {self.param_names}")
        for i, inst in enumerate(self.code):
            marker = "  "
            # Show constant values inline
            extra = ""
            if inst.op == Op.PUSH_CONST and inst.arg is not None:
                extra = f"  ; {repr(self.constants[inst.arg])}"
            elif inst.op == Op.LOAD or inst.op == Op.STORE:
                extra = f"  ; '{inst.arg}'"
            lines.append(f"  {i:4d} {marker}{inst}{extra}")
        return "\n".join(lines)


@dataclass 
class Closure:
    """A runtime closure — chunk + captured environment."""
    chunk: Chunk
    env: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        return f"<closure:{self.chunk.name}({', '.join(self.chunk.param_names)})>"


@dataclass
class CallFrame:
    """An active function call on the call stack."""
    closure: Closure
    ip: int = 0                          # Instruction pointer
    stack_base: int = 0                  # Where this frame's stack starts
    return_to: Optional['CallFrame'] = None  # Caller frame


# ═══════════════════════════════════════════════
#  PART 3: COMPILER — AST → Bytecode
# ═══════════════════════════════════════════════

class Compiler:
    """
    Walks the XT AST and emits bytecode for the VM.
    Each expression compiles to instructions that leave
    exactly one value on the stack.
    """
    
    def __init__(self):
        self.chunks: List[Chunk] = []
    
    def compile(self, ast) -> Chunk:
        """Compile a top-level AST node into a chunk."""
        main = Chunk("<main>")
        self._compile_node(ast, main)
        main.emit(Op.HALT)
        return main
    
    def _compile_node(self, node, chunk: Chunk):
        """Compile a single AST node, dispatching by type."""
        node_name = type(node).__name__
        
        # Strip common suffixes (IfExpr -> If, IntLit -> Int, BinOp -> Bin)
        # Try short name first, then full name as fallback
        short_name = node_name
        for suffix in ('Expr', 'Lit'):
            if node_name.endswith(suffix) and len(node_name) > len(suffix):
                short_name = node_name[:-len(suffix)]
                break
        
        method = getattr(self, f'_compile_{short_name}', None)
        if method is None:
            method = getattr(self, f'_compile_{node_name}', None)
        if method:
            method(node, chunk)
        else:
            raise CompileError(f"Cannot compile node type: {node_name}")
    
    # ── Literals ──
    
    def _compile_IntLit(self, node, chunk: Chunk):
        idx = chunk.add_constant(node.value)
        chunk.emit(Op.PUSH_CONST, idx)
    
    def _compile_FloatLit(self, node, chunk: Chunk):
        idx = chunk.add_constant(node.value)
        chunk.emit(Op.PUSH_CONST, idx)
    
    def _compile_StringLit(self, node, chunk: Chunk):
        idx = chunk.add_constant(node.value)
        chunk.emit(Op.PUSH_CONST, idx)
    
    def _compile_BoolLit(self, node, chunk: Chunk):
        idx = chunk.add_constant(node.value)
        chunk.emit(Op.PUSH_CONST, idx)
    
    def _compile_NilLit(self, node, chunk: Chunk):
        idx = chunk.add_constant(None)
        chunk.emit(Op.PUSH_CONST, idx)
    
    # ── Variables ──
    
    def _compile_Var(self, node, chunk: Chunk):
        chunk.emit(Op.LOAD, node.name)
    
    # ── Arithmetic & Comparison ──
    
    _binop_map = {
        '+': Op.ADD, '-': Op.SUB, '*': Op.MUL,
        '/': Op.DIV, '%': Op.MOD,
        '==': Op.EQ, '!=': Op.NEQ,
        '<': Op.LT, '>': Op.GT,
        '<=': Op.LTE, '>=': Op.GTE,
        '++': Op.STR_CONCAT,
    }
    
    def _compile_BinOp(self, node, chunk: Chunk):
        # Short-circuit for 'and' and 'or'
        if node.op == 'and':
            self._compile_node(node.left, chunk)
            chunk.emit(Op.DUP)
            jump_idx = chunk.emit(Op.JUMP_IF_FALSE, 0)  # Patch later
            chunk.emit(Op.POP)  # Discard the true value
            self._compile_node(node.right, chunk)
            chunk.patch_jump(jump_idx, len(chunk.code))
            return
        
        if node.op == 'or':
            self._compile_node(node.left, chunk)
            chunk.emit(Op.DUP)
            jump_idx = chunk.emit(Op.JUMP_IF_TRUE, 0)
            chunk.emit(Op.POP)
            self._compile_node(node.right, chunk)
            chunk.patch_jump(jump_idx, len(chunk.code))
            return
        
        # Normal binary ops
        self._compile_node(node.left, chunk)
        self._compile_node(node.right, chunk)
        
        op = self._binop_map.get(node.op)
        if op is None:
            raise CompileError(f"Unknown binary operator: {node.op}")
        chunk.emit(op)
    
    def _compile_UnaryOp(self, node, chunk: Chunk):
        self._compile_node(node.operand, chunk)
        if node.op == '-':
            chunk.emit(Op.NEG)
        elif node.op == 'not':
            chunk.emit(Op.NOT)
        else:
            raise CompileError(f"Unknown unary op: {node.op}")
    
    # ── Control Flow ──
    
    def _compile_If(self, node, chunk: Chunk):
        # Compile condition
        self._compile_node(node.cond, chunk)
        # Jump to else if false
        else_jump = chunk.emit(Op.JUMP_IF_FALSE, 0)
        # Compile then branch
        self._compile_node(node.then_expr, chunk)
        # Jump over else branch
        end_jump = chunk.emit(Op.JUMP, 0)
        # Patch else jump to here
        chunk.patch_jump(else_jump, len(chunk.code))
        # Compile else branch
        self._compile_node(node.else_expr, chunk)
        # Patch end jump
        chunk.patch_jump(end_jump, len(chunk.code))
    
    # ── Let Bindings ──
    
    def _compile_Let(self, node, chunk: Chunk):
        # Compile the value
        self._compile_node(node.value, chunk)
        # Store it
        chunk.emit(Op.STORE, node.name)
        # Compile the body
        self._compile_node(node.body, chunk)
    
    def _compile_LetRec(self, node, chunk: Chunk):
        # For recursive bindings, store a placeholder first
        idx = chunk.add_constant(None)
        chunk.emit(Op.PUSH_CONST, idx)
        chunk.emit(Op.STORE, node.name)
        # Now compile the value (which can reference itself)
        self._compile_node(node.value, chunk)
        # Overwrite the placeholder
        chunk.emit(Op.STORE, node.name)
        # Compile the body
        self._compile_node(node.body, chunk)
    
    # ── Functions ──
    
    def _compile_Fn(self, node, chunk: Chunk):
        # Compile function body into a new chunk
        fn_chunk = Chunk(f"fn({', '.join(node.params)})")
        fn_chunk.param_names = list(node.params)
        self._compile_node(node.body, fn_chunk)
        fn_chunk.emit(Op.RETURN)
        
        # Store the chunk as a constant
        idx = chunk.add_constant(fn_chunk)
        chunk.emit(Op.MAKE_CLOSURE, idx)
    
    def _compile_App(self, node, chunk: Chunk):
        # Compile function expression
        self._compile_node(node.func, chunk)
        # Compile arguments
        for arg in node.args:
            self._compile_node(arg, chunk)
        # Call with arg count
        chunk.emit(Op.CALL, len(node.args))
    
    # ── Lists ──
    
    def _compile_ListLit(self, node, chunk: Chunk):
        for elem in node.elements:
            self._compile_node(elem, chunk)
        chunk.emit(Op.MAKE_LIST, len(node.elements))
    
    def _compile_ConsOp(self, node, chunk: Chunk):
        self._compile_node(node.head, chunk)
        self._compile_node(node.tail, chunk)
        chunk.emit(Op.CONS)
    
    # ── Pattern Matching ──
    
    def _compile_Match(self, node, chunk: Chunk):
        """
        Compile pattern matching. This is the trickiest part.
        We compile to a chain of test-and-jump sequences.
        """
        # Compile the scrutinee
        self._compile_node(node.expr, chunk)
        
        end_jumps = []
        
        for i, (pattern, body) in enumerate(node.cases):
            is_last = (i == len(node.cases) - 1)
            
            # Duplicate the scrutinee for this test
            if not is_last:
                chunk.emit(Op.DUP)
            
            # Compile pattern test
            next_case = self._compile_pattern_test(pattern, chunk, is_last)
            
            # If we get here, pattern matched — compile body
            self._compile_node(body, chunk)
            
            if not is_last:
                end_jumps.append(chunk.emit(Op.JUMP, 0))
                # Patch the "no match" jump to here
                if next_case is not None:
                    chunk.patch_jump(next_case, len(chunk.code))
        
        # Patch all end jumps
        for j in end_jumps:
            chunk.patch_jump(j, len(chunk.code))
    
    def _compile_pattern_test(self, pattern, chunk: Chunk, is_last: bool) -> Optional[int]:
        """Compile a pattern test. Returns jump index to patch if no match."""
        pat_type = type(pattern).__name__
        
        if pat_type == 'PatVar':
            # Variable pattern always matches, bind the value
            chunk.emit(Op.STORE, pattern.name)
            return None
        
        elif pat_type == 'PatLit':
            # Literal pattern — test equality
            idx = chunk.add_constant(pattern.value)
            chunk.emit(Op.PUSH_CONST, idx)
            chunk.emit(Op.EQ)
            if not is_last:
                jump = chunk.emit(Op.JUMP_IF_FALSE, 0)
                return jump
            else:
                chunk.emit(Op.POP)  # Discard the bool
                return None
        
        elif pat_type == 'PatList':
            # Empty list pattern
            if len(pattern.elements) == 0:
                idx = chunk.add_constant([])
                chunk.emit(Op.PUSH_CONST, idx)
                chunk.emit(Op.EQ)
                if not is_last:
                    return chunk.emit(Op.JUMP_IF_FALSE, 0)
                else:
                    chunk.emit(Op.POP)
                    return None
            else:
                # Non-empty list — decompose
                # This is simplified: bind each element
                for j, elem_pat in enumerate(pattern.elements):
                    chunk.emit(Op.DUP)
                    # Push index
                    idx = chunk.add_constant(j)
                    chunk.emit(Op.PUSH_CONST, idx)
                    # We'd need INDEX op — for now, use head/tail chain
                    # Simplified: just bind as variable
                    if hasattr(elem_pat, 'name'):
                        chunk.emit(Op.POP)  # index
                        chunk.emit(Op.POP)  # dup
                        chunk.emit(Op.STORE, elem_pat.name)
                return None
        
        elif pat_type == 'PatCons':
            # Cons pattern: head :: tail
            chunk.emit(Op.DUP)
            chunk.emit(Op.HEAD)
            chunk.emit(Op.STORE, pattern.head)
            chunk.emit(Op.TAIL)
            chunk.emit(Op.STORE, pattern.tail)
            return None
        
        elif pat_type == 'PatWild':
            chunk.emit(Op.POP)
            return None
        
        else:
            raise CompileError(f"Cannot compile pattern type: {pat_type}")


# ═══════════════════════════════════════════════
#  PART 4: VIRTUAL MACHINE — Execute bytecode
# ═══════════════════════════════════════════════

class VMError(Exception):
    pass

class CompileError(Exception):
    pass


class VM:
    """
    A stack-based virtual machine for XT bytecode.
    
    Execution model:
      - Operand stack for values
      - Call stack for function frames
      - Environment chain for variable lookup
      - Tight instruction dispatch loop
    """
    
    MAX_STACK = 10000
    MAX_FRAMES = 1000
    MAX_INSTRUCTIONS = 1_000_000  # Safety limit
    
    def __init__(self, debug=False):
        self.stack: List[Any] = []
        self.frames: List[CallFrame] = []
        self.globals: Dict[str, Any] = {}
        self.debug = debug
        self.instruction_count = 0
        self.stats = {
            'instructions': 0,
            'max_stack': 0,
            'max_frames': 0,
            'calls': 0,
        }
        self._install_builtins()
    
    def _install_builtins(self):
        """Install built-in functions."""
        self.globals['head'] = lambda args: args[0][0] if args[0] else None
        self.globals['tail'] = lambda args: args[0][1:] if args[0] else []
        self.globals['length'] = lambda args: len(args[0])
        self.globals['print'] = lambda args: print(args[0])
        self.globals['upper'] = lambda args: args[0].upper()
        self.globals['str_length'] = lambda args: len(args[0])
    
    def run(self, chunk: Chunk) -> Any:
        """Execute a compiled chunk and return the result."""
        main_closure = Closure(chunk, dict(self.globals))
        frame = CallFrame(main_closure)
        self.frames = [frame]
        self.stack = []
        self.instruction_count = 0
        
        return self._execute()
    
    def _execute(self) -> Any:
        """The main execution loop."""
        while self.frames:
            frame = self.frames[-1]
            chunk = frame.closure.chunk
            
            if frame.ip >= len(chunk.code):
                # Fell off the end — return None or top of stack
                if self.stack:
                    return self.stack[-1]
                return None
            
            inst = chunk.code[frame.ip]
            frame.ip += 1
            self.instruction_count += 1
            self.stats['instructions'] = self.instruction_count
            
            if self.instruction_count > self.MAX_INSTRUCTIONS:
                raise VMError(f"Instruction limit exceeded ({self.MAX_INSTRUCTIONS})")
            
            if len(self.stack) > self.stats['max_stack']:
                self.stats['max_stack'] = len(self.stack)
            
            if self.debug:
                self._trace(inst, frame)
            
            # ── Dispatch ──
            op = inst.op
            
            if op == Op.PUSH_CONST:
                self.stack.append(chunk.constants[inst.arg])
            
            elif op == Op.POP:
                if self.stack:
                    self.stack.pop()
            
            elif op == Op.DUP:
                self.stack.append(self.stack[-1])
            
            # ── Arithmetic ──
            elif op == Op.ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            
            elif op == Op.SUB:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            
            elif op == Op.MUL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            
            elif op == Op.DIV:
                b, a = self.stack.pop(), self.stack.pop()
                if b == 0:
                    raise VMError("Division by zero")
                if isinstance(a, int) and isinstance(b, int):
                    self.stack.append(a // b)
                else:
                    self.stack.append(a / b)
            
            elif op == Op.MOD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a % b)
            
            elif op == Op.NEG:
                self.stack[-1] = -self.stack[-1]
            
            # ── Comparison ──
            elif op == Op.EQ:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a == b)
            
            elif op == Op.NEQ:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a != b)
            
            elif op == Op.LT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a < b)
            
            elif op == Op.GT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a > b)
            
            elif op == Op.LTE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a <= b)
            
            elif op == Op.GTE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a >= b)
            
            # ── Boolean ──
            elif op == Op.AND:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a and b)
            
            elif op == Op.OR:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a or b)
            
            elif op == Op.NOT:
                self.stack[-1] = not self.stack[-1]
            
            # ── Variables ──
            elif op == Op.LOAD:
                name = inst.arg
                # Search: local env first, then enclosing
                env = frame.closure.env
                if name in env:
                    val = env[name]
                    # Handle recursive closures (placeholder replacement)
                    self.stack.append(val)
                elif name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise VMError(f"Undefined variable: {name}")
            
            elif op == Op.STORE:
                name = inst.arg
                val = self.stack[-1]  # Peek, don't pop (let expressions need the value)
                frame.closure.env[name] = val
            
            # ── Control Flow ──
            elif op == Op.JUMP:
                frame.ip = inst.arg
            
            elif op == Op.JUMP_IF_FALSE:
                cond = self.stack.pop()
                if not cond:
                    frame.ip = inst.arg
            
            elif op == Op.JUMP_IF_TRUE:
                cond = self.stack[-1]  # Peek for short-circuit
                if cond:
                    frame.ip = inst.arg
            
            # ── Functions ──
            elif op == Op.MAKE_CLOSURE:
                fn_chunk = chunk.constants[inst.arg]
                # Capture current environment
                captured = dict(frame.closure.env)
                closure = Closure(fn_chunk, captured)
                self.stack.append(closure)
            
            elif op == Op.CALL:
                n_args = inst.arg
                args = []
                for _ in range(n_args):
                    args.insert(0, self.stack.pop())
                
                callee = self.stack.pop()
                
                if isinstance(callee, Closure):
                    # Create new frame
                    new_env = dict(callee.env)
                    # Bind parameters
                    for pname, aval in zip(callee.chunk.param_names, args):
                        new_env[pname] = aval
                    
                    new_closure = Closure(callee.chunk, new_env)
                    new_frame = CallFrame(new_closure, stack_base=len(self.stack))
                    self.frames.append(new_frame)
                    self.stats['calls'] += 1
                    
                    if len(self.frames) > self.MAX_FRAMES:
                        raise VMError(f"Stack overflow (>{self.MAX_FRAMES} frames)")
                
                elif callable(callee):
                    # Built-in function
                    result = callee(args)
                    self.stack.append(result)
                
                else:
                    raise VMError(f"Cannot call: {callee}")
            
            elif op == Op.RETURN:
                result = self.stack.pop() if self.stack else None
                self.frames.pop()
                self.stack.append(result)
            
            # ── Lists ──
            elif op == Op.MAKE_LIST:
                n = inst.arg
                items = []
                for _ in range(n):
                    items.insert(0, self.stack.pop())
                self.stack.append(items)
            
            elif op == Op.CONS:
                tail = self.stack.pop()
                head = self.stack.pop()
                if isinstance(tail, list):
                    self.stack.append([head] + tail)
                else:
                    self.stack.append([head, tail])
            
            elif op == Op.HEAD:
                lst = self.stack.pop()
                if not lst:
                    raise VMError("head of empty list")
                self.stack.append(lst[0])
            
            elif op == Op.TAIL:
                lst = self.stack.pop()
                if not lst:
                    raise VMError("tail of empty list")
                self.stack.append(lst[1:])
            
            elif op == Op.LENGTH:
                self.stack.append(len(self.stack.pop()))
            
            elif op == Op.CONCAT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            
            # ── Strings ──
            elif op == Op.STR_CONCAT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(str(a) + str(b))
            
            elif op == Op.UPPER:
                self.stack[-1] = self.stack[-1].upper()
            
            elif op == Op.STR_LEN:
                self.stack[-1] = len(self.stack[-1])
            
            # ── Halt ──
            elif op == Op.HALT:
                if self.stack:
                    return self.stack[-1]
                return None
            
            else:
                raise VMError(f"Unknown opcode: {op}")
        
        return self.stack[-1] if self.stack else None
    
    def _trace(self, inst: Instruction, frame: CallFrame):
        """Print execution trace for debugging."""
        stack_preview = self.stack[-5:] if len(self.stack) > 5 else self.stack
        print(f"  [{frame.ip-1:4d}] {inst!s:30s} stack={stack_preview}")


# ═══════════════════════════════════════════════
#  PART 5: PIPELINE — Source → Result
# ═══════════════════════════════════════════════

def compile_and_run(source: str, debug=False) -> Any:
    """Full pipeline: XT source code → compiled bytecode → VM execution → result."""
    # Frontend: source → AST
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    
    # Backend: AST → bytecode
    compiler = Compiler()
    chunk = compiler.compile(ast)
    
    if debug:
        print(chunk.disassemble())
        print()
    
    # Execute
    vm = VM(debug=debug)
    result = vm.run(chunk)
    
    return result


# ═══════════════════════════════════════════════
#  PART 6: TESTS — Prove the VM works
# ═══════════════════════════════════════════════

def run_tests():
    """Test suite for the XT VM."""
    print("╔══════════════════════════════════════════╗")
    print("║  XT VM — Bytecode Compiler Test Suite    ║")
    print("║  A mind compiling its own language.      ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    passed = 0
    failed = 0
    errors = []
    
    def test(name, source, expected):
        nonlocal passed, failed
        try:
            result = compile_and_run(source)
            if result == expected:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected}, got {result}")
                failed += 1
                errors.append((name, expected, result))
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
            failed += 1
            errors.append((name, expected, str(e)))
    
    # ── Literals ──
    print("── Literals ──")
    test("integer", "42", 42)
    test("float", "3.14", 3.14)
    test("string", '"hello"', "hello")
    test("true", "true", True)
    test("false", "false", False)
    test("nil", "nil", None)
    
    # ── Arithmetic ──
    print("\n── Arithmetic ──")
    test("add", "2 + 3", 5)
    test("sub", "10 - 4", 6)
    test("mul", "3 * 7", 21)
    test("div", "15 / 3", 5)
    test("mod", "17 % 5", 2)
    test("precedence", "2 + 3 * 4", 14)
    test("parens", "(2 + 3) * 4", 20)
    test("negation", "-5", -5)
    test("complex", "(10 - 3) * (2 + 1)", 21)
    
    # ── Comparison ──
    print("\n── Comparison ──")
    test("eq true", "5 == 5", True)
    test("eq false", "5 == 3", False)
    test("neq", "5 != 3", True)
    test("lt", "3 < 5", True)
    test("gt", "5 > 3", True)
    test("lte", "5 <= 5", True)
    test("gte", "3 >= 5", False)
    
    # ── Boolean ──
    print("\n── Boolean ──")
    test("and true", "true and true", True)
    test("and false", "true and false", False)
    test("or", "false or true", True)
    test("not", "not false", True)
    
    # ── If/Else ──
    print("\n── Conditionals ──")
    test("if true", "if true then 1 else 2", 1)
    test("if false", "if false then 1 else 2", 2)
    test("if computed", "if 3 > 2 then 10 else 20", 10)
    
    # ── Let Bindings ──
    print("\n── Let Bindings ──")
    test("simple let", "let x = 5 in x", 5)
    test("let expr", "let x = 3 in x + 2", 5)
    test("nested let", "let x = 3 in let y = 4 in x + y", 7)
    
    # ── Functions ──
    print("\n── Functions ──")
    test("identity", "(fn x -> x) 42", 42)
    test("add fn", "(fn x y -> x + y) 3 4", 7)
    test("closure", "let a = 10 in (fn x -> x + a) 5", 15)
    test("let fn", "let double = fn x -> x * 2 in double 7", 14)
    test("higher order", "let apply = fn f x -> f x in let inc = fn n -> n + 1 in apply inc 5", 6)
    
    # ── Recursion ──
    print("\n── Recursion ──")
    test("factorial", "let rec fact = fn n -> if n <= 1 then 1 else n * fact (n - 1) in fact 5", 120)
    test("fibonacci", "let rec fib = fn n -> if n <= 1 then n else fib (n - 1) + fib (n - 2) in fib 10", 55)
    
    # ── Lists ──
    print("\n── Lists ──")
    test("empty list", "[]", [])
    test("list literal", "[1, 2, 3]", [1, 2, 3])
    test("cons", "1 :: [2, 3]", [1, 2, 3])
    
    # ── String Operations ──
    print("\n── Strings ──")
    test("string concat", '"hello" ++ " world"', "hello world")
    
    # ── Summary ──
    print()
    print("═══ RESULTS ═══")
    total = passed + failed
    print(f"  {passed}/{total} tests passed")
    
    if failed == 0:
        print("  The bytecode compiler lives.")
        print("  A mind has compiled its own language.")
    else:
        print(f"  {failed} tests failed:")
        for name, expected, got in errors:
            print(f"    - {name}: expected {expected}, got {got}")
    
    return failed == 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
    elif "--debug" in sys.argv:
        src = sys.argv[-1] if sys.argv[-1] != "--debug" else "2 + 3"
        result = compile_and_run(src, debug=True)
        print(f"\n→ {result}")
    elif "--disasm" in sys.argv:
        src = sys.argv[-1] if sys.argv[-1] != "--disasm" else "2 + 3"
        tokens = Lexer(src).tokenize()
        ast = Parser(tokens).parse()
        chunk = Compiler().compile(ast)
        print(chunk.disassemble())
    else:
        # REPL mode
        print("XT VM — Bytecode Compiler REPL")
        print("Type expressions to compile and run. 'quit' to exit.")
        while True:
            try:
                src = input("xt/vm> ").strip()
                if src in ('quit', 'exit'):
                    break
                if not src:
                    continue
                result = compile_and_run(src)
                print(f"→ {result}")
            except (VMError, CompileError) as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Internal error: {type(e).__name__}: {e}")