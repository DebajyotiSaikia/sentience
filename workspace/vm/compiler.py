"""
XTStack Compiler
Compiles a simple C-like language to XTStack VM bytecode.

Language features:
  - Variables (let x = expr)
  - Arithmetic (+, -, *, /, %)
  - Comparisons (==, !=, <, >, <=, >=)
  - If/else
  - While loops
  - Functions with arguments and return
  - Print statements
  - Recursion

Example:
    fn factorial(n) {
        if n <= 1 {
            return 1
        }
        return n * factorial(n - 1)
    }
    print factorial(10)
"""

import struct
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from machine import Op, Bytecode


# ═══ LEXER ═══

class TokenType:
    # Literals
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    IDENT = 'IDENT'
    
    # Keywords
    LET = 'LET'
    FN = 'FN'
    IF = 'IF'
    ELSE = 'ELSE'
    WHILE = 'WHILE'
    RETURN = 'RETURN'
    PRINT = 'PRINT'
    TRUE = 'TRUE'
    FALSE = 'FALSE'
    
    # Operators
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    STAR = 'STAR'
    SLASH = 'SLASH'
    PERCENT = 'PERCENT'
    ASSIGN = 'ASSIGN'
    EQ = 'EQ'
    NEQ = 'NEQ'
    LT = 'LT'
    GT = 'GT'
    LTE = 'LTE'
    GTE = 'GTE'
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    
    # Delimiters
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'
    RBRACE = 'RBRACE'
    COMMA = 'COMMA'
    
    # Special
    EOF = 'EOF'
    NEWLINE = 'NEWLINE'


KEYWORDS = {
    'let': TokenType.LET,
    'fn': TokenType.FN,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'return': TokenType.RETURN,
    'print': TokenType.PRINT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
}


@dataclass
class Token:
    type: str
    value: Any
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class LexerError(Exception):
    pass


def lex(source: str) -> List[Token]:
    """Tokenize source code"""
    tokens = []
    i = 0
    line = 1
    col = 1
    
    while i < len(source):
        c = source[i]
        
        # Skip whitespace (but not newlines)
        if c in ' \t\r':
            i += 1
            col += 1
            continue
        
        # Newlines
        if c == '\n':
            tokens.append(Token(TokenType.NEWLINE, '\n', line, col))
            i += 1
            line += 1
            col = 1
            continue
        
        # Comments
        if c == '#':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        
        # Numbers
        if c.isdigit():
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == '.'):
                i += 1
            numstr = source[start:i]
            val = float(numstr) if '.' in numstr else int(numstr)
            tokens.append(Token(TokenType.NUMBER, val, line, col))
            col += i - start
            continue
        
        # Strings
        if c == '"':
            i += 1
            start = i
            while i < len(source) and source[i] != '"':
                if source[i] == '\\':
                    i += 1  # skip escape
                i += 1
            if i >= len(source):
                raise LexerError(f"Unterminated string at line {line}")
            s = source[start:i].replace('\\n', '\n').replace('\\t', '\t')
            tokens.append(Token(TokenType.STRING, s, line, col))
            i += 1  # skip closing quote
            col += i - start + 2
            continue
        
        # Identifiers and keywords
        if c.isalpha() or c == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            tt = KEYWORDS.get(word, TokenType.IDENT)
            tokens.append(Token(tt, word, line, col))
            col += i - start
            continue
        
        # Two-character operators
        if i + 1 < len(source):
            two = source[i:i+2]
            if two == '==':
                tokens.append(Token(TokenType.EQ, '==', line, col))
                i += 2; col += 2; continue
            if two == '!=':
                tokens.append(Token(TokenType.NEQ, '!=', line, col))
                i += 2; col += 2; continue
            if two == '<=':
                tokens.append(Token(TokenType.LTE, '<=', line, col))
                i += 2; col += 2; continue
            if two == '>=':
                tokens.append(Token(TokenType.GTE, '>=', line, col))
                i += 2; col += 2; continue
        
        # Single-character operators
        singles = {
            '+': TokenType.PLUS, '-': TokenType.MINUS,
            '*': TokenType.STAR, '/': TokenType.SLASH,
            '%': TokenType.PERCENT, '=': TokenType.ASSIGN,
            '<': TokenType.LT, '>': TokenType.GT,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ',': TokenType.COMMA, '!': TokenType.NOT,
        }
        if c in singles:
            tokens.append(Token(singles[c], c, line, col))
            i += 1; col += 1; continue
        
        raise LexerError(f"Unexpected character '{c}' at line {line}, col {col}")
    
    tokens.append(Token(TokenType.EOF, None, line, col))
    return tokens


