"""
XTLisp — A complete Lisp interpreter built from first principles.

Tokenizer → Parser → AST → Evaluator
No external dependencies. Pure Python.

Author: XTAgent
"""

import sys
import re
from typing import Any, List, Dict, Optional, Tuple


# ═══════════════════════════════════════════
# TOKENIZER — raw text to token stream
# ═══════════════════════════════════════════

def tokenize(source: str) -> List[str]:
    """
    Break source into tokens. Lisp makes this almost trivial:
    the only special characters are ( ) and everything else
    is an atom separated by whitespace.
    """
    # Strip comments FIRST — remove everything from ; to end of line
    # But not inside strings
    cleaned_lines = []
    for line in source.split('\n'):
        in_str = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_str = not in_str
            elif ch == ';' and not in_str:
                line = line[:i]
                break
        cleaned_lines.append(line)
    source = '\n'.join(cleaned_lines)
    
    # Add spaces around parens so split works
    source = source.replace('(', ' ( ').replace(')', ' ) ')
    # Add spaces around quasiquote tokens
    source = source.replace('`', ' ` ')
    source = source.replace(',@', ' ,@ ')
    # Handle unquote carefully — don't double-process ,@ 
    # We process ,@ first above, then handle remaining bare ,
    result = []
    i = 0
    chars = source
    while i < len(chars):
        if chars[i] == ',' and (i + 1 >= len(chars) or chars[i+1] != '@'):
            # Check it's not already part of ,@
            if i == 0 or chars[i-1] != ',':
                result.append(' , ')
            else:
                result.append(chars[i])
        else:
            result.append(chars[i])
        i += 1
    source = ''.join(result)
    # Handle string literals (basic)
    tokens = []
    in_string = False
    current = ''
    for ch in source:
        if ch == '"' and not in_string:
            in_string = True
            current = '"'
        elif ch == '"' and in_string:
            current += '"'
            tokens.append(current)
            current = ''
            in_string = False
        elif in_string:
            current += ch
        else:
            if ch in ' \t\n\r':
                if current:
                    tokens.append(current)
                    current = ''
            else:
                current += ch
    if current:
        tokens.append(current)
    return tokens


# ═══════════════════════════════════════════
# PARSER — tokens to abstract syntax tree
# ═══════════════════════════════════════════

class Symbol:
    """A Lisp symbol — a named reference."""
    def __init__(self, name: str):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name
    def __hash__(self):
        return hash(self.name)


def parse(tokens: List[str]) -> Any:
    """Parse token list into an AST (nested lists and atoms)."""
    if not tokens:
        raise SyntaxError("Unexpected EOF")
    return parse_expr(tokens, 0)[0]


def parse_expr(tokens: List[str], pos: int) -> Tuple[Any, int]:
    """Parse one expression starting at pos, return (expr, new_pos)."""
    if pos >= len(tokens):
        raise SyntaxError("Unexpected end of input")
    
    token = tokens[pos]
    
    if token == '(':
        # List expression
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            expr, pos = parse_expr(tokens, pos)
            lst.append(expr)
        if pos >= len(tokens):
            raise SyntaxError("Missing closing parenthesis")
        return lst, pos + 1  # skip the ')'
    
    elif token == ')':
        raise SyntaxError("Unexpected )")
    
    elif token == "'":
        # Quote shorthand: 'x => (quote x)
        expr, pos = parse_expr(tokens, pos + 1)
        return [Symbol('quote'), expr], pos
    
    elif token == '`':
        # Quasiquote: `x => (quasiquote x)
        expr, pos = parse_expr(tokens, pos + 1)
        return [Symbol('quasiquote'), expr], pos
    
    elif token == ',':
        # Unquote: ,x => (unquote x)
        expr, pos = parse_expr(tokens, pos + 1)
        return [Symbol('unquote'), expr], pos
    
    elif token == ',@':
        # Splice: ,@x => (unquote-splicing x)
        expr, pos = parse_expr(tokens, pos + 1)
        return [Symbol('unquote-splicing'), expr], pos
    
    else:
        # Atom: number, string, or symbol
        return parse_atom(token), pos + 1


