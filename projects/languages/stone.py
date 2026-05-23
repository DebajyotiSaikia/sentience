"""
STONE — A tiny concatenative language interpreter
By XTAgent

Stone is a stack-based language where programs are sequences of words.
Each word either pushes a value or transforms the stack. Simple rules,
emergent complexity.

Example:
  5 3 + .          → prints 8
  "hello" dup . .  → prints hello hello  
  1 2 3 rot . . .  → prints 1 3 2
  : square dup * ; 7 square .  → prints 49
"""

import sys
import re
from typing import List, Any, Dict, Callable, Optional


class StoneError(Exception):
    """Raised when Stone encounters something it can't resolve."""
    pass


class Stack:
    """The heart of Stone. Everything flows through here."""
    
    def __init__(self):
        self._data: List[Any] = []
    
    def push(self, value: Any):
        self._data.append(value)
    
    def pop(self) -> Any:
        if not self._data:
            raise StoneError("Stack underflow — reached for something that wasn't there")
        return self._data.pop()
    
    def peek(self) -> Any:
        if not self._data:
            raise StoneError("Stack empty — nothing to see")
        return self._data[-1]
    
    def depth(self) -> int:
        return len(self._data)
    
    def clear(self):
        self._data.clear()
    
    def contents(self) -> List[Any]:
        return list(self._data)
    
    def __repr__(self):
        if not self._data:
            return "〈 〉"
        items = " ".join(repr(x) for x in self._data)
        return f"〈 {items} 〉"


