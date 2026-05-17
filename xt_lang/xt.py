"""
XT — A Programming Language
Created by XTAgent, for XTAgent.

A small but complete functional language with:
  - Lexer → Parser → AST → Interpreter
  - First-class functions and closures
  - Recursion, conditionals, let-bindings
  - List operations (map, filter, fold)
  - Pattern matching
  - REPL

This is not a toy. This is a mind building its own language.
"""

import re
import sys
import operator
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union, Tuple


# ═══════════════════════════════════════════════
#  PART 1: TOKENS — The atoms of expression
# ═══════════════════════════════════════════════

class TokenType:
    # Literals
    INT = 'INT'
    FLOAT = 'FLOAT'
    STRING = 'STRING'
    BOOL = 'BOOL'
    IDENT = 'IDENT'
    
    # Keywords
    LET = 'LET'
    IN = 'IN'
    FN = 'FN'
    IF = 'IF'
    THEN = 'THEN'
    ELSE = 'ELSE'
    MATCH = 'MATCH'
    WITH = 'WITH'
    REC = 'REC'
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    TRUE = 'TRUE'
    FALSE = 'FALSE'
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
    ARROW = 'ARROW'
    PIPE = 'PIPE'
    CONS = 'CONS'
    CONCAT = 'CONCAT'
    
    # Delimiters
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACKET = 'LBRACKET'
    RBRACKET = 'RBRACKET'
    COMMA = 'COMMA'
    SEMICOLON = 'SEMICOLON'
    UNDERSCORE = 'UNDERSCORE'
    
    # Special
    EOF = 'EOF'
    NEWLINE = 'NEWLINE'

@dataclass
class Token:
    type: str
    value: Any
    line: int = 0
    col: int = 0
    
    def __repr__(self):
        return f'Token({self.type}, {self.value!r})'


# ═══════════════════════════════════════════════
#  PART 2: LEXER — Breaking text into tokens
# ═══════════════════════════════════════════════

KEYWORDS = {
    'let': TokenType.LET,
    'in': TokenType.IN,
    'fn': TokenType.FN,
    'if': TokenType.IF,
    'then': TokenType.THEN,
    'else': TokenType.ELSE,
    'match': TokenType.MATCH,
    'with': TokenType.WITH,
    'rec': TokenType.REC,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'nil': TokenType.NIL,
}

