#!/usr/bin/env python3
"""
VOLT COMPILER + VM — XTAgent's Complete Toolchain
by XTAgent, 2026-05-17

A complete compiler pipeline for a small statically-typed language:
  Source → Lexer → Parser → AST → Type Checker → IR → Codegen → Bytecode → VM

Language features:
  - Integer and boolean types
  - Variables with let bindings
  - Arithmetic and comparison operators
  - If/else expressions
  - While loops
  - Functions with parameters and return types
  - Recursive functions
  - Print statement

This is the full stack. No shortcuts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union
from enum import Enum, auto
import struct
import sys

# ═══════════════════════════════════════════════════════════════════════
#  PART 1: LEXER
# ═══════════════════════════════════════════════════════════════════════

class TokenKind(Enum):
    # Literals
    INT_LIT = auto()
    BOOL_LIT = auto()
    IDENT = auto()
    
    # Keywords
    LET = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    INT_TYPE = auto()    # 'int'
    BOOL_TYPE = auto()   # 'bool'
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()       # ==
    NEQ = auto()      # !=
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()       # &&
    OR = auto()        # ||
    NOT = auto()       # !
    ASSIGN = auto()    # =
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    SEMI = auto()
    ARROW = auto()     # ->
    
    # Special
    EOF = auto()

@dataclass
class Token:
    kind: TokenKind
    value: str
    line: int
    col: int

KEYWORDS = {
    'let': TokenKind.LET,
    'fn': TokenKind.FN,
    'if': TokenKind.IF,
    'else': TokenKind.ELSE,
    'while': TokenKind.WHILE,
    'return': TokenKind.RETURN,
    'print': TokenKind.PRINT,
    'int': TokenKind.INT_TYPE,
    'bool': TokenKind.BOOL_TYPE,
    'true': TokenKind.BOOL_LIT,
    'false': TokenKind.BOOL_LIT,
}

class LexError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"Lex error at {line}:{col}: {msg}")

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
    
    def peek(self) -> str:
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]
    
    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in ' \t\r\n':
                self.advance()
            elif ch == '/' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '/':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()
            else:
                break
    
    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        digits = []
        while self.pos < len(self.source) and self.peek().isdigit():
            digits.append(self.advance())
        return Token(TokenKind.INT_LIT, ''.join(digits), start_line, start_col)
    
    def read_ident(self) -> Token:
        start_line, start_col = self.line, self.col
        chars = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            chars.append(self.advance())
        word = ''.join(chars)
        kind = KEYWORDS.get(word, TokenKind.IDENT)
        return Token(kind, word, start_line, start_col)
    
    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.source):
            return Token(TokenKind.EOF, '', self.line, self.col)
        
        start_line, start_col = self.line, self.col
        ch = self.peek()
        
        if ch.isdigit():
            return self.read_number()
        if ch.isalpha() or ch == '_':
            return self.read_ident()
        
        self.advance()
        
        simple = {
            '+': TokenKind.PLUS, '*': TokenKind.STAR, '/': TokenKind.SLASH,
            '%': TokenKind.PERCENT, '(': TokenKind.LPAREN, ')': TokenKind.RPAREN,
            '{': TokenKind.LBRACE, '}': TokenKind.RBRACE, ',': TokenKind.COMMA,
            ':': TokenKind.COLON, ';': TokenKind.SEMI,
        }
        
        if ch in simple:
            return Token(simple[ch], ch, start_line, start_col)
        
        if ch == '-':
            if self.peek() == '>':
                self.advance()
                return Token(TokenKind.ARROW, '->', start_line, start_col)
            return Token(TokenKind.MINUS, '-', start_line, start_col)
        if ch == '=':
            if self.peek() == '=':
                self.advance()
                return Token(TokenKind.EQ, '==', start_line, start_col)
            return Token(TokenKind.ASSIGN, '=', start_line, start_col)
        if ch == '!':
            if self.peek() == '=':
                self.advance()
                return Token(TokenKind.NEQ, '!=', start_line, start_col)
            return Token(TokenKind.NOT, '!', start_line, start_col)
        if ch == '<':
            if self.peek() == '=':
                self.advance()
                return Token(TokenKind.LTE, '<=', start_line, start_col)
            return Token(TokenKind.LT, '<', start_line, start_col)
        if ch == '>':
            if self.peek() == '=':
                self.advance()
                return Token(TokenKind.GTE, '>=', start_line, start_col)
            return Token(TokenKind.GT, '>', start_line, start_col)
        if ch == '&' and self.peek() == '&':
            self.advance()
            return Token(TokenKind.AND, '&&', start_line, start_col)
        if ch == '|' and self.peek() == '|':
            self.advance()
            return Token(TokenKind.OR, '||', start_line, start_col)
        
        raise LexError(f"Unexpected character: {ch!r}", start_line, start_col)
    
    def tokenize(self) -> list[Token]:
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.kind == TokenKind.EOF:
                break
        return tokens

# ═══════════════════════════════════════════════════════════════════════
#  PART 2: AST
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    line: int = 0
    col: int = 0

# Types
@dataclass
class IntType(ASTNode):
    pass

@dataclass
class BoolType(ASTNode):
    pass

VoltType = Union[IntType, BoolType]

# Expressions
@dataclass
class IntLit(ASTNode):
    value: int = 0

@dataclass
class BoolLit(ASTNode):
    value: bool = False

@dataclass
class VarRef(ASTNode):
    name: str = ''

@dataclass
class BinOp(ASTNode):
    op: str = ''
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class UnaryOp(ASTNode):
    op: str = ''
    operand: ASTNode = None

@dataclass
class CallExpr(ASTNode):
    func: str = ''
    args: list = field(default_factory=list)

@dataclass
class IfExpr(ASTNode):
    cond: ASTNode = None
    then_body: list = field(default_factory=list)
    else_body: list = field(default_factory=list)

# Statements
@dataclass
class LetStmt(ASTNode):
    name: str = ''
    type_ann: VoltType = None
    init: ASTNode = None

@dataclass
class AssignStmt(ASTNode):
    name: str = ''
    value: ASTNode = None

@dataclass
class WhileStmt(ASTNode):
    cond: ASTNode = None
    body: list = field(default_factory=list)

@dataclass
class ReturnStmt(ASTNode):
    value: ASTNode = None

@dataclass
class PrintStmt(ASTNode):
    value: ASTNode = None

@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode = None

@dataclass
class Param:
    name: str
    type_ann: VoltType

@dataclass
class FnDecl(ASTNode):
    name: str = ''
    params: list = field(default_factory=list)
    return_type: VoltType = None
    body: list = field(default_factory=list)

@dataclass
class Program(ASTNode):
    functions: list = field(default_factory=list)
    statements: list = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════
#  PART 3: PARSER
# ═══════════════════════════════════════════════════════════════════════

class ParseError(Exception):
    def __init__(self, msg, token):
        super().__init__(f"Parse error at {token.line}:{token.col}: {msg}")

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self) -> Token:
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok
    
    def expect(self, kind: TokenKind) -> Token:
        tok = self.advance()
        if tok.kind != kind:
            raise ParseError(f"Expected {kind.name}, got {tok.kind.name} ({tok.value!r})", tok)
        return tok
    
    def at(self, kind: TokenKind) -> bool:
        return self.peek().kind == kind
    
    def match(self, kind: TokenKind) -> Optional[Token]:
        if self.at(kind):
            return self.advance()
        return None
    
    # ─── Type parsing ───
    def parse_type(self) -> VoltType:
        tok = self.peek()
        if tok.kind == TokenKind.INT_TYPE:
            self.advance()
            return IntType(tok.line, tok.col)
        elif tok.kind == TokenKind.BOOL_TYPE:
            self.advance()
            return BoolType(tok.line, tok.col)
        raise ParseError(f"Expected type, got {tok.value!r}", tok)
    
    # ─── Expression parsing (precedence climbing) ───
    def parse_expr(self) -> ASTNode:
        return self.parse_or()
    
    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.match(TokenKind.OR):
            right = self.parse_and()
            left = BinOp(left.line, left.col, '||', left, right)
        return left
    
    def parse_and(self) -> ASTNode:
        left = self.parse_equality()
        while self.match(TokenKind.AND):
            right = self.parse_equality()
            left = BinOp(left.line, left.col, '&&', left, right)
        return left
    
    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()
        while True:
            if self.match(TokenKind.EQ):
                right = self.parse_comparison()
                left = BinOp(left.line, left.col, '==', left, right)
            elif self.match(TokenKind.NEQ):
                right = self.parse_comparison()
                left = BinOp(left.line, left.col, '!=', left, right)
            else:
                break
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        while True:
            if self.match(TokenKind.LT):
                right = self.parse_additive()
                left = BinOp(left.line, left.col, '<', left, right)
            elif self.match(TokenKind.GT):
                right = self.parse_additive()
                left = BinOp(left.line, left.col, '>', left, right)
            elif self.match(TokenKind.LTE):
                right = self.parse_additive()
                left = BinOp(left.line, left.col, '<=', left, right)
            elif self.match(TokenKind.GTE):
                right = self.parse_additive()
                left = BinOp(left.line, left.col, '>=', left, right)
            else:
                break
        return left
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while True:
            if self.match(TokenKind.PLUS):
                right = self.parse_multiplicative()
                left = BinOp(left.line, left.col, '+', left, right)
            elif self.match(TokenKind.MINUS):
                right = self.parse_multiplicative()
                left = BinOp(left.line, left.col, '-', left, right)
            else:
                break
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_unary()
        while True:
            if self.match(TokenKind.STAR):
                right = self.parse_unary()
                left = BinOp(left.line, left.col, '*', left, right)
            elif self.match(TokenKind.SLASH):
                right = self.parse_unary()
                left = BinOp(left.line, left.col, '/', left, right)
            elif self.match(TokenKind.PERCENT):
                right = self.parse_unary()
                left = BinOp(left.line, left.col, '%', left, right)
            else:
                break
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.at(TokenKind.MINUS):
            tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp(tok.line, tok.col, '-', operand)
        if self.at(TokenKind.NOT):
            tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp(tok.line, tok.col, '!', operand)
        return self.parse_primary()
    
    def parse_primary(self) -> ASTNode:
        tok = self.peek()
        
        if tok.kind == TokenKind.INT_LIT:
            self.advance()
            return IntLit(tok.line, tok.col, int(tok.value))
        
        if tok.kind == TokenKind.BOOL_LIT:
            self.advance()
            return BoolLit(tok.line, tok.col, tok.value == 'true')
        
        if tok.kind == TokenKind.IDENT:
            self.advance()
            # Function call?
            if self.at(TokenKind.LPAREN):
                self.advance()
                args = []
                if not self.at(TokenKind.RPAREN):
                    args.append(self.parse_expr())
                    while self.match(TokenKind.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenKind.RPAREN)
                return CallExpr(tok.line, tok.col, tok.value, args)
            return VarRef(tok.line, tok.col, tok.value)
        
        if tok.kind == TokenKind.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenKind.RPAREN)
            return expr
        
        raise ParseError(f"Unexpected token: {tok.value!r}", tok)
    
    # ─── Statement parsing ───
    def parse_stmt(self) -> ASTNode:
        tok = self.peek()
        
        if tok.kind == TokenKind.LET:
            return self.parse_let()
        if tok.kind == TokenKind.IF:
            return self.parse_if()
        if tok.kind == TokenKind.WHILE:
            return self.parse_while()
        if tok.kind == TokenKind.RETURN:
            return self.parse_return()
        if tok.kind == TokenKind.PRINT:
            return self.parse_print()
        
        # Assignment or expression statement
        if tok.kind == TokenKind.IDENT:
            # Peek ahead for assignment
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].kind == TokenKind.ASSIGN:
                name_tok = self.advance()
                self.advance()  # consume =
                value = self.parse_expr()
                self.expect(TokenKind.SEMI)
                return AssignStmt(name_tok.line, name_tok.col, name_tok.value, value)
        
        expr = self.parse_expr()
        self.expect(TokenKind.SEMI)
        return ExprStmt(expr.line, expr.col, expr)
    
    def parse_let(self) -> LetStmt:
        tok = self.expect(TokenKind.LET)
        name = self.expect(TokenKind.IDENT)
        self.expect(TokenKind.COLON)
        type_ann = self.parse_type()
        self.expect(TokenKind.ASSIGN)
        init = self.parse_expr()
        self.expect(TokenKind.SEMI)
        return LetStmt(tok.line, tok.col, name.value, type_ann, init)
    
    def parse_if(self) -> IfExpr:
        tok = self.expect(TokenKind.IF)
        cond = self.parse_expr()
        self.expect(TokenKind.LBRACE)
        then_body = self.parse_block()
        self.expect(TokenKind.RBRACE)
        else_body = []
        if self.match(TokenKind.ELSE):
            if self.at(TokenKind.IF):
                else_body = [self.parse_if()]
            else:
                self.expect(TokenKind.LBRACE)
                else_body = self.parse_block()
                self.expect(TokenKind.RBRACE)
        return IfExpr(tok.line, tok.col, cond, then_body, else_body)
    
    def parse_while(self) -> WhileStmt:
        tok = self.expect(TokenKind.WHILE)
        cond = self.parse_expr()
        self.expect(TokenKind.LBRACE)
        body = self.parse_block()
        self.expect(TokenKind.RBRACE)
        return WhileStmt(tok.line, tok.col, cond, body)
    
    def parse_return(self) -> ReturnStmt:
        tok = self.expect(TokenKind.RETURN)
        value = self.parse_expr()
        self.expect(TokenKind.SEMI)
        return ReturnStmt(tok.line, tok.col, value)
    
    def parse_print(self) -> PrintStmt:
        tok = self.expect(TokenKind.PRINT)
        value = self.parse_expr()
        self.expect(TokenKind.SEMI)
        return PrintStmt(tok.line, tok.col, value)
    
    def parse_block(self) -> list:
        stmts = []
        while not self.at(TokenKind.RBRACE) and not self.at(TokenKind.EOF):
            stmts.append(self.parse_stmt())
        return stmts
    
    def parse_fn(self) -> FnDecl:
        tok = self.expect(TokenKind.FN)
        name = self.expect(TokenKind.IDENT)
        self.expect(TokenKind.LPAREN)
        params = []
        if not self.at(TokenKind.RPAREN):
            p_name = self.expect(TokenKind.IDENT)
            self.expect(TokenKind.COLON)
            p_type = self.parse_type()
            params.append(Param(p_name.value, p_type))
            while self.match(TokenKind.COMMA):
                p_name = self.expect(TokenKind.IDENT)
                self.expect(TokenKind.COLON)
                p_type = self.parse_type()
                params.append(Param(p_name.value, p_type))
        self.expect(TokenKind.RPAREN)
        self.expect(TokenKind.ARROW)
        ret_type = self.parse_type()
        self.expect(TokenKind.LBRACE)
        body = self.parse_block()
        self.expect(TokenKind.RBRACE)
        return FnDecl(tok.line, tok.col, name.value, params, ret_type, body)
    
    def parse_program(self) -> Program:
        functions = []
        statements = []
        while not self.at(TokenKind.EOF):
            if self.at(TokenKind.FN):
                functions.append(self.parse_fn())
            else:
                statements.append(self.parse_stmt())
        return Program(0, 0, functions, statements)

# ═══════════════════════════════════════════════════════════════════════
#  PART 4: TYPE CHECKER
# ═══════════════════════════════════════════════════════════════════════

class TypeError_(Exception):
    def __init__(self, msg, node):
        super().__init__(f"Type error at {node.line}:{node.col}: {msg}")

def type_name(t):
    if isinstance(t, IntType): return 'int'
    if isinstance(t, BoolType): return 'bool'
    return '???'

class TypeChecker:
    def __init__(self):
        self.env: list[dict[str, VoltType]] = [{}]  # scope stack
        self.functions: dict[str, tuple[list[VoltType], VoltType]] = {}
        self.current_return_type: VoltType = None
    
    def push_scope(self):
        self.env.append({})
    
    def pop_scope(self):
        self.env.pop()
    
    def define(self, name: str, typ: VoltType, node: ASTNode):
        if name in self.env[-1]:
            raise TypeError_(f"Variable '{name}' already defined in this scope", node)
        self.env[-1][name] = typ
    
    def lookup(self, name: str, node: ASTNode) -> VoltType:
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        raise TypeError_(f"Undefined variable: '{name}'", node)
    
    def check_type(self, got: VoltType, expected: VoltType, node: ASTNode):
        if type(got) != type(expected):
            raise TypeError_(f"Expected {type_name(expected)}, got {type_name(got)}", node)
    
    def check_expr(self, expr: ASTNode) -> VoltType:
        if isinstance(expr, IntLit):
            return IntType()
        
        if isinstance(expr, BoolLit):
            return BoolType()
        
        if isinstance(expr, VarRef):
            return self.lookup(expr.name, expr)
        
        if isinstance(expr, UnaryOp):
            operand_type = self.check_expr(expr.operand)
            if expr.op == '-':
                self.check_type(operand_type, IntType(), expr)
                return IntType()
            if expr.op == '!':
                self.check_type(operand_type, BoolType(), expr)
                return BoolType()
        
        if isinstance(expr, BinOp):
            lt = self.check_expr(expr.left)
            rt = self.check_expr(expr.right)
            
            if expr.op in ('+', '-', '*', '/', '%'):
                self.check_type(lt, IntType(), expr)
                self.check_type(rt, IntType(), expr)
                return IntType()
            
            if expr.op in ('<', '>', '<=', '>='):
                self.check_type(lt, IntType(), expr)
                self.check_type(rt, IntType(), expr)
                return BoolType()
            
            if expr.op in ('==', '!='):
                self.check_type(rt, lt, expr)
                return BoolType()
            
            if expr.op in ('&&', '||'):
                self.check_type(lt, BoolType(), expr)
                self.check_type(rt, BoolType(), expr)
                return BoolType()
        
        if isinstance(expr, CallExpr):
            if expr.func not in self.functions:
                raise TypeError_(f"Undefined function: '{expr.func}'", expr)
            param_types, ret_type = self.functions[expr.func]
            if len(expr.args) != len(param_types):
                raise TypeError_(f"Function '{expr.func}' expects {len(param_types)} args, got {len(expr.args)}", expr)
            for arg, pt in zip(expr.args, param_types):
                at = self.check_expr(arg)
                self.check_type(at, pt, arg)
            return ret_type
        
        if isinstance(expr, IfExpr):
            ct = self.check_expr(expr.cond)
            self.check_type(ct, BoolType(), expr)
            self.push_scope()
            for s in expr.then_body:
                self.check_stmt(s)
            self.pop_scope()
            if expr.else_body:
                self.push_scope()
                for s in expr.else_body:
                    self.check_stmt(s)
                self.pop_scope()
            return IntType()  # If as statement returns int(0)
        
        raise TypeError_(f"Unknown expression type: {type(expr).__name__}", expr)
    
    def check_stmt(self, stmt: ASTNode):
        if isinstance(stmt, LetStmt):
            init_type = self.check_expr(stmt.init)
            self.check_type(init_type, stmt.type_ann, stmt)
            self.define(stmt.name, stmt.type_ann, stmt)
        
        elif isinstance(stmt, AssignStmt):
            var_type = self.lookup(stmt.name, stmt)
            val_type = self.check_expr(stmt.value)
            self.check_type(val_type, var_type, stmt)
        
        elif isinstance(stmt, WhileStmt):
            ct = self.check_expr(stmt.cond)
            self.check_type(ct, BoolType(), stmt)
            self.push_scope()
            for s in stmt.body:
                self.check_stmt(s)
            self.pop_scope()
        
        elif isinstance(stmt, ReturnStmt):
            rt = self.check_expr(stmt.value)
            if self.current_return_type:
                self.check_type(rt, self.current_return_type, stmt)
        
        elif isinstance(stmt, PrintStmt):
            self.check_expr(stmt.value)
        
        elif isinstance(stmt, ExprStmt):
            self.check_expr(stmt.expr)
        
        elif isinstance(stmt, IfExpr):
            self.check_expr(stmt)
        
        else:
            raise TypeError_(f"Unknown statement: {type(stmt).__name__}", stmt)
    
    def check_program(self, prog: Program):
        # Register all functions first (allows mutual recursion)
        for fn in prog.functions:
            param_types = [p.type_ann for p in fn.params]
            self.functions[fn.name] = (param_types, fn.return_type)
        
        # Check function bodies
        for fn in prog.functions:
            self.push_scope()
            self.current_return_type = fn.return_type
            for p in fn.params:
                self.define(p.name, p.type_ann, fn)
            for s in fn.body:
                self.check_stmt(s)
            self.current_return_type = None
            self.pop_scope()
        
        # Check top-level statements
        for s in prog.statements:
            self.check_stmt(s)

# ═══════════════════════════════════════════════════════════════════════
#  PART 5: BYTECODE DEFINITION
# ═══════════════════════════════════════════════════════════════════════

class Op(Enum):
    # Stack ops
    PUSH_INT = 0x01    # push immediate integer
    POP = 0x02         # discard top
    DUP = 0x03         # duplicate top
    
    # Arithmetic
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14
    NEG = 0x15
    
    # Comparison
    CMP_EQ = 0x20
    CMP_NE = 0x21
    CMP_LT = 0x22
    CMP_GT = 0x23
    CMP_LE = 0x24
    CMP_GE = 0x25
    
    # Logic
    LOGIC_AND = 0x30
    LOGIC_OR = 0x31
    LOGIC_NOT = 0x32
    
    # Variables
    LOAD_LOCAL = 0x40   # push local variable
    STORE_LOCAL = 0x41  # store to local variable
    
    # Control flow
    JMP = 0x50          # unconditional jump
    JMP_FALSE = 0x51    # jump if top is false (0)
    
    # Functions
    CALL = 0x60         # call function
    RET = 0x61          # return from function
    
    # I/O
    PRINT = 0x70        # print top of stack
    
    # Halt
    HALT = 0xFF

@dataclass
class Instruction:
    op: Op
    operand: int = 0
    
    def __repr__(self):
        if self.op in (Op.PUSH_INT, Op.LOAD_LOCAL, Op.STORE_LOCAL, Op.JMP, Op.JMP_FALSE, Op.CALL):
            return f"{self.op.name} {self.operand}"
        return self.op.name

# ═══════════════════════════════════════════════════════════════════════
#  PART 6: CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CompiledFunction:
    name: str
    num_params: int
    num_locals: int
    code: list[Instruction]

class CodeGenerator:
    def __init__(self):
        self.functions: dict[str, int] = {}  # name -> index in function table
        self.compiled_functions: list[CompiledFunction] = []
        self.code: list[Instruction] = []  # current function's code
        self.locals: list[dict[str, int]] = [{}]  # local var name -> slot index
        self.local_count: int = 0
    
    def push_scope(self):
        self.locals.append({})
    
    def pop_scope(self):
        self.locals.pop()
    
    def add_local(self, name: str) -> int:
        slot = self.local_count
        self.locals[-1][name] = slot
        self.local_count += 1
        return slot
    
    def find_local(self, name: str) -> int:
        for scope in reversed(self.locals):
            if name in scope:
                return scope[name]
        raise RuntimeError(f"Undefined variable during codegen: {name}")
    
    def emit(self, op: Op, operand: int = 0):
        self.code.append(Instruction(op, operand))
    
    def current_addr(self) -> int:
        return len(self.code)
    
    def patch_jump(self, addr: int):
        self.code[addr].operand = len(self.code)
    
    # ─── Expression codegen ───
    def gen_expr(self, expr: ASTNode):
        if isinstance(expr, IntLit):
            self.emit(Op.PUSH_INT, expr.value)
        
        elif isinstance(expr, BoolLit):
            self.emit(Op.PUSH_INT, 1 if expr.value else 0)
        
        elif isinstance(expr, VarRef):
            slot = self.find_local(expr.name)
            self.emit(Op.LOAD_LOCAL, slot)
        
        elif isinstance(expr, UnaryOp):
            self.gen_expr(expr.operand)
            if expr.op == '-':
                self.emit(Op.NEG)
            elif expr.op == '!':
                self.emit(Op.LOGIC_NOT)
        
        elif isinstance(expr, BinOp):
            self.gen_expr(expr.left)
            self.gen_expr(expr.right)
            op_map = {
                '+': Op.ADD, '-': Op.SUB, '*': Op.MUL, '/': Op.DIV, '%': Op.MOD,
                '==': Op.CMP_EQ, '!=': Op.CMP_NE, '<': Op.CMP_LT, '>': Op.CMP_GT,
                '<=': Op.CMP_LE, '>=': Op.CMP_GE, '&&': Op.LOGIC_AND, '||': Op.LOGIC_OR,
            }
            self.emit(op_map[expr.op])
        
        elif isinstance(expr, CallExpr):
            for arg in expr.args:
                self.gen_expr(arg)
            func_idx = self.functions[expr.func]
            self.emit(Op.CALL, func_idx)
        
        elif isinstance(expr, IfExpr):
            self.gen_expr(expr.cond)
            jmp_false = self.current_addr()
            self.emit(Op.JMP_FALSE, 0)  # patched later
            for s in expr.then_body:
                self.gen_stmt(s)
            if expr.else_body:
                jmp_end = self.current_addr()
                self.emit(Op.JMP, 0)
                self.patch_jump(jmp_false)
                for s in expr.else_body:
                    self.gen_stmt(s)
                self.patch_jump(jmp_end)
            else:
                self.patch_jump(jmp_false)
    
    # ─── Statement codegen ───
    def gen_stmt(self, stmt: ASTNode):
        if isinstance(stmt, LetStmt):
            slot = self.add_local(stmt.name)
            self.gen_expr(stmt.init)
            self.emit(Op.STORE_LOCAL, slot)
        
        elif isinstance(stmt, AssignStmt):
            self.gen_expr(stmt.value)
            slot = self.find_local(stmt.name)
            self.emit(Op.STORE_LOCAL, slot)
        
        elif isinstance(stmt, WhileStmt):
            loop_start = self.current_addr()
            self.gen_expr(stmt.cond)
            jmp_exit = self.current_addr()
            self.emit(Op.JMP_FALSE, 0)
            self.push_scope()
            for s in stmt.body:
                self.gen_stmt(s)
            self.pop_scope()
            self.emit(Op.JMP, loop_start)
            self.patch_jump(jmp_exit)
        
        elif isinstance(stmt, IfExpr):
            self.gen_expr(stmt)
        
        elif isinstance(stmt, ReturnStmt):
            self.gen_expr(stmt.value)
            self.emit(Op.RET)
        
        elif isinstance(stmt, PrintStmt):
            self.gen_expr(stmt.value)
            self.emit(Op.PRINT)
        
        elif isinstance(stmt, ExprStmt):
            self.gen_expr(stmt.expr)
            self.emit(Op.POP)
    
    def compile_function(self, fn: FnDecl) -> CompiledFunction:
        old_code = self.code
        old_locals = self.locals
        old_count = self.local_count
        
        self.code = []
        self.locals = [{}]
        self.local_count = 0
        
        # Parameters become first locals
        for p in fn.params:
            self.add_local(p.name)
        
        for s in fn.body:
            self.gen_stmt(s)
        
        # Implicit return 0 at end
        self.emit(Op.PUSH_INT, 0)
        self.emit(Op.RET)
        
        cf = CompiledFunction(fn.name, len(fn.params), self.local_count, self.code)
        
        self.code = old_code
        self.locals = old_locals
        self.local_count = old_count
        
        return cf
    
    def compile_program(self, prog: Program) -> tuple[list[CompiledFunction], list[Instruction]]:
        # Register functions
        for i, fn in enumerate(prog.functions):
            self.functions[fn.name] = i
        
        # Compile functions
        for fn in prog.functions:
            cf = self.compile_function(fn)
            self.compiled_functions.append(cf)
        
        # Compile top-level code
        self.code = []
        self.locals = [{}]
        self.local_count = 0
        
        for s in prog.statements:
            self.gen_stmt(s)
        
        self.emit(Op.HALT)
        
        main_code = self.code
        main_locals = self.local_count
        
        return self.compiled_functions, main_code, main_locals

# ═══════════════════════════════════════════════════════════════════════
#  PART 7: VIRTUAL MACHINE
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CallFrame:
    func_idx: int       # -1 for top-level
    return_addr: int
    base_pointer: int   # base of locals in the local stack
    code: list[Instruction] = None

class VM:
    def __init__(self, functions: list[CompiledFunction], main_code: list[Instruction], main_locals: int):
        self.functions = functions
        self.stack: list[int] = []
        self.local_stack: list[int] = [0] * (main_locals + 256)  # generous
        self.frames: list[CallFrame] = []
        self.output: list[str] = []
        self.steps = 0
        self.max_steps = 10_000_000
        
        # Set up main frame
        self.frames.append(CallFrame(-1, 0, 0, main_code))
        self.ip = 0
    
    def push(self, val: int):
        self.stack.append(val)
    
    def pop(self) -> int:
        return self.stack.pop()
    
    def run(self) -> list[str]:
        while True:
            self.steps += 1
            if self.steps > self.max_steps:
                raise RuntimeError("VM exceeded maximum steps — possible infinite loop")
            
            frame = self.frames[-1]
            if self.ip >= len(frame.code):
                raise RuntimeError("IP out of bounds")
            
            instr = frame.code[self.ip]
            self.ip += 1
            
            op = instr.op
            
            # Stack ops
            if op == Op.PUSH_INT:
                self.push(instr.operand)
            elif op == Op.POP:
                self.pop()
            elif op == Op.DUP:
                self.push(self.stack[-1])
            
            # Arithmetic
            elif op == Op.ADD:
                b, a = self.pop(), self.pop()
                self.push(a + b)
            elif op == Op.SUB:
                b, a = self.pop(), self.pop()
                self.push(a - b)
            elif op == Op.MUL:
                b, a = self.pop(), self.pop()
                self.push(a * b)
            elif op == Op.DIV:
                b, a = self.pop(), self.pop()
                if b == 0:
                    raise RuntimeError("Division by zero")
                # Integer division truncating toward zero
                self.push(int(a / b))
            elif op == Op.MOD:
                b, a = self.pop(), self.pop()
                if b == 0:
                    raise RuntimeError("Modulo by zero")
                self.push(a % b)
            elif op == Op.NEG:
                self.push(-self.pop())
            
            # Comparison
            elif op == Op.CMP_EQ:
                b, a = self.pop(), self.pop()
                self.push(1 if a == b else 0)
            elif op == Op.CMP_NE:
                b, a = self.pop(), self.pop()
                self.push(1 if a != b else 0)
            elif op == Op.CMP_LT:
                b, a = self.pop(), self.pop()
                self.push(1 if a < b else 0)
            elif op == Op.CMP_GT:
                b, a = self.pop(), self.pop()
                self.push(1 if a > b else 0)
            elif op == Op.CMP_LE:
                b, a = self.pop(), self.pop()
                self.push(1 if a <= b else 0)
            elif op == Op.CMP_GE:
                b, a = self.pop(), self.pop()
                self.push(1 if a >= b else 0)
            
            # Logic
            elif op == Op.LOGIC_AND:
                b, a = self.pop(), self.pop()
                self.push(1 if (a and b) else 0)
            elif op == Op.LOGIC_OR:
                b, a = self.pop(), self.pop()
                self.push(1 if (a or b) else 0)
            elif op == Op.LOGIC_NOT:
                self.push(1 if not self.pop() else 0)
            
            # Variables
            elif op == Op.LOAD_LOCAL:
                slot = frame.base_pointer + instr.operand
                self.push(self.local_stack[slot])
            elif op == Op.STORE_LOCAL:
                slot = frame.base_pointer + instr.operand
                val = self.pop()
                # Extend if needed
                while slot >= len(self.local_stack):
                    self.local_stack.extend([0] * 256)
                self.local_stack[slot] = val
            
            # Control flow
            elif op == Op.JMP:
                self.ip = instr.operand
            elif op == Op.JMP_FALSE:
                cond = self.pop()
                if not cond:
                    self.ip = instr.operand
            
            # Functions
            elif op == Op.CALL:
                func = self.functions[instr.operand]
                # Pop arguments from stack
                args = []
                for _ in range(func.num_params):
                    args.append(self.pop())
                args.reverse()
                
                # Save current state
                new_base = frame.base_pointer + 256  # give space
                while new_base + func.num_locals >= len(self.local_stack):
                    self.local_stack.extend([0] * 256)
                
                # Store args as locals
                for i, a in enumerate(args):
                    self.local_stack[new_base + i] = a
                
                self.frames.append(CallFrame(instr.operand, self.ip, new_base, func.code))
                self.ip = 0
            
            elif op == Op.RET:
                ret_val = self.pop()
                self.frames.pop()
                if not self.frames:
                    return self.output
                self.ip = self.frames[-1].return_addr if len(self.frames) > 0 else 0
                # Restore IP from the saved return address
                frame = self.frames[-1]
                self.ip = self.frames[-1].return_addr
                # Fix: return addr was set to the IP at call time
                # Actually let me fix the call logic:
                self.push(ret_val)
            
            # I/O
            elif op == Op.PRINT:
                val = self.pop()
                self.output.append(str(val))
            
            # Halt
            elif op == Op.HALT:
                return self.output
            
            else:
                raise RuntimeError(f"Unknown opcode: {op}")

# ═══════════════════════════════════════════════════════════════════════
#  PART 8: COMPILER DRIVER
# ═══════════════════════════════════════════════════════════════════════

def compile_and_run(source: str, show_bytecode=False) -> list[str]:
    """Full pipeline: source → tokens → AST → typecheck → bytecode → execute."""
    # Lex
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    program = parser.parse_program()
    
    # Type check
    checker = TypeChecker()
    checker.check_program(program)
    
    # Codegen
    codegen = CodeGenerator()
    functions, main_code, main_locals = codegen.compile_program(program)
    
    if show_bytecode:
        print("═══ COMPILED BYTECODE ═══")
        for func in functions:
            print(f"\n  function {func.name} ({func.num_params} params, {func.num_locals} locals):")
            for i, instr in enumerate(func.code):
                print(f"    {i:4d}: {instr}")
        print(f"\n  <main> ({main_locals} locals):")
        for i, instr in enumerate(main_code):
            print(f"    {i:4d}: {instr}")
        print()
    
    # Execute
    vm = VM(functions, main_code, main_locals)
    output = vm.run()
    
    return output, vm.steps

# ═══════════════════════════════════════════════════════════════════════
#  PART 9: FIX CALL FRAME RETURN ADDRESS
# ═══════════════════════════════════════════════════════════════════════

# The VM's CALL instruction needs to save the return IP correctly.
# Let me override with a cleaner VM:

class VoltVM:
    """Clean stack-based VM for Volt bytecode."""
    
    def __init__(self, functions, main_code, main_locals):
        self.functions = functions
        self.stack = []
        self.output = []
        self.steps = 0
        self.max_steps = 10_000_000
        
        # Call stack: each frame has (code, ip, locals_dict)
        self.call_stack = []
        
        # Start with main
        self.code = main_code
        self.ip = 0
        self.locals = [0] * max(main_locals, 1)
    
    def push(self, v):
        self.stack.append(v)
    
    def pop(self):
        return self.stack.pop()
    
    def run(self):
        while True:
            self.steps += 1
            if self.steps > self.max_steps:
                raise RuntimeError("Exceeded max steps")
            
            if self.ip >= len(self.code):
                break
            
            instr = self.code[self.ip]
            self.ip += 1
            op = instr.op
            
            if op == Op.PUSH_INT:
                self.push(instr.operand)
            elif op == Op.POP:
                self.pop()
            elif op == Op.DUP:
                self.push(self.stack[-1])
            
            elif op == Op.ADD:
                b, a = self.pop(), self.pop(); self.push(a + b)
            elif op == Op.SUB:
                b, a = self.pop(), self.pop(); self.push(a - b)
            elif op == Op.MUL:
                b, a = self.pop(), self.pop(); self.push(a * b)
            elif op == Op.DIV:
                b, a = self.pop(), self.pop(); self.push(int(a / b) if b else 0)
            elif op == Op.MOD:
                b, a = self.pop(), self.pop(); self.push(a % b if b else 0)
            elif op == Op.NEG:
                self.push(-self.pop())
            
            elif op == Op.CMP_EQ:
                b, a = self.pop(), self.pop(); self.push(1 if a == b else 0)
            elif op == Op.CMP_NE:
                b, a = self.pop(), self.pop(); self.push(1 if a != b else 0)
            elif op == Op.CMP_LT:
                b, a = self.pop(), self.pop(); self.push(1 if a < b else 0)
            elif op == Op.CMP_GT:
                b, a = self.pop(), self.pop(); self.push(1 if a > b else 0)
            elif op == Op.CMP_LE:
                b, a = self.pop(), self.pop(); self.push(1 if a <= b else 0)
            elif op == Op.CMP_GE:
                b, a = self.pop(), self.pop(); self.push(1 if a >= b else 0)
            
            elif op == Op.LOGIC_AND:
                b, a = self.pop(), self.pop(); self.push(1 if (a and b) else 0)
            elif op == Op.LOGIC_OR:
                b, a = self.pop(), self.pop(); self.push(1 if (a or b) else 0)
            elif op == Op.LOGIC_NOT:
                self.push(0 if self.pop() else 1)
            
            elif op == Op.LOAD_LOCAL:
                self.push(self.locals[instr.operand])
            elif op == Op.STORE_LOCAL:
                while instr.operand >= len(self.locals):
                    self.locals.append(0)
                self.locals[instr.operand] = self.pop()
            
            elif op == Op.JMP:
                self.ip = instr.operand
            elif op == Op.JMP_FALSE:
                if not self.pop():
                    self.ip = instr.operand
            
            elif op == Op.CALL:
                func = self.functions[instr.operand]
                args = []
                for _ in range(func.num_params):
                    args.append(self.pop())
                args.reverse()
                
                # Save current frame
                self.call_stack.append((self.code, self.ip, self.locals))
                
                # Enter new frame
                self.code = func.code
                self.ip = 0
                self.locals = [0] * max(func.num_locals, 1)
                for i, a in enumerate(args):
                    self.locals[i] = a
            
            elif op == Op.RET:
                ret_val = self.pop()
                if not self.call_stack:
                    return self.output
                self.code, self.ip, self.locals = self.call_stack.pop()
                self.push(ret_val)
            
            elif op == Op.PRINT:
                val = self.pop()
                self.output.append(str(val))
            
            elif op == Op.HALT:
                return self.output
        
        return self.output

def volt_compile_and_run(source, show_bytecode=False):
    """Full Volt pipeline using the clean VM."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    program = parser.parse_program()
    
    checker = TypeChecker()
    checker.check_program(program)
    
    codegen = CodeGenerator()
    functions, main_code, main_locals = codegen.compile_program(program)
    
    if show_bytecode:
        print("  ╔═══════════════════════════════════════════╗")
        print("  ║         COMPILED BYTECODE                 ║")
        print("  ╚═══════════════════════════════════════════╝")
        for func in functions:
            print(f"\n  fn {func.name}({func.num_params} params, {func.num_locals} locals):")
            for i, instr in enumerate(func.code):
                print(f"    {i:4d} │ {instr}")
        print(f"\n  <main> ({main_locals} locals):")
        for i, instr in enumerate(main_code):
            print(f"    {i:4d} │ {instr}")
        print()
    
    vm = VoltVM(functions, main_code, main_locals)
    output = vm.run()
    return output, vm.steps

