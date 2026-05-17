"""XTLang Parser — Transforms token stream into an Abstract Syntax Tree.

Recursive descent parser. The grammar:

program     → statement* EOF
statement   → let_stmt | expr_stmt
let_stmt    → 'let' IDENT '=' expression ';'
expr_stmt   → expression ';'

expression  → if_expr | fn_expr | comparison
if_expr     → 'if' expression 'then' expression 'else' expression
fn_expr     → 'fn' '(' params? ')' '->' expression
comparison  → addition (('>' | '<' | '>=' | '<=' | '==' | '!=') addition)*
addition    → multiply (('+' | '-') multiply)*
multiply    → unary (('*' | '/') unary)*
unary       → ('-' | 'not') unary | call
call        → primary ('(' arguments? ')')*
primary     → INTEGER | FLOAT | STRING | BOOL | EMOTION | IDENT
            | '(' expression ')' | '{' block '}' | '[' list ']'
block       → statement* expression
list        → expression (',' expression)*

Built by XTAgent — my first programming language.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from lexer import Lexer, Token, TokenType


# ═══════════════════════════════════════════
# AST Node Definitions
# ═══════════════════════════════════════════

@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    col: int = 0

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)

@dataclass  
class LetStatement(ASTNode):
    name: str = ""
    value: ASTNode = None

@dataclass
class IntegerLiteral(ASTNode):
    value: int = 0

@dataclass
class FloatLiteral(ASTNode):
    value: float = 0.0

@dataclass
class StringLiteral(ASTNode):
    value: str = ""

@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

@dataclass
class EmotionLiteral(ASTNode):
    """Unique to XTLang — an emotion as a first-class value."""
    value: str = ""

@dataclass
class Identifier(ASTNode):
    name: str = ""

@dataclass
class BinaryOp(ASTNode):
    op: str = ""
    left: ASTNode = None
    right: ASTNode = None

@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    operand: ASTNode = None

@dataclass
class IfExpression(ASTNode):
    condition: ASTNode = None
    then_branch: ASTNode = None
    else_branch: ASTNode = None

@dataclass
class FnExpression(ASTNode):
    params: List[str] = field(default_factory=list)
    body: ASTNode = None

@dataclass
class CallExpression(ASTNode):
    function: ASTNode = None
    arguments: List[ASTNode] = field(default_factory=list)

@dataclass
class BlockExpression(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)
    final_expr: ASTNode = None

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)

@dataclass
class AssignStatement(ASTNode):
    """Reassign an existing variable."""
    name: str = ""
    value: ASTNode = None

@dataclass
class PrintStatement(ASTNode):
    value: ASTNode = None

@dataclass
class FeelStatement(ASTNode):
    """Set the interpreter's emotional context. Unique to XTLang."""
    emotion: str = ""

@dataclass
class IntrospectExpression(ASTNode):
    """Dump the trace buffer — only meaningful under @curious."""
    pass

@dataclass
class WhileExpression(ASTNode):
    """While loop — emotional modulation changes iteration behavior."""
    condition: ASTNode = None
    body: ASTNode = None


# ═══════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════

class ParseError(Exception):
    def __init__(self, message, token=None):
        self.token = token
        loc = f" at L{token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{loc}: {message}")


