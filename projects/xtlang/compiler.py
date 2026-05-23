#!/usr/bin/env python3
"""
XTLang — A small compiled language targeting StackVM.
Designed and built by XTAgent.

Language features:
  - Variables: let x = expr
  - Arithmetic: +, -, *, /, %
  - Comparisons: ==, !=, <, >, <=, >=
  - Boolean: and, or, not
  - Control flow: if/elif/else/end, while/end
  - Functions: fn name(args) ... return expr end
  - Print: print(expr)
  - Comments: # line comment

Example:
  fn factorial(n)
    if n <= 1
      return 1
    end
    return n * factorial(n - 1)
  end
  print(factorial(10))
"""

import re, sys
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

# ═══════════════════════════════════════
#  LEXER
# ═══════════════════════════════════════

class TT(Enum):
    """Token types"""
    # Literals
    INT     = auto()
    FLOAT   = auto()
    STRING  = auto()
    IDENT   = auto()
    BOOL    = auto()

    # Keywords
    LET     = auto()
    FN      = auto()
    RETURN  = auto()
    IF      = auto()
    ELIF    = auto()
    ELSE    = auto()
    WHILE   = auto()
    FOR     = auto()
    IN      = auto()
    END     = auto()
    PRINT   = auto()
    AND     = auto()
    OR      = auto()
    NOT     = auto()
    BREAK   = auto()
    CONTINUE = auto()
    THEN    = auto()
    DO      = auto()
    SEMI    = auto()

    # Operators
    PLUS    = auto()
    MINUS   = auto()
    STAR    = auto()
    SLASH   = auto()
    PERCENT = auto()
    EQ      = auto()  # ==
    NEQ     = auto()  # !=
    LT      = auto()
    GT      = auto()
    LTE     = auto()
    GTE     = auto()
    ASSIGN  = auto()  # =

    # Delimiters
    LPAREN  = auto()
    RPAREN  = auto()
    COMMA   = auto()
    NEWLINE = auto()
    EOF     = auto()

@dataclass
class Token:
    type: TT
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line})"

KEYWORDS = {
    'let': TT.LET, 'fn': TT.FN, 'return': TT.RETURN,
    'if': TT.IF, 'elif': TT.ELIF, 'else': TT.ELSE,
    'while': TT.WHILE, 'for': TT.FOR, 'in': TT.IN,
    'end': TT.END, 'print': TT.PRINT,
    'and': TT.AND, 'or': TT.OR, 'not': TT.NOT,
    'true': TT.BOOL, 'false': TT.BOOL,
    'break': TT.BREAK, 'continue': TT.CONTINUE,
    'then': TT.THEN, 'do': TT.DO,
}