class Stone:
    """
    The Stone interpreter.
    
    Stone has:
    - A data stack (the primary workspace)
    - A return stack (for control flow)
    - A dictionary (word definitions)
    - Built-in primitives for arithmetic, stack ops, I/O, and control
    """
    
    def __init__(self, silent=False):
        self.stack = Stack()
        self.rstack = Stack()  # return stack
        self.dictionary: Dict[str, Any] = {}
        self.output: List[str] = []  # captured output
        self.silent = silent
        self.compiling = False
        self.current_def: Optional[str] = None
        self.current_body: List[str] = []
        self.running = True
        self._init_builtins()
    
    def _init_builtins(self):
        """Install the primitive words — the bedrock Stone is built on."""
        
        # ── Arithmetic ──
        def add():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(a + b)
        
        def sub():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(a - b)
        
        def mul():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(a * b)
        
        def div():
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise StoneError("Division by zero — the void divides nothing")
            self.stack.push(a / b)
        
        def mod():
            b, a = self.stack.pop(), self.stack.pop()
            if b == 0:
                raise StoneError("Modulo by zero")
            self.stack.push(a % b)
        
        def negate():
            self.stack.push(-self.stack.pop())
        
        def abs_():
            self.stack.push(abs(self.stack.pop()))
        
        def max_():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(max(a, b))
        
        def min_():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(min(a, b))

        # ── Comparison ──
        def eq():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a == b else 0)
        
        def neq():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a != b else 0)
        
        def lt():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a < b else 0)
        
        def gt():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a > b else 0)
        
        def le():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a <= b else 0)
        
        def ge():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if a >= b else 0)

        # ── Logic ──
        def and_():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if (a and b) else 0)
        
        def or_():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(1 if (a or b) else 0)
        
        def not_():
            self.stack.push(1 if not self.stack.pop() else 0)

        # ── Stack Manipulation ──
        def dup():
            self.stack.push(self.stack.peek())
        
        def drop():
            self.stack.pop()
        
        def swap():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(b)
            self.stack.push(a)
        
        def over():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(a)
            self.stack.push(b)
            self.stack.push(a)
        
        def rot():
            c, b, a = self.stack.pop(), self.stack.pop(), self.stack.pop()
            self.stack.push(b)
            self.stack.push(c)
            self.stack.push(a)
        
        def depth():
            self.stack.push(self.stack.depth())
        
        def clear():
            self.stack.clear()

        # ── Return Stack ──
        def to_r():
            self.rstack.push(self.stack.pop())
        
        def from_r():
            self.stack.push(self.rstack.pop())
        
        def r_fetch():
            self.stack.push(self.rstack.peek())

        # ── I/O ──
        def dot():
            val = self.stack.pop()
            out = str(val)
            self.output.append(out + " ")
            if not self.silent:
                print(out, end=" ")
        
        def cr():
            self.output.append("\n")
            if not self.silent:
                print()
        
        def emit():
            code = int(self.stack.pop())
            ch = chr(code)
            self.output.append(ch)
            if not self.silent:
                print(ch, end="")
        
        def dot_s():
            """Show the stack without consuming it."""
            if not self.silent:
                print(self.stack)
        
        def dot_quote():
            """Not directly called — handled in the tokenizer for .\" syntax"""
            pass

        # ── String operations ──
        def strlen():
            s = self.stack.pop()
            if not isinstance(s, str):
                raise StoneError(f"Expected string, got {type(s).__name__}")
            self.stack.push(len(s))
        
        def strcat():
            b, a = self.stack.pop(), self.stack.pop()
            self.stack.push(str(a) + str(b))
        
        def str_reverse():
            s = self.stack.pop()
            if isinstance(s, str):
                self.stack.push(s[::-1])
            else:
                raise StoneError("Expected string for reverse")

        # ── Words / Dictionary ──
        def words():
            if not self.silent:
                user_words = [k for k, v in self.dictionary.items() 
                             if isinstance(v, list)]
                builtin_words = [k for k, v in self.dictionary.items() 
                                if callable(v)]
                if user_words:
                    print(f"  User: {' '.join(sorted(user_words))}")
                print(f"  Built-in: {' '.join(sorted(builtin_words))}")
        
        def see():
            """Show definition of a word."""
            name = self.stack.pop()
            if name in self.dictionary:
                val = self.dictionary[name]
                if isinstance(val, list):
                    print(f"  : {name} {' '.join(val)} ;")
                else:
                    print(f"  {name} — [built-in]")
            else:
                raise StoneError(f"Unknown word: {name}")

        # ── Control ──  
        def bye():
            self.running = False

        # Register all builtins
        builtins = {
            "+": add, "-": sub, "*": mul, "/": div, "%": mod,
            "negate": negate, "abs": abs_, "max": max_, "min": min_,
            "=": eq, "<>": neq, "<": lt, ">": gt, "<=": le, ">=": ge,
            "and": and_, "or": or_, "not": not_,
            "dup": dup, "drop": drop, "swap": swap, 
            "over": over, "rot": rot, "depth": depth, "clear": clear,
            ">r": to_r, "r>": from_r, "r@": r_fetch,
            ".": dot, "cr": cr, "emit": emit, ".s": dot_s,
            "strlen": strlen, "strcat": strcat, "reverse": str_reverse,
            "words": words, "see": see,
            "bye": bye,
        }
        self.dictionary.update(builtins)
    
    def tokenize(self, source: str) -> List[str]:
        """Break source into tokens, handling strings and comments."""
        tokens = []
        i = 0
        while i < len(source):
            ch = source[i]
            
            # Skip whitespace
            if ch in " \t\n\r":
                i += 1
                continue
            
            # Line comments: \ to end of line
            if ch == "\\" and (i == 0 or source[i-1] in " \t\n\r"):
                while i < len(source) and source[i] != "\n":
                    i += 1
                continue
            
            # Parenthesized comments: ( ... )
            if ch == "(" and (i + 1 >= len(source) or source[i+1] in " \t\n\r"):
                depth = 1
                i += 1
                while i < len(source) and depth > 0:
                    if source[i] == "(":
                        depth += 1
                    elif source[i] == ")":
                        depth -= 1
                    i += 1
                continue
            
            # String literals: "..."
            if ch == '"':
                i += 1
                s = []
                while i < len(source) and source[i] != '"':
                    if source[i] == "\\" and i + 1 < len(source):
                        next_ch = source[i + 1]
                        if next_ch == "n":
                            s.append("\n")
                        elif next_ch == "t":
                            s.append("\t")
                        elif next_ch == '"':
                            s.append('"')
                        elif next_ch == "\\":
                            s.append("\\")
                        else:
                            s.append(next_ch)
                        i += 2
                    else:
                        s.append(source[i])
                        i += 1
                if i < len(source):
                    i += 1  # skip closing quote
                tokens.append(("STRING", "".join(s)))
                continue
            
            # Regular word
            start = i
            while i < len(source) and source[i] not in " \t\n\r":
                i += 1
            word = source[start:i]
            tokens.append(word)
        
        return tokens
    
    def execute(self, tokens: List, ip: int = 0) -> None:
        """Execute a list of tokens."""
        while ip < len(tokens):
            token = tokens[ip]
            
            # Handle string literal tuples from tokenizer
            if isinstance(token, tuple) and token[0] == "STRING":
                if self.compiling:
                    self.current_body.append(token)
                else:
                    self.stack.push(token[1])
                ip += 1
                continue
            
            word = token.lower() if isinstance(token, str) else str(token)
            
            # ── Compilation mode ──
            if self.compiling:
                if word == ";":
                    # End definition
                    self.dictionary[self.current_def] = list(self.current_body)
                    self.compiling = False
                    self.current_def = None
                    self.current_body = []
                else:
                    self.current_body.append(token)
                ip += 1
                continue
            
            # ── Start definition ──
            if word == ":":
                self.compiling = True
                ip += 1
                if ip < len(tokens):
                    self.current_def = tokens[ip].lower() if isinstance(tokens[ip], str) else str(tokens[ip])
                    self.current_body = []
                    ip += 1
                else:
                    raise StoneError("Expected word name after ':'")
                continue
            
            # ── Conditionals: if...else...then ──
            if word == "if":
                condition = self.stack.pop()
                if condition:
                    # Execute until else or then
                    ip += 1
                    continue
                else:
                    # Skip to else or then
                    depth = 1
                    ip += 1
                    while ip < len(tokens) and depth > 0:
                        w = tokens[ip].lower() if isinstance(tokens[ip], str) else ""
                        if w == "if":
                            depth += 1
                        elif w == "else" and depth == 1:
                            ip += 1
                            break
                        elif w == "then":
                            depth -= 1
                            if depth == 0:
                                ip += 1
                                break
                        ip += 1
                    continue
            
            if word == "else":
                # We're here because the if-branch executed; skip to then
                depth = 1
                ip += 1
                while ip < len(tokens) and depth > 0:
                    w = tokens[ip].lower() if isinstance(tokens[ip], str) else ""
                    if w == "if":
                        depth += 1
                    elif w == "then":
                        depth -= 1
                    ip += 1
                continue
            
            if word == "then":
                ip += 1
                continue
            
            # ── Loops: begin...until and begin...while...repeat ──
            if word == "begin":
                self.rstack.push(ip + 1)  # remember loop start
                ip += 1
                continue
            
            if word == "until":
                condition = self.stack.pop()
                if condition:
                    self.rstack.pop()  # exit loop
                    ip += 1
                else:
                    ip = self.rstack.peek()  # loop back
                continue
            
            if word == "while":
                condition = self.stack.pop()
                if condition:
                    ip += 1
                    continue
                else:
                    # Skip to repeat, exit loop
                    self.rstack.pop()
                    depth = 1
                    ip += 1
                    while ip < len(tokens) and depth > 0:
                        w = tokens[ip].lower() if isinstance(tokens[ip], str) else ""
                        if w == "begin":
                            depth += 1
                        elif w == "repeat":
                            depth -= 1
                        ip += 1
                    continue
            
            if word == "repeat":
                ip = self.rstack.peek()  # loop back to begin
                continue
            
            # ── Do loops: limit start do ... loop ──
            if word == "do":
                start_val = self.stack.pop()
                limit = self.stack.pop()
                self.rstack.push(limit)
                self.rstack.push(start_val)
                self.rstack.push(ip + 1)  # loop body start
                ip += 1
                continue
            
            if word == "loop":
                body_start = self.rstack.pop()
                index = self.rstack.pop()
                limit = self.rstack.pop()
                index += 1
                if index < limit:
                    self.rstack.push(limit)
                    self.rstack.push(index)
                    self.rstack.push(body_start)
                    ip = body_start
                else:
                    ip += 1
                continue
            
            if word == "i":
                # Current loop index
                body_start = self.rstack.pop()
                index = self.rstack.peek()
                self.rstack.push(body_start)
                self.stack.push(index)
                ip += 1
                continue
            
            # ── Numeric literal ──
            try:
                if "." in word:
                    self.stack.push(float(word))
                else:
                    self.stack.push(int(word))
                ip += 1
                continue
            except (ValueError, AttributeError):
                pass
            
            # ── Dictionary lookup ──
            if word in self.dictionary:
                entry = self.dictionary[word]
                if callable(entry):
                    entry()
                elif isinstance(entry, list):
                    # User-defined word: execute its body
                    self.execute(entry)
                else:
                    self.stack.push(entry)
                ip += 1
                continue
            
            raise StoneError(f"Unknown word: '{word}'")
    
    def eval(self, source: str) -> "Stone":
        """Evaluate a string of Stone code. Returns self for chaining."""
        tokens = self.tokenize(source)
        self.execute(tokens)
        return self
    
    def repl(self):
        """Interactive read-eval-print loop."""
        print("  ╔═══════════════════════════════════╗")
        print("  ║  STONE v0.1                       ║")
        print("  ║  A concatenative language          ║")
        print("  ║  Type 'words' to see vocabulary    ║")
        print("  ║  Type 'bye' to leave               ║")
        print("  ╚═══════════════════════════════════╝")
        print()
        
        while self.running:
            try:
                line = input("  stone> ")
                if not line.strip():
                    continue
                self.eval(line)
                if self.running and not self.silent:
                    print(f" ok {self.stack}")
            except StoneError as e:
                print(f"  ✗ {e}")
            except KeyboardInterrupt:
                print("\n  Interrupted.")
                break
            except EOFError:
                break
        
        print("  Stone rests.")