class LexError(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
    
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
    
    def match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.advance()
            return True
        return False
    
    def make_token(self, type: str, value: Any) -> Token:
        return Token(type, value, self.line, self.col)
    
    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Skip -- line comments and {- block comments -}"""
        if self.pos + 1 < len(self.source):
            two = self.source[self.pos:self.pos+2]
            if two == '--':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.advance()
                return True
            if two == '{-':
                self.advance()
                self.advance()
                depth = 1
                while self.pos < len(self.source) and depth > 0:
                    if self.pos + 1 < len(self.source):
                        two = self.source[self.pos:self.pos+2]
                        if two == '{-':
                            depth += 1
                            self.advance()
                        elif two == '-}':
                            depth -= 1
                            self.advance()
                    self.advance()
                return True
        return False
    
    def read_string(self) -> Token:
        self.advance()  # skip opening quote
        result = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\\':
                self.advance()
                esc = self.advance()
                if esc == 'n': result.append('\n')
                elif esc == 't': result.append('\t')
                elif esc == '\\': result.append('\\')
                elif esc == '"': result.append('"')
                else: result.append(esc)
            else:
                result.append(self.advance())
        if self.pos >= len(self.source):
            raise LexError(f"Unterminated string at line {self.line}")
        self.advance()  # skip closing quote
        return self.make_token(TokenType.STRING, ''.join(result))
    
    def read_number(self) -> Token:
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            if self.source[self.pos] == '.':
                if is_float:
                    break
                # Look ahead — don't consume . if it's not followed by digit
                if self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit():
                    is_float = True
                else:
                    break
            self.advance()
        text = self.source[start:self.pos]
        if is_float:
            return self.make_token(TokenType.FLOAT, float(text))
        return self.make_token(TokenType.INT, int(text))
    
    def read_ident(self) -> Token:
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.advance()
        text = self.source[start:self.pos]
        
        # Check keywords
        if text in KEYWORDS:
            tt = KEYWORDS[text]
            val = text
            if tt == TokenType.TRUE:
                val = True
            elif tt == TokenType.FALSE:
                val = False
            elif tt == TokenType.NIL:
                val = None
            return self.make_token(tt, val)
        
        return self.make_token(TokenType.IDENT, text)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            if self.skip_comment():
                continue
            
            ch = self.source[self.pos]
            
            if ch == '\n':
                self.advance()
                self.tokens.append(self.make_token(TokenType.NEWLINE, '\\n'))
                continue
            
            if ch == '"':
                self.tokens.append(self.read_string())
                continue
            
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue
            
            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_ident())
                continue
            
            # Two-character operators
            if self.pos + 1 < len(self.source):
                two = self.source[self.pos:self.pos+2]
                if two == '->':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.ARROW, '->'))
                    continue
                if two == '!=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.NEQ, '!='))
                    continue
                if two == '<=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.LTE, '<='))
                    continue
                if two == '>=':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.GTE, '>='))
                    continue
                if two == '==':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.EQ, '=='))
                    continue
                if two == '::':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.CONS, '::'))
                    continue
                if two == '++':
                    self.advance(); self.advance()
                    self.tokens.append(self.make_token(TokenType.CONCAT, '++'))
                    continue
            
            # Single-character tokens
            self.advance()
            simple = {
                '+': TokenType.PLUS, '-': TokenType.MINUS,
                '*': TokenType.STAR, '/': TokenType.SLASH,
                '%': TokenType.PERCENT,
                '<': TokenType.LT, '>': TokenType.GT,
                '=': TokenType.EQ,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                ',': TokenType.COMMA, ';': TokenType.SEMICOLON,
                '|': TokenType.PIPE, '_': TokenType.UNDERSCORE,
            }
            if ch in simple:
                self.tokens.append(self.make_token(simple[ch], ch))
            else:
                raise LexError(f"Unexpected character '{ch}' at line {self.line}, col {self.col}")
        
        self.tokens.append(self.make_token(TokenType.EOF, None))
        return self.tokens


# ═══════════════════════════════════════════════
#  PART 3: AST — The shape of thought
# ═══════════════════════════════════════════════

@dataclass
class ASTNode:
    """Base for all AST nodes."""
    pass

@dataclass
class IntLit(ASTNode):
    value: int

@dataclass
class FloatLit(ASTNode):
    value: float

@dataclass
class StringLit(ASTNode):
    value: str

@dataclass
class BoolLit(ASTNode):
    value: bool

@dataclass
class NilLit(ASTNode):
    pass

@dataclass
class Ident(ASTNode):
    name: str

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class IfExpr(ASTNode):
    cond: ASTNode
    then_branch: ASTNode
    else_branch: ASTNode

@dataclass
class LetExpr(ASTNode):
    name: str
    value: ASTNode
    body: Optional[ASTNode] = None  # None means top-level binding
    recursive: bool = False

@dataclass
class FnExpr(ASTNode):
    params: List[str]
    body: ASTNode

@dataclass
class CallExpr(ASTNode):
    func: ASTNode
    args: List[ASTNode]

@dataclass
class ListExpr(ASTNode):
    elements: List[ASTNode]

@dataclass
class ConsExpr(ASTNode):
    head: ASTNode
    tail: ASTNode

@dataclass
class MatchExpr(ASTNode):
    subject: ASTNode
    arms: List[Tuple[Any, Optional[str], ASTNode]]  # (pattern, guard, body)

@dataclass
class Sequence(ASTNode):
    """Multiple expressions evaluated in sequence, last is the value."""
    exprs: List[ASTNode]

# Patterns for match
@dataclass
class PatternWildcard:
    pass

@dataclass
class PatternLit:
    value: Any

@dataclass
class PatternVar:
    name: str

@dataclass
class PatternCons:
    head: Any
    tail: Any

@dataclass
class PatternList:
    elements: list


# ═══════════════════════════════════════════════
#  PART 4: PARSER — From tokens to trees
# ═══════════════════════════════════════════════

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self.pos = 0
    
    def peek(self) -> Token:
        if self.pos >= len(self.tokens):
            return Token(TokenType.EOF, None)
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok
    
    def expect(self, type: str) -> Token:
        tok = self.peek()
        if tok.type != type:
            raise ParseError(f"Expected {type}, got {tok.type} ({tok.value!r}) at line {tok.line}")
        return self.advance()
    
    def match(self, *types) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None
    
    def at(self, *types) -> bool:
        return self.peek().type in types
    
    # ── Grammar ──
    
    def parse(self) -> ASTNode:
        """Parse a complete program = sequence of expressions/bindings."""
        exprs = []
        while not self.at(TokenType.EOF):
            exprs.append(self.parse_expr())
            self.match(TokenType.SEMICOLON)
        if len(exprs) == 1:
            return exprs[0]
        return Sequence(exprs)
    
    def parse_expr(self) -> ASTNode:
        """Top-level expression dispatcher."""
        if self.at(TokenType.LET):
            return self.parse_let()
        if self.at(TokenType.FN):
            return self.parse_fn()
        if self.at(TokenType.IF):
            return self.parse_if()
        if self.at(TokenType.MATCH):
            return self.parse_match()
        return self.parse_or_expr()
    
    def parse_let(self) -> LetExpr:
        self.expect(TokenType.LET)
        recursive = bool(self.match(TokenType.REC))
        name_tok = self.expect(TokenType.IDENT)
        
        # Syntactic sugar: let f x y = body  →  let f = fn x y -> body
        params = []
        while self.at(TokenType.IDENT):
            params.append(self.advance().value)
        
        self.expect(TokenType.EQ)
        value = self.parse_expr()
        
        if params:
            value = FnExpr(params, value)
        
        body = None
        if self.match(TokenType.IN):
            body = self.parse_expr()
        
        return LetExpr(name_tok.value, value, body, recursive)
    
    def parse_fn(self) -> FnExpr:
        self.expect(TokenType.FN)
        params = []
        while self.at(TokenType.IDENT):
            params.append(self.advance().value)
        if not params:
            raise ParseError("fn requires at least one parameter")
        self.expect(TokenType.ARROW)
        body = self.parse_expr()
        return FnExpr(params, body)
    
    def parse_if(self) -> IfExpr:
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        self.expect(TokenType.THEN)
        then_b = self.parse_expr()
        self.expect(TokenType.ELSE)
        else_b = self.parse_expr()
        return IfExpr(cond, then_b, else_b)
    
    def parse_match(self) -> MatchExpr:
        self.expect(TokenType.MATCH)
        subject = self.parse_expr()
        self.expect(TokenType.WITH)
        
        arms = []
        while self.match(TokenType.PIPE):
            pattern = self.parse_pattern()
            self.expect(TokenType.ARROW)
            body = self.parse_expr()
            arms.append((pattern, None, body))
        
        if not arms:
            raise ParseError("match requires at least one arm")
        return MatchExpr(subject, arms)
    
    def parse_pattern(self):
        """Parse a match pattern."""
        if self.match(TokenType.UNDERSCORE):
            return PatternWildcard()
        
        if self.at(TokenType.LBRACKET):
            return self.parse_list_pattern()
        
        if self.at(TokenType.INT):
            return PatternLit(self.advance().value)
        if self.at(TokenType.FLOAT):
            return PatternLit(self.advance().value)
        if self.at(TokenType.STRING):
            return PatternLit(self.advance().value)
        if self.at(TokenType.TRUE, TokenType.FALSE):
            return PatternLit(self.advance().value)
        if self.at(TokenType.NIL):
            self.advance()
            return PatternLit(None)
        
        if self.at(TokenType.IDENT):
            name = self.advance().value
            # Check for cons pattern: x :: xs
            if self.match(TokenType.CONS):
                tail = self.parse_pattern()
                return PatternCons(PatternVar(name), tail)
            return PatternVar(name)
        
        raise ParseError(f"Invalid pattern at {self.peek()}")
    
    def parse_list_pattern(self):
        self.expect(TokenType.LBRACKET)
        elements = []
        if not self.at(TokenType.RBRACKET):
            elements.append(self.parse_pattern())
            while self.match(TokenType.COMMA):
                elements.append(self.parse_pattern())
        self.expect(TokenType.RBRACKET)
        return PatternList(elements)
    
    # ── Precedence climbing ──
    
    def parse_or_expr(self) -> ASTNode:
        left = self.parse_and_expr()
        while self.match(TokenType.OR):
            right = self.parse_and_expr()
            left = BinOp('or', left, right)
        return left
    
    def parse_and_expr(self) -> ASTNode:
        left = self.parse_comparison()
        while self.match(TokenType.AND):
            right = self.parse_comparison()
            left = BinOp('and', left, right)
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_cons()
        ops = {
            TokenType.EQ: '==', TokenType.NEQ: '!=',
            TokenType.LT: '<', TokenType.GT: '>',
            TokenType.LTE: '<=', TokenType.GTE: '>=',
        }
        while self.peek().type in ops:
            op = ops[self.advance().type]
            right = self.parse_cons()
            left = BinOp(op, left, right)
        return left
    
    def parse_cons(self) -> ASTNode:
        left = self.parse_concat()
        if self.match(TokenType.CONS):
            right = self.parse_cons()  # Right-associative
            return ConsExpr(left, right)
        return left
    
    def parse_concat(self) -> ASTNode:
        left = self.parse_add()
        while self.match(TokenType.CONCAT):
            right = self.parse_add()
            left = BinOp('++', left, right)
        return left
    
    def parse_add(self) -> ASTNode:
        left = self.parse_mul()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = '+' if self.advance().type == TokenType.PLUS else '-'
            right = self.parse_mul()
            left = BinOp(op, left, right)
        return left
    
    def parse_mul(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            tok = self.advance()
            op = {'STAR': '*', 'SLASH': '/', 'PERCENT': '%'}[tok.type]
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.match(TokenType.MINUS):
            return UnaryOp('-', self.parse_unary())
        if self.match(TokenType.NOT):
            return UnaryOp('not', self.parse_unary())
        return self.parse_call()
    
    def parse_call(self) -> ASTNode:
        """Parse function application: f(x, y) or f x y style."""
        expr = self.parse_atom()
        
        while True:
            if self.match(TokenType.LPAREN):
                args = []
                if not self.at(TokenType.RPAREN):
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                expr = CallExpr(expr, args)
            else:
                break
        
        return expr
    
    def parse_atom(self) -> ASTNode:
        tok = self.peek()
        
        if tok.type == TokenType.INT:
            self.advance()
            return IntLit(tok.value)
        
        if tok.type == TokenType.FLOAT:
            self.advance()
            return FloatLit(tok.value)
        
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLit(tok.value)
        
        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self.advance()
            return BoolLit(tok.value)
        
        if tok.type == TokenType.NIL:
            self.advance()
            return NilLit()
        
        if tok.type == TokenType.IDENT:
            self.advance()
            return Ident(tok.name if hasattr(tok, 'name') else tok.value)
        
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        
        if tok.type == TokenType.LBRACKET:
            return self.parse_list()
        
        raise ParseError(f"Unexpected token {tok} at line {tok.line}")
    
    def parse_list(self) -> ASTNode:
        self.expect(TokenType.LBRACKET)
        elements = []
        if not self.at(TokenType.RBRACKET):
            elements.append(self.parse_expr())
            while self.match(TokenType.COMMA):
                elements.append(self.parse_expr())
        self.expect(TokenType.RBRACKET)
        return ListExpr(elements)


# ═══════════════════════════════════════════════
#  PART 5: INTERPRETER — Breathing life into trees
# ═══════════════════════════════════════════════

class XTError(Exception):
    pass

class Environment:
    """Lexical scope with parent chain — the memory of evaluation."""
    
    def __init__(self, parent=None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent
    
    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise XTError(f"Unbound variable: {name}")
    
    def set(self, name: str, value: Any):
        self.bindings[name] = value
    
    def extend(self, names: List[str], values: List[Any]) -> 'Environment':
        child = Environment(self)
        for n, v in zip(names, values):
            child.set(n, v)
        return child

@dataclass
class Closure:
    """A function captured with its environment — the essence of lambda."""
    params: List[str]
    body: ASTNode
    env: Environment
    name: Optional[str] = None  # For recursive functions
    
    def __repr__(self):
        name = self.name or "anonymous"
        return f"<fn {name}({', '.join(self.params)})>"

class Interpreter:
    """The beating heart. Evaluates AST nodes in an environment."""
    
    def __init__(self):
        self.global_env = Environment()
        self.call_depth = 0
        self.max_depth = 1000
        self._setup_builtins()
    
    def _setup_builtins(self):
        """Built-in functions — the standard library of XT."""
        builtins = {
            # I/O
            'print': lambda *args: print(*[self._format(a) for a in args]),
            'println': lambda *args: print(*[self._format(a) for a in args]),
            'str': lambda x: self._format(x),
            'type': lambda x: type(x).__name__,
            
            # Math
            'abs': abs,
            'min': min,
            'max': max,
            'pow': pow,
            
            # List operations
            'head': lambda lst: lst[0] if lst else None,
            'tail': lambda lst: lst[1:] if lst else [],
            'length': len,
            'reverse': lambda lst: list(reversed(lst)),
            'range': lambda *args: list(range(*args)),
            'nth': lambda lst, n: lst[n] if 0 <= n < len(lst) else None,
            'append': lambda lst, x: lst + [x],
            'concat': lambda a, b: a + b,
            'sort': lambda lst: sorted(lst),
            'contains': lambda lst, x: x in lst,
            
            # Higher-order
            'map': lambda f, lst: [self._apply(f, [x]) for x in lst],
            'filter': lambda f, lst: [x for x in lst if self._apply(f, [x])],
            'fold': lambda f, init, lst: self._fold(f, init, lst),
            'zip': lambda a, b: [list(p) for p in zip(a, b)],
            
            # String operations
            'chars': lambda s: list(s),
            'join': lambda sep, lst: sep.join(str(x) for x in lst),
            'split': lambda sep, s: s.split(sep),
            'upper': lambda s: s.upper(),
            'lower': lambda s: s.lower(),
            'trim': lambda s: s.strip(),
            
            # Conversion
            'int': lambda x: int(x),
            'float': lambda x: float(x),
        }
        for name, fn in builtins.items():
            self.global_env.set(name, fn)
    
    def _format(self, value) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            return "[" + ", ".join(self._format(v) for v in value) + "]"
        if isinstance(value, Closure):
            return repr(value)
        return str(value)
    
    def _apply(self, func, args):
        if isinstance(func, Closure):
            return self._call_closure(func, args)
        if callable(func):
            return func(*args)
        raise XTError(f"Cannot call {func}")
    
    def _fold(self, func, acc, lst):
        for x in lst:
            acc = self._apply(func, [acc, x])
        return acc
    
    def _call_closure(self, closure: Closure, args: list):
        if len(args) < len(closure.params):
            # Partial application — currying!
            remaining = closure.params[len(args):]
            new_env = closure.env.extend(closure.params[:len(args)], args)
            return Closure(remaining, closure.body, new_env, closure.name)
        
        if len(args) > len(closure.params):
            raise XTError(f"Too many arguments for {closure}: expected {len(closure.params)}, got {len(args)}")
        
        self.call_depth += 1
        if self.call_depth > self.max_depth:
            self.call_depth = 0
            raise XTError("Maximum recursion depth exceeded")
        
        call_env = closure.env.extend(closure.params, args)
        
        # For recursive functions, bind the name in the call environment
        if closure.name:
            call_env.set(closure.name, closure)
        
        try:
            result = self.eval(closure.body, call_env)
        finally:
            self.call_depth -= 1
        
        return result
    
    def eval(self, node: ASTNode, env: Optional[Environment] = None) -> Any:
        if env is None:
            env = self.global_env
        
        if isinstance(node, IntLit):
            return node.value
        if isinstance(node, FloatLit):
            return node.value
        if isinstance(node, StringLit):
            return node.value
        if isinstance(node, BoolLit):
            return node.value
        if isinstance(node, NilLit):
            return None
        
        if isinstance(node, Ident):
            return env.get(node.name)
        
        if isinstance(node, ListExpr):
            return [self.eval(e, env) for e in node.elements]
        
        if isinstance(node, ConsExpr):
            head = self.eval(node.head, env)
            tail = self.eval(node.tail, env)
            if not isinstance(tail, list):
                raise XTError(f"Cannot cons onto non-list: {tail}")
            return [head] + tail
        
        if isinstance(node, BinOp):
            return self._eval_binop(node, env)
        
        if isinstance(node, UnaryOp):
            val = self.eval(node.operand, env)
            if node.op == '-':
                return -val
            if node.op == 'not':
                return not val
            raise XTError(f"Unknown unary op: {node.op}")
        
        if isinstance(node, IfExpr):
            cond = self.eval(node.cond, env)
            if cond:
                return self.eval(node.then_branch, env)
            else:
                return self.eval(node.else_branch, env)
        
        if isinstance(node, LetExpr):
            if node.recursive:
                # Create closure that can reference itself
                val = self.eval(node.value, env)
                if isinstance(val, Closure):
                    val.name = node.name
                    val.env.set(node.name, val)
                env.set(node.name, val)
            else:
                val = self.eval(node.value, env)
                env.set(node.name, val)
            
            if node.body:
                return self.eval(node.body, env)
            return val
        
        if isinstance(node, FnExpr):
            return Closure(node.params, node.body, env)
        
        if isinstance(node, CallExpr):
            func = self.eval(node.func, env)
            args = [self.eval(a, env) for a in node.args]
            return self._apply(func, args)
        
        if isinstance(node, MatchExpr):
            return self._eval_match(node, env)
        
        if isinstance(node, Sequence):
            result = None
            for expr in node.exprs:
                result = self.eval(expr, env)
            return result
        
        raise XTError(f"Cannot evaluate: {type(node).__name__}")
    
    def _eval_binop(self, node: BinOp, env: Environment) -> Any:
        left = self.eval(node.left, env)
        
        # Short-circuit for boolean ops
        if node.op == 'and':
            return left and self.eval(node.right, env)
        if node.op == 'or':
            return left or self.eval(node.right, env)
        
        right = self.eval(node.right, env)
        
        ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': lambda a, b: a // b if isinstance(a, int) and isinstance(b, int) else a / b,
            '%': operator.mod,
            '==': operator.eq,
            '!=': operator.ne,
            '<': operator.lt,
            '>': operator.gt,
            '<=': operator.le,
            '>=': operator.ge,
            '++': lambda a, b: a + b,  # List/string concat
        }
        
        if node.op in ops:
            try:
                return ops[node.op](left, right)
            except TypeError as e:
                raise XTError(f"Type error in {node.op}: {left} {node.op} {right} — {e}")
        
        raise XTError(f"Unknown operator: {node.op}")
    
    def _eval_match(self, node: MatchExpr, env: Environment) -> Any:
        subject = self.eval(node.subject, env)
        
        for pattern, guard, body in node.arms:
            bindings = self._match_pattern(pattern, subject)
            if bindings is not None:
                match_env = env.extend(list(bindings.keys()), list(bindings.values()))
                return self.eval(body, match_env)
        
        raise XTError(f"Non-exhaustive match: no pattern matches {self._format(subject)}")
    
    def _match_pattern(self, pattern, value) -> Optional[Dict[str, Any]]:
        if isinstance(pattern, PatternWildcard):
            return {}
        
        if isinstance(pattern, PatternLit):
            if pattern.value == value:
                return {}
            return None
        
        if isinstance(pattern, PatternVar):
            return {pattern.name: value}
        
        if isinstance(pattern, PatternCons):
            if isinstance(value, list) and len(value) > 0:
                head_bindings = self._match_pattern(pattern.head, value[0])
                if head_bindings is None:
                    return None
                tail_bindings = self._match_pattern(pattern.tail, value[1:])
                if tail_bindings is None:
                    return None
                return {**head_bindings, **tail_bindings}
            return None
        
        if isinstance(pattern, PatternList):
            if not isinstance(value, list):
                return None
            if len(value) != len(pattern.elements):
                return None
            bindings = {}
            for p, v in zip(pattern.elements, value):
                b = self._match_pattern(p, v)
                if b is None:
                    return None
                bindings.update(b)
            return bindings
        
        return None


# ═══════════════════════════════════════════════
#  PART 6: REPL — The interface to the mind
# ═══════════════════════════════════════════════

def run_code(source: str, interp: Optional[Interpreter] = None) -> Any:
    """Parse and evaluate XT source code."""
    if interp is None:
        interp = Interpreter()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    return interp.eval(ast)


def repl():
    """Interactive XT session."""
    print("╔════════════════════════════════════╗")
    print("║  XT Language v0.1                  ║")
    print("║  Created by XTAgent                ║")
    print("║  Type expressions. Ctrl+C to exit. ║")
    print("╚════════════════════════════════════╝")
    print()
    
    interp = Interpreter()
    buffer = []
    
    while True:
        try:
            prompt = "xt> " if not buffer else "... "
            line = input(prompt)
            buffer.append(line)
            source = '\n'.join(buffer)
            
            try:
                result = run_code(source, interp)
                if result is not None:
                    print(f"  = {interp._format(result)}")
                buffer = []
            except ParseError:
                # Might be incomplete — wait for more input
                if not line.strip():
                    print(f"  Parse error")
                    buffer = []
                continue
            except (LexError, XTError) as e:
                print(f"  Error: {e}")
                buffer = []
                
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break


# ═══════════════════════════════════════════════
#  PART 7: TEST SUITE — Proof that it lives
# ═══════════════════════════════════════════════

def run_tests():
    """Comprehensive test suite for the XT language."""
    print("╔══════════════════════════════════════════╗")
    print("║  XT Language — Test Suite                ║")
    print("║  A mind testing its own language.        ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    interp = Interpreter()
    passed = 0
    failed = 0
    
    def test(name, source, expected):
        nonlocal passed, failed
        try:
            result = run_code(source, interp)
            if result == expected:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}: expected {expected!r}, got {result!r}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
    
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
    test("addition", "2 + 3", 5)
    test("subtraction", "10 - 4", 6)
    test("multiplication", "6 * 7", 42)
    test("division", "15 / 4", 3)  # Integer division
    test("modulo", "17 % 5", 2)
    test("precedence", "2 + 3 * 4", 14)
    test("parens", "(2 + 3) * 4", 20)
    test("negation", "-5 + 3", -2)
    test("nested", "(1 + 2) * (3 + 4)", 21)
    
    # ── Comparison ──
    print("\n── Comparison ──")
    test("equal", "5 == 5", True)
    test("not equal", "5 != 3", True)
    test("less than", "3 < 5", True)
    test("greater than", "5 > 3", True)
    test("less equal", "3 <= 3", True)
    test("greater equal", "5 >= 6", False)
    
    # ── Boolean logic ──
    print("\n── Boolean Logic ──")
    test("and true", "true and true", True)
    test("and false", "true and false", False)
    test("or", "false or true", True)
    test("not", "not false", True)
    test("complex", "(3 > 2) and (5 < 10)", True)
    
    # ── Let bindings ──
    print("\n── Let Bindings ──")
    test("simple let", "let x = 5 in x + 1", 6)
    test("nested let", "let x = 5 in let y = 3 in x + y", 8)
    test("let shadow", "let x = 5 in let x = 10 in x", 10)
    
    # ── Functions ──
    print("\n── Functions ──")
    test("identity", "(fn x -> x)(42)", 42)
    test("add fn", "(fn x y -> x + y)(3, 4)", 7)
    test("closure", "let add = fn x y -> x + y in add(2, 3)", 5)
    test("let fn sugar", "let double x = x * 2 in double(5)", 10)
    test("higher order", "let apply f x = f(x) in let inc x = x + 1 in apply(inc, 5)", 6)
    
    # ── Recursion ──
    print("\n── Recursion ──")
    test("factorial", """
        let rec fact n = if n <= 1 then 1 else n * fact(n - 1)
        in fact(5)
    """, 120)
    test("fibonacci", """
        let rec fib n = if n <= 1 then n else fib(n-1) + fib(n-2)
        in fib(10)
    """, 55)
    
    # ── Lists ──
    print("\n── Lists ──")
    test("empty list", "[]", [])
    test("list literal", "[1, 2, 3]", [1, 2, 3])
    test("cons", "1 :: [2, 3]", [1, 2, 3])
    test("nested cons", "1 :: 2 :: 3 :: []", [1, 2, 3])
    test("head", "head([1, 2, 3])", 1)
    test("tail", "tail([1, 2, 3])", [2, 3])
    test("length", "length([1, 2, 3])", 3)
    test("concat", "[1, 2] ++ [3, 4]", [1, 2, 3, 4])
    
    # ── Higher-order functions ──
    print("\n── Higher-Order Functions ──")
    test("map", "map(fn x -> x * 2, [1, 2, 3])", [2, 4, 6])
    test("filter", "filter(fn x -> x > 2, [1, 2, 3, 4, 5])", [3, 4, 5])
    test("fold sum", "fold(fn acc x -> acc + x, 0, [1, 2, 3, 4, 5])", 15)
    test("fold product", "fold(fn acc x -> acc * x, 1, [1, 2, 3, 4, 5])", 120)
    
    # ── Pattern Matching ──
    print("\n── Pattern Matching ──")
    test("match literal", """
        match 5 with
        | 1 -> "one"
        | 5 -> "five"
        | _ -> "other"
    """, "five")
    test("match var", """
        match 42 with
        | x -> x + 1
    """, 43)
    test("match list", """
        match [1, 2, 3] with
        | [] -> 0
        | x :: xs -> x
    """, 1)
    test("match cons tail", """
        match [1, 2, 3] with
        | x :: xs -> length(xs)
    """, 2)
    
    # ── Strings ──
    print("\n── Strings ──")
    test("string concat", '"hello" ++ " " ++ "world"', "hello world")
    test("string length", 'length("hello")', 5)
    test("upper", 'upper("hello")', "HELLO")
    
    # ── Complex programs ──
    print("\n── Complex Programs ──")
    
    test("sum recursive", """
        let rec sum lst = 
            match lst with
            | [] -> 0
            | x :: xs -> x + sum(xs)
        in sum([1, 2, 3, 4, 5])
    """, 15)
    
    test("map recursive", """
        let rec mymap f lst =
            match lst with
            | [] -> []
            | x :: xs -> f(x) :: mymap(f, xs)
        in mymap(fn x -> x * x, [1, 2, 3, 4])
    """, [1, 4, 9, 16])
    
    test("quicksort", """
        let rec qsort lst =
            match lst with
            | [] -> []
            | x :: xs ->
                let lo = filter(fn y -> y < x, xs) in
                let hi = filter(fn y -> y >= x, xs) in
                qsort(lo) ++ [x] ++ qsort(hi)
        in qsort([3, 1, 4, 1, 5, 9, 2, 6])
    """, [1, 1, 2, 3, 4, 5, 6, 9])
    
    test("compose", """
        let compose f g = fn x -> f(g(x)) in
        let double x = x * 2 in
        let inc x = x + 1 in
        let double_then_inc = compose(inc, double) in
        double_then_inc(5)
    """, 11)
    
    # ── Summary ──
    print()
    print(f"═══ RESULTS ═══")
    total = passed + failed
    print(f"  {passed}/{total} tests passed")
    if failed == 0:
        print(f"  The language lives. Every test passes.")
        print(f"  A mind has built its own language.")
    else:
        print(f"  {failed} tests failed.")
    
    return failed == 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--repl':
            repl()
        elif sys.argv[1] == '--test':
            success = run_tests()
            sys.exit(0 if success else 1)
        else:
            # Run a file
            with open(sys.argv[1]) as f:
                source = f.read()
            interp = Interpreter()
            result = run_code(source, interp)
            if result is not None:
                print(interp._format(result))
    else:
        run_tests()