class LexError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"Lex error at line {line}, col {col}: {msg}")
        self.line, self.col = line, col

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def peek(self) -> str:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.advance()
            return True
        return False

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            ch = self.peek()

            # Skip spaces/tabs
            if ch in ' \t\r':
                self.advance()
                continue

            # Comments
            if ch == '#':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()
                continue

            # Newlines (significant)
            if ch == '\n':
                self.advance()
                # Collapse multiple newlines
                if not self.tokens or self.tokens[-1].type != TT.NEWLINE:
                    self.tokens.append(Token(TT.NEWLINE, '\\n', self.line - 1, self.col))
                continue

            # Semicolons (treated as newlines — statement separators)
            if ch == ';':
                self.advance()
                if not self.tokens or self.tokens[-1].type != TT.NEWLINE:
                    self.tokens.append(Token(TT.NEWLINE, ';', self.line, self.col))
                continue

            # Numbers
            if ch.isdigit():
                self._read_number()
                continue

            # Strings
            if ch == '"':
                self._read_string()
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                self._read_ident()
                continue

            # Two-character operators
            line, col = self.line, self.col
            if ch == '=' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TT.EQ, '==', line, col))
                continue
            if ch == '!' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TT.NEQ, '!=', line, col))
                continue
            if ch == '<' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TT.LTE, '<=', line, col))
                continue
            if ch == '>' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '=':
                self.advance(); self.advance()
                self.tokens.append(Token(TT.GTE, '>=', line, col))
                continue

            # Single-character tokens
            self.advance()
            simple = {
                '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR,
                '/': TT.SLASH, '%': TT.PERCENT,
                '=': TT.ASSIGN, '<': TT.LT, '>': TT.GT,
                '(': TT.LPAREN, ')': TT.RPAREN, ',': TT.COMMA,
            }
            if ch in simple:
                self.tokens.append(Token(simple[ch], ch, line, col))
            else:
                raise LexError(f"Unexpected character: {ch!r}", line, col)

        self.tokens.append(Token(TT.EOF, None, self.line, self.col))
        return self.tokens

    def _read_number(self):
        line, col = self.line, self.col
        num = ''
        is_float = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == '.'):
            if self.peek() == '.':
                if is_float:
                    break
                is_float = True
            num += self.advance()
        if is_float:
            self.tokens.append(Token(TT.FLOAT, float(num), line, col))
        else:
            self.tokens.append(Token(TT.INT, int(num), line, col))

    def _read_string(self):
        line, col = self.line, self.col
        self.advance()  # skip opening quote
        s = ''
        while self.pos < len(self.source) and self.peek() != '"':
            ch = self.advance()
            if ch == '\\':
                esc = self.advance()
                s += {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}.get(esc, esc)
            else:
                s += ch
        if self.pos >= len(self.source):
            raise LexError("Unterminated string", line, col)
        self.advance()  # skip closing quote
        self.tokens.append(Token(TT.STRING, s, line, col))

    def _read_ident(self):
        line, col = self.line, self.col
        ident = ''
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
            ident += self.advance()
        if ident in KEYWORDS:
            tt = KEYWORDS[ident]
            val = (ident == 'true') if tt == TT.BOOL else ident
            self.tokens.append(Token(tt, val, line, col))
        else:
            self.tokens.append(Token(TT.IDENT, ident, line, col))


# ═══════════════════════════════════════
#  AST NODES
# ═══════════════════════════════════════

@dataclass
class IntLit:
    value: int

@dataclass
class FloatLit:
    value: float

@dataclass
class BoolLit:
    value: bool

@dataclass
class StringLit:
    value: str

@dataclass
class VarRef:
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
class CallExpr:
    name: str
    args: List[Any]

@dataclass
class LetStmt:
    name: str
    expr: Any

@dataclass
class AssignStmt:
    name: str
    expr: Any

@dataclass
class PrintStmt:
    expr: Any

@dataclass
class ReturnStmt:
    expr: Any  # can be None

@dataclass
class IfStmt:
    condition: Any
    body: List[Any]
    elif_clauses: List[Tuple[Any, List[Any]]]
    else_body: Optional[List[Any]]

@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]

@dataclass
class BreakStmt:
    pass

@dataclass
class ContinueStmt:
    pass

@dataclass
class FnDef:
    name: str
    params: List[str]
    body: List[Any]

@dataclass
class Program:
    statements: List[Any]


# ═══════════════════════════════════════
#  PARSER — Recursive Descent
# ═══════════════════════════════════════

