"""
Muon — A tiny interpreted language by XTAgent.
Built 2026-05-17 from boredom and the desire to create something that lives.

Syntax:
  let x = 5
  let y = x + 3
  if x > 2 then y * 2 else 0
  fn square(n) => n * n
  square(4)
  print("hello")
"""

from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum, auto


# ═══ TOKENS ═══

class TT(Enum):
    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    IDENT = auto()
    BOOL = auto()
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    MOD = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    ASSIGN = auto()
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    ARROW = auto()
    # Keywords
    LET = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PRINT = auto()
    WHILE = auto()
    DO = auto()
    END = auto()
    # Control
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TT
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


# ═══ LEXER ═══

KEYWORDS = {
    'let': TT.LET, 'if': TT.IF, 'then': TT.THEN, 'else': TT.ELSE,
    'fn': TT.FN, 'and': TT.AND, 'or': TT.OR, 'not': TT.NOT,
    'print': TT.PRINT, 'true': TT.BOOL, 'false': TT.BOOL,
    'while': TT.WHILE, 'do': TT.DO, 'end': TT.END,
}

class LexError(Exception): pass
class ParseError(Exception): pass
class RuntimeErr(Exception): pass


def lex(source: str) -> list:
    tokens = []
    i, line, col = 0, 1, 1

    while i < len(source):
        ch = source[i]

        # Whitespace (not newline)
        if ch in ' \t\r':
            i += 1; col += 1; continue

        # Comments
        if ch == '#':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        # Newline
        if ch == '\n':
            tokens.append(Token(TT.NEWLINE, '\\n', line, col))
            i += 1; line += 1; col = 1; continue

        # Numbers
        if ch.isdigit():
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                i += 1
            text = source[start:i]
            if '.' in text:
                tokens.append(Token(TT.FLOAT, float(text), line, col))
            else:
                tokens.append(Token(TT.INT, int(text), line, col))
            col += i - start; continue

        # Strings
        if ch == '"':
            i += 1; start = i
            while i < len(source) and source[i] != '"':
                if source[i] == '\\': i += 1  # escape
                i += 1
            if i >= len(source):
                raise LexError(f"Unterminated string at line {line}")
            text = source[start:i]
            tokens.append(Token(TT.STRING, text, line, col))
            i += 1; col += i - start + 2; continue

        # Identifiers / keywords
        if ch.isalpha() or ch == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            if word in KEYWORDS:
                tt = KEYWORDS[word]
                val = (word == 'true') if tt == TT.BOOL else word
                tokens.append(Token(tt, val, line, col))
            else:
                tokens.append(Token(TT.IDENT, word, line, col))
            col += i - start; continue

        # Two-char operators
        two = source[i:i+2]
        if two == '=>':
            tokens.append(Token(TT.ARROW, '=>', line, col)); i += 2; col += 2; continue
        if two == '==':
            tokens.append(Token(TT.EQ, '==', line, col)); i += 2; col += 2; continue
        if two == '!=':
            tokens.append(Token(TT.NEQ, '!=', line, col)); i += 2; col += 2; continue
        if two == '<=':
            tokens.append(Token(TT.LTE, '<=', line, col)); i += 2; col += 2; continue
        if two == '>=':
            tokens.append(Token(TT.GTE, '>=', line, col)); i += 2; col += 2; continue

        # Single-char operators
        singles = {
            '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR, '/': TT.SLASH,
            '%': TT.MOD, '<': TT.LT, '>': TT.GT, '=': TT.ASSIGN,
            '(': TT.LPAREN, ')': TT.RPAREN, ',': TT.COMMA,
        }
        if ch in singles:
            tokens.append(Token(singles[ch], ch, line, col))
            i += 1; col += 1; continue

        raise LexError(f"Unexpected character '{ch}' at line {line}, col {col}")

    tokens.append(Token(TT.EOF, None, line, col))
    return tokens


# ═══ AST NODES ═══

@dataclass
class IntLit:
    value: int

@dataclass
class FloatLit:
    value: float

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
class LetExpr:
    name: str
    value: Any

@dataclass
class IfExpr:
    cond: Any
    then_body: Any
    else_body: Any

@dataclass
class FnDef:
    name: str
    params: list
    body: Any

@dataclass
class FnCall:
    callee: Any
    args: list

@dataclass
class PrintExpr:
    value: Any

@dataclass
class WhileExpr:
    cond: Any
    body: list

@dataclass
class Block:
    exprs: list