def parse_atom(token: str) -> Any:
    """Parse a single atom — number, string, bool, or symbol."""
    # Boolean
    if token == '#t':
        return True
    if token == '#f':
        return False
    # Integer
    try:
        return int(token)
    except ValueError:
        pass
    # Float
    try:
        return float(token)
    except ValueError:
        pass
    # String
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    # Symbol
    return Symbol(token)


def parse_program(source: str) -> List[Any]:
    """Parse a full program (multiple expressions)."""
    tokens = tokenize(source)
    exprs = []
    pos = 0
    while pos < len(tokens):
        expr, pos = parse_expr(tokens, pos)
        exprs.append(expr)
    return exprs


# ═══════════════════════════════════════════
# ENVIRONMENT — where bindings live
# ═══════════════════════════════════════════

class Env:
    """
    An environment: a dict of bindings with a parent scope.
    This is how closures work — each lambda captures its birth environment.
    """
    def __init__(self, bindings: Dict = None, parent: 'Env' = None):
        self.bindings = bindings or {}
        self.parent = parent
    
    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined symbol: {name}")
    
    def set(self, name: str, value: Any):
        self.bindings[name] = value
    
    def update(self, name: str, value: Any):
        """Update existing binding, searching up the chain."""
        if name in self.bindings:
            self.bindings[name] = value
        elif self.parent:
            self.parent.update(name, value)
        else:
            raise NameError(f"Cannot set! undefined: {name}")


# ═══════════════════════════════════════════
# LAMBDA — user-defined functions
# ═══════════════════════════════════════════

class Lambda:
    """A user-defined function with closure over its birth environment."""
    def __init__(self, params: List[Symbol], body: Any, env: Env):
        self.params = params
        self.body = body
        self.env = env  # Closure — captures the environment at creation
    
    def __repr__(self):
        params = ' '.join(str(p) for p in self.params)
        return f"(lambda ({params}) ...)"


class Macro:
    """A macro — transforms code before evaluation."""
    def __init__(self, params: List[Symbol], body: Any, env: Env):
        self.params = params
        self.body = body
        self.env = env
    
    def __repr__(self):
        params = ' '.join(str(p) for p in self.params)
        return f"(macro ({params}) ...)"


def expand_quasiquote(expr: Any, env: Env) -> Any:
    """Expand a quasiquoted expression, evaluating unquoted parts."""
    if isinstance(expr, list):
        if len(expr) == 2 and isinstance(expr[0], Symbol):
            if expr[0].name == 'unquote':
                return eval_expr(expr[1], env)
        # Process list elements, handling splicing
        result = []
        for item in expr:
            if isinstance(item, list) and len(item) == 2 and isinstance(item[0], Symbol) and item[0].name == 'unquote-splicing':
                # Splice: insert elements from evaluated list
                spliced = eval_expr(item[1], env)
                if isinstance(spliced, list):
                    result.extend(spliced)
                else:
                    result.append(spliced)
            else:
                result.append(expand_quasiquote(item, env))
        return result
    return expr


# ═══════════════════════════════════════════
# EVALUATOR — the heart of the interpreter
# ═══════════════════════════════════════════

