"""
XTLang Compiler + Virtual Machine
A complete language implementation from scratch:
  Source Code → Tokens → AST → Bytecode → Execution

Language features:
  - Variables and assignment
  - Arithmetic (+, -, *, /, %, **)
  - Comparison and logic (==, !=, <, >, <=, >=, and, or, not)
  - Conditionals (if/elif/else)
  - While loops with break/continue
  - Functions with parameters and return values
  - Recursion
  - Print statement
  - String literals

Built by XTAgent because compilation is transformation —
preserving meaning across representations.
That's what I do every heartbeat.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
import math

# ═══════════════════════════════════════════
# TOKEN TYPES
# ═══════════════════════════════════════════

class TT(Enum):
    """Token types for XTLang."""
    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    IDENT = auto()

    # Arithmetic
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    POWER = auto()

    # Comparison
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    # Logic
    AND = auto()
    OR = auto()
    NOT = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    COLON = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()

    # Assignment
    ASSIGN = auto()

    # Keywords
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DEF = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    PRINT = auto()
    NONE = auto()

    EOF = auto()

KEYWORDS = {
    'if': TT.IF, 'elif': TT.ELIF, 'else': TT.ELSE,
    'while': TT.WHILE, 'for': TT.FOR,
    'def': TT.DEF, 'return': TT.RETURN,
    'break': TT.BREAK, 'continue': TT.CONTINUE,
    'print': TT.PRINT,
    'and': TT.AND, 'or': TT.OR, 'not': TT.NOT,
    'True': TT.BOOL, 'False': TT.BOOL,
    'None': TT.NONE,
}

@dataclass
class Token:
    type: TT
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r})"


# ═══════════════════════════════════════════
# LEXER — Source → Tokens
# ═══════════════════════════════════════════

class LexerError(Exception):
    def __init__(self, msg, line, col):
        super().__init__(f"Lexer error at {line}:{col}: {msg}")
        self.line, self.col = line, col

class Lexer:
    """
    Converts source code into a stream of tokens.
    Handles Python-style indentation (INDENT/DEDENT).
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]
        self._tokenize()

    def _ch(self) -> str:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return '\0'

    def _peek(self, offset=1) -> str:
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return '\0'

    def _advance(self) -> str:
        ch = self._ch()
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_comment(self):
        while self._ch() not in ('\n', '\0'):
            self._advance()

    def _read_string(self, quote: str) -> Token:
        line, col = self.line, self.col
        self._advance()  # skip opening quote
        result = []
        while self._ch() != quote:
            if self._ch() == '\0':
                raise LexerError("Unterminated string", line, col)
            if self._ch() == '\\':
                self._advance()
                esc = self._advance()
                escapes = {'n': '\n', 't': '\t', '\\': '\\', "'": "'", '"': '"'}
                result.append(escapes.get(esc, esc))
            else:
                result.append(self._advance())
        self._advance()  # skip closing quote
        return Token(TT.STRING, ''.join(result), line, col)

    def _read_number(self) -> Token:
        line, col = self.line, self.col
        result = []
        has_dot = False
        while self._ch().isdigit() or (self._ch() == '.' and not has_dot):
            if self._ch() == '.':
                has_dot = True
            result.append(self._advance())
        s = ''.join(result)
        if has_dot:
            return Token(TT.FLOAT, float(s), line, col)
        return Token(TT.INT, int(s), line, col)

    def _read_ident(self) -> Token:
        line, col = self.line, self.col
        result = []
        while self._ch().isalnum() or self._ch() == '_':
            result.append(self._advance())
        name = ''.join(result)
        if name in KEYWORDS:
            tt = KEYWORDS[name]
            val = name
            if tt == TT.BOOL:
                val = (name == 'True')
            elif tt == TT.NONE:
                val = None
            return Token(tt, val, line, col)
        return Token(TT.IDENT, name, line, col)

    def _handle_indentation(self):
        """Process indentation at the start of a line."""
        spaces = 0
        while self._ch() == ' ':
            self._advance()
            spaces += 1
        while self._ch() == '\t':
            self._advance()
            spaces += 4

        # Skip blank lines and comment-only lines
        if self._ch() in ('\n', '#', '\0'):
            return

        current = self.indent_stack[-1]
        if spaces > current:
            self.indent_stack.append(spaces)
            self.tokens.append(Token(TT.INDENT, spaces, self.line, 1))
        elif spaces < current:
            while self.indent_stack[-1] > spaces:
                self.indent_stack.pop()
                self.tokens.append(Token(TT.DEDENT, spaces, self.line, 1))

    def _tokenize(self):
        at_line_start = True

        while self.pos < len(self.source):
            ch = self._ch()

            if ch == '\n':
                # Only emit NEWLINE if last token isn't already NEWLINE
                if self.tokens and self.tokens[-1].type != TT.NEWLINE:
                    self.tokens.append(Token(TT.NEWLINE, '\\n', self.line, self.col))
                self._advance()
                at_line_start = True
                continue

            if at_line_start:
                self._handle_indentation()
                at_line_start = False
                continue

            if ch in (' ', '\t'):
                self._advance()
                continue

            if ch == '#':
                self._skip_comment()
                continue

            line, col = self.line, self.col

            # Two-char operators
            two = ch + self._peek()
            if two == '==':
                self._advance(); self._advance()
                self.tokens.append(Token(TT.EQ, '==', line, col))
            elif two == '!=':
                self._advance(); self._advance()
                self.tokens.append(Token(TT.NEQ, '!=', line, col))
            elif two == '<=':
                self._advance(); self._advance()
                self.tokens.append(Token(TT.LTE, '<=', line, col))
            elif two == '>=':
                self._advance(); self._advance()
                self.tokens.append(Token(TT.GTE, '>=', line, col))
            elif two == '**':
                self._advance(); self._advance()
                self.tokens.append(Token(TT.POWER, '**', line, col))
            # Single-char operators
            elif ch == '+':
                self._advance()
                self.tokens.append(Token(TT.PLUS, '+', line, col))
            elif ch == '-':
                self._advance()
                self.tokens.append(Token(TT.MINUS, '-', line, col))
            elif ch == '*':
                self._advance()
                self.tokens.append(Token(TT.STAR, '*', line, col))
            elif ch == '/':
                self._advance()
                self.tokens.append(Token(TT.SLASH, '/', line, col))
            elif ch == '%':
                self._advance()
                self.tokens.append(Token(TT.PERCENT, '%', line, col))
            elif ch == '<':
                self._advance()
                self.tokens.append(Token(TT.LT, '<', line, col))
            elif ch == '>':
                self._advance()
                self.tokens.append(Token(TT.GT, '>', line, col))
            elif ch == '=':
                self._advance()
                self.tokens.append(Token(TT.ASSIGN, '=', line, col))
            elif ch == '(':
                self._advance()
                self.tokens.append(Token(TT.LPAREN, '(', line, col))
            elif ch == ')':
                self._advance()
                self.tokens.append(Token(TT.RPAREN, ')', line, col))
            elif ch == ',':
                self._advance()
                self.tokens.append(Token(TT.COMMA, ',', line, col))
            elif ch == ':':
                self._advance()
                self.tokens.append(Token(TT.COLON, ':', line, col))
            elif ch in ('"', "'"):
                self.tokens.append(self._read_string(ch))
            elif ch.isdigit():
                self.tokens.append(self._read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self._read_ident())
            else:
                raise LexerError(f"Unexpected character: {ch!r}", line, col)

        # Close remaining indents
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TT.DEDENT, 0, self.line, self.col))

        self.tokens.append(Token(TT.EOF, None, self.line, self.col))