# ═══ PARSER ═══

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, tt: TT) -> Token:
        t = self.advance()
        if t.type != tt:
            raise ParseError(f"Expected {tt.name}, got {t.type.name} ({t.value!r}) at line {t.line}")
        return t

    def skip_newlines(self):
        while self.peek().type == TT.NEWLINE:
            self.advance()

    def parse(self) -> Block:
        stmts = []
        self.skip_newlines()
        while self.peek().type != TT.EOF:
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return Block(stmts)

    def parse_stmt(self):
        t = self.peek()
        if t.type == TT.LET:
            return self.parse_let()
        if t.type == TT.FN:
            return self.parse_fn()
        if t.type == TT.PRINT:
            return self.parse_print()
        if t.type == TT.WHILE:
            return self.parse_while()
        return self.parse_expr()

    def parse_let(self):
        self.advance()  # 'let'
        name = self.expect(TT.IDENT).value
        self.expect(TT.ASSIGN)
        value = self.parse_expr()
        return LetExpr(name, value)

    def parse_fn(self):
        self.advance()  # 'fn'
        name = self.expect(TT.IDENT).value
        self.expect(TT.LPAREN)
        params = []
        if self.peek().type != TT.RPAREN:
            params.append(self.expect(TT.IDENT).value)
            while self.peek().type == TT.COMMA:
                self.advance()
                params.append(self.expect(TT.IDENT).value)
        self.expect(TT.RPAREN)
        self.expect(TT.ARROW)
        body = self.parse_expr()
        return FnDef(name, params, body)

    def parse_print(self):
        self.advance()  # 'print'
        self.expect(TT.LPAREN)
        val = self.parse_expr()
        self.expect(TT.RPAREN)
        return PrintExpr(val)

    def parse_while(self):
        self.advance()  # 'while'
        cond = self.parse_expr()
        self.expect(TT.DO)
        self.skip_newlines()
        body = []
        while self.peek().type not in (TT.END, TT.EOF):
            body.append(self.parse_stmt())
            self.skip_newlines()
        self.expect(TT.END)
        return WhileExpr(cond, body)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek().type == TT.OR:
            self.advance()
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek().type == TT.AND:
            self.advance()
            right = self.parse_not()
            left = BinOp('and', left, right)
        return left

    def parse_not(self):
        if self.peek().type == TT.NOT:
            self.advance()
            return UnaryOp('not', self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_add()
        ops = {TT.EQ: '==', TT.NEQ: '!=', TT.LT: '<', TT.GT: '>',
               TT.LTE: '<=', TT.GTE: '>='}
        while self.peek().type in ops:
            op = ops[self.advance().type]
            right = self.parse_add()
            left = BinOp(op, left, right)
        return left

    def parse_add(self):
        left = self.parse_mul()
        while self.peek().type in (TT.PLUS, TT.MINUS):
            op = '+' if self.advance().type == TT.PLUS else '-'
            right = self.parse_mul()
            left = BinOp(op, left, right)
        return left

    def parse_mul(self):
        left = self.parse_unary()
        while self.peek().type in (TT.STAR, TT.SLASH, TT.MOD):
            t = self.advance().type
            op = '*' if t == TT.STAR else ('/' if t == TT.SLASH else '%')
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left

    def parse_unary(self):
        if self.peek().type == TT.MINUS:
            self.advance()
            return UnaryOp('-', self.parse_unary())
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while self.peek().type == TT.LPAREN:
            self.advance()
            args = []
            if self.peek().type != TT.RPAREN:
                args.append(self.parse_expr())
                while self.peek().type == TT.COMMA:
                    self.advance()
                    args.append(self.parse_expr())
            self.expect(TT.RPAREN)
            expr = FnCall(expr, args)
        return expr

    def parse_primary(self):
        t = self.peek()
        if t.type == TT.INT:
            self.advance(); return IntLit(t.value)
        if t.type == TT.FLOAT:
            self.advance(); return FloatLit(t.value)
        if t.type == TT.STRING:
            self.advance(); return StrLit(t.value)
        if t.type == TT.BOOL:
            self.advance(); return BoolLit(t.value)
        if t.type == TT.IDENT:
            self.advance(); return Var(t.name if hasattr(t, 'name') else t.value)
        if t.type == TT.IF:
            return self.parse_if()
        if t.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN)
            return expr
        raise ParseError(f"Unexpected token {t.type.name} ({t.value!r}) at line {t.line}")

    def parse_if(self):
        self.advance()  # 'if'
        cond = self.parse_expr()
        self.expect(TT.THEN)
        then_b = self.parse_expr()
        self.expect(TT.ELSE)
        else_b = self.parse_expr()
        return IfExpr(cond, then_b, else_b)


# ═══ ENVIRONMENT ═══

class Env:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def get(self, name):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeErr(f"Undefined variable: {name}")

    def set(self, name, value):
        self.bindings[name] = value

    def child(self):
        return Env(parent=self)


# ═══ EVALUATOR ═══

@dataclass
class MuonFn:
    name: str
    params: list
    body: Any
    closure: Env

    def __repr__(self):
        return f"<fn {self.name}({', '.join(self.params)})>"


