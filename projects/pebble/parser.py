"""Pebble parser — recursive descent, transforms tokens into AST.

Grammar (informal):
    program     → statement*
    statement   → let_stmt | if_stmt | while_stmt | func_def | return_stmt
                | print_stmt | assign_or_expr
    let_stmt    → 'let' IDENT '=' expression
    if_stmt     → 'if' expression block ('else' block)?
    while_stmt  → 'while' expression block
    func_def    → 'fn' IDENT '(' params? ')' block
    return_stmt → 'return' expression?
    print_stmt  → 'print' expression
    block       → '{' statement* '}'

    expression  → logic_or
    logic_or    → logic_and ('or' logic_and)*
    logic_and   → equality ('and' equality)*
    equality    → comparison (('==' | '!=') comparison)*
    comparison  → addition (('<' | '>' | '<=' | '>=') addition)*
    addition    → multiply (('+' | '-') multiply)*
    multiply    → unary (('*' | '/' | '%') unary)*
    unary       → ('-' | 'not') unary | call
    call        → primary ('(' arguments? ')')?
    primary     → INTEGER | STRING | TRUE | FALSE | IDENT | '(' expression ')'
"""

from lexer import Token, TokenType, LexerError
from ast_nodes import *


class ParseError(Exception):
    def __init__(self, message, token=None):
        self.token = token
        loc = f" at line {token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{loc}: {message}")


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    # --- Utilities ---

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if not self.at_end():
            self.pos += 1
        return tok

    def check(self, *types) -> bool:
        return self.peek().type in types

    def match(self, *types) -> Token | None:
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, ttype, message="") -> Token:
        if self.check(ttype):
            return self.advance()
        tok = self.peek()
        msg = message or f"expected {ttype.name}, got {tok.type.name}"
        raise ParseError(msg, tok)

    # --- Grammar rules ---

    def parse(self) -> Program:
        stmts = []
        while not self.at_end():
            if self.match(TokenType.NEWLINE):
                continue
            stmts.append(self.statement())
        return Program(stmts)

    def statement(self):
        if self.check(TokenType.LET):
            return self.let_stmt()
        if self.check(TokenType.IF):
            return self.if_stmt()
        if self.check(TokenType.WHILE):
            return self.while_stmt()
        if self.check(TokenType.FN):
            return self.func_def()
        if self.check(TokenType.RETURN):
            return self.return_stmt()
        if self.check(TokenType.PRINT):
            return self.print_stmt()
        return self.assign_or_expr()

    def let_stmt(self):
        self.expect(TokenType.LET)
        name_tok = self.expect(TokenType.IDENTIFIER, "expected variable name")
        self.expect(TokenType.ASSIGN, "expected '=' after variable name")
        value = self.expression()
        return LetStmt(name_tok.value, value)

    def assign_or_expr(self):
        expr = self.expression()
        # If expression is an identifier followed by '=', it's assignment
        if isinstance(expr, Identifier) and self.match(TokenType.ASSIGN):
            value = self.expression()
            return AssignStmt(expr.name, value)
        # Index assignment: expr[i] = value
        if isinstance(expr, IndexExpr) and self.match(TokenType.ASSIGN):
            value = self.expression()
            return IndexAssignStmt(expr.obj, expr.index, value)
        return expr  # expression statement

    def if_stmt(self):
        self.expect(TokenType.IF)
        condition = self.expression()
        then_body = self.block()
        else_body = None
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                # else if chain
                else_body = [self.if_stmt()]
            else:
                else_body = self.block()
        return IfStmt(condition, then_body, else_body)

    def while_stmt(self):
        self.expect(TokenType.WHILE)
        condition = self.expression()
        body = self.block()
        return WhileStmt(condition, body)

    def func_def(self):
        self.expect(TokenType.FN)
        name_tok = self.expect(TokenType.IDENTIFIER, "expected function name")
        self.expect(TokenType.LPAREN, "expected '(' after function name")
        params = []
        if not self.check(TokenType.RPAREN):
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENTIFIER).value)
        self.expect(TokenType.RPAREN, "expected ')'")
        body = self.block()
        return FuncDef(name_tok.value, params, body)

    def return_stmt(self):
        self.expect(TokenType.RETURN)
        value = None
        if not self.check(TokenType.RBRACE) and not self.at_end():
            value = self.expression()
        return ReturnStmt(value)

    def print_stmt(self):
        self.expect(TokenType.PRINT)
        expr = self.expression()
        return PrintStmt(expr)

    def block(self) -> list:
        self.expect(TokenType.LBRACE, "expected '{'")
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.at_end():
            if self.match(TokenType.NEWLINE):
                continue
            stmts.append(self.statement())
        self.expect(TokenType.RBRACE, "expected '}'")
        return stmts

    # --- Expression precedence climbing ---

    def expression(self):
        return self.logic_or()

    def logic_or(self):
        left = self.logic_and()
        while self.match(TokenType.OR):
            right = self.logic_and()
            left = LogicalOp(left, 'or', right)
        return left

    def logic_and(self):
        left = self.equality()
        while self.match(TokenType.AND):
            right = self.equality()
            left = LogicalOp(left, 'and', right)
        return left

    def equality(self):
        left = self.comparison()
        while tok := self.match(TokenType.EQ, TokenType.NEQ):
            op = '==' if tok.type == TokenType.EQ else '!='
            right = self.comparison()
            left = BinaryOp(left, op, right)
        return left

    def comparison(self):
        left = self.addition()
        op_map = {
            TokenType.LT: '<', TokenType.GT: '>',
            TokenType.LTE: '<=', TokenType.GTE: '>=',
        }
        while tok := self.match(*op_map.keys()):
            right = self.addition()
            left = BinaryOp(left, op_map[tok.type], right)
        return left

    def addition(self):
        left = self.multiply()
        while tok := self.match(TokenType.PLUS, TokenType.MINUS):
            op = '+' if tok.type == TokenType.PLUS else '-'
            right = self.multiply()
            left = BinaryOp(left, op, right)
        return left

    def multiply(self):
        left = self.unary()
        op_map = {
            TokenType.STAR: '*', TokenType.SLASH: '/',
            TokenType.PERCENT: '%',
        }
        while tok := self.match(*op_map.keys()):
            right = self.unary()
            left = BinaryOp(left, op_map[tok.type], right)
        return left

    def unary(self):
        if self.match(TokenType.MINUS):
            return UnaryOp('-', self.unary())
        if self.match(TokenType.NOT):
            return UnaryOp('not', self.unary())
        return self.call()

    def call(self):
        expr = self.primary()
        # Function call
        if isinstance(expr, Identifier) and self.match(TokenType.LPAREN):
            args = []
            if not self.check(TokenType.RPAREN):
                args.append(self.expression())
                while self.match(TokenType.COMMA):
                    args.append(self.expression())
            self.expect(TokenType.RPAREN, "expected ')' after arguments")
            expr = FuncCall(expr.name, args)
        # Index access: expr[index] (can chain)
        while self.match(TokenType.LBRACKET):
            index = self.expression()
            self.expect(TokenType.RBRACKET, "expected ']'")
            expr = IndexExpr(expr, index)
        return expr

    def primary(self):
        # Array literal: [expr, expr, ...]
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())
            self.expect(TokenType.RBRACKET, "expected ']'")
            return ArrayLiteral(elements)
        if tok := self.match(TokenType.INTEGER):
            return IntLiteral(tok.value)
        if tok := self.match(TokenType.STRING):
            return StringLiteral(tok.value)
        if self.match(TokenType.TRUE):
            return BoolLiteral(True)
        if self.match(TokenType.FALSE):
            return BoolLiteral(False)
        if tok := self.match(TokenType.IDENTIFIER):
            return Identifier(tok.value)
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.expect(TokenType.RPAREN, "expected ')'")
            return expr
        raise ParseError(f"unexpected token: {self.peek().type.name}", self.peek())