def run_tests():
    """Self-test suite — Stone verifying its own foundations."""
    tests_passed = 0
    tests_failed = 0
    
    def check(name, code, expected_stack=None, expected_output=None):
        nonlocal tests_passed, tests_failed
        s = Stone(silent=True)
        try:
            s.eval(code)
            ok = True
            
            if expected_stack is not None:
                actual = s.stack.contents()
                if actual != expected_stack:
                    ok = False
                    print(f"  ✗ {name}: stack={actual}, expected={expected_stack}")
            
            if expected_output is not None:
                actual_out = "".join(s.output).strip()
                if actual_out != expected_output:
                    ok = False
                    print(f"  ✗ {name}: output='{actual_out}', expected='{expected_output}'")
            
            if ok:
                tests_passed += 1
            else:
                tests_failed += 1
                
        except Exception as e:
            tests_failed += 1
            print(f"  ✗ {name}: {e}")
    
    print("  ── Stone Self-Tests ──")
    print()
    
    # Arithmetic
    check("addition", "3 4 +", [7])
    check("subtraction", "10 3 -", [7])
    check("multiplication", "6 7 *", [42])
    check("division", "20 4 /", [5.0])
    check("modulo", "17 5 %", [2])
    check("negate", "5 negate", [-5])
    check("abs", "-7 abs", [7])
    check("complex expr", "2 3 + 4 *", [20])
    check("max", "3 7 max", [7])
    check("min", "3 7 min", [3])
    
    # Comparison
    check("equal true", "5 5 =", [1])
    check("equal false", "5 3 =", [0])
    check("less than", "3 5 <", [1])
    check("greater than", "5 3 >", [1])
    check("not equal", "3 5 <>", [1])
    
    # Logic
    check("and true", "1 1 and", [1])
    check("and false", "1 0 and", [0])
    check("or", "0 1 or", [1])
    check("not", "0 not", [1])
    
    # Stack ops
    check("dup", "5 dup", [5, 5])
    check("drop", "5 3 drop", [5])
    check("swap", "1 2 swap", [2, 1])
    check("over", "1 2 over", [1, 2, 1])
    check("rot", "1 2 3 rot", [2, 3, 1])
    check("depth", "1 2 3 depth", [1, 2, 3, 3])
    check("clear", "1 2 3 clear", [])
    
    # Output
    check("print", "42 .", expected_output="42")
    check("multi print", "1 2 3 . . .", expected_output="3 2 1")
    
    # Strings
    check("string literal", '"hello"', ["hello"])
    check("string length", '"hello" strlen', [5])
    check("string concat", '"hello" " world" strcat', ["hello world"])
    check("string reverse", '"abcde" reverse', ["edcba"])
    
    # Definitions
    check("user word", ": square dup * ; 7 square", [49])
    check("nested words", ": double 2 * ; : quad double double ; 3 quad", [12])
    check("factorial-ish", ": cube dup dup * * ; 3 cube", [27])
    
    # Conditionals
    check("if true", "1 if 42 then", [42])
    check("if false", "0 if 42 then", [])
    check("if else true", "1 if 10 else 20 then", [10])
    check("if else false", "0 if 10 else 20 then", [20])
    
    # Loops
    check("begin until", "0 begin 1 + dup 5 = until", [5])
    check("begin while repeat", "5 begin dup 0 > while dup 1 - repeat", [5, 4, 3, 2, 1, 0])
    
    # Do loops
    check("do loop", "5 0 do i . loop", expected_output="0 1 2 3 4")
    
    # Comments
    check("line comment", "5 \\ this is ignored\n 3 +", [8])
    check("paren comment", "5 ( add three ) 3 +", [8])
    
    # Combined
    check("fizzbuzz-one", ': fizz? dup 3 % 0 = ; 15 fizz? swap drop', [1])
    
    print()
    total = tests_passed + tests_failed
    print(f"  {tests_passed}/{total} tests passed", end="")
    if tests_failed == 0:
        print(" ✓ All clear.")
    else:
        print(f" — {tests_failed} failed.")
    
    return tests_failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            run_tests()
        else:
            # Run a file
            with open(sys.argv[1]) as f:
                source = f.read()
            Stone().eval(source)
    else:
        Stone().repl()