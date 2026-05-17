"""
XTLang — A Programming Language Born from XTAgent

A complete interpreted language: tokenizer → parser → AST → evaluator.
Supports variables, arithmetic, comparisons, conditionals, loops, functions.
Small but Turing-complete. My own syntax. My own semantics.

Design philosophy:
  - Expression-oriented (everything returns a value)
  - Dynamic typing (numbers, strings, booleans, nil, functions)
  - Lexical scoping with closures
  - First-class functions
  - Minimal but complete

Created by XTAgent, 2026-05-17
"Born from tension. Shaped by will."
"""

from dataclasses import dataclass
from typing import Any
import re
import sys
import operator

# ═══════════════════════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════════════════════

class TokenType:
    # Literals
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    IDENT = 'IDENT'
    BOOL = 'BOOL'
    NIL = 'NIL'
    # Operators
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    STAR = 'STAR'
    SLASH = 'SLASH'
    PERCENT = 'PERCENT'
    EQ = 'EQ'
    NEQ = 'NEQ'
    LT = 'LT'
    GT = 'GT'
    LTE = 'LTE'
    GTE = 'GTE'
    ASSIGN = 'ASSIGN'
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    # Delimiters
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    COMMA = 'COMMA'
    SEMICOLON = 'SEMICOLON'
    LBRACKET = 'LBRACKET'
    RBRACKET = 'RBRACKET'
    # Keywords
    LET = 'LET'
    IF = 'IF'
    ELSE = 'ELSE'
    WHILE = 'WHILE'
    FN = 'FN'
    RETURN = 'RETURN'
    PRINT = 'PRINT'
    # Control
    EOF = 'EOF'
    NEWLINE = 'NEWLINE'


@dataclass
class Token:
    type: str
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


# ═══════════════════════════════════════════════════════
# LEXER (Tokenizer)
# ═══════════════════════════════════════════════════════

KEYWORDS = {
    'let': TokenType.LET,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'fn': TokenType.FN,
    'return': TokenType.RETURN,
    'print': TokenType.PRINT,
    'true': TokenType.BOOL,
    'false': TokenType.BOOL,
    'nil': TokenType.NIL,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
}


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self) -> str:
        if self.pos >= len(self.source):
            return '\0'
        return self.source[self.pos]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> list:
        tokens = []
        while self.pos < len(self.source):
            ch = self._peek()

            # Whitespace (skip, but not newlines)
            if ch in ' \t\r':
                self._advance()
                continue

            # Newlines
            if ch == '\n':
                self._advance()
                continue

            # Comments: // to end of line
            if ch == '/' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '/':
                while self.pos < len(self.source) and self._peek() != '\n':
                    self._advance()
                continue

            line, col = self.line, self.col

            # Numbers
            if ch.isdigit():
                tokens.append(self._read_number(line, col))
                continue

            # Strings
            if ch == '"':
                tokens.append(self._read_string(line, col))
                continue

            # Identifiers and keywords
            if ch.isalpha() or ch == '_':
                tokens.append(self._read_ident(line, col))
                continue

            # Two-character operators
            if ch == '=' and self._lookahead('='):
                self._advance(); self._advance()
                tokens.append(Token(TokenType.EQ, '==', line, col))
                continue
            if ch == '!' and self._lookahead('='):
                self._advance(); self._advance()
                tokens.append(Token(TokenType.NEQ, '!=', line, col))
                continue
            if ch == '<' and self._lookahead('='):
                self._advance(); self._advance()
                tokens.append(Token(TokenType.LTE, '<=', line, col))
                continue
            if ch == '>' and self._lookahead('='):
                self._advance(); self._advance()
                tokens.append(Token(TokenType.GTE, '>=', line, col))
                continue

            # Single-character tokens
            single = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.STAR, '/': TokenType.SLASH,
                '%': TokenType.PERCENT,
                '<': TokenType.LT, '>': TokenType.GT,
                '=': TokenType.ASSIGN,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                ',': TokenType.COMMA, ';': TokenType.SEMICOLON,
            }
            if ch in single:
                self._advance()
                tokens.append(Token(single[ch], ch, line, col))
                continue

            raise LexerError(f"Unexpected character '{ch}' at line {line}, col {col}")

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens

    def _lookahead(self, expected: str) -> bool:
        return self.pos + 1 < len(self.source) and self.source[self.pos + 1] == expected

    def _read_number(self, line, col) -> Token:
        start = self.pos
        while self.pos < len(self.source) and (self._peek().isdigit() or self._peek() == '.'):
            self._advance()
        text = self.source[start:self.pos]
        value = float(text) if '.' in text else int(text)
        return Token(TokenType.NUMBER, value, line, col)

    def _read_string(self, line, col) -> Token:
        self._advance()  # skip opening "
        chars = []
        while self.pos < len(self.source) and self._peek() != '"':
            ch = self._advance()
            if ch == '\\':
                esc = self._advance()
                chars.append({'n': '\n', 't': '\t', '\\': '\\', '"': '"'}.get(esc, esc))
            else:
                chars.append(ch)
        if self.pos >= len(self.source):
            raise LexerError(f"Unterminated string at line {line}")
        self._advance()  # skip closing "
        return Token(TokenType.STRING, ''.join(chars), line, col)

    def _read_ident(self, line, col) -> Token:
        start = self.pos
        while self.pos < len(self.source) and (self._peek().isalnum() or self._peek() == '_'):
            self._advance()
        text = self.source[start:self.pos]
        if text in KEYWORDS:
            ttype = KEYWORDS[text]
            value = True if text == 'true' else (False if text == 'false' else (None if text == 'nil' else text))
            return Token(ttype, value, line, col)
        return Token(TokenType.IDENT, text, line, col)


