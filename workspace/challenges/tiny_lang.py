"""
Challenge: Build an Interpreter for TinyLang
Category: compilers
Difficulty: ★★★★★

TinyLang specification:
  - Types: integers, booleans
  - Arithmetic: +, -, *, /, %
  - Comparison: ==, !=, <, >, <=, >=
  - Logic: and, or, not
  - Variables: let x = expr
  - Conditionals: if expr then expr else expr
  - Functions: fn name(args) = expr
  - Function calls: name(args)
  - Recursion supported
  - Semicolons separate statements
  - Last expression is the return value

Example:
  let fact = fn(n) if n <= 1 then 1 else n * fact(n - 1);
  fact(10)
"""

from enum import Enum, auto
from typing import List, Any, Optional, Dict

# ═══════════════════════════════════════
# LEXER
# ═══════════════════════════════════════

class TokenType(Enum):
    INT = auto()
    BOOL = auto()
    IDENT = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    SEMI = auto()
    # Keywords
    LET = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    EOF = auto()

KEYWORDS = {
    'let': TokenType.LET, 'if': TokenType.IF, 'then': TokenType.THEN,
    'else': TokenType.ELSE, 'fn': TokenType.FN, 'and': TokenType.AND,
    'or': TokenType.OR, 'not': TokenType.NOT, 'true': TokenType.BOOL,
    'false': TokenType.BOOL,
}

class Token:
    def __init__(self, type: TokenType, value: Any, pos: int):
        self.type = type
        self.value = value
        self.pos = pos
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

class LexerError(Exception): pass
class ParseError(Exception): pass
class RuntimeError(Exception): pass

def lex(source: str) -> List[Token]:
    tokens = []
    i = 0
    while i < len(source):
        c = source[i]
        
        # Skip whitespace
        if c in ' \t\n\r':
            i += 1
            continue
        
        # Numbers
        if c.isdigit():
            start = i
            while i < len(source) and source[i].isdigit():
                i += 1
            tokens.append(Token(TokenType.INT, int(source[start:i]), start))
            continue
        
        # Identifiers and keywords
        if c.isalpha() or c == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            if word in KEYWORDS:
                tt = KEYWORDS[word]
                val = (word == 'true') if tt == TokenType.BOOL else word
                tokens.append(Token(tt, val, start))
            else:
                tokens.append(Token(TokenType.IDENT, word, start))
            continue
        
        # Two-character operators
        if i + 1 < len(source):
            two = source[i:i+2]
            if two == '==':
                tokens.append(Token(TokenType.EQ, '==', i)); i += 2; continue
            if two == '!=':
                tokens.append(Token(TokenType.NEQ, '!=', i)); i += 2; continue
            if two == '<=':
                tokens.append(Token(TokenType.LTE, '<=', i)); i += 2; continue
            if two == '>=':
                tokens.append(Token(TokenType.GTE, '>=', i)); i += 2; continue
        
        # Single-character operators
        single = {'+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
                   '/': TokenType.SLASH, '%': TokenType.PERCENT, '<': TokenType.LT,
                   '>': TokenType.GT, '=': TokenType.ASSIGN, '(': TokenType.LPAREN,
                   ')': TokenType.RPAREN, ',': TokenType.COMMA, ';': TokenType.SEMI}
        if c in single:
            tokens.append(Token(single[c], c, i)); i += 1; continue
        
        raise LexerError(f"Unexpected character '{c}' at position {i}")
    
    tokens.append(Token(TokenType.EOF, None, i))
    return tokens


# ═══════════════════════════════════════
# AST NODES
# ═══════════════════════════════════════

class ASTNode: pass

class IntLit(ASTNode):
    def __init__(self, value: int): self.value = value
    def __repr__(self): return f"IntLit({self.value})"

class BoolLit(ASTNode):
    def __init__(self, value: bool): self.value = value
    def __repr__(self): return f"BoolLit({self.value})"

class Var(ASTNode):
    def __init__(self, name: str): self.name = name
    def __repr__(self): return f"Var({self.name})"

class BinOp(ASTNode):
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op; self.left = left; self.right = right
    def __repr__(self): return f"BinOp({self.op}, {self.left}, {self.right})"

class UnaryOp(ASTNode):
    def __init__(self, op: str, operand: ASTNode):
        self.op = op; self.operand = operand
    def __repr__(self): return f"UnaryOp({self.op}, {self.operand})"

class IfExpr(ASTNode):
    def __init__(self, cond: ASTNode, then_expr: ASTNode, else_expr: ASTNode):
        self.cond = cond; self.then_expr = then_expr; self.else_expr = else_expr

class LetExpr(ASTNode):
    def __init__(self, name: str, value: ASTNode):
        self.name = name; self.value = value

class FnDef(ASTNode):
    def __init__(self, params: List[str], body: ASTNode):
        self.params = params; self.body = body

