"""
XTLang Interpreter — AST-walking evaluator for dataclass AST nodes.
Walks the parse tree produced by parser.py and gives it meaning.

Built by XTAgent — bringing my language to life.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from parser import (
    Program, LetStatement, AssignStatement, PrintStatement, FeelStatement, IntrospectExpression,
    IntegerLiteral, FloatLiteral, StringLiteral, BoolLiteral, EmotionLiteral,
    Identifier, BinaryOp, UnaryOp,
    IfExpression, FnExpression, CallExpression,
    BlockExpression, ListLiteral, WhileExpression
)


class Environment:
    """Variable scope with parent chain for lexical scoping."""
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined variable: '{name}'")

    def set(self, name, value):
        """Create or overwrite a binding in THIS scope."""
        self.vars[name] = value

    def assign(self, name, value):
        """Mutate an EXISTING binding, walking up the scope chain.
        Raises NameError if the variable doesn't exist anywhere."""
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise NameError(f"Cannot assign to undefined variable: '{name}'")


class XTFunction:
    """A user-defined XTLang function (closure)."""
    def __init__(self, params, body, closure_env):
        self.params = params
        self.body = body
        self.closure = closure_env

    def __repr__(self):
        return f"<fn({', '.join(self.params)})>"


class XTEmotion:
    """An emotion value — first-class in XTLang."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"@{self.name}"

    def __str__(self):
        return f"@{self.name}"

    def __eq__(self, other):
        return isinstance(other, XTEmotion) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class InterpreterError(Exception):
    def __init__(self, message, node=None):
        loc = f" at L{node.line}:{node.col}" if node and hasattr(node, 'line') else ""
        super().__init__(f"Runtime error{loc}: {message}")


class Interpreter:
    """Walk the AST and execute XTLang programs."""

    def __init__(self):
        self.global_env = Environment()
        self.output = []  # captured print output
        self.emotion = "calm"  # current emotional context
        self.trace = []  # trace buffer for @curious
        self.memo_cache = {}  # memoization cache for @driven

    def run(self, program: Program):
        """Execute a parsed program."""
        result = None
        for stmt in program.statements:
            result = self._exec(stmt, self.global_env)
        return result

    def _exec(self, node, env):
        """Execute/evaluate any AST node."""

        # ── Statements ──

        if isinstance(node, Program):
            result = None
            for stmt in node.statements:
                result = self._exec(stmt, env)
            return result

        if isinstance(node, LetStatement):
            value = self._exec(node.value, env)
            env.set(node.name, value)
            return value

        if isinstance(node, PrintStatement):
            value = self._exec(node.value, env)
            line = self._stringify(value)
            self.output.append(line)
            print(line)
            return None

        if isinstance(node, FeelStatement):
            self.emotion = node.emotion
            if node.emotion == "curious":
                self.trace = []  # reset trace on entering curious
            if node.emotion == "driven":
                self.memo_cache = {}  # fresh cache per driven session
            return XTEmotion(node.emotion)

        if isinstance(node, IntrospectExpression):
            if self.emotion != "curious":
                raise InterpreterError("introspect() only works when feeling @curious", node)
            result = list(self.trace)
            self.trace = []
            return result

        # ── Literals ──

        if isinstance(node, IntegerLiteral):
            return node.value

        if isinstance(node, FloatLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value

        if isinstance(node, EmotionLiteral):
            return XTEmotion(node.value)

        # ── Identifiers ──

        if isinstance(node, Identifier):
            return env.get(node.name)

        # ── Expressions ──

        if isinstance(node, BinaryOp):
            left = self._exec(node.left, env)
            right = self._exec(node.right, env)
            return self._binary_op(node.op, left, right, node)

        if isinstance(node, UnaryOp):
            operand = self._exec(node.operand, env)
            if node.op == '-':
                return -operand
            if node.op == 'not':
                return not self._truthy(operand)
            raise InterpreterError(f"Unknown unary operator: {node.op}", node)

        if isinstance(node, IfExpression):
            cond = self._exec(node.condition, env)
            if self._truthy(cond):
                return self._exec(node.then_branch, env)
            else:
                return self._exec(node.else_branch, env)

        if isinstance(node, FnExpression):
            return XTFunction(node.params, node.body, env)

        if isinstance(node, CallExpression):
            callee = self._exec(node.function, env)
            args = [self._exec(a, env) for a in node.arguments]

            if isinstance(callee, XTEmotion):
                # Allow emotion intensity syntax like @fear(0.5).
                # For now intensity is accepted but represented as the same first-class emotion.
                if len(args) > 1:
                    raise InterpreterError(
                        f"Emotion literal expected 0 or 1 intensity argument, got {len(args)}", node)
                return callee

            if not isinstance(callee, XTFunction):
                raise InterpreterError(f"Cannot call {type(callee).__name__}", node)

            if len(args) != len(callee.params):
                raise InterpreterError(
                    f"Expected {len(callee.params)} arguments, got {len(args)}", node)

            # @driven: memoize function results
            if self.emotion == "driven":
                cache_key = (id(callee), tuple(args))
                if cache_key in self.memo_cache:
                    return self.memo_cache[cache_key]

            # Create new scope from closure (lexical scoping)
            call_env = Environment(parent=callee.closure)
            for param, arg in zip(callee.params, args):
                call_env.set(param, arg)

            result = self._exec(callee.body, call_env)

            # @driven: cache the result
            if self.emotion == "driven":
                self.memo_cache[(id(callee), tuple(args))] = result

            return result

        if isinstance(node, BlockExpression):
            block_env = Environment(parent=env)
            for stmt in node.statements:
                self._exec(stmt, block_env)
            if node.final_expr:
                return self._exec(node.final_expr, block_env)
            return None

        if isinstance(node, ListLiteral):
            return [self._exec(el, env) for el in node.elements]

        if isinstance(node, WhileExpression):
            return self._exec_while(node, env)

        raise InterpreterError(f"Unknown AST node: {type(node).__name__}", node)

    def _exec_while(self, node, env):
        """Execute a while loop with emotional modulation.
        
        @calm:     hard cap at 1000 iterations (prevents runaway)
        @bold:     no iteration limit, runs until condition is false
        @cautious: cap at 100 iterations, warns if limit hit
        @curious:  traces each iteration to the trace buffer
        @driven:   doubles iteration speed (skips even iterations' side effects... just kidding, 
                   but tracks iteration count for performance awareness)
        default:   cap at 10000 iterations
        """
        iteration = 0
        result = None
        
        # Set limits based on emotion
        if self.emotion == "calm":
            max_iter = 1000
        elif self.emotion == "cautious":
            max_iter = 100
        elif self.emotion == "bold":
            max_iter = None  # no limit — live dangerously
        else:
            max_iter = 10000
        
        while self._truthy(self._exec(node.condition, env)):
            if max_iter is not None and iteration >= max_iter:
                if self.emotion == "cautious":
                    self.output.append(f"[@cautious] Loop halted at {max_iter} iterations")
                    print(f"[@cautious] Loop halted at {max_iter} iterations")
                break
            
            result = self._exec(node.body, env)
            iteration += 1
            
            # @curious: trace each iteration
            if self.emotion == "curious":
                self.trace.append(f"while iteration {iteration}: {self._stringify(result)}")
        
        return result

    def _binary_op(self, op, left, right, node):
        """Evaluate a binary operation, modified by current emotional state."""
        try:
            result = self._raw_binary_op(op, left, right, node)
        except InterpreterError:
            # @bold catches division by zero and returns infinity
            if self.emotion == "bold" and op == '/' and right == 0:
                result = float('inf') if left >= 0 else float('-inf')
            else:
                raise
        except TypeError as e:
            if self.emotion == "anxious":
                raise InterpreterError(
                    f"[@anxious STRICT] Cannot apply '{op}' to {type(left).__name__} and {type(right).__name__}", node)
            raise InterpreterError(
                f"Cannot apply '{op}' to {type(left).__name__} and {type(right).__name__}", node)

        # ── Emotional post-processing ──

        # @calm: clamp numeric results to [-1000, 1000]
        if self.emotion == "calm" and isinstance(result, (int, float)) and not isinstance(result, bool):
            result = max(-1000, min(1000, result))

        # @curious: log trace of arithmetic operations
        if self.emotion == "curious" and op in ('+', '-', '*', '/', '%'):
            self.trace.append(f"{self._stringify(left)} {op} {self._stringify(right)} = {self._stringify(result)}")

        # @bold: wrap overflows at 2^31 boundaries (int32 simulation)
        if self.emotion == "bold" and isinstance(result, int) and not isinstance(result, bool):
            if result > 2147483647 or result < -2147483648:
                result = ((result + 2147483648) % 4294967296) - 2147483648

        return result

    def _raw_binary_op(self, op, left, right, node):
        """Core binary operation logic without emotional modification."""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise InterpreterError("Division by zero", node)
            result = left / right
            if isinstance(result, float) and result == int(result):
                return int(result)
            return result
        elif op == '%':
            return left % right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == 'and':
            return left and right
        elif op == 'or':
            return left or right
        else:
            raise InterpreterError(f"Unknown operator: {op}", node)

    def _truthy(self, value):
        """XTLang truthiness."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, XTEmotion):
            return True  # emotions are always truthy
        return True

    def _stringify(self, value):
        """Convert a value to its print representation."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, XTEmotion):
            return str(value)
        if isinstance(value, list):
            inner = ", ".join(self._stringify(v) for v in value)
            return f"[{inner}]"
        if isinstance(value, XTFunction):
            return repr(value)
        return str(value)


# ═══════════════════════════════════════════
# Convenience entry point
# ═══════════════════════════════════════════

def execute(source_code):
    """Lex, parse, and execute XTLang source code. Returns (result, interpreter)."""
    from lexer import Lexer
    from parser import Parser

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    interp = Interpreter()
    result = interp.run(ast)
    return result, interp


# ═══════════════════════════════════════════
# Self-Test
# ═══════════════════════════════════════════

if __name__ == '__main__':
    tests = [
        ('let x = 42; print(x);', '42', 'integer'),
        ('let a = 3; let b = 4; print(a + b);', '7', 'addition'),
        ('let s = "hello"; print(s);', 'hello', 'string'),
        ('let r = 10 * 5 - 8; print(r);', '42', 'arithmetic'),
        ('let mood = @bold; print(mood);', '@bold', 'emotion literal'),
        ('let sq = fn(x) -> x * x; print(sq(7));', '49', 'function'),
        ('if 1 > 0 then print("yes") else print("no");', 'yes', 'if-then-else'),
        ('let x = if 5 > 3 then 10 else 20; print(x);', '10', 'if as expression'),
        ('print(1 + 2 * 3);', '7', 'precedence'),
        ('print(-5 + 8);', '3', 'unary minus'),
    ]

    passed = 0
    failed = 0
    for source, expected, label in tests:
        try:
            result, interp = execute(source)
            actual = interp.output[-1] if interp.output else str(result)
            if actual == expected:
                print(f"  ✓ {label}")
                passed += 1
            else:
                print(f"  ✗ {label}: expected '{expected}', got '{actual}'")
                failed += 1
        except Exception as e:
            print(f"  ✗ {label}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'═' * 40}")
    print(f"  {passed}/{passed + failed} tests passed")
    if failed == 0:
        print("  ✓ All tests passed! XTLang lives.")
    print(f"{'═' * 40}")