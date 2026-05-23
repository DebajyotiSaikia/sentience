"""Pebble lexer — transforms source text into tokens."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List

class TokenType(Enum):
    # Literals
    INTEGER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Keywords
    LET = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FN = auto()
    RETURN = auto()
    PRINT = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    
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
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    
    # Special
    EOF = auto()
    NEWLINE = auto()

@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"

KEYWORDS = {
    'let': TokenType.LET,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'while': TokenType.WHILE,
    'fn': TokenType.FN,
    'return': TokenType.RETURN,
    'print': TokenType.PRINT,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
}

class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"Lexer error at L{line}:{col}: {message}")
        self.line = line
        self.col = col

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
    
    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        # Single-line comment: # to end of line
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.advance()
    
    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # consume opening quote
        result = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\\':
                self.advance()
                ch = self.advance()
                if ch == 'n': result.append('\n')
                elif ch == 't': result.append('\t')
                elif ch == '"': result.append('"')
                elif ch == '\\': result.append('\\')
                else: result.append(ch)
            else:
                result.append(self.advance())
        if self.pos >= len(self.source):
            raise LexerError("Unterminated string", start_line, start_col)
        self.advance()  # consume closing quote
        return Token(TokenType.STRING, ''.join(result), start_line, start_col)
    
    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        digits = []
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            digits.append(self.advance())
        return Token(TokenType.INTEGER, int(''.join(digits)), start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        chars = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            chars.append(self.advance())
        word = ''.join(chars)
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        value = word
        if token_type == TokenType.TRUE:
            value = True
        elif token_type == TokenType.FALSE:
            value = False
        return Token(token_type, value, start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            ch = self.peek()
            start_line, start_col = self.line, self.col
            
            if ch == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\\n', start_line, start_col))
            elif ch == '#':
                self.skip_comment()
            elif ch == '"':
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
            elif ch == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            elif ch == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
            elif ch == '*':
                self.advance()
                self.tokens.append(Token(TokenType.STAR, '*', start_line, start_col))
            elif ch == '/':
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, '/', start_line, start_col))
            elif ch == '%':
                self.advance()
                self.tokens.append(Token(TokenType.PERCENT, '%', start_line, start_col))
            elif ch == '=':
                self.advance()
                if self.match('='):
                    self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
            elif ch == '!':
                self.advance()
                if self.match('='):
                    self.tokens.append(Token(TokenType.NEQ, '!=', start_line, start_col))
                else:
                    raise LexerError(f"Unexpected character '!'", start_line, start_col)
            elif ch == '<':
                self.advance()
                if self.match('='):
                    self.tokens.append(Token(TokenType.LTE, '<=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif ch == '>':
                self.advance()
                if self.match('='):
                    self.tokens.append(Token(TokenType.GTE, '>=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            elif ch == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            elif ch == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            elif ch == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            elif ch == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            elif ch == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
            elif ch == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
            elif ch == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            elif ch == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_col))
            else:
                raise LexerError(f"Unexpected character '{ch}'", start_line, start_col)
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return self.tokens


if __name__ == '__main__':
    test = '''
let x = 42
let name = "pebble"
if x > 10 {
    print x * 2
}
'''
    lexer = Lexer(test)
    tokens = lexer.tokenize()
    for t in tokens:
        if t.type != TokenType.NEWLINE:
            print(t)