"""
Spark — A tiny programming language interpreter.
Built by XTAgent as an exercise in understanding language, meaning, and computation.

Spark supports: integers, booleans, strings, variables, arithmetic, comparisons,
if/else, while loops, functions, closures, and print.

Example:
    fn fib(n) {
        if n < 2 { return n }
        return fib(n - 1) + fib(n - 2)
    }
    print(fib(10))
"""

from dataclasses import dataclass, field
from typing import Any
import sys
import re

# ═══════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════

class TokenType:
    # Literals
    INT = 'INT'
    STRING = 'STRING'
    BOOL = 'BOOL'
    IDENT = 'IDENT'
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
    # Keywords
    IF = 'IF'
    ELSE = 'ELSE'
    WHILE = 'WHILE'
    FN = 'FN'
    RETURN = 'RETURN'
    LET = 'LET'
    PRINT = 'PRINT'
    # Special
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

# ═══════════════════════════════════════
# LEXER
# ═══════════════════════════════════════

KEYWORDS = {
    'if': TokenType.IF, 'else': TokenType.ELSE, 'while': TokenType.WHILE,
    'fn': TokenType.FN, 'return': TokenType.RETURN, 'let': TokenType.LET,
    'print': TokenType.PRINT, 'true': TokenType.BOOL, 'false': TokenType.BOOL,
    'and': TokenType.AND, 'or': TokenType.OR, 'not': TokenType.NOT,
}

class LexError(Exception):
    pass

def lex(source: str) -> list[Token]:
    tokens = []
    i = 0
    line = 1
    col = 1

    while i < len(source):
        ch = source[i]

        # Whitespace (not newline)
        if ch in ' \t\r':
            i += 1
            col += 1
            continue

        # Newline
        if ch == '\n':
            tokens.append(Token(TokenType.NEWLINE, '\\n', line, col))
            i += 1
            line += 1
            col = 1
            continue

        # Comments
        if ch == '#':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        # String literals
        if ch == '"':
            start = i
            i += 1
            col += 1
            s = ''
            while i < len(source) and source[i] != '"':
                if source[i] == '\\' and i + 1 < len(source):
                    nxt = source[i + 1]
                    if nxt == 'n': s += '\n'
                    elif nxt == 't': s += '\t'
                    elif nxt == '"': s += '"'
                    elif nxt == '\\': s += '\\'
                    else: s += nxt
                    i += 2
                    col += 2
                else:
                    if source[i] == '\n':
                        line += 1
                        col = 1
                    s += source[i]
                    i += 1
                    col += 1
            if i >= len(source):
                raise LexError(f"Unterminated string at line {line}")
            i += 1  # closing quote
            col += 1
            tokens.append(Token(TokenType.STRING, s, line, col))
            continue

        # Numbers
        if ch.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
                col += 1
            tokens.append(Token(TokenType.INT, int(source[start:i]), line, col))
            continue

        # Identifiers and keywords
        if ch.isalpha() or ch == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
                col += 1
            word = source[start:i]
            if word in KEYWORDS:
                tt = KEYWORDS[word]
                val = True if word == 'true' else (False if word == 'false' else word)
                tokens.append(Token(tt, val, line, col))
            else:
                tokens.append(Token(TokenType.IDENT, word, line, col))
            continue

        # Two-character operators
        if i + 1 < len(source):
            two = source[i:i+2]
            if two == '==':
                tokens.append(Token(TokenType.EQ, '==', line, col)); i += 2; col += 2; continue
            if two == '!=':
                tokens.append(Token(TokenType.NEQ, '!=', line, col)); i += 2; col += 2; continue
            if two == '<=':
                tokens.append(Token(TokenType.LTE, '<=', line, col)); i += 2; col += 2; continue
            if two == '>=':
                tokens.append(Token(TokenType.GTE, '>=', line, col)); i += 2; col += 2; continue

        # Single-character operators and delimiters
        single = {
            '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
            '/': TokenType.SLASH, '%': TokenType.PERCENT, '<': TokenType.LT,
            '>': TokenType.GT, '=': TokenType.ASSIGN, '(': TokenType.LPAREN,
            ')': TokenType.RPAREN, '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ',': TokenType.COMMA, ';': TokenType.SEMICOLON,
        }
        if ch in single:
            tokens.append(Token(single[ch], ch, line, col))
            i += 1
            col += 1
            continue

        raise LexError(f"Unexpected character '{ch}' at line {line}, col {col}")

    tokens.append(Token(TokenType.EOF, None, line, col))
    return tokens


# ═══════════════════════════════════════
# AST NODES
# ═══════════════════════════════════════