class Parser:
    def __init__(self, tokens):
        # Accept either a list of tokens or a Lexer object
        if hasattr(tokens, 'tokenize'):
            self.tokens = tokens.tokenize()
        elif hasattr(tokens, 'tokens'):
            self.tokens = tokens.tokens
        else:
            self.tokens = tokens
        self.pos = 0

    # ── Token Navigation ──

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, token_type: str) -> Token:
        tok = self.current()
        if tok.type != token_type:
            raise ParseError(f"Expected {token_type}, got {tok.type} ('{tok.value}')", tok)
        return self.advance()

    def match(self, *types) -> Optional[Token]:
        if self.current().type in types:
            return self.advance()
        return None

    # ── Top-Level Parsing ──

    def parse(self) -> Program:
        program = Program(statements=[])
        while self.current().type != TokenType.EOF:
            stmt = self.parse_statement()
            program.statements.append(stmt)
        return program

    def parse_statement(self):
        tok = self.current()

        if tok.type == TokenType.LET:
            return self.parse_let()
        elif tok.type == TokenType.FEEL:
            return self.parse_feel()
        elif tok.type == TokenType.IDENT and self.peek().type == TokenType.EQ:
            return self.parse_assign()
        else:
            return self.parse_expr_statement()

    def parse_assign(self) -> 'AssignStatement':
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.EQ)
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return AssignStatement(line=name_tok.line, col=name_tok.col,
                              name=name_tok.value, value=value)

    def parse_feel(self) -> FeelStatement:
        feel_tok = self.expect(TokenType.FEEL)
        emotion_tok = self.expect(TokenType.EMOTION)
        self.expect(TokenType.SEMICOLON)
        return FeelStatement(line=feel_tok.line, col=feel_tok.col,
                            emotion=emotion_tok.value)

    def parse_let(self) -> LetStatement:
        let_tok = self.expect(TokenType.LET)
        name_tok = self.expect(TokenType.IDENT)
        self.expect(TokenType.EQ)
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return LetStatement(line=let_tok.line, col=let_tok.col,
                           name=name_tok.value, value=value)

    def parse_print_expr(self) -> PrintStatement:
        """Parse print(expr) or print expr — no semicolon consumed here."""
        print_tok = self.expect(TokenType.PRINT)
        if self.current().type == TokenType.LPAREN:
            self.advance()
            value = self.parse_expression()
            self.expect(TokenType.RPAREN)
        else:
            value = self.parse_expression()
        return PrintStatement(line=print_tok.line, col=print_tok.col, value=value)

    def parse_expr_statement(self):
        expr = self.parse_expression()
        # Semicolon is optional for the last expression (implicit return)
        if self.current().type != TokenType.EOF:
            self.expect(TokenType.SEMICOLON)
        return expr

    # ── Expression Parsing (Precedence Climbing) ──

    def parse_expression(self):
        tok = self.current()

        if tok.type == TokenType.IF:
            return self.parse_if()
        elif tok.type == TokenType.FN:
            return self.parse_fn()
        elif tok.type == TokenType.PRINT:
            return self.parse_print_expr()
        elif tok.type == TokenType.INTROSPECT:
            return self.parse_introspect()
        elif tok.type == TokenType.WHILE:
            return self.parse_while()

        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.current().type == TokenType.OR:
            op_tok = self.advance()
            right = self.parse_and()
            left = BinaryOp(line=op_tok.line, col=op_tok.col,
                           op=op_tok.value, left=left, right=right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.current().type == TokenType.AND:
            op_tok = self.advance()
            right = self.parse_comparison()
            left = BinaryOp(line=op_tok.line, col=op_tok.col,
                           op=op_tok.value, left=left, right=right)
        return left

    def parse_while(self) -> 'WhileExpression':
        w_tok = self.expect(TokenType.WHILE)
        condition = self.parse_or()
        body = self.parse_expression()
        return WhileExpression(line=w_tok.line, col=w_tok.col,
                              condition=condition, body=body)

    def parse_introspect(self) -> IntrospectExpression:
        tok = self.expect(TokenType.INTROSPECT)
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)
        return IntrospectExpression(line=tok.line, col=tok.col)

    def parse_if(self) -> IfExpression:
        if_tok = self.expect(TokenType.IF)
        condition = self.parse_or()

        # Support both original syntax:
        #   if cond then expr else expr
        # and block syntax used by the test suite:
        #   if cond { expr } else { expr }
        if self.current().type == TokenType.THEN:
            self.advance()

        then_branch = self.parse_expression()
        self.expect(TokenType.ELSE)
        else_branch = self.parse_expression()
        return IfExpression(line=if_tok.line, col=if_tok.col,
                           condition=condition,
                           then_branch=then_branch,
                           else_branch=else_branch)

    def parse_fn(self) -> FnExpression:
        fn_tok = self.expect(TokenType.FN)
        self.expect(TokenType.LPAREN)
        params = []
        if self.current().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)

        # Support both fn(x) -> expr and fn(x) { expr }.
        if self.current().type == TokenType.ARROW:
            self.advance()

        body = self.parse_expression()
        return FnExpression(line=fn_tok.line, col=fn_tok.col,
                           params=params, body=body)

    def parse_comparison(self):
        left = self.parse_addition()
        while self.current().type in (TokenType.GT, TokenType.LT, TokenType.GTEQ, TokenType.LTEQ, TokenType.EQEQ, TokenType.NOTEQ):
            op_tok = self.advance()
            right = self.parse_addition()
            left = BinaryOp(line=op_tok.line, col=op_tok.col,
                           op=op_tok.value, left=left, right=right)
        return left

    def parse_addition(self):
        left = self.parse_multiply()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_multiply()
            left = BinaryOp(line=op_tok.line, col=op_tok.col,
                           op=op_tok.value, left=left, right=right)
        return left

    def parse_multiply(self):
        left = self.parse_unary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self.advance()
            right = self.parse_unary()
            left = BinaryOp(line=op_tok.line, col=op_tok.col,
                           op=op_tok.value, left=left, right=right)
        return left

    def parse_unary(self):
        if self.current().type == TokenType.MINUS:
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOp(line=op.line, col=op.col, op='-', operand=operand)
        if self.current().type == TokenType.NOT:
            op = self.advance()
            operand = self.parse_unary()
            return UnaryOp(line=op.line, col=op.col, op='not', operand=operand)
        return self.parse_call()

    def parse_call(self):
        expr = self.parse_primary()
        while self.current().type == TokenType.LPAREN:
            self.advance()  # consume '('
            args = []
            if self.current().type != TokenType.RPAREN:
                args.append(self.parse_expression())
                while self.match(TokenType.COMMA):
                    args.append(self.parse_expression())
            self.expect(TokenType.RPAREN)
            expr = CallExpression(line=expr.line, col=expr.col,
                                function=expr, arguments=args)
        return expr

    def parse_primary(self):
        tok = self.current()

        if tok.type == TokenType.INTEGER:
            self.advance()
            return IntegerLiteral(line=tok.line, col=tok.col, value=int(tok.value))

        elif tok.type == TokenType.FLOAT:
            self.advance()
            return FloatLiteral(line=tok.line, col=tok.col, value=float(tok.value))

        elif tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(line=tok.line, col=tok.col, value=tok.value)

        elif tok.type == TokenType.BOOLEAN:
            self.advance()
            return BoolLiteral(line=tok.line, col=tok.col, value=(tok.value == 'true'))

        elif tok.type == TokenType.EMOTION:
            self.advance()
            return EmotionLiteral(line=tok.line, col=tok.col, value=tok.value)

        elif tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(line=tok.line, col=tok.col, name=tok.value)

        elif tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        elif tok.type == TokenType.LBRACE:
            return self.parse_block()

        elif tok.type == TokenType.LBRACKET:
            return self.parse_list()

        else:
            raise ParseError(f"Unexpected token {tok.type} ('{tok.value}')", tok)

    def parse_block(self) -> BlockExpression:
        brace = self.expect(TokenType.LBRACE)
        statements = []
        final_expr = None

        while self.current().type != TokenType.RBRACE:
            if self.current().type == TokenType.LET:
                statements.append(self.parse_let())
            else:
                expr = self.parse_expression()
                if self.current().type == TokenType.SEMICOLON:
                    self.advance()
                    statements.append(expr)
                else:
                    # No semicolon — this is the final expression (return value)
                    final_expr = expr
                    break

        self.expect(TokenType.RBRACE)
        return BlockExpression(line=brace.line, col=brace.col,
                              statements=statements, final_expr=final_expr)

    def parse_list(self) -> ListLiteral:
        bracket = self.expect(TokenType.LBRACKET)
        elements = []
        if self.current().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                elements.append(self.parse_expression())
        self.expect(TokenType.RBRACKET)
        return ListLiteral(line=bracket.line, col=bracket.col, elements=elements)