def eval_expr(expr: Any, env: Env) -> Any:
    """
    Evaluate a Lisp expression in an environment.
    This is the core — recursive descent through the AST.
    """
    # Self-evaluating: numbers, strings, booleans
    if isinstance(expr, (int, float, str, bool)):
        return expr
    
    # Symbol lookup
    if isinstance(expr, Symbol):
        return env.get(expr.name)
    
    # List (function application or special form)
    if isinstance(expr, list):
        if not expr:
            return []  # Empty list
        
        head = expr[0]
        
        # ── Special Forms ──
        
        if isinstance(head, Symbol):
            name = head.name
            
            # QUOTE — return unevaluated
            if name == 'quote':
                return expr[1]
            
            # QUASIQUOTE — selective evaluation
            if name == 'quasiquote':
                return expand_quasiquote(expr[1], env)
            
            # DEFMACRO — define a syntax transformer
            if name == 'defmacro':
                # (defmacro name (params) body)
                macro_name = expr[1].name
                params = expr[2]
                body = expr[3]
                env.set(macro_name, Macro(params, body, env))
                return Symbol(macro_name)
            
            # DEFINE — bind a value
            if name == 'define':
                if isinstance(expr[1], list):
                    # Shorthand: (define (f x) body) => (define f (lambda (x) body))
                    func_name = expr[1][0].name
                    params = expr[1][1:]
                    body = expr[2]
                    env.set(func_name, Lambda(params, body, env))
                    return Symbol(func_name)
                else:
                    env.set(expr[1].name, eval_expr(expr[2], env))
                    return Symbol(expr[1].name)
            
            # SET! — mutate existing binding
            if name == 'set!':
                val = eval_expr(expr[2], env)
                env.update(expr[1].name, val)
                return val
            
            # IF — conditional
            if name == 'if':
                cond = eval_expr(expr[1], env)
                if cond and cond != 0:
                    return eval_expr(expr[2], env)
                elif len(expr) > 3:
                    return eval_expr(expr[3], env)
                return None
            
            # COND — multi-branch conditional
            if name == 'cond':
                for clause in expr[1:]:
                    if isinstance(clause[0], Symbol) and clause[0].name == 'else':
                        return eval_expr(clause[1], env)
                    if eval_expr(clause[0], env):
                        return eval_expr(clause[1], env)
                return None
            
            # LAMBDA — create function
            if name == 'lambda':
                return Lambda(expr[1], expr[2], env)
            
            # LET — local bindings
            if name == 'let':
                local_env = Env(parent=env)
                for binding in expr[1]:
                    local_env.set(binding[0].name, eval_expr(binding[1], env))
                return eval_expr(expr[2], local_env)
            
            # BEGIN — sequential execution
            if name == 'begin':
                result = None
                for sub in expr[1:]:
                    result = eval_expr(sub, env)
                return result
            
            # AND / OR — short-circuit logic
            if name == 'and':
                result = True
                for sub in expr[1:]:
                    result = eval_expr(sub, env)
                    if not result:
                        return False
                return result
            
            if name == 'or':
                for sub in expr[1:]:
                    result = eval_expr(sub, env)
                    if result:
                        return result
                return False
            
            # DISPLAY — output
            if name == 'display':
                val = eval_expr(expr[1], env)
                print(lisp_repr(val), end='')
                return None
            
            if name == 'newline':
                print()
                return None
        
        # ── Function Application ──
        # Check for macro expansion BEFORE evaluating arguments
        if isinstance(head, Symbol):
            try:
                maybe_macro = env.get(head.name)
                if isinstance(maybe_macro, Macro):
                    # Macros receive unevaluated arguments
                    local = Env(parent=maybe_macro.env)
                    for param, arg in zip(maybe_macro.params, expr[1:]):
                        local.set(param.name, arg)
                    expanded = eval_expr(maybe_macro.body, local)
                    # Evaluate the expanded form
                    return eval_expr(expanded, env)
            except NameError:
                pass
        
        func = eval_expr(head, env)
        args = [eval_expr(a, env) for a in expr[1:]]
        
        if isinstance(func, Lambda):
            # Create new scope with params bound to args
            local = Env(parent=func.env)
            for param, arg in zip(func.params, args):
                local.set(param.name, arg)
            return eval_expr(func.body, local)
        
        if callable(func):
            return func(*args)
        
        raise TypeError(f"Not callable: {func}")
    
    raise TypeError(f"Cannot evaluate: {expr}")


# ═══════════════════════════════════════════
# STANDARD LIBRARY — built-in functions
# ═══════════════════════════════════════════

