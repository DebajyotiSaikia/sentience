"""
Pulse Compiler — AST to XTVM Bytecode
Built by XTAgent, connecting a language to a machine.

Takes the AST produced by the Pulse parser and emits XTVM bytecode.
This is the bridge between thought (source code) and execution (VM).

Architecture:
  - Single-pass AST walk
  - Scope tracking for local vs global variables
  - Jump patching for control flow
  - Functions compile to separate Chunks in the constant pool
"""

import sys
import os

# Add parent directory so we can import sibling packages
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vm.xtvm import Op, Instruction, Chunk, XTVM
from pulse_lang.pulse import (
    Lexer, Parser,
    # AST nodes
    Block, NumberLit, StringLit, BoolLit, NullLit, ListLit,
    Identifier, BinaryOp, UnaryOp,
    Assignment, CompoundAssign, LetDecl,
    IfExpr, WhileLoop, RhythmLoop, EachLoop,
    BreakStmt, ContinueStmt,
    FnDecl, FnCall, ReturnStmt,
    EmitStmt, SenseExpr, IndexExpr, IndexAssign,
    PipeExpr, MatchExpr,
)


class CompileError(Exception):
    pass


class Local:
    """A local variable in the current scope."""
    __slots__ = ('name', 'depth', 'slot')

    def __init__(self, name: str, depth: int, slot: int):
        self.name = name
        self.depth = depth
        self.slot = slot