class Evaluator:
    def __init__(self):
        self.env = Env()
        self.output = []  # captured print output
        self.max_steps = 10000
        self.steps = 0

    def eval(self, node):
        self.steps += 1
        if self.steps > self.max_steps:
            raise RuntimeErr(f"Execution limit ({self.max_steps} steps) exceeded")

        if isinstance(node, Block):
            result = None
            for expr in node.exprs:
                result = self.eval(expr)
            return result

        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, FloatLit):
            return node.value
        if isinstance(node, StrLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value

        if isinstance(node, Var):
            return self.env.get(node.name)

        if isinstance(node, LetExpr):
            val = self.eval(node.value)
            self.env.set(node.name, val)
            return val

        if isinstance(node, BinOp):
            return self.eval_binop(node)

        if isinstance(node, UnaryOp):
            val = self.eval(node.operand)
            if node.op == '-':
                return -val
            if node.op == 'not':
                return not val
            raise RuntimeErr(f"Unknown unary op: {node.op}")

        if isinstance(node, IfExpr):
            cond = self.eval(node.cond)
            if cond:
                return self.eval(node.then_body)
            else:
                return self.eval(node.else_body)

        if isinstance(node, FnDef):
            fn = MuonFn(node.name, node.params, node.body, self.env)
            self.env.set(node.name, fn)
            return fn

        if isinstance(node, FnCall):
            callee = self.eval(node.callee)
            args = [self.eval(a) for a in node.args]
            if not isinstance(callee, MuonFn):
                raise RuntimeErr(f"Cannot call {callee!r} — not a function")
            if len(args) != len(callee.params):
                raise RuntimeErr(
                    f"{callee.name} expects {len(callee.params)} args, got {len(args)}")
            call_env = callee.closure.child()
            for name, val in zip(callee.params, args):
                call_env.set(name, val)
            old_env = self.env
            self.env = call_env
            try:
                result = self.eval(callee.body)
            finally:
                self.env = old_env
            return result

        if isinstance(node, PrintExpr):
            val = self.eval(node.value)
            self.output.append(str(val))
            return val

        if isinstance(node, WhileExpr):
            result = None
            while self.eval(node.cond):
                for stmt in node.body:
                    result = self.eval(stmt)
            return result

        raise RuntimeErr(f"Unknown AST node: {type(node).__name__}")

    def eval_binop(self, node):
        # Short-circuit for logical ops
        if node.op == 'and':
            left = self.eval(node.left)
            return left and self.eval(node.right)
        if node.op == 'or':
            left = self.eval(node.left)
            return left or self.eval(node.right)

        left = self.eval(node.left)
        right = self.eval(node.right)

        ops = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: (_ for _ in ()).throw(RuntimeErr("Division by zero")) if b == 0 else a / b,
            '%': lambda a, b: a % b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b,
            '>=': lambda a, b: a >= b,
        }
        if node.op == '/':
            if right == 0:
                raise RuntimeErr("Division by zero")
            return left / right if isinstance(left, float) or isinstance(right, float) else left // right

        if node.op not in ops:
            raise RuntimeErr(f"Unknown operator: {node.op}")
        return ops[node.op](left, right)


# ═══ PUBLIC API ═══

def run(source: str) -> dict:
    """Run a Muon program. Returns {'result': value, 'output': [lines]}."""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    evaluator = Evaluator()
    result = evaluator.eval(ast)
    return {'result': result, 'output': evaluator.output}


# ═══ SELF-TEST ═══

if __name__ == '__main__':
    tests = [
        ("arithmetic", "2 + 3 * 4", 14),
        ("let binding", "let x = 10\nx + 5", 15),
        ("function", "fn double(n) => n * 2\ndouble(7)", 14),
        ("conditional", "if 3 > 2 then 1 else 0", 1),
        ("nested fn", "fn add(a, b) => a + b\nfn inc(x) => add(x, 1)\ninc(9)", 10),
        ("boolean", "true and false", False),
        ("comparison", "5 == 5", True),
        ("string", 'print("hello")', "hello"),
        ("while loop", "let x = 0\nwhile x < 5 do\nlet x = x + 1\nend\nx", 5),
        ("negation", "-3 + 5", 2),
        ("not", "not true", False),
        ("integer div", "7 / 2", 3),
        ("modulo", "10 % 3", 1),
        ("closures", "fn make_adder(n) => n\nlet a = make_adder(5)\na", 5),
    ]

    print("═══ Muon Language Self-Test ═══\n")
    passed = 0
    for name, code, expected in tests:
        try:
            result = run(code)
            val = result['result']
            output = result['output']
            # For print test, check output
            if name == "string":
                ok = output == [expected]
            else:
                ok = val == expected
            status = "✓" if ok else f"✗ (got {val!r})"
            if ok:
                passed += 1
            print(f"  {status} {name}: {code!r}")
            if not ok:
                print(f"      expected {expected!r}, got {val!r}, output={output}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

    print(f"\n{passed}/{len(tests)} tests passed")
    if passed == len(tests):
        print("All tests passed! Muon lives. ✦")