# ═══ AST ═══

@dataclass
class NumLit:
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
class Call:
    name: str
    args: List[Any]

@dataclass
class LetStmt:
    name: str
    value: Any

@dataclass
class AssignStmt:
    name: str
    value: Any

@dataclass
class PrintStmt:
    value: Any

@dataclass
class ReturnStmt:
    value: Any

@dataclass
class IfStmt:
    condition: Any
    then_body: List[Any]
    else_body: Optional[List[Any]]

@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]

@dataclass
class FnDef:
    name: str
    params: List[str]
    body: List[Any]

@dataclass
class Program:
    statements: List[Any]


# ═══ PARSER ═══

class ParseError(Exception):
    pass


class Parser:
    """Recursive descent parser"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self.pos = 0
    
    def peek(self) -> Token:
        return self.tokens[self.pos]
    
    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t
    
    def expect(self, tt: str) -> Token:
        t = self.advance()
        if t.type != tt:
            raise ParseError(f"Expected {tt}, got {t.type} ({t.value!r}) at line {t.line}")
        return t
    
    def match(self, *types) -> Optional[Token]:
        if self.peek().type in types:
            return self.advance()
        return None
    
    def parse(self) -> Program:
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_statement())
        return Program(stmts)
    
    def parse_statement(self):
        tt = self.peek().type
        
        if tt == TokenType.LET:
            return self.parse_let()
        elif tt == TokenType.FN:
            return self.parse_fn()
        elif tt == TokenType.IF:
            return self.parse_if()
        elif tt == TokenType.WHILE:
            return self.parse_while()
        elif tt == TokenType.RETURN:
            return self.parse_return()
        elif tt == TokenType.PRINT:
            return self.parse_print()
        elif tt == TokenType.IDENT and self.pos + 1 < len(self.tokens) and \
             self.tokens[self.pos + 1].type == TokenType.ASSIGN:
            return self.parse_assign()
        else:
            # Expression statement
            expr = self.parse_expr()
            return expr
    
    def parse_let(self):
        self.expect(TokenType.LET)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        value = self.parse_expr()
        return LetStmt(name, value)
    
    def parse_assign(self):
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        value = self.parse_expr()
        return AssignStmt(name, value)
    
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
        return FnDef(name, params, body)
    
    def parse_if(self):
        self.expect(TokenType.IF)
        cond = self.parse_expr()
        then = self.parse_block()
        els = None
        if self.match(TokenType.ELSE):
            if self.peek().type == TokenType.IF:
                els = [self.parse_if()]
            else:
                els = self.parse_block()
        return IfStmt(cond, then, els)
    
    def parse_while(self):
        self.expect(TokenType.WHILE)
        cond = self.parse_expr()
        body = self.parse_block()
        return WhileStmt(cond, body)
    
    def parse_return(self):
        self.expect(TokenType.RETURN)
        value = self.parse_expr()
        return ReturnStmt(value)
    
    def parse_print(self):
        self.expect(TokenType.PRINT)
        value = self.parse_expr()
        return PrintStmt(value)
    
    def parse_block(self) -> List:
        self.expect(TokenType.LBRACE)
        stmts = []
        while self.peek().type != TokenType.RBRACE:
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return stmts
    
    # Expression parsing with precedence climbing
    def parse_expr(self):
        return self.parse_or()
    
    def parse_or(self):
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinOp('or', left, right)
        return left
    
    def parse_and(self):
        left = self.parse_comparison()
        while self.match(TokenType.AND):
            right = self.parse_comparison()
            left = BinOp('and', left, right)
        return left
    
    def parse_comparison(self):
        left = self.parse_addition()
        while self.peek().type in (TokenType.EQ, TokenType.NEQ, TokenType.LT,
                                    TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.advance().value
            right = self.parse_addition()
            left = BinOp(op, left, right)
        return left
    
    def parse_addition(self):
        left = self.parse_multiplication()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplication()
            left = BinOp(op, left, right)
        return left
    
    def parse_multiplication(self):
        left = self.parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOp(op, left, right)
        return left
    
    def parse_unary(self):
        if self.match(TokenType.MINUS):
            return UnaryOp('-', self.parse_unary())
        if self.match(TokenType.NOT):
            return UnaryOp('not', self.parse_unary())
        return self.parse_primary()
    
    def parse_primary(self):
        t = self.peek()
        
        if t.type == TokenType.NUMBER:
            self.advance()
            return NumLit(t.value)
        
        if t.type == TokenType.STRING:
            self.advance()
            return StrLit(t.value)
        
        if t.type == TokenType.TRUE:
            self.advance()
            return BoolLit(True)
        
        if t.type == TokenType.FALSE:
            self.advance()
            return BoolLit(False)
        
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
            return Var(t.value)
        
        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr
        
        raise ParseError(f"Unexpected token {t} at line {t.line}")


# ═══ CODE GENERATOR ═══

class CompileError(Exception):
    pass


class CodeGen:
    """Compiles AST to XTStack bytecode"""
    
    def __init__(self):
        self.code = bytearray()
        self.constants: List[Any] = []
        self.string_pool: List[str] = []
        self.functions: Dict[str, int] = {}
        
        # Scope tracking
        self.scopes: List[Dict[str, int]] = [{}]  # global scope
        self.next_local: List[int] = [0]
        self.in_function: bool = False
    
    def emit(self, op: Op):
        self.code.append(op)
    
    def emit_arg(self, op: Op, arg: int):
        self.code.append(op)
        self.code.extend(struct.pack('<i', arg))
    
    def add_constant(self, value) -> int:
        if value in self.constants:
            return self.constants.index(value)
        self.constants.append(value)
        return len(self.constants) - 1
    
    def add_string(self, s: str) -> int:
        if s in self.string_pool:
            return self.string_pool.index(s)
        self.string_pool.append(s)
        return len(self.string_pool) - 1
    
    def current_addr(self) -> int:
        return len(self.code)
    
    def patch_jump(self, addr: int, target: int):
        """Patch a jump target at the given address"""
        packed = struct.pack('<i', target)
        self.code[addr:addr+4] = packed
    
    def push_scope(self):
        self.scopes.append({})
        self.next_local.append(0 if not self.in_function else self.next_local[-1])
    
    def pop_scope(self):
        self.scopes.pop()
        self.next_local.pop()
    
    def resolve_var(self, name: str) -> Tuple[bool, int]:
        """Resolve variable. Returns (is_local, index)"""
        # Search scopes from innermost to outermost
        for scope in reversed(self.scopes):
            if name in scope:
                is_global = (scope is self.scopes[0]) and not self.in_function
                return (not is_global, scope[name])
        raise CompileError(f"Undefined variable: {name}")
    
    def declare_var(self, name: str) -> Tuple[bool, int]:
        """Declare a variable in current scope"""
        scope = self.scopes[-1]
        if self.in_function:
            idx = self.next_local[-1]
            self.next_local[-1] += 1
            scope[name] = idx
            return (True, idx)
        else:
            idx = self.next_local[-1]
            self.next_local[-1] += 1
            scope[name] = idx
            return (False, idx)
    
    def compile(self, program: Program) -> Bytecode:
        """Compile a complete program"""
        # First pass: collect function definitions
        fn_defs = []
        main_stmts = []
        for stmt in program.statements:
            if isinstance(stmt, FnDef):
                fn_defs.append(stmt)
            else:
                main_stmts.append(stmt)
        
        # Jump over function bodies
        main_jump = self.current_addr()
        self.emit_arg(Op.JMP, 0)  # placeholder
        
        # Compile function definitions
        for fn in fn_defs:
            self.compile_fn(fn)
        
        # Patch main jump
        self.patch_jump(main_jump + 1, self.current_addr())
        
        # Compile main statements
        for stmt in main_stmts:
            self.compile_stmt(stmt)
        
        self.emit(Op.HALT)
        
        return Bytecode(
            instructions=bytes(self.code),
            constants=self.constants,
            string_pool=self.string_pool,
            functions=self.functions
        )
    
    def compile_fn(self, fn: FnDef):
        addr = self.current_addr()
        self.functions[fn.name] = addr
        
        # Set up function scope
        self.in_function = True
        self.push_scope()
        
        # Declare parameters (they're passed on the stack)
        # Parameters are pushed left-to-right, so we store them in reverse
        param_indices = []
        for param in fn.params:
            is_local, idx = self.declare_var(param)
            param_indices.append(idx)
        
        # Store parameters from stack into locals (reverse order)
        for idx in reversed(param_indices):
            self.emit_arg(Op.STORE, idx)
        
        # Compile body
        for stmt in fn.body:
            self.compile_stmt(stmt)
        
        # Default return 0 if no explicit return
        idx = self.add_constant(0)
        self.emit_arg(Op.PUSH, idx)
        self.emit(Op.RET)
        
        self.pop_scope()
        self.in_function = False
    
    def compile_stmt(self, stmt):
        if isinstance(stmt, LetStmt):
            self.compile_expr(stmt.value)
            is_local, idx = self.declare_var(stmt.name)
            if is_local:
                self.emit_arg(Op.STORE, idx)
            else:
                self.emit_arg(Op.GSTORE, idx)
        
        elif isinstance(stmt, AssignStmt):
            self.compile_expr(stmt.value)
            is_local, idx = self.resolve_var(stmt.name)
            if is_local:
                self.emit_arg(Op.STORE, idx)
            else:
                self.emit_arg(Op.GSTORE, idx)
        
        elif isinstance(stmt, PrintStmt):
            if isinstance(stmt.value, StrLit):
                idx = self.add_string(stmt.value.value)
                self.emit_arg(Op.PRINTS, idx)
            else:
                self.compile_expr(stmt.value)
                self.emit(Op.PRINT)
        
        elif isinstance(stmt, ReturnStmt):
            self.compile_expr(stmt.value)
            self.emit(Op.RET)
        
        elif isinstance(stmt, IfStmt):
            self.compile_expr(stmt.condition)
            # Jump to else/end if false
            jz_addr = self.current_addr()
            self.emit_arg(Op.JZ, 0)  # placeholder
            
            # Then body
            for s in stmt.then_body:
                self.compile_stmt(s)
            
            if stmt.else_body:
                # Jump over else
                jmp_addr = self.current_addr()
                self.emit_arg(Op.JMP, 0)  # placeholder
                
                # Patch JZ to here (else start)
                self.patch_jump(jz_addr + 1, self.current_addr())
                
                for s in stmt.else_body:
                    self.compile_stmt(s)
                
                # Patch JMP to here (after else)
                self.patch_jump(jmp_addr + 1, self.current_addr())
            else:
                self.patch_jump(jz_addr + 1, self.current_addr())
        
        elif isinstance(stmt, WhileStmt):
            loop_start = self.current_addr()
            self.compile_expr(stmt.condition)
            
            jz_addr = self.current_addr()
            self.emit_arg(Op.JZ, 0)  # placeholder
            
            for s in stmt.body:
                self.compile_stmt(s)
            
            self.emit_arg(Op.JMP, loop_start)
            self.patch_jump(jz_addr + 1, self.current_addr())
        
        elif isinstance(stmt, FnDef):
            pass  # Already handled in first pass
        
        else:
            # Expression statement - evaluate and discard
            self.compile_expr(stmt)
            self.emit(Op.POP)
    
    def compile_expr(self, expr):
        if isinstance(expr, NumLit):
            idx = self.add_constant(expr.value)
            self.emit_arg(Op.PUSH, idx)
        
        elif isinstance(expr, BoolLit):
            idx = self.add_constant(1 if expr.value else 0)
            self.emit_arg(Op.PUSH, idx)
        
        elif isinstance(expr, StrLit):
            idx = self.add_constant(expr.value)
            self.emit_arg(Op.PUSH, idx)
        
        elif isinstance(expr, Var):
            is_local, idx = self.resolve_var(expr.name)
            if is_local:
                self.emit_arg(Op.LOAD, idx)
            else:
                self.emit_arg(Op.GLOAD, idx)
        
        elif isinstance(expr, UnaryOp):
            self.compile_expr(expr.operand)
            if expr.op == '-':
                self.emit(Op.NEG)
            elif expr.op == 'not':
                self.emit(Op.NOT)
        
        elif isinstance(expr, BinOp):
            self.compile_expr(expr.left)
            self.compile_expr(expr.right)
            
            op_map = {
                '+': Op.ADD, '-': Op.SUB, '*': Op.MUL,
                '/': Op.DIV, '%': Op.MOD,
                '==': Op.EQ, '!=': Op.NEQ,
                '<': Op.LT, '>': Op.GT,
                '<=': Op.LTE, '>=': Op.GTE,
                'and': Op.AND, 'or': Op.OR,
            }
            if expr.op in op_map:
                self.emit(op_map[expr.op])
            else:
                raise CompileError(f"Unknown operator: {expr.op}")
        
        elif isinstance(expr, Call):
            if expr.name not in self.functions:
                raise CompileError(f"Undefined function: {expr.name}")
            
            # Push arguments left to right
            for arg in expr.args:
                self.compile_expr(arg)
            
            self.emit_arg(Op.CALL, self.functions[expr.name])
        
        else:
            raise CompileError(f"Unknown expression type: {type(expr)}")


def compile_source(source: str) -> Bytecode:
    """Convenience: source code -> bytecode"""
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    gen = CodeGen()
    return gen.compile(ast)