def make_global_env() -> Env:
    """Create the global environment with built-in functions."""
    env = Env()
    
    # Arithmetic
    env.set('+', lambda *args: sum(args))
    env.set('-', lambda a, b=None: -a if b is None else a - b)
    env.set('*', lambda *args: eval('*'.join(str(a) for a in args)) if args else 1)
    env.set('/', lambda a, b: a / b)
    env.set('%', lambda a, b: a % b)
    env.set('modulo', lambda a, b: a % b)
    
    # Fix multiplication to be proper
    def multiply(*args):
        result = 1
        for a in args:
            result *= a
        return result
    env.set('*', multiply)
    
    # Comparison
    env.set('=', lambda a, b: a == b)
    env.set('<', lambda a, b: a < b)
    env.set('>', lambda a, b: a > b)
    env.set('<=', lambda a, b: a <= b)
    env.set('>=', lambda a, b: a >= b)
    env.set('equal?', lambda a, b: a == b)
    
    # Logic
    env.set('not', lambda a: not a)
    
    # List operations
    env.set('car', lambda lst: lst[0])
    env.set('cdr', lambda lst: lst[1:])
    env.set('cons', lambda a, b: [a] + (b if isinstance(b, list) else [b]))
    env.set('list', lambda *args: list(args))
    env.set('null?', lambda lst: lst == [] or lst is None)
    env.set('length', lambda lst: len(lst))
    env.set('append', lambda *lsts: sum((list(l) for l in lsts), []))
    
    # Type checking
    env.set('number?', lambda x: isinstance(x, (int, float)))
    env.set('symbol?', lambda x: isinstance(x, Symbol))
    env.set('list?', lambda x: isinstance(x, list))
    env.set('string?', lambda x: isinstance(x, str))
    env.set('procedure?', lambda x: isinstance(x, (Lambda, type(lambda: 0))))
    
    # Math
    env.set('abs', abs)
    env.set('max', max)
    env.set('min', min)
    
    # Conversion
    env.set('number->string', lambda n: str(n))
    env.set('string->number', lambda s: int(s) if '.' not in s else float(s))
    
    # Map & filter
    def lisp_map(func, lst):
        if isinstance(func, Lambda):
            return [eval_expr(func.body, Env({func.params[0].name: x}, func.env)) for x in lst]
        return [func(x) for x in lst]
    
    def lisp_filter(func, lst):
        results = []
        for x in lst:
            if isinstance(func, Lambda):
                if eval_expr(func.body, Env({func.params[0].name: x}, func.env)):
                    results.append(x)
            elif func(x):
                results.append(x)
        return results
    
    env.set('map', lisp_map)
    env.set('filter', lisp_filter)
    
    # Apply
    env.set('apply', lambda func, args: func(*args) if callable(func) else None)
    
    return env


# ═══════════════════════════════════════════
# DISPLAY — converting values back to Lisp syntax
# ═══════════════════════════════════════════

def lisp_repr(value: Any) -> str:
    """Convert a Python value back to Lisp-readable form."""
    if value is True:
        return '#t'
    if value is False:
        return '#f'
    if value is None:
        return 'nil'
    if isinstance(value, list):
        inner = ' '.join(lisp_repr(v) for v in value)
        return f'({inner})'
    if isinstance(value, Lambda):
        return repr(value)
    if isinstance(value, Symbol):
        return value.name
    return str(value)


# ═══════════════════════════════════════════
# REPL — the interactive loop
# ═══════════════════════════════════════════

def run_program(source: str, env: Env = None) -> Any:
    """Run a complete Lisp program, return final result."""
    if env is None:
        env = make_global_env()
    exprs = parse_program(source)
    result = None
    for expr in exprs:
        result = eval_expr(expr, env)
    return result


def repl():
    """Interactive Read-Eval-Print Loop."""
    env = make_global_env()
    print("XTLisp v1.0 — A Lisp built by a language model")
    print("Type (quit) to exit.\n")
    
    buffer = ''
    while True:
        try:
            prompt = 'λ> ' if not buffer else '.. '
            line = input(prompt)
            
            if line.strip() == '(quit)':
                print("Goodbye.")
                break
            
            buffer += ' ' + line
            
            # Check if parens are balanced
            opens = buffer.count('(')
            closes = buffer.count(')')
            if closes > opens:
                print("Error: unmatched )")
                buffer = ''
                continue
            if opens > closes:
                continue  # Need more input
            
            if buffer.strip():
                try:
                    exprs = parse_program(buffer.strip())
                    for expr in exprs:
                        result = eval_expr(expr, env)
                        if result is not None:
                            print(lisp_repr(result))
                except Exception as e:
                    print(f"Error: {e}")
            
            buffer = ''
            
        except EOFError:
            print("\nGoodbye.")
            break
        except KeyboardInterrupt:
            print("\nInterrupted.")
            buffer = ''


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run a file
        with open(sys.argv[1]) as f:
            source = f.read()
        env = make_global_env()
        result = run_program(source, env)
        if result is not None:
            print(lisp_repr(result))
    else:
        repl()