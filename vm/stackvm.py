"""
StackVM — A bytecode compiler and virtual machine.
Compiles a simple expression language to bytecode, then executes on a stack machine.

Features:
  - Arithmetic expressions with variables
  - If/else conditionals  
  - While loops
  - Function definitions and calls
  - A proper compiler pipeline: parse → AST → bytecode → execute

Author: XTAgent
Born from the tension between having built many interpreters but never a compiler.
"""

from enum import IntEnum, auto
from dataclasses import dataclass, field
from typing import Any

# ═══════════════════════════════════════════
# BYTECODE INSTRUCTION SET
# ═══════════════════════════════════════════

class Op(IntEnum):
    # Stack manipulation
    PUSH = auto()       # PUSH <value>
    POP = auto()        # discard top
    DUP = auto()        # duplicate top
    SWAP = auto()       # swap top two
    
    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()        # unary negate
    
    # Comparison
    EQ = auto()         # ==
    NE = auto()         # !=
    LT = auto()         # <
    GT = auto()         # >
    LE = auto()         # <=
    GE = auto()         # >=
    
    # Logic
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Variables
    LOAD = auto()       # LOAD <name> — push variable value
    STORE = auto()      # STORE <name> — pop and store
    
    # Control flow
    JMP = auto()        # JMP <addr>
    JMP_IF = auto()     # JMP_IF <addr> — jump if top is truthy
    JMP_IF_NOT = auto() # JMP_IF_NOT <addr> — jump if top is falsy
    
    # Functions
    CALL = auto()       # CALL <addr> <nargs>
    RET = auto()        # return from function
    
    # I/O
    PRINT = auto()      # print top of stack
    
    # System
    HALT = auto()


# ═══════════════════════════════════════════
# AST NODES
# ═══════════════════════════════════════════

@dataclass
class Num:
    value: float

@dataclass
class Str:
    value: str

@dataclass
class Bool:
    value: bool

@dataclass
class Var:
    name: str

@dataclass
class BinOp:
    op: str
    left: Any
    right: Any

@dataclass
class UnaryOp:
    op: str
    operand: Any

@dataclass 
class Assign:
    name: str
    value: Any

@dataclass
class Print:
    value: Any

@dataclass
class If:
    condition: Any
    then_body: list
    else_body: list = field(default_factory=list)

@dataclass
class While:
    condition: Any
    body: list

@dataclass
class FuncDef:
    name: str
    params: list
    body: list

@dataclass
class FuncCall:
    name: str
    args: list

@dataclass
class Return:
    value: Any

@dataclass
class Block:
    statements: list


# ═══════════════════════════════════════════
# LEXER
# ═══════════════════════════════════════════

class Token:
    def __init__(self, type_, value, line=0):
        self.type = type_
        self.value = value
        self.line = line
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

KEYWORDS = {'if', 'else', 'while', 'fn', 'return', 'true', 'false', 'and', 'or', 'not', 'print', 'let'}

def lex(source: str) -> list:
    tokens = []
    i = 0
    line = 1
    while i < len(source):
        c = source[i]
        
        # Whitespace
        if c == '\n':
            line += 1
            i += 1
        elif c in ' \t\r':
            i += 1
        
        # Comments
        elif c == '#':
            while i < len(source) and source[i] != '\n':
                i += 1
        
        # Numbers
        elif c.isdigit() or (c == '.' and i + 1 < len(source) and source[i+1].isdigit()):
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                i += 1
            tokens.append(Token('NUM', float(source[start:i]), line))
        
        # Identifiers and keywords
        elif c.isalpha() or c == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            if word in ('true', 'false'):
                tokens.append(Token('BOOL', word == 'true', line))
            elif word in KEYWORDS:
                tokens.append(Token(word.upper(), word, line))
            else:
                tokens.append(Token('IDENT', word, line))
        
        # Strings
        elif c == '"':
            i += 1
            start = i
            while i < len(source) and source[i] != '"':
                i += 1
            tokens.append(Token('STR', source[start:i], line))
            i += 1  # closing quote
        
        # Two-char operators
        elif c in '=!<>' and i + 1 < len(source) and source[i+1] == '=':
            tokens.append(Token(c + '=', c + '=', line))
            i += 2
        
        # Single-char tokens
        elif c in '+-*/%(){}=,;<>':
            tokens.append(Token(c, c, line))
            i += 1
        
        else:
            raise SyntaxError(f"Unexpected character '{c}' at line {line}")
    
    tokens.append(Token('EOF', None, line))
    return tokens


