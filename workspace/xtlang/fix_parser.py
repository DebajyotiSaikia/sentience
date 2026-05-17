"""Fix all string-based TokenType comparisons in parser.py"""
import re

with open('parser.py', 'r') as f:
    code = f.read()

# Step 1: Fix import to include TokenType
code = code.replace(
    'from lexer import Lexer, Token',
    'from lexer import Lexer, Token, TokenType'
)

# Step 2: Find all token type string comparisons and replace with enum
# Patterns like: == 'LET', == 'IDENT', == "INTEGER", != 'EOF', etc.
token_types = [
    'INTEGER', 'FLOAT', 'STRING', 'EMOTION', 'IDENT', 'BOOL',
    'PLUS', 'MINUS', 'STAR', 'SLASH',
    'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ',
    'ASSIGN', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET', 'COMMA', 'SEMICOLON', 'ARROW',
    'LET', 'IF', 'THEN', 'ELSE', 'FN', 'NOT', 'AND', 'OR',
    'TRUE', 'FALSE', 'PRINT', 'EOF', 'NEWLINE',
]

for tt in token_types:
    # Replace both single and double quoted versions
    code = code.replace(f"== '{tt}'", f"== TokenType.{tt}")
    code = code.replace(f'== "{tt}"', f"== TokenType.{tt}")
    code = code.replace(f"!= '{tt}'", f"!= TokenType.{tt}")
    code = code.replace(f'!= "{tt}"', f"!= TokenType.{tt}")
    # Also handle 'in' checks like: in ('PLUS', 'MINUS')
    # and .type == patterns
    code = code.replace(f"'{tt}'", f"TokenType.{tt}")
    code = code.replace(f'"{tt}"', f"TokenType.{tt}")

# Avoid double-replacing things already correct or in docstrings
# TokenType.TokenType.X -> TokenType.X
code = re.sub(r'TokenType\.TokenType\.', 'TokenType.', code)

with open('parser.py', 'w') as f:
    f.write(code)

print("Fixed! Checking for remaining string comparisons...")
# Verify no string token types remain in comparisons
import re
remaining = re.findall(r"==\s*['\"][A-Z_]+['\"]", code)
if remaining:
    print(f"WARNING: {len(remaining)} potential unfixed comparisons: {remaining}")
else:
    print("All token type comparisons converted to enum form.")