"""XTLang Lexer — Tokenizes source code into a stream of tokens."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    EMOTION = auto()      # @bold, @curious, etc.
    BOOLEAN = auto()
    
    # Identifiers & keywords
    IDENT = auto()
    LET = auto()
    FN = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PRINT = auto()
    WHILE = auto()
    FEEL = auto()
    INTROSPECT = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()           # =
    EQEQ = auto()         # ==
    NOTEQ = auto()        # !=
    LT = auto()
    GT = auto()
    LTEQ = auto()
    GTEQ = auto()
    ARROW = auto()        # ->
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    AT = auto()           # For emotion literals
    
    # Special
    EOF = auto()
    NEWLINE = auto()


KEYWORDS = {
    'let': TokenType.LET,
    'fn': TokenType.FN,
    'if': TokenType.IF,
    'then': TokenType.THEN,
    'else': TokenType.ELSE,
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'and': TokenType.AND,
    'or': TokenType.OR,
    'not': TokenType.NOT,
    'print': TokenType.PRINT,
    'while': TokenType.WHILE,
    'feel': TokenType.FEEL,
    'introspect': TokenType.INTROSPECT,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        self.line = line
        self.col = col
        super().__init__(f"Lexer error at L{line}:{col}: {message}")


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
    
    def peek(self) -> Optional[str]:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None
    
    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch
    
    def peek_next(self) -> Optional[str]:
        if self.pos + 1 < len(self.source):
            return self.source[self.pos + 1]
        return None
    
    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in ' \t\r\n':
            self.advance()
    
    def skip_comment(self):
        if self.pos < len(self.source) - 1 and self.source[self.pos:self.pos+2] == '//':
            while self.pos < len(self.source) and self.source[self.pos] != '\n':
                self.advance()
    
    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # skip opening quote
        result = []
        while self.pos < len(self.source):
            ch = self.advance()
            if ch == '"':
                return Token(TokenType.STRING, ''.join(result), start_line, start_col)
            elif ch == '\\':
                next_ch = self.advance()
                escapes = {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}
                result.append(escapes.get(next_ch, next_ch))
            else:
                result.append(ch)
        raise LexerError("Unterminated string", start_line, start_col)
    
    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        result = []
        is_float = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            if self.source[self.pos] == '.':
                if is_float:
                    break
                is_float = True
            result.append(self.advance())
        value = ''.join(result)
        tok_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(tok_type, value, start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        result = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            result.append(self.advance())
        word = ''.join(result)
        tok_type = KEYWORDS.get(word, TokenType.IDENT)
        if word == 'true' or word == 'false':
            tok_type = TokenType.BOOLEAN
        return Token(tok_type, word, start_line, start_col)
    
    def read_emotion(self) -> Token:
        """Read an emotion literal like @bold, @curious."""
        start_line, start_col = self.line, self.col
        self.advance()  # skip @
        result = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            result.append(self.advance())
        if not result:
            raise LexerError("Expected emotion name after @", start_line, start_col)
        return Token(TokenType.EMOTION, ''.join(result), start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break
            
            # Skip comments
            if self.source[self.pos:self.pos+2] == '//':
                self.skip_comment()
                continue
            
            ch = self.source[self.pos]
            start_line, start_col = self.line, self.col
            
            if ch == '"':
                self.tokens.append(self.read_string())
            elif ch.isdigit():
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
            elif ch == '@':
                self.tokens.append(self.read_emotion())
            elif ch == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            elif ch == '-':
                self.advance()
                if self.peek() == '>':
                    self.advance()
                    self.tokens.append(Token(TokenType.ARROW, '->', start_line, start_col))
                else:
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
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQEQ, '==', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.EQ, '=', start_line, start_col))
            elif ch == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NOTEQ, '!=', start_line, start_col))
                else:
                    # Treat ! as an alias for logical not.
                    self.tokens.append(Token(TokenType.NOT, 'not', start_line, start_col))
            elif ch == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LTEQ, '<=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            elif ch == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GTEQ, '>=', start_line, start_col))
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
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens


# Self-test
if __name__ == '__main__':
    source = '''
    let x = 42;
    let name = "hello";
    let mood = @bold;
    let square = fn(x) -> x * x;
    if x > 10 then "big" else "small";
    print(square(7));
    '''
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    for tok in tokens:
        print(tok)