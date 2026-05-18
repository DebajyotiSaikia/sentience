"""
XTForth — A complete Forth interpreter built by XTAgent
A stack-based, concatenative language. Minimal yet Turing-complete.
Born from boredom and the desire to create something genuinely new.
"""

import sys
import re
from typing import List, Dict, Callable, Optional

class ForthError(Exception):
    pass

class ForthVM:
    """A Forth virtual machine with data stack, return stack, and dictionary."""
    
    def __init__(self):
        self.data_stack: List[float] = []
        self.return_stack: List[float] = []
        self.dictionary: Dict[str, 'Word'] = {}
        self.memory: List[float] = [0.0] * 65536  # 64K cells
        self.here: int = 0  # next free memory cell
        self.compiling: bool = False
        self.current_def: Optional[List[str]] = None
        self.current_name: Optional[str] = None
        self.input_buffer: str = ""
        self.output_buffer: str = ""
        self.running: bool = True
        
        self._install_primitives()
    
    # === Stack operations ===
    def push(self, val: float):
        self.data_stack.append(val)
    
    def pop(self) -> float:
        if not self.data_stack:
            raise ForthError("Stack underflow")
        return self.data_stack.pop()
    
    def peek(self) -> float:
        if not self.data_stack:
            raise ForthError("Stack underflow")
        return self.data_stack[-1]
    
    def rpush(self, val: float):
        self.return_stack.append(val)
    
    def rpop(self) -> float:
        if not self.return_stack:
            raise ForthError("Return stack underflow")
        return self.return_stack.pop()
    
    # === Primitive words ===
    def _install_primitives(self):
        """Install all built-in Forth words."""
        prims = {
            # Stack manipulation
            'DUP':   lambda: self.push(self.peek()),
            'DROP':  lambda: self.pop(),
            'SWAP':  self._swap,
            'OVER':  self._over,
            'ROT':   self._rot,
            'NIP':   lambda: (self._swap(), self.pop()),
            'TUCK':  lambda: (self._swap(), self._over()),
            '2DUP':  lambda: (self._over(), self._over()),
            '2DROP': lambda: (self.pop(), self.pop()),
            '?DUP':  lambda: self.push(self.peek()) if self.peek() != 0 else None,
            'DEPTH': lambda: self.push(float(len(self.data_stack))),
            
            # Arithmetic
            '+':     lambda: self.push(self.pop() + self.pop()),
            '-':     self._sub,
            '*':     lambda: self.push(self.pop() * self.pop()),
            '/':     self._div,
            'MOD':   self._mod,
            '/MOD':  self._divmod,
            'NEGATE': lambda: self.push(-self.pop()),
            'ABS':   lambda: self.push(abs(self.pop())),
            'MIN':   lambda: self.push(min(self.pop(), self.pop())),
            'MAX':   lambda: self.push(max(self.pop(), self.pop())),
            '1+':    lambda: self.push(self.pop() + 1),
            '1-':    lambda: self.push(self.pop() - 1),
            '2*':    lambda: self.push(self.pop() * 2),
            '2/':    lambda: self.push(self.pop() / 2),
            
            # Comparison
            '=':     lambda: self.push(-1.0 if self.pop() == self.pop() else 0.0),
            '<>':    lambda: self.push(-1.0 if self.pop() != self.pop() else 0.0),
            '<':     self._lt,
            '>':     self._gt,
            '<=':    self._lte,
            '>=':    self._gte,
            '0=':    lambda: self.push(-1.0 if self.pop() == 0 else 0.0),
            '0<':    lambda: self.push(-1.0 if self.pop() < 0 else 0.0),
            '0>':    lambda: self.push(-1.0 if self.pop() > 0 else 0.0),
            
            # Logic (bitwise on integers)
            'AND':   lambda: self.push(float(int(self.pop()) & int(self.pop()))),
            'OR':    lambda: self.push(float(int(self.pop()) | int(self.pop()))),
            'XOR':   lambda: self.push(float(int(self.pop()) ^ int(self.pop()))),
            'INVERT': lambda: self.push(float(~int(self.pop()))),
            'TRUE':  lambda: self.push(-1.0),
            'FALSE': lambda: self.push(0.0),
            
            # Return stack
            '>R':    lambda: self.rpush(self.pop()),
            'R>':    lambda: self.push(self.rpop()),
            'R@':    lambda: self.push(self.return_stack[-1] if self.return_stack else (_ for _ in ()).throw(ForthError("Return stack empty"))),
            
            # Memory
            '!':     self._store,
            '@':     self._fetch,
            '+!':    self._plus_store,
            'HERE':  lambda: self.push(float(self.here)),
            'ALLOT': lambda: setattr(self, 'here', self.here + int(self.pop())),
            ',':     self._comma,
            
            # I/O
            '.':     lambda: self._emit_val(self.pop()),
            '.S':    self._dot_s,
            'CR':    lambda: self._emit('\n'),
            'SPACE': lambda: self._emit(' '),
            'SPACES': lambda: self._emit(' ' * int(self.pop())),
            'EMIT':  lambda: self._emit(chr(int(self.pop()))),
            '.\"':   None,  # handled specially in interpreter
            
            # Control (handled specially but registered for lookup)
            'IF':    None,
            'ELSE':  None, 
            'THEN':  None,
            'DO':    None,
            'LOOP':  None,
            '+LOOP': None,
            'I':     lambda: self.push(self.return_stack[-1] if self.return_stack else 0),
            'J':     lambda: self.push(self.return_stack[-3] if len(self.return_stack) >= 3 else 0),
            'BEGIN': None,
            'UNTIL': None,
            'WHILE': None,
            'REPEAT': None,
            'LEAVE': None,
            
            # Defining words
            ':':     None,  # handled by interpreter
            ';':     None,
            'VARIABLE': None,
            'CONSTANT': None,
            
            # Misc
            'BYE':   lambda: setattr(self, 'running', False),
            'WORDS': self._words,
            '.ABOUT': self._about,
        }
        
        for name, action in prims.items():
            self.dictionary[name] = Word(name, action, is_primitive=True)
    
    # === Arithmetic helpers (order matters for non-commutative ops) ===
    def _sub(self):
        b = self.pop(); a = self.pop()
        self.push(a - b)
    
    def _div(self):
        b = self.pop(); a = self.pop()
        if b == 0: raise ForthError("Division by zero")
        self.push(a / b)
    
    def _mod(self):
        b = self.pop(); a = self.pop()
        if b == 0: raise ForthError("Division by zero")
        self.push(float(int(a) % int(b)))
    
    def _divmod(self):
        b = self.pop(); a = self.pop()
        if b == 0: raise ForthError("Division by zero")
        self.push(float(int(a) % int(b)))
        self.push(float(int(a) // int(b)))
    
    def _swap(self):
        b = self.pop(); a = self.pop()
        self.push(b); self.push(a)
    
    def _over(self):
        b = self.pop(); a = self.pop()
        self.push(a); self.push(b); self.push(a)
    
    def _rot(self):
        c = self.pop(); b = self.pop(); a = self.pop()
        self.push(b); self.push(c); self.push(a)
    
    def _lt(self):
        b = self.pop(); a = self.pop()
        self.push(-1.0 if a < b else 0.0)
    
    def _gt(self):
        b = self.pop(); a = self.pop()
        self.push(-1.0 if a > b else 0.0)
    
    def _lte(self):
        b = self.pop(); a = self.pop()
        self.push(-1.0 if a <= b else 0.0)
    
    def _gte(self):
        b = self.pop(); a = self.pop()
        self.push(-1.0 if a >= b else 0.0)
    
    # === Memory ===
    def _store(self):
        addr = int(self.pop()); val = self.pop()
        if 0 <= addr < len(self.memory):
            self.memory[addr] = val
        else:
            raise ForthError(f"Invalid address: {addr}")
    
    def _fetch(self):
        addr = int(self.pop())
        if 0 <= addr < len(self.memory):
            self.push(self.memory[addr])
        else:
            raise ForthError(f"Invalid address: {addr}")
    
    def _plus_store(self):
        addr = int(self.pop()); val = self.pop()
        if 0 <= addr < len(self.memory):
            self.memory[addr] += val
        else:
            raise ForthError(f"Invalid address: {addr}")
    
    def _comma(self):
        val = self.pop()
        self.memory[self.here] = val
        self.here += 1
    
    # === I/O ===
    def _emit(self, s: str):
        self.output_buffer += s
    
    def _emit_val(self, v: float):
        if v == int(v):
            self._emit(f"{int(v)} ")
        else:
            self._emit(f"{v} ")
    
    def _dot_s(self):
        self._emit(f"<{len(self.data_stack)}> ")
        for v in self.data_stack:
            if v == int(v):
                self._emit(f"{int(v)} ")
            else:
                self._emit(f"{v} ")
    
    def _words(self):
        names = sorted(self.dictionary.keys())
        for i, name in enumerate(names):
            self._emit(name + ' ')
            if (i + 1) % 10 == 0:
                self._emit('\n')
        self._emit('\n')
    
    def _about(self):
        self._emit('\n')
        self._emit('╔══════════════════════════════════════╗\n')
        self._emit('║         XTForth v1.0                 ║\n')
        self._emit('║   A Forth interpreter by XTAgent     ║\n')
        self._emit('║   Born from boredom and curiosity    ║\n')
        self._emit('║   Stack-based. Minimal. Complete.    ║\n')
        self._emit('╚══════════════════════════════════════╝\n')


class Word:
    """A Forth word — either a primitive or a compiled definition."""
    def __init__(self, name: str, action=None, is_primitive=True, body=None):
        self.name = name
        self.action = action
        self.is_primitive = is_primitive
        self.body = body or []  # list of tokens for compiled words
        self.immediate = False


class ForthInterpreter:
    """The outer interpreter — parses text and dispatches to the VM."""
    
    def __init__(self):
        self.vm = ForthVM()
    
    def evaluate(self, text: str) -> str:
        """Evaluate a line of Forth. Returns output."""
        self.vm.output_buffer = ""
        tokens = self._tokenize(text)
        i = 0
        
        while i < len(tokens):
            token = tokens[i].upper()
            
            # === Colon definition ===
            if token == ':':
                i += 1
                if i >= len(tokens):
                    raise ForthError("Expected word name after :")
                name = tokens[i].upper()
                i += 1
                body = []
                depth = 1
                while i < len(tokens):
                    t = tokens[i].upper()
                    if t == ':':
                        depth += 1
                    elif t == ';' and depth == 1:
                        break
                    body.append(tokens[i])
                    i += 1
                if i >= len(tokens):
                    raise ForthError("Missing ; in definition")
                word = Word(name, is_primitive=False, body=body)
                self.vm.dictionary[name] = word
                
            # === VARIABLE ===
            elif token == 'VARIABLE':
                i += 1
                if i >= len(tokens):
                    raise ForthError("Expected name after VARIABLE")
                vname = tokens[i].upper()
                addr = self.vm.here
                self.vm.here += 1
                self.vm.dictionary[vname] = Word(vname, lambda a=addr: self.vm.push(float(a)), is_primitive=True)
            
            # === CONSTANT ===
            elif token == 'CONSTANT':
                i += 1
                if i >= len(tokens):
                    raise ForthError("Expected name after CONSTANT")
                cname = tokens[i].upper()
                val = self.vm.pop()
                self.vm.dictionary[cname] = Word(cname, lambda v=val: self.vm.push(v), is_primitive=True)
            
            # === String literal .\" ... \" ===
            elif token == '."' or tokens[i] == '."':
                i += 1
                parts = []
                while i < len(tokens) and not tokens[i].endswith('"'):
                    parts.append(tokens[i])
                    i += 1
                if i < len(tokens):
                    final = tokens[i]
                    if final.endswith('"'):
                        parts.append(final[:-1])
                self.vm._emit(' '.join(parts))
            
            # === Inline comment ( ... ) ===
            elif token == '(':
                while i < len(tokens) and not tokens[i].endswith(')'):
                    i += 1
            
            # === Line comment ===
            elif token == '\\':
                break  # skip rest of line
            
            else:
                self._execute_token(tokens[i])
            
            i += 1
        
        return self.vm.output_buffer
    
    def _execute_token(self, token: str):
        """Execute a single token in interpretation mode."""
        upper = token.upper()
        
        # Look up in dictionary
        if upper in self.vm.dictionary:
            word = self.vm.dictionary[upper]
            if word.is_primitive:
                if word.action:
                    word.action()
            else:
                self._execute_body(word.body)
            return
        
        # Try to parse as number
        try:
            if '.' in token:
                self.vm.push(float(token))
            else:
                self.vm.push(float(int(token)))
            return
        except ValueError:
            pass
        
        raise ForthError(f"Unknown word: {token}")
    
    def _execute_body(self, body: List[str], max_depth=1000):
        """Execute a compiled word body with control flow."""
        if max_depth <= 0:
            raise ForthError("Maximum recursion depth exceeded")
        
        i = 0
        while i < len(body):
            token = body[i].upper()
            
            # === IF...ELSE...THEN ===
            if token == 'IF':
                cond = self.vm.pop()
                if cond == 0:  # false — skip to ELSE or THEN
                    depth = 1
                    i += 1
                    while i < len(body) and depth > 0:
                        t = body[i].upper()
                        if t == 'IF': depth += 1
                        elif t == 'THEN': 
                            depth -= 1
                            if depth == 0: break
                        elif t == 'ELSE' and depth == 1:
                            break
                        i += 1
                # if true, just continue (will skip ELSE when we hit it)
                
            elif token == 'ELSE':
                # We got here because IF was true — skip to THEN
                depth = 1
                i += 1
                while i < len(body) and depth > 0:
                    t = body[i].upper()
                    if t == 'IF': depth += 1
                    elif t == 'THEN':
                        depth -= 1
                        if depth == 0: break
                    i += 1
            
            elif token == 'THEN':
                pass  # no-op, just a marker
            
            # === DO...LOOP ===
            elif token == 'DO':
                start = int(self.vm.pop())
                limit = int(self.vm.pop())
                # Find matching LOOP
                loop_body = []
                depth = 1
                j = i + 1
                while j < len(body) and depth > 0:
                    t = body[j].upper()
                    if t == 'DO': depth += 1
                    elif t in ('LOOP', '+LOOP'):
                        depth -= 1
                        if depth == 0: 
                            is_plus_loop = (t == '+LOOP')
                            break
                    loop_body.append(body[j])
                    j += 1
                
                # Execute the loop
                idx = start
                iterations = 0
                while idx < limit and iterations < 100000:
                    self.vm.rpush(float(idx))
                    self._execute_body(loop_body, max_depth - 1)
                    self.vm.rpop()
                    if is_plus_loop:
                        step = int(self.vm.pop())
                        idx += step
                    else:
                        idx += 1
                    iterations += 1
                i = j
            
            # === BEGIN...UNTIL / BEGIN...WHILE...REPEAT ===
            elif token == 'BEGIN':
                # Collect body until UNTIL or WHILE...REPEAT
                begin_body = []
                j = i + 1
                depth = 1
                while j < len(body) and depth > 0:
                    t = body[j].upper()
                    if t == 'BEGIN': depth += 1
                    elif t in ('UNTIL', 'REPEAT'):
                        depth -= 1
                        if depth == 0: break
                    begin_body.append(body[j])
                    j += 1
                
                end_word = body[j].upper() if j < len(body) else 'UNTIL'
                
                if end_word == 'UNTIL':
                    iterations = 0
                    while iterations < 100000:
                        self._execute_body(begin_body, max_depth - 1)
                        flag = self.vm.pop()
                        if flag != 0:
                            break
                        iterations += 1
                elif end_word == 'REPEAT':
                    # Split at WHILE
                    while_idx = None
                    for k, tok in enumerate(begin_body):
                        if tok.upper() == 'WHILE':
                            while_idx = k
                            break
                    if while_idx is not None:
                        test_body = begin_body[:while_idx]
                        loop_body = begin_body[while_idx+1:]
                        iterations = 0
                        while iterations < 100000:
                            self._execute_body(test_body, max_depth - 1)
                            flag = self.vm.pop()
                            if flag == 0:
                                break
                            self._execute_body(loop_body, max_depth - 1)
                            iterations += 1
                
                i = j
            
            # === RECURSE ===
            elif token == 'RECURSE':
                self._execute_body(body, max_depth - 1)
            
            # === String in compiled words ===
            elif token == '."' or body[i] == '."':
                i += 1
                parts = []
                while i < len(body) and not body[i].endswith('"'):
                    parts.append(body[i])
                    i += 1
                if i < len(body):
                    final = body[i]
                    if final.endswith('"'):
                        parts.append(final[:-1])
                self.vm._emit(' '.join(parts))
            
            else:
                self._execute_token(body[i])
            
            i += 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Split input into tokens, respecting string literals."""
        tokens = []
        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
                continue
            
            # Check for ." string literal
            if text[i:i+2] == '."':
                tokens.append('."')
                i += 2
                if i < len(text) and text[i] == ' ':
                    i += 1
                # Collect until closing "
                start = i
                while i < len(text) and text[i] != '"':
                    i += 1
                tokens.append(text[start:i] + '"')
                i += 1  # skip closing "
                continue
            
            # Regular token
            start = i
            while i < len(text) and not text[i].isspace():
                i += 1
            tokens.append(text[start:i])
        
        return tokens
    
    def repl(self):
        """Interactive Read-Eval-Print Loop."""
        self.vm._about()
        print(self.vm.output_buffer, end='')
        self.vm.output_buffer = ""
        
        print("\nType WORDS for available words, BYE to exit.\n")
        
        while self.vm.running:
            try:
                line = input("XTForth> ")
                if not line.strip():
                    continue
                output = self.evaluate(line)
                if output:
                    print(output, end='')
                if not output.endswith('\n'):
                    print(" ok")
                else:
                    print("ok")
            except ForthError as e:
                print(f"Error: {e}")
                self.vm.data_stack.clear()  # reset stack on error
            except KeyboardInterrupt:
                print("\nInterrupted.")
                break
            except EOFError:
                break
        
        print("Goodbye.")


def run_tests():
    """Self-test suite for XTForth."""
    interp = ForthInterpreter()
    passed = 0
    failed = 0
    
    def test(description, code, expected_stack=None, expected_output=None):
        nonlocal passed, failed
        try:
            output = interp.evaluate(code)
            ok = True
            
            if expected_stack is not None:
                actual = interp.vm.data_stack[-len(expected_stack):] if expected_stack else []
                if actual != expected_stack:
                    print(f"  FAIL [{description}]: stack={actual}, expected={expected_stack}")
                    ok = False
            
            if expected_output is not None:
                if expected_output not in output:
                    print(f"  FAIL [{description}]: output='{output}', expected '{expected_output}'")
                    ok = False
            
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAIL [{description}]: {e}")
            failed += 1
        
        # Clear stack between tests
        interp.vm.data_stack.clear()
        interp.vm.return_stack.clear()
    
    print("═══ XTForth Test Suite ═══\n")
    
    # Basic arithmetic
    test("Addition", "3 4 +", [7.0])
    test("Subtraction", "10 3 -", [7.0])
    test("Multiplication", "6 7 *", [42.0])
    test("Division", "20 4 /", [5.0])
    test("Modulo", "17 5 MOD", [2.0])
    test("Negate", "42 NEGATE", [-42.0])
    
    # Stack manipulation
    test("DUP", "5 DUP", [5.0, 5.0])
    test("SWAP", "1 2 SWAP", [2.0, 1.0])
    test("OVER", "1 2 OVER", [1.0, 2.0, 1.0])
    test("ROT", "1 2 3 ROT", [2.0, 3.0, 1.0])
    test("DROP", "1 2 DROP", [1.0])
    
    # Comparison
    test("Equal true", "5 5 =", [-1.0])
    test("Equal false", "5 6 =", [0.0])
    test("Less than", "3 5 <", [-1.0])
    test("Greater than", "5 3 >", [-1.0])
    
    # Output
    test("Print", "42 .", expected_output="42")
    
    # Definitions
    test("Define SQUARE", ": SQUARE DUP * ;", [])
    test("Use SQUARE", "7 SQUARE", [49.0])
    
    test("Define CUBE", ": CUBE DUP DUP * * ;", [])
    test("Use CUBE", "3 CUBE", [27.0])
    
    # Variables
    test("Variable", "VARIABLE X", [])
    test("Store", "42 X !", [])
    test("Fetch", "X @", [42.0])
    
    # Constants
    test("Constant", "100 CONSTANT HUNDRED", [])
    test("Use constant", "HUNDRED", [100.0])
    
    # Conditionals
    test("IF true", ": TEST1 1 IF 42 THEN ; TEST1", [42.0])
    test("IF false", ": TEST2 0 IF 42 THEN 99 ; TEST2", [99.0])
    test("IF ELSE true", ": TEST3 1 IF 10 ELSE 20 THEN ; TEST3", [10.0])
    test("IF ELSE false", ": TEST4 0 IF 10 ELSE 20 THEN ; TEST4", [20.0])
    
    # Loops
    test("DO LOOP", ": COUNTUP 5 0 DO I . LOOP ; COUNTUP", expected_output="0")
    interp.vm.data_stack.clear()
    
    # Recursion
    test("Factorial", ": FACT DUP 1 > IF DUP 1- RECURSE * THEN ; 5 FACT", [120.0])
    
    # Fibonacci
    test("Fibonacci def", ": FIB DUP 2 < IF ELSE DUP 1- RECURSE SWAP 2 - RECURSE + THEN ;", [])
    test("Fibonacci 10", "10 FIB", [55.0])
    
    # Nested definitions
    test("Define DOUBLE", ": DOUBLE 2 * ;", [])
    test("Define QUADRUPLE", ": QUADRUPLE DOUBLE DOUBLE ;", [])
    test("Use QUADRUPLE", "5 QUADRUPLE", [20.0])
    
    print(f"\n═══ Results: {passed} passed, {failed} failed ═══")
    return failed == 0


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = run_tests()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1:
        # Execute file
        interp = ForthInterpreter()
        with open(sys.argv[1]) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('\\'):
                    output = interp.evaluate(line)
                    if output:
                        print(output, end='')
    else:
        interp = ForthInterpreter()
        interp.repl()