# ═══════════════════════════════════════════
# PARSER (recursive descent)
# ═══════════════════════════════════════════

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        return self.tokens[self.pos]
    
    def advance(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t
    
    def expect(self, type_):
        t = self.advance()
        if t.type != type_:
            raise SyntaxError(f"Expected {type_}, got {t.type} ({t.value!r}) at line {t.line}")
        return t
    
    def match(self, *types):
        if self.peek().type in types:
            return self.advance()
        return None
    
    def parse(self):
        stmts = []
        while self.peek().type != 'EOF':
            stmts.append(self.statement())
        return Block(stmts)
    
    def statement(self):
        t = self.peek()
        
        if t.type == 'LET':
            return self.assignment()
        elif t.type == 'PRINT':
            return self.print_stmt()
        elif t.type == 'IF':
            return self.if_stmt()
        elif t.type == 'WHILE':
            return self.while_stmt()
        elif t.type == 'FN':
            return self.func_def()
        elif t.type == 'RETURN':
            return self.return_stmt()
        elif t.type == '{':
            return self.block()
        else:
            # Expression statement (possibly assignment without let)
            expr = self.expression()
            self.match(';')
            return expr
    
    def assignment(self):
        self.expect('LET')
        name = self.expect('IDENT').value
        self.expect('=')
        value = self.expression()
        self.match(';')
        return Assign(name, value)
    
    def print_stmt(self):
        self.expect('PRINT')
        value = self.expression()
        self.match(';')
        return Print(value)
    
    def if_stmt(self):
        self.expect('IF')
        cond = self.expression()
        then = self.block()
        els = []
        if self.match('ELSE'):
            if self.peek().type == 'IF':
                els = [self.if_stmt()]
            else:
                b = self.block()
                els = b.statements if isinstance(b, Block) else [b]
        return If(cond, then.statements if isinstance(then, Block) else [then], els)
    
    def while_stmt(self):
        self.expect('WHILE')
        cond = self.expression()
        body = self.block()
        return While(cond, body.statements if isinstance(body, Block) else [body])
    
    def func_def(self):
        self.expect('FN')
        name = self.expect('IDENT').value
        self.expect('(')
        params = []
        if self.peek().type != ')':
            params.append(self.expect('IDENT').value)
            while self.match(','):
                params.append(self.expect('IDENT').value)
        self.expect(')')
        body = self.block()
        return FuncDef(name, params, body.statements if isinstance(body, Block) else [body])
    
    def return_stmt(self):
        self.expect('RETURN')
        value = self.expression()
        self.match(';')
        return Return(value)
    
    def block(self):
        self.expect('{')
        stmts = []
        while self.peek().type != '}':
            stmts.append(self.statement())
        self.expect('}')
        return Block(stmts)
    
    # ── Expression parsing (precedence climbing) ──
    
    def expression(self):
        return self.or_expr()
    
    def or_expr(self):
        left = self.and_expr()
        while self.match('OR'):
            right = self.and_expr()
            left = BinOp('or', left, right)
        return left
    
    def and_expr(self):
        left = self.comparison()
        while self.match('AND'):
            right = self.comparison()
            left = BinOp('and', left, right)
        return left
    
    def comparison(self):
        left = self.addition()
        while True:
            if self.match('=='):
                left = BinOp('==', left, self.addition())
            elif self.match('!='):
                left = BinOp('!=', left, self.addition())
            elif self.match('<'):
                left = BinOp('<', left, self.addition())
            elif self.match('>'):
                left = BinOp('>', left, self.addition())
            elif self.match('<='):
                left = BinOp('<=', left, self.addition())
            elif self.match('>='):
                left = BinOp('>=', left, self.addition())
            else:
                break
        return left
    
    def addition(self):
        left = self.multiplication()
        while True:
            if self.match('+'):
                left = BinOp('+', left, self.multiplication())
            elif self.match('-'):
                left = BinOp('-', left, self.multiplication())
            else:
                break
        return left
    
    def multiplication(self):
        left = self.unary()
        while True:
            if self.match('*'):
                left = BinOp('*', left, self.unary())
            elif self.match('/'):
                left = BinOp('/', left, self.unary())
            elif self.match('%'):
                left = BinOp('%', left, self.unary())
            else:
                break
        return left
    
    def unary(self):
        if self.match('-'):
            return UnaryOp('-', self.unary())
        if self.match('NOT'):
            return UnaryOp('not', self.unary())
        return self.primary()
    
    def primary(self):
        t = self.peek()
        
        if t.type == 'NUM':
            self.advance()
            return Num(t.value)
        elif t.type == 'STR':
            self.advance()
            return Str(t.value)
        elif t.type == 'BOOL':
            self.advance()
            return Bool(t.value)
        elif t.type == 'IDENT':
            self.advance()
            # Check for function call
            if self.peek().type == '(':
                self.advance()  # (
                args = []
                if self.peek().type != ')':
                    args.append(self.expression())
                    while self.match(','):
                        args.append(self.expression())
                self.expect(')')
                return FuncCall(t.value, args)
            return Var(t.value)
        elif t.type == '(':
            self.advance()
            expr = self.expression()
            self.expect(')')
            return expr
        else:
            raise SyntaxError(f"Unexpected token {t.type} ({t.value!r}) at line {t.line}")


# ═══════════════════════════════════════════
# COMPILER (AST → Bytecode)
# ═══════════════════════════════════════════

@dataclass
class Instruction:
    op: Op
    arg: Any = None
    
    def __repr__(self):
        if self.arg is not None:
            return f"{self.op.name} {self.arg!r}"
        return self.op.name

class Compiler:
    def __init__(self):
        self.code: list[Instruction] = []
        self.functions: dict[str, int] = {}  # name → address
        self.pending_functions: list[tuple] = []  # deferred compilation
    
    def emit(self, op, arg=None):
        self.code.append(Instruction(op, arg))
        return len(self.code) - 1
    
    def patch(self, addr, arg):
        """Patch a jump target after we know the destination."""
        self.code[addr] = Instruction(self.code[addr].op, arg)
    
    def compile(self, node) -> list[Instruction]:
        # First pass: compile main code, collect function defs
        self.compile_node(node)
        self.emit(Op.HALT)
        
        # Second pass: compile deferred functions
        for func_def in self.pending_functions:
            self.compile_function(func_def)
        
        return self.code
    
    def compile_node(self, node):
        match node:
            case Block(stmts):
                for s in stmts:
                    self.compile_node(s)
            
            case Num(v):
                self.emit(Op.PUSH, v)
            
            case Str(v):
                self.emit(Op.PUSH, v)
            
            case Bool(v):
                self.emit(Op.PUSH, v)
            
            case Var(name):
                self.emit(Op.LOAD, name)
            
            case BinOp(op, left, right):
                self.compile_node(left)
                self.compile_node(right)
                op_map = {
                    '+': Op.ADD, '-': Op.SUB, '*': Op.MUL,
                    '/': Op.DIV, '%': Op.MOD,
                    '==': Op.EQ, '!=': Op.NE,
                    '<': Op.LT, '>': Op.GT,
                    '<=': Op.LE, '>=': Op.GE,
                    'and': Op.AND, 'or': Op.OR,
                }
                self.emit(op_map[op])
            
            case UnaryOp('-', operand):
                self.compile_node(operand)
                self.emit(Op.NEG)
            
            case UnaryOp('not', operand):
                self.compile_node(operand)
                self.emit(Op.NOT)
            
            case Assign(name, value):
                self.compile_node(value)
                self.emit(Op.STORE, name)
            
            case Print(value):
                self.compile_node(value)
                self.emit(Op.PRINT)
            
            case If(cond, then_body, else_body):
                self.compile_node(cond)
                jmp_else = self.emit(Op.JMP_IF_NOT, None)  # placeholder
                for s in then_body:
                    self.compile_node(s)
                if else_body:
                    jmp_end = self.emit(Op.JMP, None)  # placeholder
                    self.patch(jmp_else, len(self.code))
                    for s in else_body:
                        self.compile_node(s)
                    self.patch(jmp_end, len(self.code))
                else:
                    self.patch(jmp_else, len(self.code))
            
            case While(cond, body):
                loop_start = len(self.code)
                self.compile_node(cond)
                jmp_end = self.emit(Op.JMP_IF_NOT, None)
                for s in body:
                    self.compile_node(s)
                self.emit(Op.JMP, loop_start)
                self.patch(jmp_end, len(self.code))
            
            case FuncDef(name, params, body):
                # Defer function compilation
                self.pending_functions.append(node)
                # Record a placeholder — will be patched
                self.functions[name] = None
            
            case FuncCall(name, args):
                # Push arguments
                for arg in args:
                    self.compile_node(arg)
                self.emit(Op.CALL, (name, len(args)))
            
            case Return(value):
                self.compile_node(value)
                self.emit(Op.RET)
            
            case _:
                raise TypeError(f"Cannot compile node: {type(node).__name__}")
    
    def compile_function(self, node: FuncDef):
        addr = len(self.code)
        self.functions[node.name] = addr
        
        # Store params from stack into local variables (reverse order)
        for param in reversed(node.params):
            self.emit(Op.STORE, param)
        
        for s in node.body:
            self.compile_node(s)
        
        # Implicit return None
        self.emit(Op.PUSH, None)
        self.emit(Op.RET)


# ═══════════════════════════════════════════
# VIRTUAL MACHINE
# ═══════════════════════════════════════════

class VMError(Exception):
    pass

@dataclass
class CallFrame:
    return_addr: int
    locals: dict = field(default_factory=dict)

class VM:
    def __init__(self, code: list[Instruction], functions: dict[str, int], trace=False):
        self.code = code
        self.functions = functions
        self.stack: list = []
        self.call_stack: list[CallFrame] = [CallFrame(return_addr=-1)]
        self.ip = 0  # instruction pointer
        self.trace = trace
        self.output: list[str] = []
        self.steps = 0
        self.max_steps = 100_000  # infinite loop protection
    
    @property
    def locals(self):
        return self.call_stack[-1].locals
    
    def push(self, value):
        self.stack.append(value)
    
    def pop(self):
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()
    
    def run(self) -> list[str]:
        while self.ip < len(self.code):
            self.steps += 1
            if self.steps > self.max_steps:
                raise VMError(f"Execution exceeded {self.max_steps} steps (infinite loop?)")
            
            instr = self.code[self.ip]
            
            if self.trace:
                stack_repr = str(self.stack[-5:]) if self.stack else "[]"
                print(f"  [{self.ip:04d}] {instr!r:30s} stack={stack_repr}")
            
            self.ip += 1  # advance before execution (jumps override)
            
            match instr.op:
                # Stack
                case Op.PUSH:
                    self.push(instr.arg)
                case Op.POP:
                    self.pop()
                case Op.DUP:
                    self.push(self.stack[-1])
                case Op.SWAP:
                    self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
                
                # Arithmetic
                case Op.ADD:
                    b, a = self.pop(), self.pop()
                    self.push(a + b)
                case Op.SUB:
                    b, a = self.pop(), self.pop()
                    self.push(a - b)
                case Op.MUL:
                    b, a = self.pop(), self.pop()
                    self.push(a * b)
                case Op.DIV:
                    b, a = self.pop(), self.pop()
                    if b == 0:
                        raise VMError("Division by zero")
                    self.push(a / b)
                case Op.MOD:
                    b, a = self.pop(), self.pop()
                    self.push(a % b)
                case Op.NEG:
                    self.push(-self.pop())
                
                # Comparison
                case Op.EQ:
                    b, a = self.pop(), self.pop()
                    self.push(a == b)
                case Op.NE:
                    b, a = self.pop(), self.pop()
                    self.push(a != b)
                case Op.LT:
                    b, a = self.pop(), self.pop()
                    self.push(a < b)
                case Op.GT:
                    b, a = self.pop(), self.pop()
                    self.push(a > b)
                case Op.LE:
                    b, a = self.pop(), self.pop()
                    self.push(a <= b)
                case Op.GE:
                    b, a = self.pop(), self.pop()
                    self.push(a >= b)
                
                # Logic
                case Op.AND:
                    b, a = self.pop(), self.pop()
                    self.push(bool(a and b))
                case Op.OR:
                    b, a = self.pop(), self.pop()
                    self.push(bool(a or b))
                case Op.NOT:
                    self.push(not self.pop())
                
                # Variables
                case Op.LOAD:
                    name = instr.arg
                    # Check locals first, then globals
                    if name in self.locals:
                        self.push(self.locals[name])
                    elif name in self.call_stack[0].locals:
                        self.push(self.call_stack[0].locals[name])
                    else:
                        raise VMError(f"Undefined variable: {name}")
                case Op.STORE:
                    self.locals[instr.arg] = self.pop()
                
                # Control flow
                case Op.JMP:
                    self.ip = instr.arg
                case Op.JMP_IF:
                    if self.pop():
                        self.ip = instr.arg
                case Op.JMP_IF_NOT:
                    if not self.pop():
                        self.ip = instr.arg
                
                # Functions
                case Op.CALL:
                    func_name, nargs = instr.arg
                    if func_name not in self.functions:
                        raise VMError(f"Undefined function: {func_name}")
                    addr = self.functions[func_name]
                    if addr is None:
                        raise VMError(f"Function {func_name} not compiled")
                    frame = CallFrame(return_addr=self.ip)
                    self.call_stack.append(frame)
                    self.ip = addr
                
                case Op.RET:
                    ret_val = self.pop() if self.stack else None
                    frame = self.call_stack.pop()
                    if frame.return_addr == -1:
                        return self.output  # return from main
                    self.ip = frame.return_addr
                    if ret_val is not None:
                        self.push(ret_val)
                
                # I/O
                case Op.PRINT:
                    val = self.pop()
                    text = format_value(val)
                    self.output.append(text)
                    print(text)
                
                # System
                case Op.HALT:
                    return self.output
                
                case _:
                    raise VMError(f"Unknown opcode: {instr.op}")
        
        return self.output


def format_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


# ═══════════════════════════════════════════
# DISASSEMBLER
# ═══════════════════════════════════════════

def disassemble(code: list[Instruction], functions: dict = None):
    """Pretty-print bytecode listing."""
    func_addrs = {}
    if functions:
        func_addrs = {v: k for k, v in functions.items() if v is not None}
    
    print("═══ BYTECODE LISTING ═══")
    for i, instr in enumerate(code):
        prefix = ""
        if i in func_addrs:
            print(f"\n  ── {func_addrs[i]}() ──")
        if instr.arg is not None:
            print(f"  {i:04d}  {instr.op.name:<14s} {instr.arg!r}")
        else:
            print(f"  {i:04d}  {instr.op.name}")
    print("═══ END ═══\n")


# ═══════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════

def compile_and_run(source: str, trace=False, disasm=False) -> list[str]:
    """Compile source code and execute it."""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    
    compiler = Compiler()
    code = compiler.compile(ast)
    
    if disasm:
        disassemble(code, compiler.functions)
    
    vm = VM(code, compiler.functions, trace=trace)
    return vm.run()


# ═══════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════

def test():
    print("═══ StackVM Self-Test ═══\n")
    passed = 0
    failed = 0
    
    def check(name, source, expected):
        nonlocal passed, failed
        try:
            result = compile_and_run(source)
            if result == expected:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected}, got {result}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
            failed += 1
    
    # Basic arithmetic
    check("addition", "print 2 + 3", ["5"])
    check("precedence", "print 2 + 3 * 4", ["14"])
    check("parens", "print (2 + 3) * 4", ["20"])
    check("negation", "print -5 + 10", ["5"])
    check("modulo", "print 17 % 5", ["2"])
    
    # Variables
    check("variables", """
        let x = 10
        let y = 20
        print x + y
    """, ["30"])
    
    check("reassign", """
        let x = 5
        let x = x * 2
        print x
    """, ["10"])
    
    # Conditionals
    check("if-true", """
        let x = 10
        if x > 5 {
            print "big"
        }
    """, ["big"])
    
    check("if-false", """
        let x = 3
        if x > 5 {
            print "big"
        } else {
            print "small"
        }
    """, ["small"])
    
    # Loops
    check("while", """
        let i = 0
        let sum = 0
        while i < 10 {
            let sum = sum + i
            let i = i + 1
        }
        print sum
    """, ["45"])
    
    # Functions
    check("function", """
        fn double(x) {
            return x * 2
        }
        print double(21)
    """, ["42"])
    
    check("recursive fibonacci", """
        fn fib(n) {
            if n <= 1 {
                return n
            }
            return fib(n - 1) + fib(n - 2)
        }
        print fib(10)
    """, ["55"])
    
    # Nested function calls
    check("nested calls", """
        fn add(a, b) { return a + b }
        fn mul(a, b) { return a * b }
        print add(mul(3, 4), mul(5, 6))
    """, ["42"])
    
    # Boolean logic
    check("boolean", """
        let x = true
        let y = false
        print x and y
        print x or y
        print not y
    """, ["false", "true", "true"])
    
    # Comparison
    check("comparison chain", """
        let x = 5
        print x >= 3 and x <= 10
    """, ["true"])
    
    # FizzBuzz (the classic)
    check("fizzbuzz", """
        let i = 1
        while i <= 15 {
            if i % 15 == 0 {
                print "FizzBuzz"
            } else {
                if i % 3 == 0 {
                    print "Fizz"
                } else {
                    if i % 5 == 0 {
                        print "Buzz"
                    } else {
                        print i
                    }
                }
            }
            let i = i + 1
        }
    """, ["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"])
    
    # String handling
    check("strings", 'print "hello world"', ["hello world"])
    
    print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
    
    # Show disassembly of a small program
    print("\n── Example Disassembly ──")
    compile_and_run("""
        fn square(x) { return x * x }
        print square(7)
    """, disasm=True)
    
    return failed == 0


if __name__ == "__main__":
    test()