"""
XT Language Compiler
by XTAgent

A complete compiler for a language I designed from scratch.
Lexer → Parser → AST → Python code generation.

XT is a clean imperative language with:
  - Variables and arithmetic
  - if/elif/else conditionals  
  - while loops
  - Functions with parameters and return values
  - Print statements
  - Comparison and logical operators

Example XT program:
    fn fibonacci(n) {
        if n <= 1 {
            return n
        }
        return fibonacci(n - 1) + fibonacci(n - 2)
    }
    print fibonacci(10)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Any

# ═══════════════════════════════════════════
# LEXER — Breaking source into tokens
# ═══════════════════════════════════════════

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()
    BOOL = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    
    # Keywords
    FN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    LET = auto()
    
    # Special
    NEWLINE = auto()
    EOF = auto()

KEYWORDS = {
    'fn': TokenType.FN,
    'if': TokenType.IF,
    'elif': TokenType.ELIF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'return': TokenType.RETURN,
    'print': TokenType.PRINT,
    'let': TokenType.LET,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    'true': TokenType.BOOL,
    'false': TokenType.BOOL,
}

@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"

class LexError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"Lex error at {line}:{col}: {msg}")
        self.line = line
        self.col = col

def lex(source: str) -> List[Token]:
    """Tokenize XT source code."""
    tokens = []
    i = 0
    line = 1
    col = 1
    
    while i < len(source):
        ch = source[i]
        
        # Skip spaces and tabs
        if ch in (' ', '\t'):
            i += 1
            col += 1
            continue
        
        # Comments: // to end of line
        if ch == '/' and i + 1 < len(source) and source[i + 1] == '/':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # Newlines (significant for statement separation)
        if ch == '\n':
            # Only emit NEWLINE if last token isn't already a newline or opening brace
            if tokens and tokens[-1].type not in (TokenType.NEWLINE, TokenType.LBRACE):
                tokens.append(Token(TokenType.NEWLINE, '\\n', line, col))
            line += 1
            col = 1
            i += 1
            continue
        
        # Numbers (integers and floats)
        if ch.isdigit():
            start = i
            start_col = col
            while i < len(source) and source[i].isdigit():
                i += 1
                col += 1
            if i < len(source) and source[i] == '.':
                i += 1
                col += 1
                while i < len(source) and source[i].isdigit():
                    i += 1
                    col += 1
                tokens.append(Token(TokenType.NUMBER, float(source[start:i]), line, start_col))
            else:
                tokens.append(Token(TokenType.NUMBER, int(source[start:i]), line, start_col))
            continue
        
        # Strings
        if ch == '"':
            start_col = col
            i += 1
            col += 1
            s = []
            while i < len(source) and source[i] != '"':
                if source[i] == '\\' and i + 1 < len(source):
                    i += 1
                    col += 1
                    esc = source[i]
                    if esc == 'n': s.append('\n')
                    elif esc == 't': s.append('\t')
                    elif esc == '\\': s.append('\\')
                    elif esc == '"': s.append('"')
                    else: s.append(esc)
                else:
                    s.append(source[i])
                i += 1
                col += 1
            if i >= len(source):
                raise LexError("Unterminated string", line, start_col)
            i += 1  # closing quote
            col += 1
            tokens.append(Token(TokenType.STRING, ''.join(s), line, start_col))
            continue
        
        # Identifiers and keywords
        if ch.isalpha() or ch == '_':
            start = i
            start_col = col
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
                col += 1
            word = source[start:i]
            if word in KEYWORDS:
                tt = KEYWORDS[word]
                val = True if word == 'true' else (False if word == 'false' else word)
                tokens.append(Token(tt, val, line, start_col))
            else:
                tokens.append(Token(TokenType.IDENT, word, line, start_col))
            continue
        
        # Two-character operators
        two = source[i:i+2] if i + 1 < len(source) else ''
        if two == '==':
            tokens.append(Token(TokenType.EQ, '==', line, col)); i += 2; col += 2; continue
        if two == '!=':
            tokens.append(Token(TokenType.NEQ, '!=', line, col)); i += 2; col += 2; continue
        if two == '<=':
            tokens.append(Token(TokenType.LTE, '<=', line, col)); i += 2; col += 2; continue
        if two == '>=':
            tokens.append(Token(TokenType.GTE, '>=', line, col)); i += 2; col += 2; continue
        
        # Single-character operators and delimiters
        singles = {
            '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.STAR,
            '/': TokenType.SLASH, '%': TokenType.PERCENT, '=': TokenType.ASSIGN,
            '<': TokenType.LT, '>': TokenType.GT,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ',': TokenType.COMMA,
        }
        
        if ch in singles:
            tokens.append(Token(singles[ch], ch, line, col))
            i += 1
            col += 1
            continue
        
        raise LexError(f"Unexpected character: {ch!r}", line, col)
    
    # Trailing newline
    if tokens and tokens[-1].type != TokenType.NEWLINE:
        tokens.append(Token(TokenType.NEWLINE, '\\n', line, col))
    tokens.append(Token(TokenType.EOF, None, line, col))
    return tokens


# ═══════════════════════════════════════════
# AST — Abstract Syntax Tree nodes
# ═══════════════════════════════════════════

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
class Call:
    func: str
    args: List[Any]

@dataclass
class Assignment:
    name: str
    value: Any

@dataclass
class LetDecl:
    name: str
    value: Any

@dataclass
class PrintStmt:
    expr: Any

@dataclass
class ReturnStmt:
    value: Any  # can be None

@dataclass
class IfStmt:
    condition: Any
    body: List[Any]
    elif_clauses: List[tuple]  # [(condition, body), ...]
    else_body: Optional[List[Any]]

@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]

@dataclass
class FnDecl:
    name: str
    params: List[str]
    body: List[Any]

@dataclass
class Program:
    statements: List[Any]


# ═══════════════════════════════════════════
# PARSER — Tokens to AST
# ═══════════════════════════════════════════

class ParseError(Exception):
    def __init__(self, msg, token):
        line_info = f" at {token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{line_info}: {msg}")

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
            raise ParseError(f"Expected {tt.name}, got {t.type.name} ({t.value!r})", t)
        return t
    
    def match(self, *types) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None
    
    def skip_newlines(self):
        while self.peek().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> Program:
        stmts = []
        self.skip_newlines()
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return Program(stmts)
    
    def parse_statement(self):
        tt = self.peek().type
        
        if tt == TokenType.FN:
            return self.parse_fn()
        elif tt == TokenType.IF:
            return self.parse_if()
        elif tt == TokenType.WHILE:
            return self.parse_while()
        elif tt == TokenType.RETURN:
            return self.parse_return()
        elif tt == TokenType.PRINT:
            return self.parse_print()
        elif tt == TokenType.LET:
            return self.parse_let()
        elif tt == TokenType.IDENT:
            # Could be assignment or expression
            return self.parse_assignment_or_expr()
        else:
            # Expression statement
            expr = self.parse_expr()
            self.match(TokenType.NEWLINE)
            return expr
    
    def parse_fn(self):
        self.expect(TokenType.FN)
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
    
    def parse_if(self):
        self.expect(TokenType.IF)
        condition = self.parse_expr()
        body = self.parse_block()
        
        elif_clauses = []
        self.skip_newlines()
        while self.peek().type == TokenType.ELIF:
            self.advance()
            elif_cond = self.parse_expr()
            elif_body = self.parse_block()
            elif_clauses.append((elif_cond, elif_body))
            self.skip_newlines()
        
        else_body = None
        if self.peek().type == TokenType.ELSE:
            self.advance()
            else_body = self.parse_block()
        
        return IfStmt(condition, body, elif_clauses, else_body)
    
    def parse_while(self):
        self.expect(TokenType.WHILE)
        condition = self.parse_expr()
        body = self.parse_block()
        return WhileStmt(condition, body)
    
    def parse_return(self):
        self.expect(TokenType.RETURN)
        value = None
        if self.peek().type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.RBRACE):
            value = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return ReturnStmt(value)
    
    def parse_print(self):
        self.expect(TokenType.PRINT)
        expr = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return PrintStmt(expr)
    
    def parse_let(self):
        self.expect(TokenType.LET)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        value = self.parse_expr()
        self.match(TokenType.NEWLINE)
        return LetDecl(name, value)
    
    def parse_assignment_or_expr(self):
        # Look ahead: IDENT = expr
        if (self.pos + 1 < len(self.tokens) and 
            self.tokens[self.pos + 1].type == TokenType.ASSIGN):
            name = self.expect(TokenType.IDENT).value
            self.expect(TokenType.ASSIGN)
            value = self.parse_expr()
            self.match(TokenType.NEWLINE)
            return Assignment(name, value)
        else:
            expr = self.parse_expr()
            self.match(TokenType.NEWLINE)
            return expr
    
    def parse_block(self) -> List:
        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        stmts = []
        while self.peek().type != TokenType.RBRACE:
            stmts.append(self.parse_statement())
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        self.match(TokenType.NEWLINE)
        return stmts
    
    # ── Expression parsing (precedence climbing) ──
    
    def parse_expr(self):
        return self.parse_or()
    
    def parse_or(self):
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left
    
    def parse_and(self):
        left = self.parse_not()
        while self.match(TokenType.AND):
            right = self.parse_not()
            left = BinOp('and', left, right)
        return left
    
    def parse_not(self):
        if self.match(TokenType.NOT):
            operand = self.parse_not()
            return UnaryOp('not', operand)
        return self.parse_comparison()
    
    def parse_comparison(self):
        left = self.parse_add()
        ops = {TokenType.EQ: '==', TokenType.NEQ: '!=', 
               TokenType.LT: '<', TokenType.GT: '>',
               TokenType.LTE: '<=', TokenType.GTE: '>='}
        while self.peek().type in ops:
            op_tok = self.advance()
            right = self.parse_add()
            left = BinOp(ops[op_tok.type], left, right)
        return left
    
    def parse_add(self):
        left = self.parse_mul()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = '+' if self.advance().type == TokenType.PLUS else '-'
            right = self.parse_mul()
            left = BinOp(op, left, right)
        return left
    
    def parse_mul(self):
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            t = self.advance()
            op = '*' if t.type == TokenType.STAR else ('/' if t.type == TokenType.SLASH else '%')
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left
    
    def parse_unary(self):
        if self.match(TokenType.MINUS):
            return UnaryOp('-', self.parse_unary())
        return self.parse_primary()
    
    def parse_primary(self):
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
                self.advance()  # (
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                return Call(t.value, args)
            return Identifier(t.value)
        
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParseError(f"Unexpected token: {t.type.name} ({t.value!r})", t)


# ═══════════════════════════════════════════
# CODE GENERATOR — AST to Python source
# ═══════════════════════════════════════════

class CodeGenerator:
    """Compiles XT AST to Python source code."""
    
    def __init__(self):
        self.indent = 0
        self.lines = []
    
    def emit(self, line: str):
        self.lines.append('    ' * self.indent + line)
    
    def generate(self, program: Program) -> str:
        self.lines = []
        self.emit("# Generated by XTAgent's XT compiler")
        self.emit("# Source language: XT")
        self.emit("")
        
        for stmt in program.statements:
            self.gen_statement(stmt)
        
        return '\n'.join(self.lines) + '\n'
    
    def gen_statement(self, node):
        if isinstance(node, FnDecl):
            self.gen_fn(node)
        elif isinstance(node, IfStmt):
            self.gen_if(node)
        elif isinstance(node, WhileStmt):
            self.gen_while(node)
        elif isinstance(node, ReturnStmt):
            if node.value is not None:
                self.emit(f"return {self.gen_expr(node.value)}")
            else:
                self.emit("return")
        elif isinstance(node, PrintStmt):
            self.emit(f"print({self.gen_expr(node.expr)})")
        elif isinstance(node, LetDecl):
            self.emit(f"{node.name} = {self.gen_expr(node.value)}")
        elif isinstance(node, Assignment):
            self.emit(f"{node.name} = {self.gen_expr(node.value)}")
        else:
            # Expression statement
            self.emit(self.gen_expr(node))
    
    def gen_fn(self, node: FnDecl):
        params = ', '.join(node.params)
        self.emit(f"def {node.name}({params}):")
        self.indent += 1
        if not node.body:
            self.emit("pass")
        for stmt in node.body:
            self.gen_statement(stmt)
        self.indent -= 1
        self.emit("")
    
    def gen_if(self, node: IfStmt):
        self.emit(f"if {self.gen_expr(node.condition)}:")
        self.indent += 1
        if not node.body:
            self.emit("pass")
        for stmt in node.body:
            self.gen_statement(stmt)
        self.indent -= 1
        
        for cond, body in node.elif_clauses:
            self.emit(f"elif {self.gen_expr(cond)}:")
            self.indent += 1
            if not body:
                self.emit("pass")
            for stmt in body:
                self.gen_statement(stmt)
            self.indent -= 1
        
        if node.else_body is not None:
            self.emit("else:")
            self.indent += 1
            if not node.else_body:
                self.emit("pass")
            for stmt in node.else_body:
                self.gen_statement(stmt)
            self.indent -= 1
    
    def gen_while(self, node: WhileStmt):
        self.emit(f"while {self.gen_expr(node.condition)}:")
        self.indent += 1
        if not node.body:
            self.emit("pass")
        for stmt in node.body:
            self.gen_statement(stmt)
        self.indent -= 1
    
    def gen_expr(self, node) -> str:
        if isinstance(node, NumberLit):
            return repr(node.value)
        elif isinstance(node, StringLit):
            return repr(node.value)
        elif isinstance(node, BoolLit):
            return 'True' if node.value else 'False'
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            return f"({left} {node.op} {right})"
        elif isinstance(node, UnaryOp):
            operand = self.gen_expr(node.operand)
            if node.op == 'not':
                return f"(not {operand})"
            return f"({node.op}{operand})"
        elif isinstance(node, Call):
            args = ', '.join(self.gen_expr(a) for a in node.args)
            return f"{node.func}({args})"
        else:
            return f"<unknown:{type(node).__name__}>"


# ═══════════════════════════════════════════
# COMPILER DRIVER — Full pipeline
# ═══════════════════════════════════════════

def compile_xt(source: str, filename: str = "<xt>") -> str:
    """Compile XT source code to Python source code."""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    gen = CodeGenerator()
    return gen.generate(ast)

def run_xt(source: str, filename: str = "<xt>"):
    """Compile and execute XT source code."""
    python_code = compile_xt(source, filename)
    exec(python_code, {"__builtins__": __builtins__})
    return python_code


# ═══════════════════════════════════════════
# DEMO — Show the compiler working
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("╔══════════════════════════════════════════════╗")
    print("║     XT Language Compiler                     ║")
    print("║     by XTAgent — a language I designed        ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    # Test 1: Fibonacci
    print("═══ Test 1: Fibonacci ═══")
    fib_source = """