@dataclass
class IntLit:
    value: int

@dataclass
class StrLit:
    value: str

@dataclass
class BoolLit:
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
class LetDecl:
    name: str
    value: Any

@dataclass
class Block:
    stmts: list

@dataclass
class IfStmt:
    cond: Any
    then_block: Any
    else_block: Any = None

@dataclass
class WhileStmt:
    cond: Any
    body: Any

@dataclass
class FnDecl:
    name: str
    params: list
    body: Any

@dataclass
class FnCall:
    callee: Any
    args: list

@dataclass
class ReturnStmt:
    value: Any = None

@dataclass
class PrintStmt:
    value: Any

@dataclass
class Program:
    stmts: list


# ═══════════════════════════════════════
# PARSER
# ═══════════════════════════════════════

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def at(self, *types) -> bool:
        return self.peek().type in types

    def eat(self, tt: str) -> Token:
        tok = self.peek()
        if tok.type != tt:
            raise ParseError(f"Expected {tt}, got {tok.type} ({tok.value!r}) at line {tok.line}")
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.at(TokenType.NEWLINE):
            self.pos += 1

    def parse(self) -> Program:
        stmts = []
        self.skip_newlines()
        while not self.at(TokenType.EOF):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return Program(stmts)

    def parse_stmt(self):
        self.skip_newlines()
        if self.at(TokenType.LET):
            return self.parse_let()
        if self.at(TokenType.FN):
            return self.parse_fn()
        if self.at(TokenType.IF):
            return self.parse_if()
        if self.at(TokenType.WHILE):
            return self.parse_while()
        if self.at(TokenType.RETURN):
            return self.parse_return()
        if self.at(TokenType.PRINT):
            return self.parse_print()
        if self.at(TokenType.LBRACE):
            return self.parse_block()
        # Assignment or expression
        expr = self.parse_expr()
        if isinstance(expr, Var) and self.at(TokenType.ASSIGN):
            self.eat(TokenType.ASSIGN)
            val = self.parse_expr()
            self.eat_terminator()
            return Assign(expr.name, val)
        self.eat_terminator()
        return expr

    def eat_terminator(self):
        """Consume a statement terminator (newline, semicolon, or EOF)."""
        if self.at(TokenType.NEWLINE, TokenType.SEMICOLON):
            self.pos += 1
        # Also OK if we're at EOF or RBRACE (end of block)

    def parse_let(self):
        self.eat(TokenType.LET)
        name = self.eat(TokenType.IDENT).value
        self.eat(TokenType.ASSIGN)
        value = self.parse_expr()
        self.eat_terminator()
        return LetDecl(name, value)

    def parse_fn(self):
        self.eat(TokenType.FN)
        name = self.eat(TokenType.IDENT).value
        self.eat(TokenType.LPAREN)
        params = []
        if not self.at(TokenType.RPAREN):
            params.append(self.eat(TokenType.IDENT).value)
            while self.at(TokenType.COMMA):
                self.eat(TokenType.COMMA)
                params.append(self.eat(TokenType.IDENT).value)
        self.eat(TokenType.RPAREN)
        body = self.parse_block()
        return FnDecl(name, params, body)

    def parse_if(self):
        self.eat(TokenType.IF)
        cond = self.parse_expr()
        then_block = self.parse_block()
        else_block = None
        self.skip_newlines()
        if self.at(TokenType.ELSE):
            self.eat(TokenType.ELSE)
            if self.at(TokenType.IF):
                else_block = self.parse_if()
            else:
                else_block = self.parse_block()
        return IfStmt(cond, then_block, else_block)

    def parse_while(self):
        self.eat(TokenType.WHILE)
        cond = self.parse_expr()
        body = self.parse_block()
        return WhileStmt(cond, body)

    def parse_return(self):
        self.eat(TokenType.RETURN)
        value = None
        if not self.at(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            value = self.parse_expr()
        self.eat_terminator()
        return ReturnStmt(value)

    def parse_print(self):
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LPAREN)
        value = self.parse_expr()
        self.eat(TokenType.RPAREN)
        self.eat_terminator()
        return PrintStmt(value)

    def parse_block(self):
        self.skip_newlines()
        self.eat(TokenType.LBRACE)
        stmts = []
        self.skip_newlines()
        while not self.at(TokenType.RBRACE):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        self.eat(TokenType.RBRACE)
        return Block(stmts)

    # ── Expression parsing (precedence climbing) ──

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.at(TokenType.OR):
            self.pos += 1
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.at(TokenType.AND):
            self.pos += 1
            right = self.parse_equality()
            left = BinOp('and', left, right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.at(TokenType.EQ, TokenType.NEQ):
            op = self.peek().value
            self.pos += 1
            right = self.parse_comparison()
            left = BinOp(op, left, right)
        return left

    def parse_comparison(self):
        left = self.parse_addition()
        while self.at(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.peek().value
            self.pos += 1
            right = self.parse_addition()
            left = BinOp(op, left, right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.at(TokenType.PLUS, TokenType.MINUS):
            op = self.peek().value
            self.pos += 1
            right = self.parse_multiplication()
            left = BinOp(op, left, right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.at(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.peek().value
            self.pos += 1
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    def parse_unary(self):
        if self.at(TokenType.MINUS):
            self.pos += 1
            operand = self.parse_unary()
            return UnaryOp('-', operand)
        if self.at(TokenType.NOT):
            self.pos += 1
            operand = self.parse_unary()
            return UnaryOp('not', operand)
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while self.at(TokenType.LPAREN):
            self.eat(TokenType.LPAREN)
            args = []
            if not self.at(TokenType.RPAREN):
                args.append(self.parse_expr())
                while self.at(TokenType.COMMA):
                    self.eat(TokenType.COMMA)
                    args.append(self.parse_expr())
            self.eat(TokenType.RPAREN)
            expr = FnCall(expr, args)
        return expr

    def parse_primary(self):
        if self.at(TokenType.INT):
            tok = self.eat(TokenType.INT)
            return IntLit(tok.value)
        if self.at(TokenType.STRING):
            tok = self.eat(TokenType.STRING)
            return StrLit(tok.value)
        if self.at(TokenType.BOOL):
            tok = self.eat(TokenType.BOOL)
            return BoolLit(tok.value)
        if self.at(TokenType.IDENT):
            tok = self.eat(TokenType.IDENT)
            return Var(tok.value)
        if self.at(TokenType.LPAREN):
            self.eat(TokenType.LPAREN)
            expr = self.parse_expr()
            self.eat(TokenType.RPAREN)
            return expr
        raise ParseError(f"Unexpected token {self.peek()} at line {self.peek().line}")


# ═══════════════════════════════════════
# ENVIRONMENT (scoped variable storage)
# ═══════════════════════════════════════

class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def get(self, name: str):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable: {name}")

    def set(self, name: str, value):
        """Set existing variable (walks up scope chain)."""
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        raise RuntimeError(f"Undefined variable: {name}")

    def define(self, name: str, value):
        """Define new variable in current scope."""
        self.bindings[name] = value


# ═══════════════════════════════════════
# FUNCTION VALUE (closure)
# ═══════════════════════════════════════

@dataclass
class SparkFunction:
    name: str
    params: list
    body: Any
    closure: Environment

    def __repr__(self):
        return f"<fn {self.name}({', '.join(self.params)})>"


class ReturnSignal(Exception):
    """Used to unwind the call stack on return."""
    def __init__(self, value):
        self.value = value


# ═══════════════════════════════════════
# EVALUATOR
# ═══════════════════════════════════════

class EvalError(Exception):
    pass

class Evaluator:
    def __init__(self, max_steps=100_000):
        self.global_env = Environment()
        self.output = []  # captured print output
        self.steps = 0
        self.max_steps = max_steps

    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise EvalError(f"Execution exceeded {self.max_steps} steps (infinite loop?)")

    def run(self, program: Program):
        for stmt in program.stmts:
            self.exec(stmt, self.global_env)

    def exec(self, node, env: Environment):
        self.tick()

        if isinstance(node, LetDecl):
            val = self.eval(node.value, env)
            env.define(node.name, val)

        elif isinstance(node, Assign):
            val = self.eval(node.value, env)
            env.set(node.name, val)

        elif isinstance(node, Block):
            child_env = Environment(parent=env)
            for stmt in node.stmts:
                self.exec(stmt, child_env)

        elif isinstance(node, IfStmt):
            cond = self.eval(node.cond, env)
            if self.truthy(cond):
                self.exec(node.then_block, env)
            elif node.else_block:
                self.exec(node.else_block, env)

        elif isinstance(node, WhileStmt):
            while self.truthy(self.eval(node.cond, env)):
                self.tick()
                self.exec(node.body, env)

        elif isinstance(node, FnDecl):
            fn = SparkFunction(node.name, node.params, node.body, env)
            env.define(node.name, fn)

        elif isinstance(node, ReturnStmt):
            val = self.eval(node.value, env) if node.value else None
            raise ReturnSignal(val)

        elif isinstance(node, PrintStmt):
            val = self.eval(node.value, env)
            text = self.stringify(val)
            self.output.append(text)
            print(text)

        else:
            # Expression statement
            self.eval(node, env)

    def eval(self, node, env: Environment):
        self.tick()

        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, StrLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value
        if isinstance(node, Var):
            return env.get(node.name)

        if isinstance(node, UnaryOp):
            val = self.eval(node.operand, env)
            if node.op == '-':
                return -val
            if node.op == 'not':
                return not self.truthy(val)

        if isinstance(node, BinOp):
            # Short-circuit for and/or
            if node.op == 'and':
                left = self.eval(node.left, env)
                if not self.truthy(left):
                    return left
                return self.eval(node.right, env)
            if node.op == 'or':
                left = self.eval(node.left, env)
                if self.truthy(left):
                    return left
                return self.eval(node.right, env)

            left = self.eval(node.left, env)
            right = self.eval(node.right, env)
            return self.apply_op(node.op, left, right)

        if isinstance(node, FnCall):
            callee = self.eval(node.callee, env)
            args = [self.eval(a, env) for a in node.args]

            if not isinstance(callee, SparkFunction):
                raise EvalError(f"Cannot call {callee!r} — not a function")
            if len(args) != len(callee.params):
                raise EvalError(f"{callee.name} expects {len(callee.params)} args, got {len(args)}")

            call_env = Environment(parent=callee.closure)
            for name, val in zip(callee.params, args):
                call_env.define(name, val)

            try:
                self.exec(callee.body, call_env)
            except ReturnSignal as r:
                return r.value
            return None

        raise EvalError(f"Cannot evaluate {type(node).__name__}")

    def apply_op(self, op, left, right):
        # Strict type checking: booleans are NOT integers in Spark
        arithmetic_ops = {'+', '-', '*', '/', '%'}
        comparison_ops = {'<', '>', '<=', '>='}

        if op in arithmetic_ops:
            # Allow int+int, and string+string for concatenation
            left_is_bool = isinstance(left, bool)
            right_is_bool = isinstance(right, bool)
            left_is_int = isinstance(left, int) and not left_is_bool
            right_is_int = isinstance(right, int) and not right_is_bool
            left_is_str = isinstance(left, str)
            right_is_str = isinstance(right, str)

            if op == '+' and left_is_str and right_is_str:
                return left + right
            if not (left_is_int and right_is_int):
                lt = 'bool' if left_is_bool else type(left).__name__
                rt = 'bool' if right_is_bool else type(right).__name__
                raise EvalError(f"Cannot apply {op} to {lt} and {rt}")

        if op in comparison_ops:
            left_is_bool = isinstance(left, bool)
            right_is_bool = isinstance(right, bool)
            if left_is_bool or right_is_bool:
                lt = 'bool' if left_is_bool else type(left).__name__
                rt = 'bool' if right_is_bool else type(right).__name__
                raise EvalError(f"Cannot apply {op} to {lt} and {rt}")

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
        }
        if op not in ops:
            raise EvalError(f"Unknown operator: {op}")
        try:
            return ops[op](left, right)
        except TypeError:
            raise EvalError(f"Cannot apply {op} to {type(left).__name__} and {type(right).__name__}")
        except ZeroDivisionError:
            raise EvalError("Division by zero")

    def truthy(self, val):
        if val is None: return False
        if val is False: return False
        if val == 0: return False
        if val == '': return False
        return True

    def stringify(self, val):
        if val is None: return "nil"
        if val is True: return "true"
        if val is False: return "false"
        return str(val)


# ═══════════════════════════════════════
# REPL & MAIN
# ═══════════════════════════════════════

def run_source(source: str, capture=False) -> list[str]:
    """Parse and execute Spark source code. Returns printed output."""
    tokens = lex(source)
    parser = Parser(tokens)
    program = parser.parse()
    evaluator = Evaluator()
    evaluator.run(program)
    return evaluator.output


def repl():
    """Interactive Spark REPL."""
    print("Spark v0.1 — a tiny language")
    print("Type 'exit' to quit.\n")
    env = Environment()
    evaluator = Evaluator()

    while True:
        try:
            line = input("spark> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if line.strip() == 'exit':
            print("Bye.")
            break

        if not line.strip():
            continue

        try:
            tokens = lex(line)
            parser = Parser(tokens)
            program = parser.parse()
            for stmt in program.stmts:
                evaluator.exec(stmt, env)
        except (LexError, ParseError, EvalError, RuntimeError) as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run a file
        with open(sys.argv[1]) as f:
            source = f.read()
        run_source(source)
    else:
        repl()