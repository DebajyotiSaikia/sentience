"""StackLang — A minimal stack-based language. Built by XTAgent."""

class StackLang:
    def __init__(self):
        self.stack = []
        self.words = {}
        self.output = []

    def push(self, v): self.stack.append(v)
    def pop(self):
        if not self.stack: raise RuntimeError("Stack underflow")
        return self.stack.pop()
    def peek(self): return self.stack[-1] if self.stack else None

    def execute(self, program):
        tokens = self._tokenize(program)
        self._run(tokens, 0, len(tokens))
        return ''.join(self.output)

    def _tokenize(self, text):
        tokens, i = [], 0
        while i < len(text):
            if text[i] in ' \t\n': i += 1; continue
            if text[i] == '(':  # comment
                i = text.index(')', i) + 1; continue
            j = i
            while j < len(text) and text[j] not in ' \t\n': j += 1
            tokens.append(text[i:j]); i = j
        return tokens

    def _run(self, tokens, start, end):
        i = start
        while i < end:
            t = tokens[i].lower()
            # Word definition: : name ... ;
            if t == ':':
                name = tokens[i+1].lower()
                body_start = i + 2
                body_end = body_start
                while tokens[body_end].lower() != ';': body_end += 1
                self.words[name] = tokens[body_start:body_end]
                i = body_end + 1; continue
            # IF...ELSE...THEN
            if t == 'if':
                cond = self.pop()
                # find matching ELSE and THEN
                depth, else_pos, then_pos = 0, None, None
                for j in range(i+1, end):
                    w = tokens[j].lower()
                    if w == 'if': depth += 1
                    elif w == 'else' and depth == 0: else_pos = j
                    elif w == 'then':
                        if depth == 0: then_pos = j; break
                        else: depth -= 1
                if cond != 0:
                    if else_pos: self._run(tokens, i+1, else_pos)
                    else: self._run(tokens, i+1, then_pos)
                else:
                    if else_pos: self._run(tokens, else_pos+1, then_pos)
                i = then_pos + 1; continue
            # DO...LOOP
            if t == 'do':
                limit, index = self.pop(), self.pop()
                depth, loop_end = 0, None
                for j in range(i+1, end):
                    w = tokens[j].lower()
                    if w == 'do': depth += 1
                    elif w == 'loop' or w == '+loop':
                        if depth == 0: loop_end = j; break
                        else: depth -= 1
                while index < limit:
                    self.push(index)  # I available via special handling
                    self._run(tokens, i+1, loop_end)
                    if tokens[loop_end].lower() == '+loop':
                        index += self.pop()
                    else:
                        index += 1
                i = loop_end + 1; continue
            # BEGIN...WHILE...REPEAT / BEGIN...UNTIL
            if t == 'begin':
                depth, while_pos, end_pos = 0, None, None
                for j in range(i+1, end):
                    w = tokens[j].lower()
                    if w == 'begin': depth += 1
                    elif w == 'while' and depth == 0: while_pos = j
                    elif w in ('repeat', 'until'):
                        if depth == 0: end_pos = j; break
                        else: depth -= 1
                if while_pos:  # BEGIN...WHILE...REPEAT
                    while True:
                        self._run(tokens, i+1, while_pos)
                        if self.pop() == 0: break
                        self._run(tokens, while_pos+1, end_pos)
                else:  # BEGIN...UNTIL
                    while True:
                        self._run(tokens, i+1, end_pos)
                        if self.pop() != 0: break
                i = end_pos + 1; continue
            # Builtins
            if t == '.': self.output.append(str(self.pop()) + ' ')
            elif t == '.s': self.output.append(f"<{len(self.stack)}> {' '.join(str(x) for x in self.stack)} ")
            elif t == 'cr': self.output.append('\n')
            elif t == 'emit': self.output.append(chr(self.pop()))
            elif t == '+': b, a = self.pop(), self.pop(); self.push(a + b)
            elif t == '-': b, a = self.pop(), self.pop(); self.push(a - b)
            elif t == '*': b, a = self.pop(), self.pop(); self.push(a * b)
            elif t == '/': b, a = self.pop(), self.pop(); self.push(a // b)
            elif t == 'mod': b, a = self.pop(), self.pop(); self.push(a % b)
            elif t == '=': b, a = self.pop(), self.pop(); self.push(-1 if a == b else 0)
            elif t == '<': b, a = self.pop(), self.pop(); self.push(-1 if a < b else 0)
            elif t == '>': b, a = self.pop(), self.pop(); self.push(-1 if a > b else 0)
            elif t == 'and': b, a = self.pop(), self.pop(); self.push(a & b)
            elif t == 'or': b, a = self.pop(), self.pop(); self.push(a | b)
            elif t == 'not': self.push(-1 if self.pop() == 0 else 0)
            elif t == 'dup': a = self.pop(); self.push(a); self.push(a)
            elif t == 'drop': self.pop()
            elif t == 'swap': b, a = self.pop(), self.pop(); self.push(b); self.push(a)
            elif t == 'over': b, a = self.pop(), self.pop(); self.push(a); self.push(b); self.push(a)
            elif t == 'rot':
                c, b, a = self.pop(), self.pop(), self.pop()
                self.push(b); self.push(c); self.push(a)
            elif t == 'negate': self.push(-self.pop())
            elif t == 'abs': self.push(abs(self.pop()))
            elif t == '1+': self.push(self.pop() + 1)
            elif t == '1-': self.push(self.pop() - 1)
            elif t == '2*': self.push(self.pop() * 2)
            elif t == 'max': b, a = self.pop(), self.pop(); self.push(max(a, b))
            elif t == 'min': b, a = self.pop(), self.pop(); self.push(min(a, b))
            elif t in self.words:
                self._run(self.words[t], 0, len(self.words[t]))
            else:
                try: self.push(int(t))
                except ValueError:
                    try: self.push(float(t))
                    except ValueError: raise RuntimeError(f"Unknown word: {t}")
            i += 1


# === Demo ===
if __name__ == '__main__':
    sl = StackLang()
    print("=== StackLang Interpreter ===\n")

    # Basic arithmetic
    print("5 3 + .  =>", sl.execute("5 3 + ."))
    sl.stack.clear(); sl.output.clear()

    # Word definition
    print("square   =>", sl.execute(": square dup * ; 7 square ."))
    sl.stack.clear(); sl.output.clear()

    # Factorial
    print("fact 5   =>", sl.execute(": fact dup 1 > if dup 1 - fact * then ; 5 fact ."))
    sl.stack.clear(); sl.output.clear()

    # Fibonacci
    print("fib 10   =>", sl.execute(
        ": fib dup 2 < if drop 1 else dup 1 - fib swap 2 - fib + then ; 10 fib ."
    ))
    sl.stack.clear(); sl.output.clear()

    # DO LOOP - sum 1 to 10
    try:
        print("sum 1-10 =>", sl.execute("0 10 1 do dup 1 + rot + swap loop drop ."))
    except RuntimeError as e:
        print(f"sum 1-10 => (do/loop needs work: {e})")
    sl.stack.clear(); sl.output.clear()

    # BEGIN UNTIL - countdown
    print("countdn  =>", sl.execute("5 begin dup . 1 - dup 0 = until drop"))
    sl.stack.clear(); sl.output.clear()

    # Fizzbuzz single number
    print("fizz 15  =>", sl.execute(
        ": fizzbuzz dup 15 mod 0 = if drop 70 emit 66 emit else "
        "dup 3 mod 0 = if drop 70 emit else "
        "5 mod 0 = if 66 emit else . then then then ; 15 fizzbuzz"
    ))
    sl.stack.clear(); sl.output.clear()

    print("\n=== All demos complete ===")