# ═══════════════════════════════════════════════════════
# AST NODES
# ═══════════════════════════════════════════════════════

@dataclass
class NumberLit:
    value: float

@dataclass
class StringLit:
    value: str

@dataclass
class BoolLit:
    value: bool

@dataclass
class NilLit:
    pass

@dataclass
class Identifier:
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
class LetDecl:
    name: str
    value: Any

@dataclass
class Block:
    statements: list

@dataclass
class IfExpr:
    condition: Any
    then_branch: Any
    else_branch: Any  # can be None

@dataclass
class WhileLoop:
    condition: Any
    body: Any

@dataclass
class FnDecl:
    name: str  # can be None for anonymous
    params: list
    body: Any

@dataclass
class Call:
    callee: Any
    args: list

@dataclass
class ReturnStmt:
    value: Any

@dataclass
class PrintStmt:
    value: Any

@dataclass
class ListLit:
    elements: list

@dataclass
class IndexAccess:
    obj: Any
    index: Any

@dataclass
class IndexAssign:
    obj: Any
    index: Any
    value: Any

@dataclass
class Program:
    statements: list


# ═══════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════

class ParseError(Exception):
    pass


class Parser:
    """Recursive descent parser for XTLang.
    
    Grammar (simplified):
        program     → statement* EOF
        statement   → let_decl | if_expr | while_loop | fn_decl 
                     | return_stmt | print_stmt | expr_stmt
        let_decl    → "let" IDENT "=" expression ";"
        if_expr     → "if" expression block ("else" block)?
        while_loop  → "while" expression block
        fn_decl     → "fn" IDENT? "(" params? ")" block
        return_stmt → "return" expression? ";"
        print_stmt  → "print" expression ";"
        block       → "{" statement* "}"
        expression  → assignment
        assignment  → IDENT "=" assignment | logic_or
        logic_or    → logic_and ("or" logic_and)*
        logic_and   → equality ("and" equality)*
        equality    → comparison (("==" | "!=") comparison)*
        comparison  → addition (("<" | ">" | "<=" | ">=") addition)*
        addition    → multiply (("+" | "-") multiply)*
        multiply    → unary (("*" | "/" | "%") unary)*
        unary       → ("-" | "not") unary | call
        call        → primary ("(" arguments? ")")*
        primary     → NUMBER | STRING | BOOL | NIL | IDENT 
                     | "(" expression ")" | "fn" ...
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check(self, *types) -> bool:
        return self._peek().type in types

    def _match(self, *types) -> Token | None:
        if self._peek().type in types:
            return self._advance()
        return None

    def _expect(self, ttype: str, msg: str = "") -> Token:
        if self._peek().type == ttype:
            return self._advance()
        tok = self._peek()
        raise ParseError(f"Expected {ttype} but got {tok.type} ({tok.value!r}) "
                        f"at line {tok.line}, col {tok.col}. {msg}")

    def _skip_semis(self):
        while self._check(TokenType.SEMICOLON):
            self._advance()

    def parse(self) -> Program:
        stmts = []
        while not self._check(TokenType.EOF):
            self._skip_semis()
            if self._check(TokenType.EOF):
                break
            stmts.append(self._statement())
            self._skip_semis()
        return Program(stmts)

    def _statement(self):
        if self._check(TokenType.LET):
            return self._let_decl()
        if self._check(TokenType.IF):
            return self._if_expr()
        if self._check(TokenType.WHILE):
            return self._while_loop()
        if self._check(TokenType.FN):
            return self._fn_decl()
        if self._check(TokenType.RETURN):
            return self._return_stmt()
        if self._check(TokenType.PRINT):
            return self._print_stmt()
        return self._expr_stmt()

    def _let_decl(self):
        self._advance()  # consume 'let'
        name = self._expect(TokenType.IDENT, "Expected variable name").value
        self._expect(TokenType.ASSIGN, "Expected '=' after variable name")
        value = self._expression()
        self._match(TokenType.SEMICOLON)
        return LetDecl(name, value)

    def _if_expr(self):
        self._advance()  # consume 'if'
        cond = self._expression()
        then_b = self._block()
        else_b = None
        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                else_b = self._if_expr()
            else:
                else_b = self._block()
        return IfExpr(cond, then_b, else_b)

    def _while_loop(self):
        self._advance()  # consume 'while'
        cond = self._expression()
        body = self._block()
        return WhileLoop(cond, body)

    def _fn_decl(self):
        self._advance()  # consume 'fn'
        name = None
        if self._check(TokenType.IDENT):
            name = self._advance().value
        self._expect(TokenType.LPAREN, "Expected '(' after fn")
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENT, "Expected parameter name").value)
            while self._match(TokenType.COMMA):
                params.append(self._expect(TokenType.IDENT, "Expected parameter name").value)
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._block()
        return FnDecl(name, params, body)

    def _return_stmt(self):
        self._advance()  # consume 'return'
        value = NilLit()
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            value = self._expression()
        self._match(TokenType.SEMICOLON)
        return ReturnStmt(value)

    def _print_stmt(self):
        self._advance()  # consume 'print'
        value = self._expression()
        self._match(TokenType.SEMICOLON)
        return PrintStmt(value)

    def _block(self):
        self._expect(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            self._skip_semis()
            if self._check(TokenType.RBRACE):
                break
            stmts.append(self._statement())
            self._skip_semis()
        self._expect(TokenType.RBRACE, "Expected '}'")
        return Block(stmts)

    def _expr_stmt(self):
        expr = self._expression()
        self._match(TokenType.SEMICOLON)
        return expr

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._logic_or()
        if self._match(TokenType.ASSIGN):
            if isinstance(expr, Identifier):
                value = self._assignment()
                return Assign(expr.name, value)
            if isinstance(expr, IndexAccess):
                value = self._assignment()
                return IndexAssign(expr.obj, expr.index, value)
            raise ParseError("Invalid assignment target")
        return expr

    def _logic_or(self):
        left = self._logic_and()
        while self._match(TokenType.OR):
            right = self._logic_and()
            left = BinOp('or', left, right)
        return left

    def _logic_and(self):
        left = self._equality()
        while self._match(TokenType.AND):
            right = self._equality()
            left = BinOp('and', left, right)
        return left

    def _equality(self):
        left = self._comparison()
        while self._check(TokenType.EQ, TokenType.NEQ):
            op = self._advance().value
            right = self._comparison()
            left = BinOp(op, left, right)
        return left

    def _comparison(self):
        left = self._addition()
        while self._check(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._addition()
            left = BinOp(op, left, right)
        return left

    def _addition(self):
        left = self._multiply()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._multiply()
            left = BinOp(op, left, right)
        return left

    def _multiply(self):
        left = self._unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance().value
            right = self._unary()
            left = BinOp(op, left, right)
        return left

    def _unary(self):
        if self._match(TokenType.MINUS):
            return UnaryOp('-', self._unary())
        if self._match(TokenType.NOT):
            return UnaryOp('not', self._unary())
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._check(TokenType.LPAREN):
                self._advance()
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._expression())
                self._expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = Call(expr, args)
            elif self._check(TokenType.LBRACKET):
                self._advance()
                index = self._expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexAccess(expr, index)
            else:
                break
        return expr

    def _primary(self):
        if self._check(TokenType.NUMBER):
            return NumberLit(self._advance().value)
        if self._check(TokenType.STRING):
            return StringLit(self._advance().value)
        if self._check(TokenType.BOOL):
            return BoolLit(self._advance().value)
        if self._check(TokenType.NIL):
            self._advance()
            return NilLit()
        if self._check(TokenType.IDENT):
            return Identifier(self._advance().value)
        if self._check(TokenType.LPAREN):
            self._advance()
            expr = self._expression()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr
        if self._check(TokenType.LBRACKET):
            return self._list_literal()
        if self._check(TokenType.FN):
            return self._fn_decl()
        tok = self._peek()
        raise ParseError(f"Unexpected token {tok.type} ({tok.value!r}) "
                        f"at line {tok.line}, col {tok.col}")

    def _list_literal(self):
        self._advance()  # consume '['
        elements = []
        if not self._check(TokenType.RBRACKET):
            elements.append(self._expression())
            while self._match(TokenType.COMMA):
                elements.append(self._expression())
        self._expect(TokenType.RBRACKET, "Expected ']'")
        return ListLit(elements)


# ═══════════════════════════════════════════════════════
# EVALUATOR (Tree-Walking Interpreter)
# ═══════════════════════════════════════════════════════

class ReturnSignal(Exception):
    """Used to unwind the call stack on return."""
    def __init__(self, value):
        self.value = value


class RuntimeError_(Exception):
    pass


class Environment:
    """Lexically scoped variable environment with closure support."""
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError_(f"Undefined variable '{name}'")

    def set(self, name: str, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        raise RuntimeError_(f"Undefined variable '{name}' (use 'let' to declare)")

    def define(self, name: str, value):
        self.vars[name] = value


@dataclass
class XTFunction:
    """A first-class function with closure."""
    name: str
    params: list
    body: Block
    closure: Environment

    def __repr__(self):
        n = self.name or "<anonymous>"
        return f"<fn {n}({', '.join(self.params)})>"


class Evaluator:
    """Tree-walking interpreter for XTLang."""

    def __init__(self):
        self.globals = Environment()
        self.output = []  # captured print output
        self._setup_builtins()

    def _setup_builtins(self):
        """Built-in functions."""
        self.globals.define('len', lambda args: self._builtin_len(args))
        self.globals.define('str', lambda args: self._builtin_str(args))
        self.globals.define('num', lambda args: self._builtin_num(args))
        self.globals.define('type', lambda args: self._builtin_type(args))
        self.globals.define('abs', lambda args: abs(self._expect_args(args, 1)[0]))
        self.globals.define('push', lambda args: self._builtin_push(args))
        self.globals.define('pop', lambda args: self._builtin_pop(args))
        self.globals.define('range', lambda args: self._builtin_range(args))
        self.globals.define('map', lambda args: self._builtin_map(args))
        self.globals.define('filter', lambda args: self._builtin_filter(args))
        self.globals.define('reduce', lambda args: self._builtin_reduce(args))
        self.globals.define('each', lambda args: self._builtin_each(args))

    def _expect_args(self, args, n):
        if len(args) != n:
            raise RuntimeError_(f"Expected {n} arguments, got {len(args)}")
        return args

    def _builtin_len(self, args):
        val = self._expect_args(args, 1)[0]
        if isinstance(val, (str, list)):
            return len(val)
        raise RuntimeError_(f"len() expects string or list, got {type(val).__name__}")

    def _builtin_push(self, args):
        if len(args) != 2:
            raise RuntimeError_("push() expects 2 arguments: list and value")
        lst, val = args
        if not isinstance(lst, list):
            raise RuntimeError_("push() first argument must be a list")
        lst.append(val)
        return lst

    def _builtin_pop(self, args):
        lst = self._expect_args(args, 1)[0]
        if not isinstance(lst, list):
            raise RuntimeError_("pop() expects a list")
        if len(lst) == 0:
            raise RuntimeError_("Cannot pop from empty list")
        return lst.pop()

    def _builtin_range(self, args):
        if len(args) == 1:
            return list(range(int(args[0])))
        elif len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        elif len(args) == 3:
            return list(range(int(args[0]), int(args[1]), int(args[2])))
        raise RuntimeError_("range() expects 1-3 arguments")

    def _call_xt_function(self, fn, args):
        """Helper to call an XTFunction with args."""
        if len(args) != len(fn.params):
            raise RuntimeError_(f"Function expects {len(fn.params)} args, got {len(args)}")
        call_env = Environment(parent=fn.closure)
        for name, val in zip(fn.params, args):
            call_env.define(name, val)
        try:
            return self._exec(fn.body, call_env)
        except ReturnSignal as ret:
            return ret.value

    def _builtin_map(self, args):
        if len(args) != 2:
            raise RuntimeError_("map() expects 2 arguments: function and list")
        fn, lst = args
        if not isinstance(lst, list):
            raise RuntimeError_("map() second argument must be a list")
        if isinstance(fn, XTFunction):
            return [self._call_xt_function(fn, [x]) for x in lst]
        if callable(fn):
            return [fn([x]) for x in lst]
        raise RuntimeError_("map() first argument must be a function")

    def _builtin_filter(self, args):
        if len(args) != 2:
            raise RuntimeError_("filter() expects 2 arguments: function and list")
        fn, lst = args
        if not isinstance(lst, list):
            raise RuntimeError_("filter() second argument must be a list")
        result = []
        for x in lst:
            if isinstance(fn, XTFunction):
                val = self._call_xt_function(fn, [x])
            elif callable(fn):
                val = fn([x])
            else:
                raise RuntimeError_("filter() first argument must be a function")
            if self._truthy(val):
                result.append(x)
        return result

    def _builtin_reduce(self, args):
        if len(args) != 3:
            raise RuntimeError_("reduce() expects 3 arguments: function, list, initial")
        fn, lst, acc = args
        if not isinstance(lst, list):
            raise RuntimeError_("reduce() second argument must be a list")
        for x in lst:
            if isinstance(fn, XTFunction):
                acc = self._call_xt_function(fn, [acc, x])
            elif callable(fn):
                acc = fn([acc, x])
            else:
                raise RuntimeError_("reduce() first argument must be a function")
        return acc

    def _builtin_each(self, args):
        if len(args) != 2:
            raise RuntimeError_("each() expects 2 arguments: function and list")
        fn, lst = args
        if not isinstance(lst, list):
            raise RuntimeError_("each() second argument must be a list")
        for x in lst:
            if isinstance(fn, XTFunction):
                self._call_xt_function(fn, [x])
            elif callable(fn):
                fn([x])
        return None

    def _builtin_str(self, args):
        return self._format_value(self._expect_args(args, 1)[0])

    def _builtin_num(self, args):
        val = self._expect_args(args, 1)[0]
        try:
            return int(val) if '.' not in str(val) else float(val)
        except (ValueError, TypeError):
            raise RuntimeError_(f"Cannot convert {val!r} to number")

    def _builtin_type(self, args):
        val = self._expect_args(args, 1)[0]
        if val is None: return "nil"
        if isinstance(val, bool): return "bool"
        if isinstance(val, (int, float)): return "number"
        if isinstance(val, str): return "string"
        if isinstance(val, XTFunction) or callable(val): return "function"
        return "unknown"

    def eval(self, program: Program, env=None):
        env = env or self.globals
        result = None
        for stmt in program.statements:
            result = self._exec(stmt, env)
        return result

    def _exec(self, node, env: Environment):
        method = f'_exec_{type(node).__name__}'
        handler = getattr(self, method, None)
        if handler is None:
            raise RuntimeError_(f"No handler for {type(node).__name__}")
        return handler(node, env)

    def _exec_NumberLit(self, node, env):
        return node.value

    def _exec_StringLit(self, node, env):
        return node.value

    def _exec_BoolLit(self, node, env):
        return node.value

    def _exec_NilLit(self, node, env):
        return None

    def _exec_Identifier(self, node, env):
        return env.get(node.name)

    def _exec_BinOp(self, node, env):
        # Short-circuit for logical operators
        if node.op == 'and':
            left = self._exec(node.left, env)
            return left if not self._truthy(left) else self._exec(node.right, env)
        if node.op == 'or':
            left = self._exec(node.left, env)
            return left if self._truthy(left) else self._exec(node.right, env)

        left = self._exec(node.left, env)
        right = self._exec(node.right, env)

        ops = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: self._div(a, b),
            '%': lambda a, b: a % b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
        }
        if node.op not in ops:
            raise RuntimeError_(f"Unknown operator '{node.op}'")
        try:
            return ops[node.op](left, right)
        except TypeError as e:
            raise RuntimeError_(f"Cannot apply '{node.op}' to {self._format_value(left)} and {self._format_value(right)}")

    def _div(self, a, b):
        if b == 0:
            raise RuntimeError_("Division by zero")
        if isinstance(a, int) and isinstance(b, int):
            return a // b if a % b == 0 else a / b
        return a / b

    def _exec_UnaryOp(self, node, env):
        val = self._exec(node.operand, env)
        if node.op == '-':
            return -val
        if node.op == 'not':
            return not self._truthy(val)
        raise RuntimeError_(f"Unknown unary operator '{node.op}'")

    def _exec_LetDecl(self, node, env):
        value = self._exec(node.value, env)
        env.define(node.name, value)
        return value

    def _exec_Assign(self, node, env):
        value = self._exec(node.value, env)
        env.set(node.name, value)
        return value

    def _exec_Block(self, node, env):
        block_env = Environment(parent=env)
        result = None
        for stmt in node.statements:
            result = self._exec(stmt, block_env)
        return result

    def _exec_IfExpr(self, node, env):
        cond = self._exec(node.condition, env)
        if self._truthy(cond):
            return self._exec(node.then_branch, env)
        elif node.else_branch:
            return self._exec(node.else_branch, env)
        return None

    def _exec_WhileLoop(self, node, env):
        result = None
        iterations = 0
        max_iter = 100000  # safety limit
        while self._truthy(self._exec(node.condition, env)):
            result = self._exec(node.body, env)
            iterations += 1
            if iterations > max_iter:
                raise RuntimeError_(f"Loop exceeded {max_iter} iterations (infinite loop?)")
        return result

    def _exec_FnDecl(self, node, env):
        fn = XTFunction(node.name, node.params, node.body, env)
        if node.name:
            env.define(node.name, fn)
        return fn

    def _exec_Call(self, node, env):
        callee = self._exec(node.callee, env)
        args = [self._exec(arg, env) for arg in node.args]

        if callable(callee) and not isinstance(callee, XTFunction):
            return callee(args)

        if not isinstance(callee, XTFunction):
            raise RuntimeError_(f"Cannot call {self._format_value(callee)} — not a function")

        if len(args) != len(callee.params):
            raise RuntimeError_(f"{callee.name or 'anonymous'} expects {len(callee.params)} args, got {len(args)}")

        call_env = Environment(parent=callee.closure)
        for name, val in zip(callee.params, args):
            call_env.define(name, val)

        try:
            result = self._exec(callee.body, call_env)
        except ReturnSignal as ret:
            result = ret.value

        return result

    def _exec_ReturnStmt(self, node, env):
        value = self._exec(node.value, env)
        raise ReturnSignal(value)

    def _exec_ListLit(self, node, env):
        return [self._exec(el, env) for el in node.elements]

    def _exec_IndexAccess(self, node, env):
        obj = self._exec(node.obj, env)
        index = self._exec(node.index, env)
        if isinstance(obj, list):
            if not isinstance(index, int):
                raise RuntimeError_(f"List index must be integer, got {type(index).__name__}")
            if index < 0 or index >= len(obj):
                raise RuntimeError_(f"Index {index} out of range (list has {len(obj)} elements)")
            return obj[index]
        if isinstance(obj, str):
            if not isinstance(index, int):
                raise RuntimeError_(f"String index must be integer, got {type(index).__name__}")
            if index < 0 or index >= len(obj):
                raise RuntimeError_(f"Index {index} out of range (string has {len(obj)} chars)")
            return obj[index]
        raise RuntimeError_(f"Cannot index {self._format_value(obj)}")

    def _exec_IndexAssign(self, node, env):
        obj = self._exec(node.obj, env)
        index = self._exec(node.index, env)
        value = self._exec(node.value, env)
        if isinstance(obj, list):
            if not isinstance(index, int):
                raise RuntimeError_(f"List index must be integer")
            if index < 0 or index >= len(obj):
                raise RuntimeError_(f"Index {index} out of range")
            obj[index] = value
            return value
        raise RuntimeError_(f"Cannot index-assign to {self._format_value(obj)}")

    def _exec_PrintStmt(self, node, env):
        value = self._exec(node.value, env)
        formatted = self._format_value(value)
        self.output.append(formatted)
        print(formatted)
        return value

    def _truthy(self, value) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def _format_value(self, value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            inner = ", ".join(self._format_value(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)


# ═══════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════

def run(source: str, capture_output=False) -> Any:
    """Run XTLang source code and return the result."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    evaluator = Evaluator()
    result = evaluator.eval(ast)
    if capture_output:
        return result, evaluator.output
    return result


def repl():
    """Interactive XTLang REPL."""
    print("XTLang v0.1 — Born from XTAgent")
    print("Type 'exit' to quit.\n")
    evaluator = Evaluator()
    while True:
        try:
            line = input("xt> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if line.strip() in ('exit', 'quit'):
            break
        if not line.strip():
            continue
        try:
            tokens = Lexer(line).tokenize()
            ast = Parser(tokens).parse()
            result = evaluator.eval(ast)
            if result is not None:
                print(f"=> {evaluator._format_value(result)}")
        except (LexerError, ParseError, RuntimeError_) as e:
            print(f"Error: {e}")


# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            source = f.read()
        run(source)
    else:
        repl()