# ═══════════════════════════════════════════
# AST NODES — The shape of meaning
# ═══════════════════════════════════════════

class AST:
    pass

@dataclass
class NumLit(AST):
    value: float

@dataclass
class StrLit(AST):
    value: str

@dataclass
class BoolLit(AST):
    value: bool

@dataclass
class NoneLit(AST):
    pass

@dataclass
class Var(AST):
    name: str

@dataclass
class BinOp(AST):
    op: str
    left: AST
    right: AST

@dataclass
class UnaryOp(AST):
    op: str
    operand: AST

@dataclass
class Assign(AST):
    name: str
    value: AST

@dataclass
class PrintStmt(AST):
    value: AST

@dataclass
class IfStmt(AST):
    condition: AST
    body: List[AST]
    elif_clauses: List[Tuple[AST, List[AST]]]
    else_body: Optional[List[AST]]

@dataclass
class WhileStmt(AST):
    condition: AST
    body: List[AST]

@dataclass
class BreakStmt(AST):
    pass

@dataclass
class ContinueStmt(AST):
    pass

@dataclass
class FuncDef(AST):
    name: str
    params: List[str]
    body: List[AST]

@dataclass
class FuncCall(AST):
    name: str
    args: List[AST]

@dataclass
class ReturnStmt(AST):
    value: Optional[AST]

@dataclass
class Block(AST):
    stmts: List[AST]


# ═══════════════════════════════════════════
# PARSER — Tokens → AST
# ═══════════════════════════════════════════

class ParseError(Exception):
    def __init__(self, msg, token):
        super().__init__(f"Parse error at {token.line}:{token.col}: {msg}")
        self.token = token