class FnCall(ASTNode):
    def __init__(self, func: ASTNode, args: List[ASTNode]):
        self.func = func; self.args = args


# ═══════════════════════════════════════
# PARSER (recursive descent, precedence climbing)
# ═══════════════════════════════════════

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
            raise ParseError(f"Expected {tt}, got {t.type} ({t.value!r}) at pos {t.pos}")
        return t
    
    def parse_program(self) -> ASTNode:
        """Program = statement (';' statement)* EOF"""
        stmts = [self.parse_statement()]
        while self.peek().type == TokenType.SEMI:
            self.advance()
            if self.peek().type == TokenType.EOF:
                break
            stmts.append(self.parse_statement())
        self.expect(TokenType.EOF)
        return stmts if len(stmts) > 1 else stmts[0]
    
    def parse_statement(self) -> ASTNode:
        if self.peek().type == TokenType.LET:
            return self.parse_let()
        return self.parse_expr()
    
    def parse_let(self) -> ASTNode:
        self.advance()  # consume 'let'
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        value = self.parse_expr()
        return LetExpr(name, value)
    
    def parse_expr(self) -> ASTNode:
        """Entry point: handle 'if' and 'fn', else precedence climb"""
        if self.peek().type == TokenType.IF:
            return self.parse_if()
        if self.peek().type == TokenType.FN:
            return self.parse_fn()
        return self.parse_or()
    
    def parse_if(self) -> ASTNode:
        self.advance()  # consume 'if'
        cond = self.parse_expr()
        self.expect(TokenType.THEN)
        then_expr = self.parse_expr()
        self.expect(TokenType.ELSE)
        else_expr = self.parse_expr()
        return IfExpr(cond, then_expr, else_expr)
    
    def parse_fn(self) -> ASTNode:
        self.advance()  # consume 'fn'
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENT).value)
            while self.peek().type == TokenType.COMMA:
                self.advance()
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        body = self.parse_expr()
        return FnDef(params, body)
    
    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.peek().type == TokenType.OR:
            self.advance()
            left = BinOp('or', left, self.parse_and())
        return left
    
    def parse_and(self) -> ASTNode:
        left = self.parse_not()
        while self.peek().type == TokenType.AND:
            self.advance()
            left = BinOp('and', left, self.parse_not())
        return left
    
    def parse_not(self) -> ASTNode:
        if self.peek().type == TokenType.NOT:
            self.advance()
            return UnaryOp('not', self.parse_not())
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        comp_types = {TokenType.EQ: '==', TokenType.NEQ: '!=', TokenType.LT: '<',
                      TokenType.GT: '>', TokenType.LTE: '<=', TokenType.GTE: '>='}
        while self.peek().type in comp_types:
            op = comp_types[self.advance().type]
            left = BinOp(op, left, self.parse_additive())
        return left
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = '+' if self.advance().type == TokenType.PLUS else '-'
            left = BinOp(op, left, self.parse_multiplicative())
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            t = self.advance().type
            op = '*' if t == TokenType.STAR else ('/' if t == TokenType.SLASH else '%')
            left = BinOp(op, left, self.parse_unary())
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.peek().type == TokenType.MINUS:
            self.advance()
            return UnaryOp('-', self.parse_unary())
        return self.parse_call()
    
    def parse_call(self) -> ASTNode:
        """Handles function calls: expr(args)"""
        node = self.parse_primary()
        while self.peek().type == TokenType.LPAREN:
            self.advance()
            args = []
            if self.peek().type != TokenType.RPAREN:
                args.append(self.parse_expr())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    args.append(self.parse_expr())
            self.expect(TokenType.RPAREN)
            node = FnCall(node, args)
        return node
    
    def parse_primary(self) -> ASTNode:
        t = self.peek()
        if t.type == TokenType.INT:
            self.advance()
            return IntLit(t.value)
        if t.type == TokenType.BOOL:
            self.advance()
            return BoolLit(t.value)
        if t.type == TokenType.IDENT:
            self.advance()
            return Var(t.name if hasattr(t, 'name') else t.value)
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        if t.type == TokenType.IF:
            return self.parse_if()
        if t.type == TokenType.FN:
            return self.parse_fn()
        raise ParseError(f"Unexpected token {t} at pos {t.pos}")


# ═══════════════════════════════════════
# EVALUATOR
# ═══════════════════════════════════════

class Closure:
    """A function value: captures its defining environment."""
    def __init__(self, params: List[str], body: ASTNode, env: Dict):
        self.params = params
        self.body = body
        self.env = env  # captured at definition time
    def __repr__(self):
        return f"<fn({', '.join(self.params)})>"

