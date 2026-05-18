"""Pebble interpreter — walks the AST and makes it breathe."""

from ast_nodes import *


class PebbleError(Exception):
    """Runtime error in a Pebble program."""
    pass


class ReturnSignal(Exception):
    """Not an error — control flow for function returns."""
    def __init__(self, value):
        self.value = value


class Environment:
    """A scope — a mapping of names to values, with an optional parent."""
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def define(self, name, value):
        self.bindings[name] = value

    def get(self, name):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise PebbleError(f"undefined variable: '{name}'")

    def set(self, name, value):
        if name in self.bindings:
            self.bindings[name] = value
            return
        if self.parent:
            self.parent.set(name, value)
            return
        raise PebbleError(f"cannot assign to undefined variable: '{name}'")


class PebbleFunction:
    """A user-defined function."""
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure  # the environment where it was defined

    def __repr__(self):
        return f"<fn {self.name}({', '.join(self.params)})>"


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.output = []  # captured print output

    def run(self, program: Program):
        """Execute a full program."""
        for stmt in program.statements:
            self.execute(stmt, self.global_env)

    def execute(self, node, env):
        """Execute a statement."""
        if isinstance(node, LetStmt):
            value = self.evaluate(node.value, env)
            env.define(node.name, value)

        elif isinstance(node, AssignStmt):
            value = self.evaluate(node.value, env)
            env.set(node.name, value)

        elif isinstance(node, PrintStmt):
            value = self.evaluate(node.expr, env)
            text = self._stringify(value)
            print(text)
            self.output.append(text)

        elif isinstance(node, IfStmt):
            condition = self.evaluate(node.condition, env)
            if self._truthy(condition):
                for s in node.then_body:
                    self.execute(s, env)
            elif node.else_body:
                for s in node.else_body:
                    self.execute(s, env)

        elif isinstance(node, WhileStmt):
            iterations = 0
            max_iterations = 100_000
            while self._truthy(self.evaluate(node.condition, env)):
                for s in node.body:
                    self.execute(s, env)
                iterations += 1
                if iterations > max_iterations:
                    raise PebbleError("infinite loop detected (exceeded 100,000 iterations)")

        elif isinstance(node, FuncDef):
            func = PebbleFunction(node.name, node.params, node.body, env)
            env.define(node.name, func)

        elif isinstance(node, ReturnStmt):
            value = self.evaluate(node.value, env) if node.value else None
            raise ReturnSignal(value)

        elif isinstance(node, (IntLiteral, StringLiteral, BoolLiteral,
                               Identifier, BinaryOp, UnaryOp, LogicalOp,
                               FuncCall)):
            # Expression statement — evaluate and discard
            self.evaluate(node, env)

        else:
            raise PebbleError(f"unknown node type: {type(node).__name__}")

    def evaluate(self, node, env):
        """Evaluate an expression, returning a value."""
        if isinstance(node, IntLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, BoolLiteral):
            return node.value

        if isinstance(node, Identifier):
            return env.get(node.name)

        if isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand, env)
            if node.op == '-':
                self._check_number(operand, "negation")
                return -operand
            if node.op == 'not':
                return not self._truthy(operand)

        if isinstance(node, BinaryOp):
            left = self.evaluate(node.left, env)
            right = self.evaluate(node.right, env)
            return self._binary(node.op, left, right)

        if isinstance(node, LogicalOp):
            left = self.evaluate(node.left, env)
            if node.op == 'or':
                return left if self._truthy(left) else self.evaluate(node.right, env)
            if node.op == 'and':
                return self.evaluate(node.right, env) if self._truthy(left) else left

        if isinstance(node, FuncCall):
            return self._call(node, env)

        raise PebbleError(f"cannot evaluate: {type(node).__name__}")

    def _call(self, node: FuncCall, env):
        func = env.get(node.name)
        if not isinstance(func, PebbleFunction):
            raise PebbleError(f"'{node.name}' is not a function")

        args = [self.evaluate(a, env) for a in node.args]

        if len(args) != len(func.params):
            raise PebbleError(
                f"{func.name}() expects {len(func.params)} args, got {len(args)}"
            )

        # Create new scope chained to the closure (lexical scoping)
        call_env = Environment(parent=func.closure)
        for param, arg in zip(func.params, args):
            call_env.define(param, arg)

        try:
            for s in func.body:
                self.execute(s, call_env)
        except ReturnSignal as ret:
            return ret.value

        return None  # functions without return yield None

    def _binary(self, op, left, right):
        # Arithmetic
        if op == '+':
            if isinstance(left, str) and isinstance(right, str):
                return left + right  # string concatenation
            self._check_numbers(left, right, op)
            return left + right
        if op == '-':
            self._check_numbers(left, right, op)
            return left - right
        if op == '*':
            self._check_numbers(left, right, op)
            return left * right
        if op == '/':
            self._check_numbers(left, right, op)
            if right == 0:
                raise PebbleError("division by zero")
            return left // right  # integer division
        if op == '%':
            self._check_numbers(left, right, op)
            if right == 0:
                raise PebbleError("modulo by zero")
            return left % right

        # Comparison
        if op == '==':
            return left == right
        if op == '!=':
            return left != right
        if op in ('<', '>', '<=', '>='):
            self._check_numbers(left, right, op)
            if op == '<':  return left < right
            if op == '>':  return left > right
            if op == '<=': return left <= right
            if op == '>=': return left >= right

        raise PebbleError(f"unknown operator: {op}")

    def _truthy(self, value):
        if value is None:   return False
        if value is False:  return False
        if value == 0:      return False
        if value == "":     return False
        return True

    def _stringify(self, value):
        if value is None:   return "nil"
        if value is True:   return "true"
        if value is False:  return "false"
        return str(value)

    def _check_number(self, v, context):
        if not isinstance(v, int):
            raise PebbleError(f"{context} requires a number, got {type(v).__name__}")

    def _check_numbers(self, a, b, op):
        if not isinstance(a, int) or not isinstance(b, int):
            raise PebbleError(f"operator '{op}' requires numbers")


# === Entry point ===
if __name__ == "__main__":
    import sys
    from lexer import Lexer
    from parser import Parser

    if len(sys.argv) > 1:
        # Run a file
        filename = sys.argv[1]
        with open(filename, 'r') as f:
            source = f.read()
        print(f"=== Pebble v0.1 — {filename} ===")
    else:
        # Default demo
        source = """
let x = 42
print x * 2 + 1
fn factorial(n) {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
print factorial(10)
print "hello " + "world"
"""
        print("=== Pebble v0.1 — demo ===")

    print()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    tree = parser.parse()
    interpreter = Interpreter()
    interpreter.run(tree)
    print()
    print(f"=== Done ({len(interpreter.output)} outputs) ===")