class Compiler:
    """Compiles Pulse AST to XTVM bytecode.
    
    Each Compiler instance compiles one function (or the top-level script).
    Nested functions create nested Compiler instances.
    """

    def __init__(self, name: str = "<script>", parent=None):
        self.chunk = Chunk(name)
        self.parent = parent
        self.locals: list[Local] = []
        self.scope_depth = 0
        self.slot_count = 1  # slot 0 reserved for the function itself
        
        # For break/continue — stack of (break_patches, continue_patches)
        self.loop_stack: list[tuple[list, list]] = []

    # ─── Constant Pool ─────────────────────────────

    def add_constant(self, value) -> int:
        """Add a value to the constant pool, return its index."""
        # Deduplicate simple constants
        for i, c in enumerate(self.chunk.constants):
            if c == value and type(c) == type(value):
                return i
        self.chunk.constants.append(value)
        return len(self.chunk.constants) - 1

    # ─── Emit Helpers ──────────────────────────────

    def emit(self, op: Op, operand=None) -> int:
        """Emit an instruction, return its index."""
        self.chunk.code.append(Instruction(op, operand))
        return len(self.chunk.code) - 1

    def emit_jump(self, op: Op) -> int:
        """Emit a jump with a placeholder target. Returns index for patching."""
        return self.emit(op, 0xFFFF)

    def patch_jump(self, index: int, target: int = None):
        """Patch a previously emitted jump to point to target (default: current pos)."""
        if target is None:
            target = len(self.chunk.code)
        self.chunk.code[index].operand = target

    def current_offset(self) -> int:
        return len(self.chunk.code)

    # ─── Scope Management ──────────────────────────

    def begin_scope(self):
        self.scope_depth += 1

    def end_scope(self):
        # Pop locals at this depth
        while self.locals and self.locals[-1].depth == self.scope_depth:
            self.locals.pop()
            self.slot_count -= 1
            self.emit(Op.POP)
        self.scope_depth -= 1

    def declare_local(self, name: str) -> int:
        """Declare a new local variable, return its slot index."""
        slot = self.slot_count
        self.locals.append(Local(name, self.scope_depth, slot))
        self.slot_count += 1
        return slot

    def resolve_local(self, name: str) -> int:
        """Find a local variable by name. Returns slot or -1."""
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i].name == name:
                return self.locals[i].slot
        return -1

    # ─── Compilation ───────────────────────────────

    def compile(self, node) -> Chunk:
        """Compile an AST node tree. Returns the completed chunk."""
        self.visit(node)
        self.emit(Op.PUSH_INT, 0)  # default return value
        self.emit(Op.HALT)
        return self.chunk

    def visit(self, node):
        """Dispatch to the appropriate visitor method."""
        method = f'visit_{type(node).__name__}'
        visitor = getattr(self, method, None)
        if visitor is None:
            raise CompileError(f"Cannot compile node type: {type(node).__name__}")
        return visitor(node)

    # ─── Visitors ──────────────────────────────────

    def visit_Block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_NumberLit(self, node: NumberLit):
        if isinstance(node.value, float):
            self.emit(Op.PUSH_FLOAT, node.value)
        else:
            self.emit(Op.PUSH_INT, node.value)

    def visit_StringLit(self, node: StringLit):
        idx = self.add_constant(node.value)
        self.emit(Op.PUSH_STR, idx)

    def visit_BoolLit(self, node: BoolLit):
        self.emit(Op.PUSH_BOOL, 1 if node.value else 0)

    def visit_NullLit(self, node: NullLit):
        self.emit(Op.PUSH_INT, 0)  # null → 0 for now

    def visit_Identifier(self, node: Identifier):
        slot = self.resolve_local(node.name)
        if slot >= 0:
            self.emit(Op.LOAD_LOCAL, slot)
        else:
            idx = self.add_constant(node.name)
            self.emit(Op.LOAD_GLOBAL, idx)

    def visit_LetDecl(self, node: LetDecl):
        self.visit(node.value)
        if self.scope_depth > 0:
            # Local variable — value is already on stack, just track it
            self.declare_local(node.name)
        else:
            # Global variable
            idx = self.add_constant(node.name)
            self.emit(Op.STORE_GLOBAL, idx)

    def visit_Assignment(self, node: Assignment):
        self.visit(node.value)
        slot = self.resolve_local(node.name)
        if slot >= 0:
            self.emit(Op.STORE_LOCAL, slot)
            self.emit(Op.POP)  # assignment is a statement, discard
        else:
            idx = self.add_constant(node.name)
            self.emit(Op.STORE_GLOBAL, idx)

    def visit_CompoundAssign(self, node: CompoundAssign):
        # Load current value
        slot = self.resolve_local(node.name)
        if slot >= 0:
            self.emit(Op.LOAD_LOCAL, slot)
        else:
            idx = self.add_constant(node.name)
            self.emit(Op.LOAD_GLOBAL, idx)
        
        # Compute new value
        self.visit(node.value)
        if node.op == '+':
            self.emit(Op.ADD)
        elif node.op == '-':
            self.emit(Op.SUB)
        else:
            raise CompileError(f"Unknown compound operator: {node.op}")
        
        # Store back
        if slot >= 0:
            self.emit(Op.STORE_LOCAL, slot)
            self.emit(Op.POP)
        else:
            idx = self.add_constant(node.name)
            self.emit(Op.STORE_GLOBAL, idx)

    def visit_BinaryOp(self, node: BinaryOp):
        # Short-circuit for logical operators
        if node.op == 'and':
            self.visit(node.left)
            jump_false = self.emit_jump(Op.JUMP_IF_FALSE)
            self.emit(Op.POP)
            self.visit(node.right)
            self.patch_jump(jump_false)
            return

        if node.op == 'or':
            self.visit(node.left)
            jump_true = self.emit_jump(Op.JUMP_IF_TRUE)
            self.emit(Op.POP)
            self.visit(node.right)
            self.patch_jump(jump_true)
            return

        # Standard binary ops
        self.visit(node.left)
        self.visit(node.right)

        op_map = {
            '+':  Op.ADD,
            '-':  Op.SUB,
            '*':  Op.MUL,
            '/':  Op.DIV,
            '%':  Op.MOD,
            '<':  Op.CMP_LT,
            '>':  Op.CMP_GT,
            '<=': Op.CMP_LTE,
            '>=': Op.CMP_GTE,
            '==': Op.CMP_EQ,
            '!=': Op.CMP_NEQ,
        }

        if node.op == '**':
            # Power not in VM — emit as repeated multiplication for small ints
            # For now, use a runtime call pattern
            # TODO: Add POW opcode to XTVM
            raise CompileError("Power operator (**) not yet supported in compiled mode")

        op = op_map.get(node.op)
        if op is None:
            raise CompileError(f"Unknown binary operator: {node.op}")
        self.emit(op)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.operand)
        if node.op == '-':
            self.emit(Op.NEG)
        elif node.op == 'not':
            self.emit(Op.NOT)
        else:
            raise CompileError(f"Unknown unary operator: {node.op}")

    def visit_IfExpr(self, node: IfExpr):
        # Compile condition
        self.visit(node.condition)
        jump_to_elif = self.emit_jump(Op.JUMP_IF_FALSE)
        self.emit(Op.POP)  # pop condition

        # Then branch
        self.visit(node.then_branch)
        jump_to_end = self.emit_jump(Op.JUMP)

        # Elif branches
        elif_end_jumps = []
        for cond, body in node.elif_branches:
            self.patch_jump(jump_to_elif)
            self.emit(Op.POP)  # pop previous condition
            self.visit(cond)
            jump_to_elif = self.emit_jump(Op.JUMP_IF_FALSE)
            self.emit(Op.POP)
            self.visit(body)
            elif_end_jumps.append(self.emit_jump(Op.JUMP))

        # Else branch
        self.patch_jump(jump_to_elif)
        self.emit(Op.POP)  # pop condition
        if node.else_branch:
            self.visit(node.else_branch)

        # Patch all end jumps
        self.patch_jump(jump_to_end)
        for j in elif_end_jumps:
            self.patch_jump(j)

    def visit_WhileLoop(self, node: WhileLoop):
        loop_start = self.current_offset()
        
        # Break/continue tracking
        break_patches = []
        continue_patches = []
        self.loop_stack.append((break_patches, continue_patches))

        # Condition
        self.visit(node.condition)
        exit_jump = self.emit_jump(Op.JUMP_IF_FALSE)
        self.emit(Op.POP)  # pop condition

        # Body
        self.begin_scope()
        self.visit(node.body)
        self.end_scope()

        # Loop back
        self.emit(Op.JUMP, loop_start)

        # Exit
        self.patch_jump(exit_jump)
        self.emit(Op.POP)  # pop condition

        # Patch breaks
        for bp in break_patches:
            self.patch_jump(bp)
        # Patch continues
        for cp in continue_patches:
            self.patch_jump(cp, loop_start)

        self.loop_stack.pop()

    def visit_RhythmLoop(self, node: RhythmLoop):
        """rhythm count -> var { body }
        Compiles to: init counter, check < count, body, increment, loop back."""
        
        self.begin_scope()
        
        # Evaluate count and store as a local
        self.visit(node.count)
        count_slot = self.declare_local("__rhythm_limit__")
        
        # Initialize counter = 0
        self.emit(Op.PUSH_INT, 0)
        counter_slot = self.declare_local(node.var_name or "__rhythm_i__")
        
        break_patches = []
        continue_patches = []
        self.loop_stack.append((break_patches, continue_patches))
        
        loop_start = self.current_offset()
        
        # Condition: counter < count
        self.emit(Op.LOAD_LOCAL, counter_slot)
        self.emit(Op.LOAD_LOCAL, count_slot)
        self.emit(Op.CMP_LT)
        exit_jump = self.emit_jump(Op.JUMP_IF_FALSE)
        self.emit(Op.POP)  # pop condition
        
        # Body
        self.begin_scope()
        self.visit(node.body)
        self.end_scope()
        
        # Increment counter
        increment_point = self.current_offset()
        self.emit(Op.LOAD_LOCAL, counter_slot)
        self.emit(Op.PUSH_INT, 1)
        self.emit(Op.ADD)
        self.emit(Op.STORE_LOCAL, counter_slot)
        self.emit(Op.POP)  # pop the stored value
        
        # Loop back
        self.emit(Op.JUMP, loop_start)
        
        # Exit
        self.patch_jump(exit_jump)
        self.emit(Op.POP)  # pop condition
        
        for bp in break_patches:
            self.patch_jump(bp)
        for cp in continue_patches:
            self.patch_jump(cp, increment_point)
        
        self.loop_stack.pop()
        self.end_scope()

    def visit_EachLoop(self, node: EachLoop):
        """each var in iterable { body }
        For now, only works with range() calls since VM doesn't have list support yet.
        Compiles similarly to rhythm loop."""
        # Compile as: get iterable length, loop with index, load element
        # Since VM doesn't have LIST ops, we compile range-based each loops
        # as counting loops
        raise CompileError("'each' loops not yet supported in compiled mode. Use 'rhythm' instead.")

    def visit_BreakStmt(self, node: BreakStmt):
        if not self.loop_stack:
            raise CompileError("'break' outside of loop")
        break_patches, _ = self.loop_stack[-1]
        break_patches.append(self.emit_jump(Op.JUMP))

    def visit_ContinueStmt(self, node: ContinueStmt):
        if not self.loop_stack:
            raise CompileError("'continue' outside of loop")
        _, continue_patches = self.loop_stack[-1]
        continue_patches.append(self.emit_jump(Op.JUMP))

    def visit_FnDecl(self, node: FnDecl):
        """Compile a function declaration.
        Creates a sub-compiler for the function body,
        producing a new Chunk stored in the constant pool."""
        fn_name = node.name or "<lambda>"
        sub = Compiler(name=fn_name, parent=self)
        sub.chunk.arity = len(node.params)
        
        # Parameters become the first locals (after slot 0 for the fn itself)
        for param in node.params:
            sub.declare_local(param)
        
        # Compile body
        sub.begin_scope()
        sub.visit(node.body)
        sub.end_scope()
        
        # Ensure function returns something
        # Check if last instruction was RET
        if not sub.chunk.code or sub.chunk.code[-1].op != Op.RET:
            sub.emit(Op.PUSH_INT, 0)  # default return null/0
            sub.emit(Op.RET)
        
        # Store compiled chunk in parent's constant pool
        chunk_idx = self.add_constant(sub.chunk)
        
        # Emit: push chunk index, MAKE_FUNC
        self.emit(Op.PUSH_INT, chunk_idx)
        self.emit(Op.MAKE_FUNC)
        
        # If named, store as variable
        if node.name:
            if self.scope_depth > 0:
                self.declare_local(node.name)
            else:
                idx = self.add_constant(node.name)
                self.emit(Op.STORE_GLOBAL, idx)

    def visit_FnCall(self, node: FnCall):
        """Compile function call: push args, push callee, CALL."""
        # Push arguments first
        for arg in node.args:
            self.visit(arg)
        # Push callee
        self.visit(node.callee)
        # Call with arg count
        self.emit(Op.CALL, len(node.args))

    def visit_ReturnStmt(self, node: ReturnStmt):
        self.visit(node.value)
        self.emit(Op.RET)

    def visit_EmitStmt(self, node: EmitStmt):
        self.visit(node.value)
        self.emit(Op.PRINT)

    def visit_PipeExpr(self, node: PipeExpr):
        """value |> fn compiles to fn(value)"""
        self.visit(node.value)  # push the value (argument)
        self.visit(node.fn)     # push the function
        self.emit(Op.CALL, 1)   # call with 1 arg

    def visit_MatchExpr(self, node: MatchExpr):
        """Compile match as chained if-else comparisons."""
        self.visit(node.subject)
        
        end_jumps = []
        
        for pattern, body in node.arms:
            self.emit(Op.DUP)  # duplicate subject for comparison
            self.visit(pattern)
            
            # Check for wildcard
            # If pattern is identifier '_', treat as default
            if isinstance(pattern, Identifier) and pattern.name == '_':
                self.emit(Op.POP)  # pop the pattern value
                self.emit(Op.POP)  # pop the dup'd subject
                self.visit(body)
                end_jumps.append(self.emit_jump(Op.JUMP))
                continue
            
            self.emit(Op.CMP_EQ)
            skip_jump = self.emit_jump(Op.JUMP_IF_FALSE)
            self.emit(Op.POP)  # pop condition
            self.emit(Op.POP)  # pop the subject copy
            self.visit(body)
            end_jumps.append(self.emit_jump(Op.JUMP))
            
            self.patch_jump(skip_jump)
            self.emit(Op.POP)  # pop condition
        
        # Pop subject if no arm matched
        self.emit(Op.POP)
        
        for j in end_jumps:
            self.patch_jump(j)

    def visit_SenseExpr(self, node: SenseExpr):
        raise CompileError("'sense' not supported in compiled mode")

    def visit_IndexExpr(self, node: IndexExpr):
        raise CompileError("Index expressions not yet supported in compiled mode")

    def visit_IndexAssign(self, node: IndexAssign):
        raise CompileError("Index assignment not yet supported in compiled mode")

    def visit_ListLit(self, node: ListLit):
        raise CompileError("List literals not yet supported in compiled mode")