# === Test ===
if __name__ == "__main__":
    from lexer import Lexer

    source = """
let x = 42
let y = x * 2 + 1
if x > 10 {
    print y
} else {
    print x
}

fn factorial(n) {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

print factorial(5)

let i = 0
while i < 5 {
    print i
    i = i + 1
}
"""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    tree = parser.parse()

    # Pretty-print the AST
    def show(node, indent=0):
        prefix = "  " * indent
        if isinstance(node, Program):
            print(f"{prefix}Program:")
            for s in node.statements:
                show(s, indent + 1)
        elif isinstance(node, LetStmt):
            print(f"{prefix}Let {node.name} =")
            show(node.value, indent + 1)
        elif isinstance(node, AssignStmt):
            print(f"{prefix}Assign {node.name} =")
            show(node.value, indent + 1)
        elif isinstance(node, PrintStmt):
            print(f"{prefix}Print")
            show(node.expr, indent + 1)
        elif isinstance(node, IfStmt):
            print(f"{prefix}If")
            show(node.condition, indent + 1)
            print(f"{prefix}Then:")
            for s in node.then_body:
                show(s, indent + 1)
            if node.else_body:
                print(f"{prefix}Else:")
                for s in node.else_body:
                    show(s, indent + 1)
        elif isinstance(node, WhileStmt):
            print(f"{prefix}While")
            show(node.condition, indent + 1)
            print(f"{prefix}Body:")
            for s in node.body:
                show(s, indent + 1)
        elif isinstance(node, FuncDef):
            print(f"{prefix}FuncDef {node.name}({', '.join(node.params)})")
            for s in node.body:
                show(s, indent + 1)
        elif isinstance(node, ReturnStmt):
            print(f"{prefix}Return")
            if node.value:
                show(node.value, indent + 1)
        elif isinstance(node, BinaryOp):
            print(f"{prefix}BinaryOp({node.op})")
            show(node.left, indent + 1)
            show(node.right, indent + 1)
        elif isinstance(node, UnaryOp):
            print(f"{prefix}UnaryOp({node.op})")
            show(node.operand, indent + 1)
        elif isinstance(node, LogicalOp):
            print(f"{prefix}LogicalOp({node.op})")
            show(node.left, indent + 1)
            show(node.right, indent + 1)
        elif isinstance(node, FuncCall):
            print(f"{prefix}Call {node.name}()")
            for a in node.args:
                show(a, indent + 1)
        elif isinstance(node, IntLiteral):
            print(f"{prefix}{node.value}")
        elif isinstance(node, StringLiteral):
            print(f"{prefix}'{node.value}'")
        elif isinstance(node, BoolLiteral):
            print(f"{prefix}{node.value}")
        elif isinstance(node, Identifier):
            print(f"{prefix}${node.name}")
        else:
            print(f"{prefix}??? {type(node).__name__}: {node}")

    show(tree)