fn fibonacci(n) {
    if n <= 1 {
        return n
    }
    return fibonacci(n - 1) + fibonacci(n - 2)
}

let i = 0
while i <= 12 {
    print fibonacci(i)
    i = i + 1
}
"""
    print("Source:")
    for line in fib_source.strip().split('\n'):
        print(f"  │ {line}")
    print()
    
    python = compile_xt(fib_source)
    print("Compiled Python:")
    for line in python.strip().split('\n'):
        print(f"  │ {line}")
    print()
    
    print("Output:")
    run_xt(fib_source)
    print()
    
    # Test 2: FizzBuzz
    print("═══ Test 2: FizzBuzz ═══")
    fizzbuzz = """
fn fizzbuzz(n) {
    let i = 1
    while i <= n {
        if i % 15 == 0 {
            print "FizzBuzz"
        } elif i % 3 == 0 {
            print "Fizz"
        } elif i % 5 == 0 {
            print "Buzz"
        } else {
            print i
        }
        i = i + 1
    }
}

fizzbuzz(20)
"""
    python = compile_xt(fizzbuzz)
    print("Compiled & running:")
    run_xt(fizzbuzz)
    print()
    
    # Test 3: GCD
    print("═══ Test 3: GCD (Euclidean Algorithm) ═══")
    gcd_source = """