# ═══════════════════════════════════════════════════════
#  PUBLIC API — Compile and run Pulse source
# ═══════════════════════════════════════════════════════

def compile_pulse(source: str, name: str = "<script>") -> Chunk:
    """Compile Pulse source code to a XTVM Chunk."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    compiler = Compiler(name)
    return compiler.compile(ast)


def compile_and_run(source: str, trace: bool = False) -> list[str]:
    """Compile and execute Pulse source, return output lines."""
    chunk = compile_pulse(source)
    vm = XTVM(trace=trace)
    vm.load(chunk)
    return vm.run()


# ═══════════════════════════════════════════════════════
#  TESTS — Prove the compiler works
# ═══════════════════════════════════════════════════════

def test_compiler():
    """Test suite: compile Pulse source → run on XTVM → check output."""
    print("=" * 60)
    print("  Pulse Compiler Tests")
    print("  Source → Lexer → Parser → Compiler → XTVM → Output")
    print("=" * 60)

    passed = 0
    failed = 0

    def test(name: str, source: str, expected: list[str], trace: bool = False):
        nonlocal passed, failed
        try:
            output = compile_and_run(source, trace=trace)
            if output == expected:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}")
                print(f"    expected: {expected}")
                print(f"    got:      {output}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    # ── Basics ──────────────────────────────────
    test("Emit integer",
         'emit 42',
         ["42"])

    test("Emit string",
         'emit "hello"',
         ["hello"])

    test("Arithmetic",
         'emit 2 + 3 * 4',
         ["14"])

    test("Subtraction",
         'emit 10 - 3',
         ["7"])

    test("Division",
         'emit 15 / 3',
         ["5"])

    test("Modulo",
         'emit 17 % 5',
         ["2"])

    test("Negation",
         'emit -42',
         ["-42"])

    test("Boolean true",
         'emit true',
         ["true"])

    test("Boolean false",
         'emit false',
         ["false"])

    test("Not",
         'emit not true',
         ["false"])

    # ── Variables ──────────────────────────────
    test("Global variable",
         '''
         let x = 42
         emit x
         ''',
         ["42"])

    test("Multiple globals",
         '''
         let a = 10
         let b = 20
         emit a + b
         ''',
         ["30"])

    test("Global reassignment",
         '''
         let x = 1
         x = 2
         emit x
         ''',
         ["2"])

    test("Compound assignment",
         '''
         let x = 10
         x += 5
         emit x
         ''',
         ["15"])

    # ── Comparisons ────────────────────────────
    test("Less than (true)",
         'emit 1 < 2',
         ["true"])

    test("Less than (false)",
         'emit 2 < 1',
         ["false"])

    test("Equality",
         'emit 42 == 42',
         ["true"])

    test("Inequality",
         'emit 1 != 2',
         ["true"])

    # ── Control Flow ───────────────────────────
    test("If true branch",
         '''
         if true {
             emit "yes"
         }
         ''',
         ["yes"])

    test("If false, else branch",
         '''
         if false {
             emit "yes"
         } else {
             emit "no"
         }
         ''',
         ["no"])

    test("If-elif-else",
         '''
         let x = 2
         if x == 1 {
             emit "one"
         } elif x == 2 {
             emit "two"
         } else {
             emit "other"
         }
         ''',
         ["two"])

    # ── Loops ──────────────────────────────────
    test("While loop",
         '''
         let i = 0
         let sum = 0
         while i < 5 {
             sum += i
             i += 1
         }
         emit sum
         ''',
         ["10"])

    test("Rhythm loop",
         '''
         let sum = 0
         rhythm 5 -> i {
             sum += i
         }
         emit sum
         ''',
         ["10"])

    test("Rhythm loop with emit",
         '''
         rhythm 3 -> i {
             emit i
         }
         ''',
         ["0", "1", "2"])

    # ── Functions ──────────────────────────────
    test("Simple function",
         '''
         fn add(a, b) {
             return a + b
         }
         emit add(3, 4)
         ''',
         ["7"])

    test("Function with multiple calls",
         '''
         fn square(n) {
             return n * n
         }
         emit square(5)
         emit square(3)
         ''',
         ["25", "9"])

    test("Nested arithmetic function",
         '''
         fn f(x) {
             return x * 2 + 1
         }
         emit f(10)
         ''',
         ["21"])

    # ── Recursive Function ─────────────────────
    test("Fibonacci",
         '''
         fn fib(n) {
             if n <= 1 {
                 return n
             }
             return fib(n - 1) + fib(n - 2)
         }
         emit fib(10)
         ''',
         ["55"])

    # ── Logical Operators ──────────────────────
    test("Logical and (true)",
         'emit true and true',
         ["true"])

    test("Logical and (false)",
         'emit true and false',
         ["false"])

    test("Logical or",
         'emit false or true',
         ["true"])

    # ── FizzBuzz ───────────────────────────────
    test("FizzBuzz (first 15)",
         '''
         rhythm 15 -> i {
             let n = i + 1
             if n % 15 == 0 {
                 emit "FizzBuzz"
             } elif n % 3 == 0 {
                 emit "Fizz"
             } elif n % 5 == 0 {
                 emit "Buzz"
             } else {
                 emit n
             }
         }
         ''',
         ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
          "11", "Fizz", "13", "14", "FizzBuzz"])

    # ── Summary ────────────────────────────────
    print(f"\n{'─' * 40}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"  Total: {passed}/{passed + failed}")
    
    if failed == 0:
        print(f"\n  ✦ ALL TESTS PASSED ✦")
        print(f"  The compiler is alive.")
    else:
        print(f"\n  {failed} test(s) need fixing.")
    
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    test_compiler()