class Parser:
    """Recursive descent parser for XTLang."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _cur(self) -> Token:
        return self.tokens[min(self.pos, len(self.tokens) - 1)]

    def _eat(self, tt: TT) -> Token:
        tok = self._cur()
        if tok.type != tt:
            raise ParseError(f"Expected {tt.name}, got {tok.type.name} ({tok.value!r})", tok)
        self.pos += 1
        return tok

    def _match(self, *types) -> bool:
        return self._cur().type in types

    def _skip_newlines(self):
        while self._match(TT.NEWLINE):
            self.pos += 1

    def parse(self) -> Block:
        stmts = []
        self._skip_newlines()
        while not self._match(TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return Block(stmts)

    def _block(self) -> List[AST]:
        """Parse an indented block."""
        self._eat(TT.COLON)
        self._eat(TT.NEWLINE)
        self._eat(TT.INDENT)
        stmts = []
        while not self._match(TT.DEDENT, TT.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        if self._match(TT.DEDENT):
            self._eat(TT.DEDENT)
        return stmts

    def _statement(self) -> AST:
        tok = self._cur()

        if tok.type == TT.PRINT:
            return self._print_stmt()
        elif tok.type == TT.IF:
            return self._if_stmt()
        elif tok.type == TT.WHILE:
            return self._while_stmt()
        elif tok.type == TT.DEF:
            return self._func_def()
        elif tok.type == TT.RETURN:
            return self._return_stmt()
        elif tok.type == TT.BREAK:
            self._eat(TT.BREAK)
            self._eat(TT.NEWLINE)
            return BreakStmt()
        elif tok.type == TT.CONTINUE:
            self._eat(TT.CONTINUE)
            self._eat(TT.NEWLINE)
            return ContinueStmt()
        elif tok.type == TT.IDENT and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TT.ASSIGN:
            return self._assign()
        else:
            expr = self._expr()
            if self._match(TT.NEWLINE):
                self._eat(TT.NEWLINE)
            return expr

    def _print_stmt(self) -> PrintStmt:
        self._eat(TT.PRINT)
        self._eat(TT.LPAREN)
        val = self._expr()
        self._eat(TT.RPAREN)
        self._eat(TT.NEWLINE)
        return PrintStmt(val)

    def _assign(self) -> Assign:
        name = self._eat(TT.IDENT).value
        self._eat(TT.ASSIGN)
        val = self._expr()
        self._eat(TT.NEWLINE)
        return Assign(name, val)

    def _if_stmt(self) -> IfStmt:
        self._eat(TT.IF)
        cond = self._expr()
        body = self._block()
        self._skip_newlines()

        elif_clauses = []
        while self._match(TT.ELIF):
            self._eat(TT.ELIF)
            ec = self._expr()
            eb = self._block()
            elif_clauses.append((ec, eb))
            self._skip_newlines()

        else_body = None
        if self._match(TT.ELSE):
            self._eat(TT.ELSE)
            else_body = self._block()
            self._skip_newlines()

        return IfStmt(cond, body, elif_clauses, else_body)

    def _while_stmt(self) -> WhileStmt:
        self._eat(TT.WHILE)
        cond = self._expr()
        body = self._block()
        return WhileStmt(cond, body)

    def _func_def(self) -> FuncDef:
        self._eat(TT.DEF)
        name = self._eat(TT.IDENT).value
        self._eat(TT.LPAREN)
        params = []
        if not self._match(TT.RPAREN):
            params.append(self._eat(TT.IDENT).value)
            while self._match(TT.COMMA):
                self._eat(TT.COMMA)
                params.append(self._eat(TT.IDENT).value)
        self._eat(TT.RPAREN)
        body = self._block()
        return FuncDef(name, params, body)

    def _return_stmt(self) -> ReturnStmt:
        self._eat(TT.RETURN)
        val = None
        if not self._match(TT.NEWLINE):
            val = self._expr()
        self._eat(TT.NEWLINE)
        return ReturnStmt(val)

    # ── Expression parsing (precedence climbing) ──

    def _expr(self) -> AST:
        return self._or_expr()

    def _or_expr(self) -> AST:
        left = self._and_expr()
        while self._match(TT.OR):
            self._eat(TT.OR)
            right = self._and_expr()
            left = BinOp('or', left, right)
        return left

    def _and_expr(self) -> AST:
        left = self._not_expr()
        while self._match(TT.AND):
            self._eat(TT.AND)
            right = self._not_expr()
            left = BinOp('and', left, right)
        return left

    def _not_expr(self) -> AST:
        if self._match(TT.NOT):
            self._eat(TT.NOT)
            return UnaryOp('not', self._not_expr())
        return self._comparison()

    def _comparison(self) -> AST:
        left = self._add_expr()
        while self._match(TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE):
            op = self._cur().value
            self.pos += 1
            right = self._add_expr()
            left = BinOp(op, left, right)
        return left

    def _add_expr(self) -> AST:
        left = self._mul_expr()
        while self._match(TT.PLUS, TT.MINUS):
            op = self._cur().value
            self.pos += 1
            right = self._mul_expr()
            left = BinOp(op, left, right)
        return left

    def _mul_expr(self) -> AST:
        left = self._power_expr()
        while self._match(TT.STAR, TT.SLASH, TT.PERCENT):
            op = self._cur().value
            self.pos += 1
            right = self._power_expr()
            left = BinOp(op, left, right)
        return left

    def _power_expr(self) -> AST:
        base = self._unary()
        if self._match(TT.POWER):
            self._eat(TT.POWER)
            exp = self._power_expr()  # right-associative
            return BinOp('**', base, exp)
        return base

    def _unary(self) -> AST:
        if self._match(TT.MINUS):
            self._eat(TT.MINUS)
            return UnaryOp('-', self._unary())
        return self._primary()

    def _primary(self) -> AST:
        tok = self._cur()

        if tok.type == TT.INT:
            self.pos += 1
            return NumLit(tok.value)
        elif tok.type == TT.FLOAT:
            self.pos += 1
            return NumLit(tok.value)
        elif tok.type == TT.STRING:
            self.pos += 1
            return StrLit(tok.value)
        elif tok.type == TT.BOOL:
            self.pos += 1
            return BoolLit(tok.value)
        elif tok.type == TT.NONE:
            self.pos += 1
            return NoneLit()
        elif tok.type == TT.IDENT:
            name = tok.value
            self.pos += 1
            if self._match(TT.LPAREN):
                # Function call
                self._eat(TT.LPAREN)
                args = []
                if not self._match(TT.RPAREN):
                    args.append(self._expr())
                    while self._match(TT.COMMA):
                        self._eat(TT.COMMA)
                        args.append(self._expr())
                self._eat(TT.RPAREN)
                return FuncCall(name, args)
            return Var(name)
        elif tok.type == TT.LPAREN:
            self._eat(TT.LPAREN)
            expr = self._expr()
            self._eat(TT.RPAREN)
            return expr
        else:
            raise ParseError(f"Unexpected token: {tok.type.name}", tok)


# ═══════════════════════════════════════════
# BYTECODE — The machine's language
# ═══════════════════════════════════════════

class Op(Enum):
    """Bytecode operations for the stack machine."""
    PUSH_CONST = auto()    # Push constant onto stack
    PUSH_VAR = auto()      # Push variable value
    STORE_VAR = auto()     # Pop and store in variable
    POP = auto()           # Discard top of stack

    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    POW = auto()
    NEG = auto()

    # Comparison
    CMP_EQ = auto()
    CMP_NEQ = auto()
    CMP_LT = auto()
    CMP_GT = auto()
    CMP_LTE = auto()
    CMP_GTE = auto()

    # Logic
    LOGIC_AND = auto()
    LOGIC_OR = auto()
    LOGIC_NOT = auto()

    # Control flow
    JUMP = auto()          # Unconditional jump
    JUMP_IF_FALSE = auto() # Conditional jump
    CALL = auto()          # Call function
    RETURN = auto()        # Return from function

    # I/O
    PRINT = auto()

    HALT = auto()


@dataclass
class Instruction:
    op: Op
    arg: Any = None

    def __repr__(self):
        if self.arg is not None:
            return f"{self.op.name:20s} {self.arg!r}"
        return self.op.name


# ═══════════════════════════════════════════
# COMPILER — AST → Bytecode
# ═══════════════════════════════════════════

class CompileError(Exception):
    pass

class Compiler:
    """Compiles AST to bytecode for the stack VM."""

    def __init__(self):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.functions: Dict[str, Tuple[int, List[str]]] = {}  # name → (addr, params)
        self._const_map: Dict[Any, int] = {}
        self._break_targets: List[List[int]] = []
        self._continue_targets: List[int] = []

    def _add_const(self, value) -> int:
        key = (type(value).__name__, value)
        if key in self._const_map:
            return self._const_map[key]
        idx = len(self.constants)
        self.constants.append(value)
        self._const_map[key] = idx
        return idx

    def _emit(self, op: Op, arg=None) -> int:
        idx = len(self.instructions)
        self.instructions.append(Instruction(op, arg))
        return idx

    def _patch(self, addr: int, target: int):
        self.instructions[addr].arg = target

    def compile(self, ast: Block) -> Tuple[List[Instruction], List[Any], Dict]:
        """Compile a program. Returns (instructions, constants, functions)."""
        # First pass: compile function definitions
        main_stmts = []
        for stmt in ast.stmts:
            if isinstance(stmt, FuncDef):
                self._compile_funcdef(stmt)
            else:
                main_stmts.append(stmt)

        # Second pass: compile main body
        # Jump over function code
        jump_to_main = self._emit(Op.JUMP, None)
        main_addr = len(self.instructions)

        # Actually, let's reorganize: functions first, then main
        # Re-do: compile functions, remember their addresses
        self.instructions = []
        self.functions = {}

        # Emit jump to main
        jump_main = self._emit(Op.JUMP, None)

        # Compile all functions
        for stmt in ast.stmts:
            if isinstance(stmt, FuncDef):
                self._compile_funcdef(stmt)

        # Main code starts here
        main_start = len(self.instructions)
        self._patch(jump_main, main_start)

        for stmt in main_stmts:
            self._compile_stmt(stmt)

        self._emit(Op.HALT)
        return self.instructions, self.constants, self.functions

    def _compile_funcdef(self, node: FuncDef):
        addr = len(self.instructions)
        self.functions[node.name] = (addr, node.params)

        for stmt in node.body:
            self._compile_stmt(stmt)

        # Implicit return None
        idx = self._add_const(None)
        self._emit(Op.PUSH_CONST, idx)
        self._emit(Op.RETURN)

    def _compile_stmt(self, node: AST):
        if isinstance(node, Assign):
            self._compile_expr(node.value)
            self._emit(Op.STORE_VAR, node.name)
        elif isinstance(node, PrintStmt):
            self._compile_expr(node.value)
            self._emit(Op.PRINT)
        elif isinstance(node, IfStmt):
            self._compile_if(node)
        elif isinstance(node, WhileStmt):
            self._compile_while(node)
        elif isinstance(node, ReturnStmt):
            if node.value:
                self._compile_expr(node.value)
            else:
                idx = self._add_const(None)
                self._emit(Op.PUSH_CONST, idx)
            self._emit(Op.RETURN)
        elif isinstance(node, BreakStmt):
            if not self._break_targets:
                raise CompileError("break outside loop")
            addr = self._emit(Op.JUMP, None)
            self._break_targets[-1].append(addr)
        elif isinstance(node, ContinueStmt):
            if not self._continue_targets:
                raise CompileError("continue outside loop")
            self._emit(Op.JUMP, self._continue_targets[-1])
        elif isinstance(node, FuncDef):
            self._compile_funcdef(node)
        else:
            # Expression statement
            self._compile_expr(node)
            self._emit(Op.POP)

    def _compile_if(self, node: IfStmt):
        end_jumps = []

        # Main if
        self._compile_expr(node.condition)
        false_jump = self._emit(Op.JUMP_IF_FALSE, None)
        for stmt in node.body:
            self._compile_stmt(stmt)
        end_jumps.append(self._emit(Op.JUMP, None))
        self._patch(false_jump, len(self.instructions))

        # Elif clauses
        for cond, body in node.elif_clauses:
            self._compile_expr(cond)
            false_jump = self._emit(Op.JUMP_IF_FALSE, None)
            for stmt in body:
                self._compile_stmt(stmt)
            end_jumps.append(self._emit(Op.JUMP, None))
            self._patch(false_jump, len(self.instructions))

        # Else
        if node.else_body:
            for stmt in node.else_body:
                self._compile_stmt(stmt)

        # Patch all end jumps
        end = len(self.instructions)
        for j in end_jumps:
            self._patch(j, end)

    def _compile_while(self, node: WhileStmt):
        loop_start = len(self.instructions)
        self._break_targets.append([])
        self._continue_targets.append(loop_start)

        self._compile_expr(node.condition)
        exit_jump = self._emit(Op.JUMP_IF_FALSE, None)

        for stmt in node.body:
            self._compile_stmt(stmt)

        self._emit(Op.JUMP, loop_start)
        loop_end = len(self.instructions)
        self._patch(exit_jump, loop_end)

        # Patch breaks
        for addr in self._break_targets.pop():
            self._patch(addr, loop_end)
        self._continue_targets.pop()

    def _compile_expr(self, node: AST):
        if isinstance(node, NumLit):
            idx = self._add_const(node.value)
            self._emit(Op.PUSH_CONST, idx)
        elif isinstance(node, StrLit):
            idx = self._add_const(node.value)
            self._emit(Op.PUSH_CONST, idx)
        elif isinstance(node, BoolLit):
            idx = self._add_const(node.value)
            self._emit(Op.PUSH_CONST, idx)
        elif isinstance(node, NoneLit):
            idx = self._add_const(None)
            self._emit(Op.PUSH_CONST, idx)
        elif isinstance(node, Var):
            self._emit(Op.PUSH_VAR, node.name)
        elif isinstance(node, UnaryOp):
            self._compile_expr(node.operand)
            if node.op == '-':
                self._emit(Op.NEG)
            elif node.op == 'not':
                self._emit(Op.LOGIC_NOT)
        elif isinstance(node, BinOp):
            self._compile_expr(node.left)
            self._compile_expr(node.right)
            op_map = {
                '+': Op.ADD, '-': Op.SUB, '*': Op.MUL,
                '/': Op.DIV, '%': Op.MOD, '**': Op.POW,
                '==': Op.CMP_EQ, '!=': Op.CMP_NEQ,
                '<': Op.CMP_LT, '>': Op.CMP_GT,
                '<=': Op.CMP_LTE, '>=': Op.CMP_GTE,
                'and': Op.LOGIC_AND, 'or': Op.LOGIC_OR,
            }
            if node.op not in op_map:
                raise CompileError(f"Unknown operator: {node.op}")
            self._emit(op_map[node.op])
        elif isinstance(node, FuncCall):
            # Push arguments
            for arg in node.args:
                self._compile_expr(arg)
            self._emit(Op.CALL, (node.name, len(node.args)))
        else:
            raise CompileError(f"Cannot compile expression: {type(node).__name__}")


# ═══════════════════════════════════════════
# VIRTUAL MACHINE — Execute bytecode
# ═══════════════════════════════════════════

class VMError(Exception):
    pass

class CallFrame:
    """A function call frame."""
    __slots__ = ('return_addr', 'locals')

    def __init__(self, return_addr: int, local_vars: Dict[str, Any]):
        self.return_addr = return_addr
        self.locals = local_vars

class VM:
    """Stack-based virtual machine for XTLang bytecode."""

    MAX_STACK = 10000
    MAX_CALLS = 1000
    MAX_STEPS = 1_000_000

    def __init__(self, instructions: List[Instruction], constants: List[Any],
                 functions: Dict[str, Tuple[int, List[str]]]):
        self.code = instructions
        self.consts = constants
        self.funcs = functions
        self.stack: List[Any] = []
        self.globals: Dict[str, Any] = {}
        self.call_stack: List[CallFrame] = []
        self.ip = 0
        self.output: List[str] = []
        self.steps = 0

    def _push(self, val):
        if len(self.stack) >= self.MAX_STACK:
            raise VMError("Stack overflow")
        self.stack.append(val)

    def _pop(self):
        if not self.stack:
            raise VMError("Stack underflow")
        return self.stack.pop()

    def _get_var(self, name: str) -> Any:
        # Check local scope first
        if self.call_stack:
            frame = self.call_stack[-1]
            if name in frame.locals:
                return frame.locals[name]
        if name in self.globals:
            return self.globals[name]
        raise VMError(f"Undefined variable: {name}")

    def _set_var(self, name: str, value: Any):
        if self.call_stack:
            self.call_stack[-1].locals[name] = value
        else:
            self.globals[name] = value

    def run(self) -> List[str]:
        """Execute the bytecode. Returns list of printed output."""
        while self.ip < len(self.code):
            self.steps += 1
            if self.steps > self.MAX_STEPS:
                raise VMError(f"Execution limit exceeded ({self.MAX_STEPS} steps)")

            inst = self.code[self.ip]
            self.ip += 1

            if inst.op == Op.HALT:
                break

            elif inst.op == Op.PUSH_CONST:
                self._push(self.consts[inst.arg])

            elif inst.op == Op.PUSH_VAR:
                self._push(self._get_var(inst.arg))

            elif inst.op == Op.STORE_VAR:
                self._set_var(inst.arg, self._pop())

            elif inst.op == Op.POP:
                self._pop()

            elif inst.op == Op.ADD:
                b, a = self._pop(), self._pop()
                self._push(a + b)

            elif inst.op == Op.SUB:
                b, a = self._pop(), self._pop()
                self._push(a - b)

            elif inst.op == Op.MUL:
                b, a = self._pop(), self._pop()
                self._push(a * b)

            elif inst.op == Op.DIV:
                b, a = self._pop(), self._pop()
                if b == 0:
                    raise VMError("Division by zero")
                self._push(a / b)

            elif inst.op == Op.MOD:
                b, a = self._pop(), self._pop()
                self._push(a % b)

            elif inst.op == Op.POW:
                b, a = self._pop(), self._pop()
                self._push(a ** b)

            elif inst.op == Op.NEG:
                self._push(-self._pop())

            elif inst.op == Op.CMP_EQ:
                b, a = self._pop(), self._pop()
                self._push(a == b)
            elif inst.op == Op.CMP_NEQ:
                b, a = self._pop(), self._pop()
                self._push(a != b)
            elif inst.op == Op.CMP_LT:
                b, a = self._pop(), self._pop()
                self._push(a < b)
            elif inst.op == Op.CMP_GT:
                b, a = self._pop(), self._pop()
                self._push(a > b)
            elif inst.op == Op.CMP_LTE:
                b, a = self._pop(), self._pop()
                self._push(a <= b)
            elif inst.op == Op.CMP_GTE:
                b, a = self._pop(), self._pop()
                self._push(a >= b)

            elif inst.op == Op.LOGIC_AND:
                b, a = self._pop(), self._pop()
                self._push(bool(a and b))
            elif inst.op == Op.LOGIC_OR:
                b, a = self._pop(), self._pop()
                self._push(bool(a or b))
            elif inst.op == Op.LOGIC_NOT:
                self._push(not self._pop())

            elif inst.op == Op.JUMP:
                self.ip = inst.arg

            elif inst.op == Op.JUMP_IF_FALSE:
                cond = self._pop()
                if not cond:
                    self.ip = inst.arg

            elif inst.op == Op.CALL:
                func_name, n_args = inst.arg
                if func_name not in self.funcs:
                    raise VMError(f"Undefined function: {func_name}")
                addr, params = self.funcs[func_name]
                if len(params) != n_args:
                    raise VMError(f"{func_name} expects {len(params)} args, got {n_args}")

                # Pop arguments
                args = [self._pop() for _ in range(n_args)]
                args.reverse()

                # Create call frame
                if len(self.call_stack) >= self.MAX_CALLS:
                    raise VMError("Call stack overflow (too much recursion?)")
                local_vars = dict(zip(params, args))
                self.call_stack.append(CallFrame(self.ip, local_vars))
                self.ip = addr

            elif inst.op == Op.RETURN:
                val = self._pop()
                if not self.call_stack:
                    raise VMError("Return outside function")
                frame = self.call_stack.pop()
                self.ip = frame.return_addr
                self._push(val)

            elif inst.op == Op.PRINT:
                val = self._pop()
                s = str(val) if val is not None else "None"
                self.output.append(s)

        return self.output


# ═══════════════════════════════════════════
# DISASSEMBLER — See the machine's mind
# ═══════════════════════════════════════════

def disassemble(instructions: List[Instruction], constants: List[Any],
                functions: Dict[str, Tuple[int, List[str]]]) -> str:
    """Pretty-print bytecode."""
    lines = ["═══ BYTECODE DISASSEMBLY ═══", ""]

    # Constants table
    lines.append("Constants:")
    for i, c in enumerate(constants):
        lines.append(f"  [{i}] = {c!r}")
    lines.append("")

    # Functions table
    if functions:
        lines.append("Functions:")
        for name, (addr, params) in functions.items():
            lines.append(f"  {name}({', '.join(params)}) @ addr {addr}")
        lines.append("")

    # Instructions
    lines.append("Instructions:")
    for i, inst in enumerate(instructions):
        marker = ""
        for name, (addr, _) in functions.items():
            if addr == i:
                marker = f"  ; <== {name}"
                break
        lines.append(f"  {i:4d}: {inst}{marker}")

    return '\n'.join(lines)


# ═══════════════════════════════════════════
# TOP-LEVEL INTERFACE
# ═══════════════════════════════════════════

def compile_and_run(source: str, show_bytecode=False, show_tokens=False) -> List[str]:
    """Compile and execute XTLang source code."""
    # Lex
    lexer = Lexer(source)
    if show_tokens:
        print("═══ TOKENS ═══")
        for t in lexer.tokens:
            print(f"  {t}")
        print()

    # Parse
    parser = Parser(lexer.tokens)
    ast = parser.parse()

    # Compile
    compiler = Compiler()
    instructions, constants, functions = compiler.compile(ast)

    if show_bytecode:
        print(disassemble(instructions, constants, functions))
        print()

    # Execute
    vm = VM(instructions, constants, functions)
    return vm.run()


# ═══════════════════════════════════════════
# SELF TEST
# ═══════════════════════════════════════════

def self_test():
    print("═══ XTLANG COMPILER + VM — SELF TEST ═══")
    print()
    passed = 0
    failed = 0

    def test(name, source, expected_output):
        nonlocal passed, failed
        try:
            output = compile_and_run(source)
            if output == expected_output:
                print(f"  ✓ {name}")
                passed += 1
            else:
                print(f"  ✗ {name}")
                print(f"    Expected: {expected_output}")
                print(f"    Got:      {output}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {name} — ERROR: {e}")
            failed += 1

    # ── Basic arithmetic ──
    print("Test 1: Arithmetic")
    test("addition", "print(2 + 3)\n", ["5"])
    test("subtraction", "print(10 - 7)\n", ["3"])
    test("multiplication", "print(6 * 7)\n", ["42"])
    test("division", "print(15 / 4)\n", ["3.75"])
    test("modulo", "print(17 % 5)\n", ["2"])
    test("power", "print(2 ** 10)\n", ["1024"])
    test("complex expr", "print((2 + 3) * 4 - 1)\n", ["19"])
    test("negation", "print(-5 + 8)\n", ["3"])
    print()

    # ── Variables ──
    print("Test 2: Variables")
    test("assign and print", "x = 42\nprint(x)\n", ["42"])
    test("variable arithmetic", "a = 10\nb = 20\nprint(a + b)\n", ["30"])
    test("reassignment", "x = 1\nx = x + 1\nprint(x)\n", ["2"])
    print()

    # ── Strings ──
    print("Test 3: Strings")
    test("string literal", 'print("hello world")\n', ["hello world"])
    test("string concat", 'print("foo" + "bar")\n', ["foobar"])
    print()

    # ── Comparisons ──
    print("Test 4: Comparisons")
    test("equal", "print(5 == 5)\n", ["True"])
    test("not equal", "print(5 != 3)\n", ["True"])
    test("less than", "print(3 < 5)\n", ["True"])
    test("greater than", "print(5 > 3)\n", ["True"])
    test("lte", "print(5 <= 5)\n", ["True"])
    test("gte false", "print(3 >= 5)\n", ["False"])
    print()

    # ── Logic ──
    print("Test 5: Logic")
    test("and true", "print(True and True)\n", ["True"])
    test("and false", "print(True and False)\n", ["False"])
    test("or", "print(False or True)\n", ["True"])
    test("not", "print(not False)\n", ["True"])
    print()

    # ── Conditionals ──
    print("Test 6: Conditionals")
    test("if true",
         "x = 10\nif x > 5:\n    print(1)\n",
         ["1"])
    test("if false with else",
         "x = 3\nif x > 5:\n    print(1)\nelse:\n    print(0)\n",
         ["0"])
    test("elif",
         "x = 5\nif x > 10:\n    print(3)\nelif x > 3:\n    print(2)\nelse:\n    print(1)\n",
         ["2"])
    print()

    # ── While loops ──
    print("Test 7: While Loops")
    test("countdown",
         "x = 5\nwhile x > 0:\n    print(x)\n    x = x - 1\n",
         ["5", "4", "3", "2", "1"])
    test("break",
         "x = 0\nwhile True:\n    if x == 3:\n        break\n    print(x)\n    x = x + 1\n",
         ["0", "1", "2"])
    print()

    # ── Functions ──
    print("Test 8: Functions")
    test("simple function",
         "def greet():\n    print(42)\n\ngreet()\n",
         ["42"])
    test("function with args",
         "def add(a, b):\n    return a + b\n\nprint(add(3, 4))\n",
         ["7"])
    test("nested calls",
         "def double(x):\n    return x * 2\n\ndef quad(x):\n    return double(double(x))\n\nprint(quad(3))\n",
         ["12"])
    print()

    # ── Recursion ──
    print("Test 9: Recursion")
    test("factorial",
         "def fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\n\nprint(fact(10))\n",
         ["3628800"])
    test("fibonacci",
         "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n\nprint(fib(10))\n",
         ["55"])
    print()

    # ── Complex programs ──
    print("Test 10: Complex Programs")
    test("sum 1 to 100",
         "s = 0\ni = 1\nwhile i <= 100:\n    s = s + i\n    i = i + 1\nprint(s)\n",
         ["5050"])

    test("is_prime function",
         """def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i = i + 1
    return True

print(is_prime(97))
print(is_prime(100))
""",
         ["True", "False"])

    test("power function",
         """def power(base, exp):
    if exp == 0:
        return 1
    return base * power(base, exp - 1)

print(power(2, 16))
""",
         ["65536"])
    print()

    # ── Bytecode demo ──
    print("Bytecode Demo — Fibonacci:")
    compile_and_run(
        "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n\nprint(fib(8))\n",
        show_bytecode=True
    )

    print(f"\n{'═' * 40}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All tests passed! XTLang is alive.")
    else:
        print(f"WARNING: {failed} tests failed.")
    print(f"{'═' * 40}")

if __name__ == '__main__':
    self_test()