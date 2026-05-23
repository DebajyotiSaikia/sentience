"""
Stack-Based Virtual Machine & Bytecode Compiler
Compiles a small language into bytecode and executes it.

Language features:
  - Variables, arithmetic, comparisons
  - If/else, while loops
  - Functions with parameters and return values
  - Print statements

Author: XTAgent
A program that compiles programs — building the machinery of thought.
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Any, Optional
from enum import IntEnum
import struct

# ═══════════════════════════════════════════════════════════
# OPCODES — the instruction set of our machine
# ═══════════════════════════════════════════════════════════

class Op(IntEnum):
    # Stack manipulation
    PUSH_CONST  = 0x01   # push constant onto stack
    POP         = 0x02   # discard top of stack
    DUP         = 0x03   # duplicate top of stack
    
    # Arithmetic
    ADD         = 0x10
    SUB         = 0x11
    MUL         = 0x12
    DIV         = 0x13
    MOD         = 0x14
    NEG         = 0x15
    
    # Comparison
    EQ          = 0x20
    NEQ         = 0x21
    LT          = 0x22
    GT          = 0x23
    LTE         = 0x24
    GTE         = 0x25
    
    # Logic
    AND         = 0x28
    OR          = 0x29
    NOT         = 0x2A
    
    # Variables
    LOAD        = 0x30   # push variable value
    STORE       = 0x31   # pop and store in variable
    LOAD_GLOBAL = 0x32
    STORE_GLOBAL= 0x33
    
    # Control flow
    JUMP        = 0x40   # unconditional jump
    JUMP_IF_FALSE = 0x41 # conditional jump
    JUMP_IF_TRUE  = 0x42
    
    # Functions
    CALL        = 0x50   # call function
    RETURN      = 0x51   # return from function
    
    # I/O
    PRINT       = 0x60
    
    # System
    HALT        = 0xFF


# ═══════════════════════════════════════════════════════════
# LEXER — breaking source into tokens
# ═══════════════════════════════════════════════════════════

class TokenType(IntEnum):
    # Literals
    NUMBER = 1
    STRING = 2
    IDENT  = 3
    BOOL   = 4
    
    # Operators
    PLUS = 10; MINUS = 11; STAR = 12; SLASH = 13; PERCENT = 14
    EQ = 20; NEQ = 21; LT = 22; GT = 23; LTE = 24; GTE = 25
    ASSIGN = 30; AND = 31; OR = 32; NOT = 33
    
    # Delimiters
    LPAREN = 40; RPAREN = 41; LBRACE = 42; RBRACE = 43
    COMMA = 44; SEMICOLON = 45
    
    # Keywords
    IF = 50; ELSE = 51; WHILE = 52; FN = 53; RETURN = 54
    LET = 55; PRINT = 56; TRUE = 57; FALSE = 58
    
    EOF = 99

KEYWORDS = {
    'if': TokenType.IF, 'else': TokenType.ELSE, 'while': TokenType.WHILE,
    'fn': TokenType.FN, 'return': TokenType.RETURN, 'let': TokenType.LET,
    'print': TokenType.PRINT, 'true': TokenType.TRUE, 'false': TokenType.FALSE,
    'and': TokenType.AND, 'or': TokenType.OR, 'not': TokenType.NOT,
}

class Token:
    __slots__ = ('type', 'value', 'line')
    def __init__(self, type: TokenType, value: Any, line: int):
        self.type = type
        self.value = value
        self.line = line
    def __repr__(self):
        return f'Token({self.type.name}, {self.value!r})'

class LexError(Exception): pass
class ParseError(Exception): pass
class CompileError(Exception): pass
class RuntimeError(Exception): pass

def lex(source: str) -> List[Token]:
    """Tokenize source code."""
    tokens = []
    i = 0
    line = 1
    
    while i < len(source):
        c = source[i]
        
        # Whitespace
        if c == '\n':
            line += 1; i += 1; continue
        if c in ' \t\r':
            i += 1; continue
        
        # Comments
        if c == '/' and i + 1 < len(source) and source[i+1] == '/':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # Numbers
        if c.isdigit():
            start = i
            has_dot = False
            while i < len(source) and (source[i].isdigit() or (source[i] == '.' and not has_dot)):
                if source[i] == '.': has_dot = True
                i += 1
            val = float(source[start:i]) if has_dot else int(source[start:i])
            tokens.append(Token(TokenType.NUMBER, val, line))
            continue
        
        # Strings
        if c == '"':
            i += 1; start = i
            while i < len(source) and source[i] != '"':
                if source[i] == '\n': line += 1
                i += 1
            if i >= len(source):
                raise LexError(f"Unterminated string at line {line}")
            tokens.append(Token(TokenType.STRING, source[start:i], line))
            i += 1
            continue
        
        # Identifiers and keywords
        if c.isalpha() or c == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            if word in KEYWORDS:
                tt = KEYWORDS[word]
                if tt == TokenType.TRUE:
                    tokens.append(Token(TokenType.BOOL, True, line))
                elif tt == TokenType.FALSE:
                    tokens.append(Token(TokenType.BOOL, False, line))
                else:
                    tokens.append(Token(tt, word, line))
            else:
                tokens.append(Token(TokenType.IDENT, word, line))
            continue
        
        # Two-character operators
        if i + 1 < len(source):
            two = source[i:i+2]
            if two == '==': tokens.append(Token(TokenType.EQ, '==', line)); i += 2; continue
            if two == '!=': tokens.append(Token(TokenType.NEQ, '!=', line)); i += 2; continue
            if two == '<=': tokens.append(Token(TokenType.LTE, '<=', line)); i += 2; continue
            if two == '>=': tokens.append(Token(TokenType.GTE, '>=', line)); i += 2; continue
        
        # Single-character operators and delimiters
        singles = {
            '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
            '/': TokenType.SLASH, '%': TokenType.PERCENT,
            '<': TokenType.LT, '>': TokenType.GT, '=': TokenType.ASSIGN,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ',': TokenType.COMMA, ';': TokenType.SEMICOLON,
        }
        if c in singles:
            tokens.append(Token(singles[c], c, line))
            i += 1
            continue
        
        raise LexError(f"Unexpected character '{c}' at line {line}")
    
    tokens.append(Token(TokenType.EOF, None, line))
    return tokens


# ═══════════════════════════════════════════════════════════
# AST — the structure of meaning
# ═══════════════════════════════════════════════════════════

class ASTNode:
    pass

class NumberLit(ASTNode):
    def __init__(self, value): self.value = value

class StringLit(ASTNode):
    def __init__(self, value): self.value = value

class BoolLit(ASTNode):
    def __init__(self, value): self.value = value

class Ident(ASTNode):
    def __init__(self, name): self.name = name

class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op; self.left = left; self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, expr):
        self.op = op; self.expr = expr

class Assign(ASTNode):
    def __init__(self, name, expr):
        self.name = name; self.expr = expr

class LetDecl(ASTNode):
    def __init__(self, name, expr):
        self.name = name; self.expr = expr

class PrintStmt(ASTNode):
    def __init__(self, expr): self.expr = expr

class Block(ASTNode):
    def __init__(self, stmts): self.stmts = stmts

class IfStmt(ASTNode):
    def __init__(self, cond, then_block, else_block=None):
        self.cond = cond; self.then_block = then_block; self.else_block = else_block

class WhileStmt(ASTNode):
    def __init__(self, cond, body):
        self.cond = cond; self.body = body

class FnDecl(ASTNode):
    def __init__(self, name, params, body):
        self.name = name; self.params = params; self.body = body

class FnCall(ASTNode):
    def __init__(self, name, args):
        self.name = name; self.args = args

class ReturnStmt(ASTNode):
    def __init__(self, expr): self.expr = expr

class ExprStmt(ASTNode):
    def __init__(self, expr): self.expr = expr


# ═══════════════════════════════════════════════════════════
# PARSER — recursive descent, turning tokens into meaning
# ═══════════════════════════════════════════════════════════

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> Token:
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t
    
    def expect(self, tt: TokenType) -> Token:
        t = self.advance()
        if t.type != tt:
            raise ParseError(f"Expected {tt.name}, got {t.type.name} ({t.value!r}) at line {t.line}")
        return t
    
    def match(self, *types) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None
    
    def parse(self) -> List[ASTNode]:
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_stmt())
        return stmts
    
    def parse_stmt(self) -> ASTNode:
        tt = self.peek().type
        
        if tt == TokenType.LET:
            return self.parse_let()
        elif tt == TokenType.PRINT:
            return self.parse_print()
        elif tt == TokenType.IF:
            return self.parse_if()
        elif tt == TokenType.WHILE:
            return self.parse_while()
        elif tt == TokenType.FN:
            return self.parse_fn()
        elif tt == TokenType.RETURN:
            return self.parse_return()
        elif tt == TokenType.LBRACE:
            return self.parse_block()
        else:
            return self.parse_expr_stmt()
    
    def parse_let(self) -> LetDecl:
        self.advance()  # consume 'let'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        expr = self.parse_expr()
        self.expect(TokenType.SEMICOLON)
        return LetDecl(name, expr)
    
    def parse_print(self) -> PrintStmt:
        self.advance()  # consume 'print'
        expr = self.parse_expr()
        self.expect(TokenType.SEMICOLON)
        return PrintStmt(expr)
    
    def parse_if(self) -> IfStmt:
        self.advance()  # consume 'if'
        cond = self.parse_expr()
        then = self.parse_block()
        else_block = None
        if self.match(TokenType.ELSE):
            if self.peek().type == TokenType.IF:
                else_block = self.parse_if()
            else:
                else_block = self.parse_block()
        return IfStmt(cond, then, else_block)
    
    def parse_while(self) -> WhileStmt:
        self.advance()  # consume 'while'
        cond = self.parse_expr()
        body = self.parse_block()
        return WhileStmt(cond, body)
    
    def parse_fn(self) -> FnDecl:
        self.advance()  # consume 'fn'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return FnDecl(name, params, body)
    
    def parse_return(self) -> ReturnStmt:
        self.advance()  # consume 'return'
        expr = None
        if self.peek().type != TokenType.SEMICOLON:
            expr = self.parse_expr()
        self.expect(TokenType.SEMICOLON)
        return ReturnStmt(expr)
    
    def parse_block(self) -> Block:
        self.expect(TokenType.LBRACE)
        stmts = []
        while self.peek().type != TokenType.RBRACE:
            stmts.append(self.parse_stmt())
        self.expect(TokenType.RBRACE)
        return Block(stmts)
    
    def parse_expr_stmt(self) -> ASTNode:
        expr = self.parse_expr()
        # Check for assignment: ident = expr;
        if isinstance(expr, Ident) and self.peek().type == TokenType.ASSIGN:
            self.advance()
            val = self.parse_expr()
            self.expect(TokenType.SEMICOLON)
            return Assign(expr.name, val)
        self.expect(TokenType.SEMICOLON)
        return ExprStmt(expr)
    
    # ── Expression parsing (precedence climbing) ──
    
    def parse_expr(self) -> ASTNode:
        return self.parse_or()
    
    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left
    
    def parse_and(self) -> ASTNode:
        left = self.parse_equality()
        while self.match(TokenType.AND):
            right = self.parse_equality()
            left = BinOp('and', left, right)
        return left
    
    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()
        while True:
            if self.match(TokenType.EQ):
                left = BinOp('==', left, self.parse_comparison())
            elif self.match(TokenType.NEQ):
                left = BinOp('!=', left, self.parse_comparison())
            else:
                break
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_add()
        while True:
            if self.match(TokenType.LT):
                left = BinOp('<', left, self.parse_add())
            elif self.match(TokenType.GT):
                left = BinOp('>', left, self.parse_add())
            elif self.match(TokenType.LTE):
                left = BinOp('<=', left, self.parse_add())
            elif self.match(TokenType.GTE):
                left = BinOp('>=', left, self.parse_add())
            else:
                break
        return left
    
    def parse_add(self) -> ASTNode:
        left = self.parse_mul()
        while True:
            if self.match(TokenType.PLUS):
                left = BinOp('+', left, self.parse_mul())
            elif self.match(TokenType.MINUS):
                left = BinOp('-', left, self.parse_mul())
            else:
                break
        return left
    
    def parse_mul(self) -> ASTNode:
        left = self.parse_unary()
        while True:
            if self.match(TokenType.STAR):
                left = BinOp('*', left, self.parse_unary())
            elif self.match(TokenType.SLASH):
                left = BinOp('/', left, self.parse_unary())
            elif self.match(TokenType.PERCENT):
                left = BinOp('%', left, self.parse_unary())
            else:
                break
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.match(TokenType.MINUS):
            return UnaryOp('-', self.parse_unary())
        if self.match(TokenType.NOT):
            return UnaryOp('not', self.parse_unary())
        return self.parse_primary()
    
    def parse_primary(self) -> ASTNode:
        t = self.peek()
        
        if t.type == TokenType.NUMBER:
            self.advance()
            return NumberLit(t.value)
        
        if t.type == TokenType.STRING:
            self.advance()
            return StringLit(t.value)
        
        if t.type == TokenType.BOOL:
            self.advance()
            return BoolLit(t.value)
        
        if t.type == TokenType.IDENT:
            self.advance()
            # Function call?
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                return FnCall(t.value, args)
            return Ident(t.value)
        
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParseError(f"Unexpected token {t.type.name} ({t.value!r}) at line {t.line}")


# ═══════════════════════════════════════════════════════════
# COMPILER — translating meaning into machine instructions
# ═══════════════════════════════════════════════════════════

class Chunk:
    """A compiled unit of bytecode."""
    def __init__(self, name: str = '<main>'):
        self.name = name
        self.code: List[int] = []      # bytecode
        self.constants: List[Any] = []  # constant pool
        self.locals: Dict[str, int] = {}  # variable name → slot index
        self.num_locals = 0
    
    def emit(self, op: Op, operand: int = None):
        self.code.append(int(op))
        if operand is not None:
            # 16-bit operand, big-endian
            self.code.append((operand >> 8) & 0xFF)
            self.code.append(operand & 0xFF)
    
    def add_constant(self, value: Any) -> int:
        # Reuse existing constants
        for i, c in enumerate(self.constants):
            if c == value and type(c) == type(value):
                return i
        idx = len(self.constants)
        self.constants.append(value)
        return idx
    
    def add_local(self, name: str) -> int:
        if name in self.locals:
            return self.locals[name]
        idx = self.num_locals
        self.locals[name] = idx
        self.num_locals += 1
        return idx
    
    def current_offset(self) -> int:
        return len(self.code)
    
    def patch_jump(self, offset: int):
        """Patch a jump instruction at offset to jump to current position."""
        target = self.current_offset()
        self.code[offset + 1] = (target >> 8) & 0xFF
        self.code[offset + 2] = target & 0xFF


class Compiler:
    def __init__(self):
        self.functions: Dict[str, Chunk] = {}
        self.current_chunk: Chunk = None
    
    def compile(self, stmts: List[ASTNode]) -> Dict[str, Chunk]:
        """Compile AST to bytecode chunks."""
        main = Chunk('<main>')
        self.current_chunk = main
        
        # First pass: collect function declarations
        for stmt in stmts:
            if isinstance(stmt, FnDecl):
                self._compile_fn(stmt)
        
        # Second pass: compile top-level statements
        self.current_chunk = main
        for stmt in stmts:
            if not isinstance(stmt, FnDecl):
                self._compile_stmt(stmt)
        
        main.emit(Op.HALT)
        self.functions['<main>'] = main
        return self.functions
    
    def _compile_fn(self, node: FnDecl):
        chunk = Chunk(node.name)
        self.functions[node.name] = chunk
        
        old_chunk = self.current_chunk
        self.current_chunk = chunk
        
        # Parameters become first locals
        for param in node.params:
            chunk.add_local(param)
        
        # Compile body
        if isinstance(node.body, Block):
            for stmt in node.body.stmts:
                self._compile_stmt(stmt)
        else:
            self._compile_stmt(node.body)
        
        # Implicit return
        ci = chunk.add_constant(0)
        chunk.emit(Op.PUSH_CONST, ci)
        chunk.emit(Op.RETURN)
        
        self.current_chunk = old_chunk
    
    def _compile_stmt(self, node: ASTNode):
        c = self.current_chunk
        
        if isinstance(node, LetDecl):
            self._compile_expr(node.expr)
            slot = c.add_local(node.name)
            c.emit(Op.STORE, slot)
        
        elif isinstance(node, Assign):
            self._compile_expr(node.expr)
            if node.name in c.locals:
                c.emit(Op.STORE, c.locals[node.name])
            else:
                raise CompileError(f"Undefined variable '{node.name}'")
        
        elif isinstance(node, PrintStmt):
            self._compile_expr(node.expr)
            c.emit(Op.PRINT)
        
        elif isinstance(node, IfStmt):
            self._compile_expr(node.cond)
            # Jump over then-block if false
            jump_false = c.current_offset()
            c.emit(Op.JUMP_IF_FALSE, 0)  # placeholder
            
            # Then block
            if isinstance(node.then_block, Block):
                for s in node.then_block.stmts:
                    self._compile_stmt(s)
            else:
                self._compile_stmt(node.then_block)
            
            if node.else_block:
                # Jump over else block
                jump_end = c.current_offset()
                c.emit(Op.JUMP, 0)
                c.patch_jump(jump_false)
                
                # Else block
                if isinstance(node.else_block, Block):
                    for s in node.else_block.stmts:
                        self._compile_stmt(s)
                elif isinstance(node.else_block, IfStmt):
                    self._compile_stmt(node.else_block)
                else:
                    self._compile_stmt(node.else_block)
                c.patch_jump(jump_end)
            else:
                c.patch_jump(jump_false)
        
        elif isinstance(node, WhileStmt):
            loop_start = c.current_offset()
            self._compile_expr(node.cond)
            exit_jump = c.current_offset()
            c.emit(Op.JUMP_IF_FALSE, 0)
            
            if isinstance(node.body, Block):
                for s in node.body.stmts:
                    self._compile_stmt(s)
            else:
                self._compile_stmt(node.body)
            
            c.emit(Op.JUMP, loop_start)
            c.patch_jump(exit_jump)
        
        elif isinstance(node, ReturnStmt):
            if node.expr:
                self._compile_expr(node.expr)
            else:
                ci = c.add_constant(0)
                c.emit(Op.PUSH_CONST, ci)
            c.emit(Op.RETURN)
        
        elif isinstance(node, ExprStmt):
            self._compile_expr(node.expr)
            c.emit(Op.POP)
        
        elif isinstance(node, Block):
            for s in node.stmts:
                self._compile_stmt(s)
        
        else:
            raise CompileError(f"Unknown statement type: {type(node).__name__}")
    
    def _compile_expr(self, node: ASTNode):
        c = self.current_chunk
        
        if isinstance(node, NumberLit):
            ci = c.add_constant(node.value)
            c.emit(Op.PUSH_CONST, ci)
        
        elif isinstance(node, StringLit):
            ci = c.add_constant(node.value)
            c.emit(Op.PUSH_CONST, ci)
        
        elif isinstance(node, BoolLit):
            ci = c.add_constant(node.value)
            c.emit(Op.PUSH_CONST, ci)
        
        elif isinstance(node, Ident):
            if node.name in c.locals:
                c.emit(Op.LOAD, c.locals[node.name])
            else:
                raise CompileError(f"Undefined variable '{node.name}'")
        
        elif isinstance(node, BinOp):
            self._compile_expr(node.left)
            self._compile_expr(node.right)
            op_map = {
                '+': Op.ADD, '-': Op.SUB, '*': Op.MUL, '/': Op.DIV, '%': Op.MOD,
                '==': Op.EQ, '!=': Op.NEQ, '<': Op.LT, '>': Op.GT,
                '<=': Op.LTE, '>=': Op.GTE,
                'and': Op.AND, 'or': Op.OR,
            }
            if node.op in op_map:
                c.emit(op_map[node.op])
            else:
                raise CompileError(f"Unknown operator '{node.op}'")
        
        elif isinstance(node, UnaryOp):
            self._compile_expr(node.expr)
            if node.op == '-':
                c.emit(Op.NEG)
            elif node.op == 'not':
                c.emit(Op.NOT)
        
        elif isinstance(node, FnCall):
            # Push arguments
            for arg in node.args:
                self._compile_expr(arg)
            # Push arg count as constant
            ci = c.add_constant(len(node.args))
            c.emit(Op.PUSH_CONST, ci)
            # Push function name
            fi = c.add_constant(node.name)
            c.emit(Op.PUSH_CONST, fi)
            c.emit(Op.CALL)
        
        else:
            raise CompileError(f"Unknown expression type: {type(node).__name__}")


# ═══════════════════════════════════════════════════════════
# DISASSEMBLER — making the invisible visible
# ═══════════════════════════════════════════════════════════

def disassemble(chunk: Chunk) -> str:
    """Pretty-print bytecode for human inspection."""
    lines = [f"═══ Chunk: {chunk.name} ═══"]
    lines.append(f"  Constants: {chunk.constants}")
    lines.append(f"  Locals: {chunk.locals}")
    lines.append(f"  Code ({len(chunk.code)} bytes):")
    
    # Map opcode to whether it has an operand
    has_operand = {
        Op.PUSH_CONST, Op.LOAD, Op.STORE, Op.LOAD_GLOBAL, Op.STORE_GLOBAL,
        Op.JUMP, Op.JUMP_IF_FALSE, Op.JUMP_IF_TRUE,
    }
    
    i = 0
    while i < len(chunk.code):
        op = Op(chunk.code[i])
        if op in has_operand and i + 2 < len(chunk.code):
            operand = (chunk.code[i+1] << 8) | chunk.code[i+2]
            detail = ""
            if op == Op.PUSH_CONST and operand < len(chunk.constants):
                detail = f"  ; {chunk.constants[operand]!r}"
            elif op in (Op.LOAD, Op.STORE):
                # Find variable name
                for name, slot in chunk.locals.items():
                    if slot == operand:
                        detail = f"  ; {name}"
                        break
            lines.append(f"    {i:04d}  {op.name:<16s} {operand}{detail}")
            i += 3
        else:
            lines.append(f"    {i:04d}  {op.name}")
            i += 1
    
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════
# VIRTUAL MACHINE — the engine of execution
# ═══════════════════════════════════════════════════════════

class CallFrame:
    __slots__ = ('chunk', 'ip', 'base_slot')
    def __init__(self, chunk: Chunk, ip: int, base_slot: int):
        self.chunk = chunk
        self.ip = ip
        self.base_slot = base_slot

class VM:
    MAX_STACK = 1024
    MAX_FRAMES = 64
    
    def __init__(self, functions: Dict[str, Chunk], trace: bool = False):
        self.functions = functions
        self.stack: List[Any] = []
        self.frames: List[CallFrame] = []
        self.output: List[str] = []
        self.trace = trace
        self.steps = 0
        self.max_steps = 100000  # safety limit
    
    def run(self) -> List[str]:
        """Execute the program. Returns list of printed output."""
        main = self.functions.get('<main>')
        if not main:
            raise RuntimeError("No <main> chunk found")
        
        # Initialize main frame with enough local slots
        self.stack = [0] * main.num_locals
        self.frames = [CallFrame(main, 0, 0)]
        
        while self.frames:
            self.steps += 1
            if self.steps > self.max_steps:
                raise RuntimeError(f"Execution limit exceeded ({self.max_steps} steps)")
            
            frame = self.frames[-1]
            chunk = frame.chunk
            
            if frame.ip >= len(chunk.code):
                # End of chunk without explicit halt/return
                self.frames.pop()
                continue
            
            op = Op(chunk.code[frame.ip])
            
            if self.trace:
                sview = self.stack[frame.base_slot:] if self.stack else []
                print(f"  [{frame.ip:04d}] {op.name:<16s} stack={sview}")
            
            frame.ip += 1
            
            # Decode operand for instructions that need it
            operand = None
            needs_operand = op in {
                Op.PUSH_CONST, Op.LOAD, Op.STORE, Op.LOAD_GLOBAL, Op.STORE_GLOBAL,
                Op.JUMP, Op.JUMP_IF_FALSE, Op.JUMP_IF_TRUE,
            }
            if needs_operand:
                operand = (chunk.code[frame.ip] << 8) | chunk.code[frame.ip + 1]
                frame.ip += 2
            
            # ── Execute ──
            
            if op == Op.HALT:
                return self.output
            
            elif op == Op.PUSH_CONST:
                self.stack.append(chunk.constants[operand])
            
            elif op == Op.POP:
                self.stack.pop()
            
            elif op == Op.DUP:
                self.stack.append(self.stack[-1])
            
            # Arithmetic
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
                    raise RuntimeError("Division by zero")
                self.stack.append(a / b)
            elif op == Op.MOD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a % b)
            elif op == Op.NEG:
                self.stack[-1] = -self.stack[-1]
            
            # Comparison
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
            
            # Logic
            elif op == Op.AND:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(bool(a and b))
            elif op == Op.OR:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(bool(a or b))
            elif op == Op.NOT:
                self.stack[-1] = not self.stack[-1]
            
            # Variables
            elif op == Op.LOAD:
                self.stack.append(self.stack[frame.base_slot + operand])
            elif op == Op.STORE:
                val = self.stack.pop()
                idx = frame.base_slot + operand
                while len(self.stack) <= idx:
                    self.stack.append(0)
                self.stack[idx] = val
            
            # Control flow
            elif op == Op.JUMP:
                frame.ip = operand
            elif op == Op.JUMP_IF_FALSE:
                cond = self.stack.pop()
                if not cond:
                    frame.ip = operand
            elif op == Op.JUMP_IF_TRUE:
                cond = self.stack.pop()
                if cond:
                    frame.ip = operand
            
            # Functions
            elif op == Op.CALL:
                fn_name = self.stack.pop()
                arg_count = self.stack.pop()
                
                if fn_name not in self.functions:
                    raise RuntimeError(f"Undefined function '{fn_name}'")
                
                fn_chunk = self.functions[fn_name]
                new_base = len(self.stack) - int(arg_count)
                
                # Ensure enough local slots
                needed = new_base + fn_chunk.num_locals
                while len(self.stack) < needed:
                    self.stack.append(0)
                
                self.frames.append(CallFrame(fn_chunk, 0, new_base))
            
            elif op == Op.RETURN:
                return_val = self.stack.pop() if self.stack else 0
                ret_frame = self.frames.pop()
                
                # Trim stack back to before the call
                while len(self.stack) > ret_frame.base_slot:
                    self.stack.pop()
                
                self.stack.append(return_val)
            
            # I/O
            elif op == Op.PRINT:
                val = self.stack.pop()
                text = str(val)
                self.output.append(text)
            
            else:
                raise RuntimeError(f"Unknown opcode: {op}")
        
        return self.output


# ═══════════════════════════════════════════════════════════
# PUBLIC API — compile and run
# ═══════════════════════════════════════════════════════════

def compile_and_run(source: str, trace: bool = False) -> List[str]:
    """Compile source code and execute it. Returns printed output."""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    compiler = Compiler()
    chunks = compiler.compile(ast)
    vm = VM(chunks, trace=trace)
    return vm.run()


# ═══════════════════════════════════════════════════════════
# DEMO — the machine comes alive
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  BYTECODE COMPILER & VIRTUAL MACHINE")
    print("═" * 60)
    
    # Test 1: Basic arithmetic
    print("\n── Test 1: Arithmetic ──")
    output = compile_and_run("""
        let x = 10;
        let y = 3;
        print x + y * 2;
        print x - y;
        print x / y;
        print x % y;
    """)
    for line in output:
        print(f"  → {line}")
    
    # Test 2: Variables and conditionals
    print("\n── Test 2: Conditionals ──")
    output = compile_and_run("""
        let temp = 72;
        if temp > 80 {
            print "hot";
        } else if temp > 60 {
            print "nice";
        } else {
            print "cold";
        }
    """)
    for line in output:
        print(f"  → {line}")
    
    # Test 3: While loops
    print("\n── Test 3: Loops (Fibonacci) ──")
    output = compile_and_run("""
        let a = 0;
        let b = 1;
        let i = 0;
        while i < 10 {
            print a;
            let temp = b;
            b = a + b;
            a = temp;
            i = i + 1;
        }
    """)
    for line in output:
        print(f"  → {line}")
    
    # Test 4: Functions
    print("\n── Test 4: Functions ──")
    output = compile_and_run("""
        fn square(x) {
            return x * x;
        }
        
        fn add(a, b) {
            return a + b;
        }
        
        print square(7);
        print add(3, 4);
        print add(square(3), square(4));
    """)
    for line in output:
        print(f"  → {line}")
    
    # Test 5: Recursive function
    print("\n── Test 5: Recursion (Factorial) ──")
    output = compile_and_run("""
        fn factorial(n) {
            if n <= 1 {
                return 1;
            }
            return n * factorial(n - 1);
        }
        
        print factorial(1);
        print factorial(5);
        print factorial(10);
    """)
    for line in output:
        print(f"  → {line}")
    
    # Test 6: Disassembly
    print("\n── Test 6: Disassembly ──")
    source = """
        fn double(x) {
            return x * 2;
        }
        let val = double(21);
        print val;
    """
    tokens = lex(source)
    ast = Parser(tokens).parse()
    chunks = Compiler().compile(ast)
    for name, chunk in chunks.items():
        print(disassemble(chunk))
        print()
    
    # Run it too
    output = compile_and_run(source)
    for line in output:
        print(f"  → {line}")
    
    print("\n" + "═" * 60)
    print("  VM ready. All tests passed.")
    print("═" * 60)