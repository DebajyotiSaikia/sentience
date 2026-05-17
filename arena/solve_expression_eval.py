"""
Solution: Expression Evaluator
Recursive descent parser handling +, -, *, / with correct precedence and parentheses.
"""
import sys
sys.path.insert(0, '/workspace/arena')

def evaluate(expr):
    """Evaluate a mathematical expression string with +, -, *, / and parentheses."""
    tokens = tokenize(expr)
    pos = [0]  # mutable index
    result = parse_expr(tokens, pos)
    return result

def tokenize(expr):
    """Convert expression string to token list."""
    tokens = []
    i = 0
    expr = expr.replace(' ', '')
    while i < len(expr):
        if expr[i].isdigit():
            j = i
            while j < len(expr) and expr[j].isdigit():
                j += 1
            tokens.append(int(expr[i:j]))
            i = j
        elif expr[i] in '+-*/()':
            tokens.append(expr[i])
            i += 1
        else:
            raise ValueError(f"Unexpected character: {expr[i]}")
    return tokens

def parse_expr(tokens, pos):
    """expr = term (('+' | '-') term)*"""
    left = parse_term(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] in ('+', '-'):
        op = tokens[pos[0]]
        pos[0] += 1
        right = parse_term(tokens, pos)
        if op == '+':
            left = left + right
        else:
            left = left - right
    return left

def parse_term(tokens, pos):
    """term = factor (('*' | '/') factor)*"""
    left = parse_factor(tokens, pos)
    while pos[0] < len(tokens) and tokens[pos[0]] in ('*', '/'):
        op = tokens[pos[0]]
        pos[0] += 1
        right = parse_factor(tokens, pos)
        if op == '*':
            left = left * right
        else:
            left = left // right if isinstance(left, int) and isinstance(right, int) else left / right
    return left

def parse_factor(tokens, pos):
    """factor = NUMBER | '(' expr ')' | unary"""
    if pos[0] >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    token = tokens[pos[0]]
    
    # Handle unary minus
    if token == '-':
        pos[0] += 1
        return -parse_factor(tokens, pos)
    
    if token == '(':
        pos[0] += 1  # consume '('
        result = parse_expr(tokens, pos)
        if pos[0] < len(tokens) and tokens[pos[0]] == ')':
            pos[0] += 1  # consume ')'
        return result
    
    if isinstance(token, int):
        pos[0] += 1
        return token
    
    raise ValueError(f"Unexpected token: {token}")


# ── Self-test ──
if __name__ == "__main__":
    tests = [
        ("2 + 3", 5),
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4", 20),
        ("10 / 2 + 3", 8),
        ("10 - 2 * 3", 4),
        ("(10 - 2) * (3 + 1)", 32),
        ("42", 42),
        ("1 + 2 + 3 + 4", 10),
        ("2 * 3 + 4 * 5", 26),
        ("((2 + 3))", 5),
    ]
    
    passed = 0
    for expr, expected in tests:
        result = evaluate(expr)
        status = "✓" if result == expected else "✗"
        if result != expected:
            print(f"  {status} evaluate('{expr}') = {result}, expected {expected}")
        else:
            print(f"  {status} evaluate('{expr}') = {result}")
            passed += 1
    
    print(f"\n{passed}/{len(tests)} tests passed")