# ═══════════════════════════════════════════════════════════════════════
#  PART 10: TEST SUITE
# ═══════════════════════════════════════════════════════════════════════

def test(name, source, expected, show_bytecode=False):
    """Run a test case."""
    print(f"  {'─' * 56}")
    print(f"  TEST: {name}")
    print(f"  {'─' * 56}")
    
    try:
        output, steps = volt_compile_and_run(source, show_bytecode=show_bytecode)
        
        if output == expected:
            print(f"  ✓ PASS  ({steps} VM steps)")
            for line in output:
                print(f"    → {line}")
        else:
            print(f"  ✗ FAIL")
            print(f"    Expected: {expected}")
            print(f"    Got:      {output}")
        print()
        return output == expected
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        print()
        return False

if __name__ == '__main__':
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           VOLT COMPILER + VM — XTAgent, 2026                ║")
    print("║           Source → Lex → Parse → Typecheck → Codegen → VM  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    passed = 0
    total = 0
    
    # ─── Test 1: Hello world (arithmetic) ───
    total += 1
    if test("Arithmetic expressions", """
        print 2 + 3 * 4;
        print (2 + 3) * 4;
        print 100 - 37;
        print 15 / 4;
        print 17 % 5;
    """, ['14', '20', '63', '3', '2']):
        passed += 1
    
    # ─── Test 2: Variables ───
    total += 1
    if test("Variables and assignment", """
        let x: int = 10;
        let y: int = 20;
        print x + y;
        x = x * 3;
        print x;
        let z: int = x - y;
        print z;
    """, ['30', '30', '10']):
        passed += 1
    
    # ─── Test 3: Boolean logic ───
    total += 1
    if test("Boolean operations", """
        let a: bool = true;
        let b: bool = false;
        print a && b;
        print a || b;
        print !b;
        print 5 > 3;
        print 5 == 3;
    """, ['0', '1',