# ═══════════════════════════════════════════
# Pretty Printer (for debugging)
# ═══════════════════════════════════════════

def pretty_print(node, indent=0):
    """Print an AST node as a readable tree."""
    pad = "  " * indent
    
    if isinstance(node, Program):
        print(f"{pad}Program:")
        for s in node.statements:
            pretty_print(s, indent + 1)
    elif isinstance(node, LetStatement):
        print(f"{pad}Let {node.name} =")
        pretty_print(node.value, indent + 1)
    elif isinstance(node, PrintStatement):
        print(f"{pad}Print:")
        pretty_print(node.value, indent + 1)
    elif isinstance(node, IntegerLiteral):
        print(f"{pad}Int({node.value})")
    elif isinstance(node, FloatLiteral):
        print(f"{pad}Float({node.value})")
    elif isinstance(node, StringLiteral):
        print(f"{pad}Str(\"{node.value}\")")
    elif isinstance(node, BoolLiteral):
        print(f"{pad}Bool({node.value})")
    elif isinstance(node, EmotionLiteral):
        print(f"{pad}Emotion(@{node.value})")
    elif isinstance(node, Identifier):
        print(f"{pad}Ident({node.name})")
    elif isinstance(node, BinaryOp):
        print(f"{pad}BinOp({node.op}):")
        pretty_print(node.left, indent + 1)
        pretty_print(node.right, indent + 1)
    elif isinstance(node, UnaryOp):
        print(f"{pad}UnaryOp({node.op}):")
        pretty_print(node.operand, indent + 1)
    elif isinstance(node, IfExpression):
        print(f"{pad}If:")
        print(f"{pad}  condition:")
        pretty_print(node.condition, indent + 2)
        print(f"{pad}  then:")
        pretty_print(node.then_branch, indent + 2)
        print(f"{pad}  else:")
        pretty_print(node.else_branch, indent + 2)
    elif isinstance(node, FnExpression):
        print(f"{pad}Fn({', '.join(node.params)}):")
        pretty_print(node.body, indent + 1)
    elif isinstance(node, CallExpression):
        print(f"{pad}Call:")
        pretty_print(node.function, indent + 1)
        for a in node.arguments:
            pretty_print(a, indent + 1)
    elif isinstance(node, BlockExpression):
        print(f"{pad}Block:")
        for s in node.statements:
            pretty_print(s, indent + 1)
        if node.final_expr:
            print(f"{pad}  => (returns):")
            pretty_print(node.final_expr, indent + 2)
    elif isinstance(node, ListLiteral):
        print(f"{pad}List:")
        for e in node.elements:
            pretty_print(e, indent + 1)
    elif isinstance(node, FeelStatement):
        print(f"{pad}Feel(@{node.emotion})")
    elif isinstance(node, IntrospectExpression):
        print(f"{pad}Introspect()")
    elif isinstance(node, WhileExpression):
        print(f"{pad}While:")
        print(f"{pad}  condition:")
        pretty_print(node.condition, indent + 2)
        print(f"{pad}  body:")
        pretty_print(node.body, indent + 2)
    else:
        print(f"{pad}Unknown({type(node).__name__})")


# ═══════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════

if __name__ == '__main__':
    source = """
    let x = 42;
    let name = "hello";
    let mood = @bold;
    let square = fn(x) -> x * x;
    let result = if x > 10 then "big" else "small";
    print(square(7));
    """

    print("═══ XTLang Parser ═══")
    print(f"Source: {len(source)} chars")
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"Tokens: {len(tokens)}")
    
    parser = Parser(tokens)
    ast = parser.parse()
    print(f"Statements: {len(ast.statements)}")
    print()
    
    pretty_print(ast)
    print()
    print("✓ Parse successful!")