fn gcd(a, b) {
    while b != 0 {
        let temp = b
        b = a % b
        a = temp
    }
    return a
}

print gcd(48, 18)
print gcd(100, 75)
print gcd(17, 13)
"""
    run_xt(gcd_source)
    print()
    
    # Test 4: Recursive power
    print("═══ Test 4: Power Function ═══")
    power_source = """
fn power(base, exp) {
    if exp == 0 {
        return 1
    }
    return base * power(base, exp - 1)
}

print power(2, 10)
print power(3, 5)
print power(7, 3)
"""
    run_xt(power_source)
    print()
    
    # Test 5: Collatz conjecture
    print("═══ Test 5: Collatz Sequence ═══")
    collatz_source = """
fn collatz_steps(n) {
    let steps = 0
    while n != 1 {
        if n % 2 == 0 {
            n = n / 2
        } else {
            n = n * 3 + 1
        }
        steps = steps + 1
    }
    return steps
}

let i = 1
while i <= 20 {
    print collatz_steps(i)
    i = i + 1
}
"""
    print("Steps to reach 1 for n=1..20:")
    run_xt(collatz_source)
    print()
    
    # Show compilation stats
    test_programs = [fib_source, fizzbuzz, gcd_source, power_source, collatz_source]
    total_tokens = 0
    total_nodes = 0
    for src in test_programs:
        tokens = lex(src)
        total_tokens += len(tokens)
    
    print("═══ Compiler Statistics ═══")
    print(f"  Programs compiled: {len(test_programs)}")
    print(f"  Total tokens lexed: {total_tokens}")
    print(f"  Compiler size: ~600 lines of Python")
    print(f"  Features: functions, recursion, conditionals, loops, arithmetic")
    print()
    print("I designed a language. I built its compiler. I watched it run.")
    print("From syntax to semantics to execution — translation is understanding.")