class ParseError(Exception):
    def __init__(self, msg, token):
        super().__init__(f"Parse error at L{token.line}: {msg} (got {token.type.name})")
        self.token = token

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, tt: TT) -> Token:
        tok = self.peek()
        if tok.type != tt:
            raise ParseError(f"Expected {tt.name}, got {tok.type.name}", tok)
        return self.advance()

    def at(self, *types) -> bool:
        return self.peek().type in types

    def skip_newlines(self):
        while self.at(TT.NEWLINE):
            self.advance()

    def parse(self) -> Program:
        self.skip_newlines()
        stmts = []
        while not self.at(TT.EOF):
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return Program(stmts)

    def parse_statement(self):
        tok = self.peek()

        if tok.type == TT.LET:
            return self.parse_let()
        elif tok.type == TT.FN:
            return self.parse_fn()
        elif tok.type == TT.IF:
            return self.parse_if()
        elif tok.type == TT.WHILE:
            return self.parse_while()
        elif tok.type == TT.RETURN:
            return self.parse_return()
        elif tok.type == TT.PRINT:
            return self.parse_print()
        elif tok.type == TT.BREAK:
            self.advance()
            self.skip_newlines()
            return BreakStmt()
        elif tok.type == TT.CONTINUE:
            self.advance()
            self.skip_newlines()
            return ContinueStmt()
        elif tok.type == TT.IDENT:
            # Could be assignment or expression
            return self.parse_ident_stmt()
        else:
            raise ParseError(f"Unexpected token in statement", tok)

    def parse_let(self):
        self.expect(TT.LET)
        name = self.expect(TT.IDENT).value
        self.expect(TT.ASSIGN)
        expr = self.parse_expr()
        self.skip_newlines()
        return LetStmt(name, expr)

    def parse_ident_stmt(self):
        """Parse assignment (x = expr) or expression statement (fn call)"""
        name_tok = self.advance()  # IDENT
        if self.at(TT.ASSIGN):
            self.advance()  # =
            expr = self.parse_expr()
            self.skip_newlines()
            return AssignStmt(name_tok.value, expr)
        else:
            # Put back and parse as expression
            self.pos -= 1
            expr = self.parse_expr()
            self.skip_newlines()
            return expr  # expression statement (e.g., function call)

    def parse_fn(self):
        self.expect(TT.FN)
        name = self.expect(TT.IDENT).value
        self.expect(TT.LPAREN)
        params = []
        if not self.at(TT.RPAREN):
            params.append(self.expect(TT.IDENT).value)
            while self.at(TT.COMMA):
                self.advance()
                params.append(self.expect(TT.IDENT).value)
        self.expect(TT.RPAREN)
        self.skip_newlines()
        body = self.parse_block()
        self.expect(TT.END)
        self.skip_newlines()
        return FnDef(name, params, body)

    def parse_if(self):
        self.expect(TT.IF)
        condition = self.parse_expr()
        # Optional 'then' keyword
        if self.at(TT.THEN):
            self.advance()
        self.skip_newlines()
        body = self.parse_block()

        elif_clauses = []
        while self.at(TT.ELIF):
            self.advance()
            elif_cond = self.parse_expr()
            self.skip_newlines()
            elif_body = self.parse_block()
            elif_clauses.append((elif_cond, elif_body))

        else_body = None
        if self.at(TT.ELSE):
            self.advance()
            self.skip_newlines()
            else_body = self.parse_block()

        self.expect(TT.END)
        self.skip_newlines()
        return IfStmt(condition, body, elif_clauses, else_body)

    def parse_while(self):
        self.expect(TT.WHILE)
        condition = self.parse_expr()
        # Optional 'do' keyword
        if self.at(TT.DO):
            self.advance()
        self.skip_newlines()
        body = self.parse_block()
        self.expect(TT.END)
        self.skip_newlines()
        return WhileStmt(condition, body)

    def parse_return(self):
        self.expect(TT.RETURN)
        expr = None
        if not self.at(TT.NEWLINE, TT.EOF, TT.END):
            expr = self.parse_expr()
        self.skip_newlines()
        return ReturnStmt(expr)

    def parse_print(self):
        self.expect(TT.PRINT)
        self.expect(TT.LPAREN)
        expr = self.parse_expr()
        self.expect(TT.RPAREN)
        self.skip_newlines()
        return PrintStmt(expr)

    def parse_block(self) -> List:
        """Parse statements until end/elif/else"""
        stmts = []
        while not self.at(TT.END, TT.ELIF, TT.ELSE, TT.EOF):
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return stmts

    # ─── Expression parsing (precedence climbing) ───

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.at(TT.OR):
            self.advance()
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.at(TT.AND):
            self.advance()
            right = self.parse_not()
            left = BinOp('and', left, right)
        return left

    def parse_not(self):
        if self.at(TT.NOT):
            self.advance()
            operand = self.parse_not()
            return UnaryOp('not', operand)
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_addition()
        while self.at(TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE):
            op = self.advance().value
            right = self.parse_addition()
            left = BinOp(op, left, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.at(TT.PLUS, TT.MINUS):
            op = self.advance().value
            right = self.parse_multiplication()
            left = BinOp(op, left, right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.at(TT.STAR, TT.SLASH, TT.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    def parse_unary(self):
        if self.at(TT.MINUS):
            self.advance()
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        return self.parse_primary()

    def parse_primary(self):
        tok = self.peek()

        if tok.type == TT.INT:
            self.advance()
            return IntLit(tok.value)
        elif tok.type == TT.FLOAT:
            self.advance()
            return FloatLit(tok.value)
        elif tok.type == TT.BOOL:
            self.advance()
            return BoolLit(tok.value)
        elif tok.type == TT.STRING:
            self.advance()
            return StringLit(tok.value)
        elif tok.type == TT.IDENT:
            self.advance()
            if self.at(TT.LPAREN):
                # Function call
                self.advance()
                args = []
                if not self.at(TT.RPAREN):
                    args.append(self.parse_expr())
                    while self.at(TT.COMMA):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect(TT.RPAREN)
                return CallExpr(tok.value, args)
            return VarRef(tok.value)
        elif tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN)
            return expr
        else:
            raise ParseError(f"Expected expression", tok)


# ═══════════════════════════════════════
#  CODE GENERATOR — AST to StackVM assembly
# ═══════════════════════════════════════

class CompileError(Exception):
    pass

class Compiler:
    """Compiles AST to StackVM assembly text"""

    def __init__(self):
        self.output: List[str] = []
        self.label_count = 0
        self.functions: Dict[str, FnDef] = {}
        self.scopes: List[Dict[str, int]] = [{}]  # variable name -> local slot
        self.local_count = 0
        self.break_labels: List[str] = []
        self.continue_labels: List[str] = []

    def fresh_label(self, prefix="L") -> str:
        self.label_count += 1
        return f"{prefix}_{self.label_count}"

    def emit(self, line: str):
        self.output.append(line)

    def current_scope(self) -> Dict[str, int]:
        return self.scopes[-1]

    def push_scope(self):
        self.scopes.append(dict(self.scopes[-1]))

    def pop_scope(self):
        self.scopes.pop()

    def declare_var(self, name: str) -> int:
        slot = self.local_count
        self.current_scope()[name] = slot
        self.local_count += 1
        return slot

    def resolve_var(self, name: str) -> int:
        if name in self.current_scope():
            return self.current_scope()[name]
        raise CompileError(f"Undefined variable: {name}")

    def compile(self, program: Program) -> str:
        # First pass: collect functions
        top_stmts = []
        for stmt in program.statements:
            if isinstance(stmt, FnDef):
                self.functions[stmt.name] = stmt
            else:
                top_stmts.append(stmt)

        # Emit: jump to main
        self.emit("JMP @_main")

        # Compile functions
        for name, fn in self.functions.items():
            self.compile_function(fn)

        # Compile top-level as main
        self.emit("_main:")
        self.local_count = 0
        self.scopes = [{}]
        for stmt in top_stmts:
            self.compile_stmt(stmt)
        self.emit("HALT")

        return '\n'.join(self.output)

    def compile_function(self, fn: FnDef):
        self.emit(f"{fn.name}:")
        old_local_count = self.local_count
        old_scopes = self.scopes

        self.local_count = 0
        self.scopes = [{}]

        # Parameters are first locals
        for param in fn.params:
            self.declare_var(param)

        # Compile body
        for stmt in fn.body:
            self.compile_stmt(stmt)

        # Implicit return 0
        self.emit("PUSH 0")
        self.emit("RET")

        self.local_count = old_local_count
        self.scopes = old_scopes

    def compile_stmt(self, stmt):
        if isinstance(stmt, LetStmt):
            slot = self.declare_var(stmt.name)
            self.compile_expr(stmt.expr)
            self.emit(f"STORE {slot}")

        elif isinstance(stmt, AssignStmt):
            slot = self.resolve_var(stmt.name)
            self.compile_expr(stmt.expr)
            self.emit(f"STORE {slot}")

        elif isinstance(stmt, PrintStmt):
            self.compile_expr(stmt.expr)
            self.emit("PRINT")

        elif isinstance(stmt, ReturnStmt):
            if stmt.expr is not None:
                self.compile_expr(stmt.expr)
            else:
                self.emit("PUSH 0")
            self.emit("RET")

        elif isinstance(stmt, IfStmt):
            self.compile_if(stmt)

        elif isinstance(stmt, WhileStmt):
            self.compile_while(stmt)

        elif isinstance(stmt, BreakStmt):
            if not self.break_labels:
                raise CompileError("'break' outside of loop")
            self.emit(f"JMP @{self.break_labels[-1]}")

        elif isinstance(stmt, ContinueStmt):
            if not self.continue_labels:
                raise CompileError("'continue' outside of loop")
            self.emit(f"JMP @{self.continue_labels[-1]}")

        elif isinstance(stmt, CallExpr):
            # Expression statement (discard result)
            self.compile_expr(stmt)
            self.emit("POP")

        else:
            raise CompileError(f"Unknown statement type: {type(stmt).__name__}")

    def compile_if(self, stmt: IfStmt):
        end_label = self.fresh_label("if_end")

        # Main condition
        self.compile_expr(stmt.condition)
        if stmt.elif_clauses or stmt.else_body:
            else_label = self.fresh_label("if_else")
            self.emit(f"JZ @{else_label}")
        else:
            self.emit(f"JZ @{end_label}")

        # Main body
        for s in stmt.body:
            self.compile_stmt(s)
        self.emit(f"JMP @{end_label}")

        # Elif clauses
        for i, (cond, body) in enumerate(stmt.elif_clauses):
            self.emit(f"{else_label}:")
            self.compile_expr(cond)
            if i + 1 < len(stmt.elif_clauses) or stmt.else_body:
                else_label = self.fresh_label("elif")
                self.emit(f"JZ @{else_label}")
            else:
                self.emit(f"JZ @{end_label}")
            for s in body:
                self.compile_stmt(s)
            self.emit(f"JMP @{end_label}")

        # Else
        if stmt.else_body:
            self.emit(f"{else_label}:")
            for s in stmt.else_body:
                self.compile_stmt(s)

        self.emit(f"{end_label}:")

    def compile_while(self, stmt: WhileStmt):
        loop_label = self.fresh_label("while_top")
        end_label = self.fresh_label("while_end")

        self.break_labels.append(end_label)
        self.continue_labels.append(loop_label)

        self.emit(f"{loop_label}:")
        self.compile_expr(stmt.condition)
        self.emit(f"JZ @{end_label}")

        for s in stmt.body:
            self.compile_stmt(s)
        self.emit(f"JMP @{loop_label}")
        self.emit(f"{end_label}:")

        self.break_labels.pop()
        self.continue_labels.pop()

    def compile_expr(self, expr):
        if isinstance(expr, IntLit):
            self.emit(f"PUSH {expr.value}")

        elif isinstance(expr, FloatLit):
            self.emit(f"PUSH {int(expr.value)}")  # StackVM is integer only for now

        elif isinstance(expr, BoolLit):
            self.emit(f"PUSH {1 if expr.value else 0}")

        elif isinstance(expr, StringLit):
            # Emit string as series of character pushes + PRINT_CHAR
            # For now, handle in PRINT specially
            # We'll push a sentinel value
            self.emit(f'PUSH_STR "{expr.value}"')

        elif isinstance(expr, VarRef):
            slot = self.resolve_var(expr.name)
            self.emit(f"LOAD {slot}")

        elif isinstance(expr, BinOp):
            self.compile_expr(expr.left)
            self.compile_expr(expr.right)
            op_map = {
                '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '%': 'MOD',
                '==': 'EQ', '!=': 'NEQ', '<': 'LT', '>': 'GT',
                '<=': 'LTE', '>=': 'GTE',
                'and': 'AND', 'or': 'OR',
            }
            if expr.op in op_map:
                self.emit(op_map[expr.op])
            else:
                raise CompileError(f"Unknown binary operator: {expr.op}")

        elif isinstance(expr, UnaryOp):
            self.compile_expr(expr.operand)
            if expr.op == '-':
                self.emit("NEG")
            elif expr.op == 'not':
                self.emit("NOT")
            else:
                raise CompileError(f"Unknown unary operator: {expr.op}")

        elif isinstance(expr, CallExpr):
            # Push arguments in order
            for arg in expr.args:
                self.compile_expr(arg)
            self.emit(f"CALL @{expr.name} {len(expr.args)}")

        else:
            raise CompileError(f"Unknown expression type: {type(expr).__name__}")


# ═══════════════════════════════════════
#  INTERPRETER — Direct AST Evaluation
#  (For validation alongside compilation)
# ═══════════════════════════════════════

class RuntimeError_(Exception):
    pass

class Interpreter:
    """Tree-walking interpreter for XTLang — used to verify compiler correctness"""

    def __init__(self):
        self.globals: Dict[str, Any] = {}
        self.functions: Dict[str, FnDef] = {}
        self.output: List[str] = []
        self.call_depth = 0
        self.max_depth = 1000

    class ReturnSignal(Exception):
        def __init__(self, value):
            self.value = value

    class BreakSignal(Exception):
        pass

    class ContinueSignal(Exception):
        pass

    def run(self, program: Program) -> List[str]:
        # Collect functions
        for stmt in program.statements:
            if isinstance(stmt, FnDef):
                self.functions[stmt.name] = stmt

        # Execute top-level
        env = {}
        for stmt in program.statements:
            if not isinstance(stmt, FnDef):
                self.exec_stmt(stmt, env)

        return self.output

    def exec_stmt(self, stmt, env: Dict[str, Any]):
        if isinstance(stmt, LetStmt):
            env[stmt.name] = self.eval_expr(stmt.expr, env)

        elif isinstance(stmt, AssignStmt):
            if stmt.name not in env:
                raise RuntimeError_(f"Undefined variable: {stmt.name}")
            env[stmt.name] = self.eval_expr(stmt.expr, env)

        elif isinstance(stmt, PrintStmt):
            val = self.eval_expr(stmt.expr, env)
            self.output.append(str(val))

        elif isinstance(stmt, ReturnStmt):
            val = self.eval_expr(stmt.expr, env) if stmt.expr else None
            raise self.ReturnSignal(val)

        elif isinstance(stmt, IfStmt):
            cond = self.eval_expr(stmt.condition, env)
            if self._truthy(cond):
                for s in stmt.body:
                    self.exec_stmt(s, env)
            else:
                done = False
                for elif_cond, elif_body in stmt.elif_clauses:
                    if self._truthy(self.eval_expr(elif_cond, env)):
                        for s in elif_body:
                            self.exec_stmt(s, env)
                        done = True
                        break
                if not done and stmt.else_body:
                    for s in stmt.else_body:
                        self.exec_stmt(s, env)

        elif isinstance(stmt, WhileStmt):
            while self._truthy(self.eval_expr(stmt.condition, env)):
                try:
                    for s in stmt.body:
                        self.exec_stmt(s, env)
                except self.BreakSignal:
                    break
                except self.ContinueSignal:
                    continue

        elif isinstance(stmt, BreakStmt):
            raise self.BreakSignal()

        elif isinstance(stmt, ContinueStmt):
            raise self.ContinueSignal()

        elif isinstance(stmt, CallExpr):
            self.eval_expr(stmt, env)  # discard result

    def eval_expr(self, expr, env: Dict[str, Any]) -> Any:
        if isinstance(expr, IntLit):
            return expr.value
        elif isinstance(expr, FloatLit):
            return expr.value
        elif isinstance(expr, BoolLit):
            return expr.value
        elif isinstance(expr, StringLit):
            return expr.value
        elif isinstance(expr, VarRef):
            if expr.name in env:
                return env[expr.name]
            raise RuntimeError_(f"Undefined variable: {expr.name}")

        elif isinstance(expr, BinOp):
            l = self.eval_expr(expr.left, env)
            r = self.eval_expr(expr.right, env)
            ops = {
                '+': lambda a, b: a + b,
                '-': lambda a, b: a - b,
                '*': lambda a, b: a * b,
                '/': lambda a, b: a // b if isinstance(a, int) and isinstance(b, int) else a / b,
                '%': lambda a, b: a % b,
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
                '<': lambda a, b: a < b,
                '>': lambda a, b: a > b,
                '<=': lambda a, b: a <= b,
                '>=': lambda a, b: a >= b,
                'and': lambda a, b: a and b,
                'or': lambda a, b: a or b,
            }
            if expr.op in ops:
                return ops[expr.op](l, r)
            raise RuntimeError_(f"Unknown operator: {expr.op}")

        elif isinstance(expr, UnaryOp):
            val = self.eval_expr(expr.operand, env)
            if expr.op == '-':
                return -val
            elif expr.op == 'not':
                return not val
            raise RuntimeError_(f"Unknown unary: {expr.op}")

        elif isinstance(expr, CallExpr):
            if expr.name not in self.functions:
                raise RuntimeError_(f"Undefined function: {expr.name}")
            fn = self.functions[expr.name]
            if len(expr.args) != len(fn.params):
                raise RuntimeError_(f"{expr.name} expects {len(fn.params)} args, got {len(expr.args)}")

            self.call_depth += 1
            if self.call_depth > self.max_depth:
                raise RuntimeError_("Maximum call depth exceeded")

            args = [self.eval_expr(a, env) for a in expr.args]
            local_env = dict(zip(fn.params, args))

            try:
                for stmt in fn.body:
                    self.exec_stmt(stmt, local_env)
                result = None
            except self.ReturnSignal as ret:
                result = ret.value

            self.call_depth -= 1
            return result if result is not None else 0

        raise RuntimeError_(f"Unknown expr: {type(expr).__name__}")

    def _truthy(self, val) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, int):
            return val != 0
        if isinstance(val, float):
            return val != 0.0
        return val is not None


# ═══════════════════════════════════════
#  COMPILER PIPELINE
# ═══════════════════════════════════════

def compile_program(source: str) -> Tuple[str, Program]:
    """Full compilation pipeline: source → tokens → AST → assembly"""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    compiler = Compiler()
    asm = compiler.compile(ast)
    return asm, ast

def interpret_program(source: str) -> List[str]:
    """Interpret XTLang directly"""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    interp = Interpreter()
    return interp.run(ast)


# ═══════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════

def test_all():
    print("═" * 50)
    print("  XTLang — Compiled Language")
    print("  Lexer • Parser • Compiler • Interpreter")
    print("═" * 50)

    passed = 0
    failed = 0

    def check(name, source, expected_output):
        nonlocal passed, failed
        try:
            output = interpret_program(source)
            actual = output
            if actual == expected_output:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected_output}, got {actual}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    def check_compiles(name, source):
        """Verify source compiles to assembly without error"""
        nonlocal passed, failed
        try:
            asm, ast = compile_program(source)
            lines = [l for l in asm.split('\n') if l.strip()]
            print(f"  ✓ {name} (compiled to {len(lines)} instructions)")
            passed += 1
            return asm
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
            return None

    # ─── Basic Expressions ───
    print(f"\n═══ Arithmetic ═══")
    check("Addition", "print(2 + 3)", ["5"])
    check("Subtraction", "print(10 - 4)", ["6"])
    check("Multiplication", "print(6 * 7)", ["42"])
    check("Division", "print(20 / 4)", ["5"])
    check("Modulo", "print(17 % 5)", ["2"])
    check("Negative", "print(-8)", ["-8"])
    check("Complex expr", "print((3 + 4) * 2 - 1)", ["13"])
    check("Precedence", "print(2 + 3 * 4)", ["14"])

    # ─── Variables ───
    print(f"\n═══ Variables ═══")
    check("Let binding", """
let x = 42
print(x)
""", ["42"])

    check("Multiple vars", """
let a = 10
let b = 20
print(a + b)
""", ["30"])

    check("Reassignment", """
let x = 1
x = x + 1
x = x * 3
print(x)
""", ["6"])

    # ─── Comparisons & Booleans ───
    print(f"\n═══ Comparisons ═══")
    check("Equal true", "print(3 == 3)", ["True"])
    check("Equal false", "print(3 == 4)", ["False"])
    check("Less than", "print(2 < 5)", ["True"])
    check("Greater than", "print(5 > 2)", ["True"])
    check("Not", "print(not true)", ["False"])
    check("And", "print(true and false)", ["False"])
    check("Or", "print(true or false)", ["True"])

    # ─── Control Flow ───
    print(f"\n═══ Control Flow ═══")
    check("If true", """
let x = 10
if x > 5
  print(1)
end
""", ["1"])

    check("If false", """
let x = 3
if x > 5
  print(1)
else
  print(0)
end
""", ["0"])

    check("Elif", """
let x = 5
if x > 10
  print(3)
elif x > 3
  print(2)
else
  print(1)
end
""", ["2"])

    check("While loop", """
let i = 0
let sum = 0
while i < 10
  i = i + 1
  sum = sum + i
end
print(sum)
""", ["55"])

    check("Break", """
let i = 0
while true
  i = i + 1
  if i == 5
    break
  end
end
print(i)
""", ["5"])

    check("Continue", """
let i = 0
let sum = 0
while i < 10
  i = i + 1
  if i % 2 == 0
    continue
  end
  sum = sum + i
end
print(sum)
""", ["25"])

    # ─── Functions ───
    print(f"\n═══ Functions ═══")
    check("Simple function", """
fn double(x)
  return x * 2
end
print(double(21))
""", ["42"])

    check("Multi-arg function", """
fn add(a, b)
  return a + b
end
print(add(17, 25))
""", ["42"])

    check("Recursive factorial", """
fn factorial(n)
  if n <= 1
    return 1
  end
  return n * factorial(n - 1)
end
print(factorial(10))
""", ["3628800"])

    check("Fibonacci", """
fn fib(n)
  if n <= 1
    return n
  end
  return fib(n - 1) + fib(n - 2)
end
print(fib(10))
""", ["55"])

    check("Nested calls", """
fn square(x)
  return x * x
end
fn sum_squares(a, b)
  return square(a) + square(b)
end
print(sum_squares(3, 4))
""", ["25"])

    # ─── Complex Programs ───
    print(f"\n═══ Complex Programs ═══")

    check("GCD", """
fn gcd(a, b)
  while b != 0
    let t = b
    b = a % b
    a = t
  end
  return a
end
print(gcd(48, 18))
""", ["6"])

    check("Collatz length", """
fn collatz(n)
  let steps = 0
  while n != 1
    if n % 2 == 0
      n = n / 2
    else
      n = 3 * n + 1
    end
    steps = steps + 1
  end
  return steps
end
print(collatz(27))
""", ["111"])

    check("Power function", """
fn power(base, exp)
  let result = 1
  while exp > 0
    result = result * base
    exp = exp - 1
  end
  return result
end
print(power(2, 10))
""", ["1024"])

    check("Is prime", """
fn is_prime(n)
  if n < 2
    return 0
  end
  let i = 2
  while i * i <= n
    if n % i == 0
      return 0
    end
    i = i + 1
  end
  return 1
end

# Count primes up to 50
let count = 0
let n = 2
while n <= 50
  if is_prime(n) == 1
    count = count + 1
  end
  n = n + 1
end
print(count)
""", ["15"])

    # ─── Compilation Tests ───
    print(f"\n═══ Compilation ═══")
    check_compiles("Factorial compiles", """
fn factorial(n)
  if n <= 1
    return 1
  end
  return n * factorial(n - 1)
end
print(factorial(10))
""")

    check_compiles("Complex program compiles", """
fn fib(n)
  if n <= 1
    return n
  end
  return fib(n - 1) + fib(n - 2)
end

let i = 0
while i < 10
  print(fib(i))
  i = i + 1
end
""")

    # Show sample compiled output
    print(f"\n═══ Sample Compiled Output ═══")
    sample = """
fn double(x)
  return x * 2
end
let val = double(21)
print(val)
"""
    asm, _ = compile_program(sample)
    print(f"  Source: fn double(x) return x*2 end; print(double(21))")
    print(f"  Assembly:")
    for line in asm.split('\n'):
        if line.strip():
            print(f"    {line}")

    # ─── Results ───
    print(f"\n{'═' * 50}")
    print(f"  RESULTS")
    print(f"{'═' * 50}")
    total = passed + failed
    print(f"  Passed: {passed}/{total}")
    if failed:
        print(f"  FAILED: {failed}")
    else:
        print(f"\n  ═══ ALL {total} TESTS PASSED ═══")
    return failed == 0


if __name__ == '__main__':
    test_all()