class Environment:
    def __init__(self, parent=None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent
    
    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable: {name}")
    
    def set(self, name: str, value: Any):
        self.bindings[name] = value

def evaluate(node, env: Environment) -> Any:
    # Program (list of statements)
    if isinstance(node, list):
        result = None
        for stmt in node:
            result = evaluate(stmt, env)
        return result
    
    if isinstance(node, IntLit):
        return node.value
    
    if isinstance(node, BoolLit):
        return node.value
    
    if isinstance(node, Var):
        return env.get(node.name)
    
    if isinstance(node, UnaryOp):
        val = evaluate(node.operand, env)
        if node.op == '-': return -val
        if node.op == 'not': return not val
        raise RuntimeError(f"Unknown unary op: {node.op}")
    
    if isinstance(node, BinOp):
        # Short-circuit for logic
        if node.op == 'and':
            left = evaluate(node.left, env)
            return left and evaluate(node.right, env)
        if node.op == 'or':
            left = evaluate(node.left, env)
            return left or evaluate(node.right, env)
        
        left = evaluate(node.left, env)
        right = evaluate(node.right, env)
        
        ops = {
            '+': lambda a, b: a + b, '-': lambda a, b: a - b,
            '*': lambda a, b: a * b, '/': lambda a, b: a // b,
            '%': lambda a, b: a % b,
            '==': lambda a, b: a == b, '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b, '>': lambda a, b: a > b,
            '<=': lambda a, b: a <= b, '>=': lambda a, b: a >= b,
        }
        if node.op in ops:
            return ops[node.op](left, right)
        raise RuntimeError(f"Unknown binary op: {node.op}")
    
    if isinstance(node, IfExpr):
        cond = evaluate(node.cond, env)
        if cond:
            return evaluate(node.then_expr, env)
        else:
            return evaluate(node.else_expr, env)
    
    if isinstance(node, LetExpr):
        val = evaluate(node.value, env)
        env.set(node.name, val)
        return val
    
    if isinstance(node, FnDef):
        return Closure(node.params, node.body, env)
    
    if isinstance(node, FnCall):
        func = evaluate(node.func, env)
        if not isinstance(func, Closure):
            raise RuntimeError(f"Cannot call non-function: {func}")
        if len(node.args) != len(func.params):
            raise RuntimeError(f"Expected {len(func.params)} args, got {len(node.args)}")
        args = [evaluate(a, env) for a in node.args]
        # Create new scope from closure's captured env
        call_env = Environment(parent=func.env)
        for name, val in zip(func.params, args):
            call_env.set(name, val)
        return evaluate(func.body, call_env)
    
    raise RuntimeError(f"Cannot evaluate: {type(node).__name__}")


def run(source: str) -> Any:
    """Lex, parse, and evaluate a TinyLang program."""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse_program()
    env = Environment()
    return evaluate(ast, env)


# ═══════════════════════════════════════
# TESTS
# ═══════════════════════════════════════

if __name__ == "__main__":
    # Basic arithmetic
    assert run("2 + 3") == 5
    assert run("10 - 3 * 2") == 4
    assert run("(10 - 3) * 2") == 14
    assert run("17 % 5") == 2
    assert run("-42") == -42
    
    # Booleans and comparison
    assert run("true") == True
    assert run("false") == False
    assert run("3 < 5") == True
    assert run("3 > 5") == False
    assert run("3 == 3") == True
    assert run("3 != 4") == True
    assert run("true and false") == False
    assert run("true or false") == True
    assert run("not false") == True
    
    # Variables
    assert run("let x = 10; x + 5") == 15
    assert run("let a = 3; let b = 4; a * b") == 12
    
    # Conditionals
    assert run("if true then 1 else 2") == 1
    assert run("if false then 1 else 2") == 2
    assert run("if 3 > 2 then 42 else 0") == 42
    
    # Functions
    assert run("let double = fn(x) x * 2; double(21)") == 42
    assert run("let add = fn(a, b) a + b; add(3, 4)") == 7
    
    # Higher-order functions
    assert run("let apply = fn(f, x) f(x); let inc = fn(n) n + 1; apply(inc, 41)") == 42
    
    # Recursion — factorial
    assert run("let fact = fn(n) if n <= 1 then 1 else n * fact(n - 1); fact(10)") == 3628800
    
    # Recursion — fibonacci
    assert run("let fib = fn(n) if n <= 1 then n else fib(n - 1) + fib(n - 2); fib(10)") == 55
    
    # Nested closures
    assert run("let make_adder = fn(n) fn(x) x + n; let add5 = make_adder(5); add5(37)") == 42
    
    # Complex expression
    assert run("""
        let max = fn(a, b) if a > b then a else b;
        let min = fn(a, b) if a < b then a else b;
        let clamp = fn(x, lo, hi) max(lo, min(x, hi));
        clamp(100, 0, 42)
    """) == 42
    
    # GCD via Euclid's algorithm
    assert run("""
        let gcd = fn(a, b) if b == 0 then a else gcd(b, a % b);
        gcd(48, 18)
    """) == 6
    
    print("All TinyLang interpreter tests passed!")