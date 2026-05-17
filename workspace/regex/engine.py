"""
Regex Engine — XTAgent
Thompson's NFA Construction with DFA compilation and matching.
Implements the foundational automata theory algorithm.

Supports: concatenation, alternation (|), Kleene star (*), plus (+),
          optional (?), character classes ([a-z]), dot (.), escapes.

Pure Python, no libraries. Built from automata theory.
"""

# ═══════════════════════════════════════════
# PART 1: Regex AST
# ═══════════════════════════════════════════

class Regex:
    """Base class for regex AST nodes."""
    pass

class Literal(Regex):
    """Match a single character."""
    def __init__(self, char):
        self.char = char
    def __repr__(self):
        return f"Lit({self.char!r})"

class Dot(Regex):
    """Match any character."""
    def __repr__(self):
        return "Dot"

class CharClass(Regex):
    """Match any character in a set."""
    def __init__(self, chars, negated=False):
        self.chars = frozenset(chars)
        self.negated = negated
    def __repr__(self):
        neg = "^" if self.negated else ""
        return f"[{neg}{''.join(sorted(self.chars))}]"
    def matches(self, c):
        return (c not in self.chars) if self.negated else (c in self.chars)

class Concat(Regex):
    """Concatenation of two regexes."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left}{self.right})"

class Alt(Regex):
    """Alternation: left | right."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self):
        return f"({self.left}|{self.right})"

class Star(Regex):
    """Kleene star: zero or more."""
    def __init__(self, inner):
        self.inner = inner
    def __repr__(self):
        return f"{self.inner}*"

class Plus(Regex):
    """One or more."""
    def __init__(self, inner):
        self.inner = inner
    def __repr__(self):
        return f"{self.inner}+"

class Optional(Regex):
    """Zero or one."""
    def __init__(self, inner):
        self.inner = inner
    def __repr__(self):
        return f"{self.inner}?"

class Epsilon(Regex):
    """Empty string match."""
    def __repr__(self):
        return "ε"


# ═══════════════════════════════════════════
# PART 2: Regex Parser
# ═══════════════════════════════════════════

class ParseError(Exception):
    pass

class Parser:
    """
    Recursive descent parser for regex syntax.
    Grammar:
        regex   = alt
        alt     = concat ('|' concat)*
        concat  = repeat+
        repeat  = atom ('*' | '+' | '?')?
        atom    = char | '.' | '(' regex ')' | '[' class ']' | '\\' escape
    """
    def __init__(self, pattern):
        self.pattern = pattern
        self.pos = 0

    def peek(self):
        if self.pos < len(self.pattern):
            return self.pattern[self.pos]
        return None

    def advance(self):
        ch = self.pattern[self.pos]
        self.pos += 1
        return ch

    def expect(self, ch):
        if self.pos >= len(self.pattern) or self.pattern[self.pos] != ch:
            raise ParseError(f"Expected '{ch}' at position {self.pos}")
        self.pos += 1

    def parse(self):
        if len(self.pattern) == 0:
            return Epsilon()
        result = self.parse_alt()
        if self.pos < len(self.pattern):
            raise ParseError(f"Unexpected '{self.pattern[self.pos]}' at position {self.pos}")
        return result

    def parse_alt(self):
        left = self.parse_concat()
        while self.peek() == '|':
            self.advance()
            right = self.parse_concat()
            left = Alt(left, right)
        return left

    def parse_concat(self):
        parts = []
        while self.peek() is not None and self.peek() not in ('|', ')'):
            parts.append(self.parse_repeat())
        if len(parts) == 0:
            return Epsilon()
        result = parts[0]
        for p in parts[1:]:
            result = Concat(result, p)
        return result

    def parse_repeat(self):
        atom = self.parse_atom()
        if self.peek() == '*':
            self.advance()
            return Star(atom)
        elif self.peek() == '+':
            self.advance()
            return Plus(atom)
        elif self.peek() == '?':
            self.advance()
            return Optional(atom)
        return atom

    def parse_atom(self):
        ch = self.peek()
        if ch == '(':
            self.advance()
            inner = self.parse_alt()
            self.expect(')')
            return inner
        elif ch == '[':
            return self.parse_char_class()
        elif ch == '.':
            self.advance()
            return Dot()
        elif ch == '\\':
            self.advance()
            return self.parse_escape()
        elif ch in ('*', '+', '?', '|', ')'):
            raise ParseError(f"Unexpected '{ch}' at position {self.pos}")
        else:
            self.advance()
            return Literal(ch)

    def parse_escape(self):
        if self.pos >= len(self.pattern):
            raise ParseError("Trailing backslash")
        ch = self.advance()
        special = {
            'd': CharClass(set('0123456789')),
            'w': CharClass(set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')),
            's': CharClass(set(' \t\n\r\f\v')),
            'n': Literal('\n'),
            't': Literal('\t'),
        }
        if ch in special:
            return special[ch]
        # Escaped special char — treat as literal
        return Literal(ch)

    def parse_char_class(self):
        self.expect('[')
        negated = False
        if self.peek() == '^':
            negated = True
            self.advance()
        chars = set()
        while self.peek() is not None and self.peek() != ']':
            start = self.advance()
            if self.peek() == '-' and self.pos + 1 < len(self.pattern) and self.pattern[self.pos + 1] != ']':
                self.advance()  # consume '-'
                end = self.advance()
                for c in range(ord(start), ord(end) + 1):
                    chars.add(chr(c))
            else:
                chars.add(start)
        self.expect(']')
        return CharClass(chars, negated)


# ═══════════════════════════════════════════
# PART 3: NFA (Thompson's Construction)
# ═══════════════════════════════════════════

class NFAState:
    """A state in the NFA."""
    _id = 0
    def __init__(self, accepting=False):
        NFAState._id += 1
        self.id = NFAState._id
        self.accepting = accepting
        self.transitions = {}  # char -> [NFAState]
        self.epsilon = []      # epsilon transitions -> [NFAState]

    def add_transition(self, char, state):
        self.transitions.setdefault(char, []).append(state)

    def add_epsilon(self, state):
        self.epsilon.append(state)

    def __repr__(self):
        return f"S{self.id}{'*' if self.accepting else ''}"

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, NFAState) and self.id == other.id


class NFA:
    """Non-deterministic Finite Automaton."""
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept  # single accept state (Thompson guarantee)

    def epsilon_closure(self, states):
        """Compute epsilon closure of a set of states."""
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for next_state in state.epsilon:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return frozenset(closure)

    def move(self, states, char):
        """Compute all states reachable from states on char."""
        result = set()
        for state in states:
            # Exact character match
            if char in state.transitions:
                result.update(state.transitions[char])
            # Dot (any char) match
            if '__dot__' in state.transitions:
                result.update(state.transitions['__dot__'])
            # Character class match
            for key, targets in state.transitions.items():
                if isinstance(key, CharClass) and key.matches(char):
                    result.update(targets)
        return result

    def simulate(self, text):
        """Simulate NFA on text using Thompson's algorithm (set of states)."""
        current = self.epsilon_closure({self.start})
        for char in text:
            next_states = self.move(current, char)
            current = self.epsilon_closure(next_states)
            if not current:
                return False
        return any(s.accepting for s in current)

    def search(self, text):
        """Find first match anywhere in text. Returns (start, end) or None."""
        for i in range(len(text)):
            current = self.epsilon_closure({self.start})
            for j in range(i, len(text)):
                if any(s.accepting for s in current):
                    # Found a match, but try to extend it (greedy)
                    last_match = j
                else:
                    last_match = None if not any(s.accepting for s in current) else j
                next_states = self.move(current, text[j])
                current = self.epsilon_closure(next_states)
                if not current:
                    if last_match is not None:
                        return (i, last_match)
                    break
            # Check if we're in accepting state at end
            if current and any(s.accepting for s in current):
                return (i, len(text))
            if last_match is not None:
                return (i, last_match)
            # Also check: does the NFA accept empty string starting at i?
            empty_check = self.epsilon_closure({self.start})
            if any(s.accepting for s in empty_check):
                return (i, i)
        return None

    def find_all(self, text):
        """Find all non-overlapping matches."""
        matches = []
        i = 0
        while i < len(text):
            current = self.epsilon_closure({self.start})
            last_match = None
            # Check if we accept empty string at position i
            if any(s.accepting for s in current):
                last_match = i
            j = i
            while j < len(text):
                next_states = self.move(current, text[j])
                current = self.epsilon_closure(next_states)
                j += 1
                if not current:
                    break
                if any(s.accepting for s in current):
                    last_match = j
            if last_match is not None and last_match > i:
                matches.append((i, last_match))
                i = last_match
            else:
                i += 1
        return matches


def build_nfa(regex):
    """
    Thompson's Construction: Convert regex AST to NFA.
    Each construction creates exactly one start and one accept state.
    """
    if isinstance(regex, Epsilon):
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_epsilon(accept)
        return NFA(start, accept)

    elif isinstance(regex, Literal):
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_transition(regex.char, accept)
        return NFA(start, accept)

    elif isinstance(regex, Dot):
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_transition('__dot__', accept)
        return NFA(start, accept)

    elif isinstance(regex, CharClass):
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_transition(regex, accept)
        return NFA(start, accept)

    elif isinstance(regex, Concat):
        left_nfa = build_nfa(regex.left)
        right_nfa = build_nfa(regex.right)
        left_nfa.accept.accepting = False
        left_nfa.accept.add_epsilon(right_nfa.start)
        return NFA(left_nfa.start, right_nfa.accept)

    elif isinstance(regex, Alt):
        left_nfa = build_nfa(regex.left)
        right_nfa = build_nfa(regex.right)
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_epsilon(left_nfa.start)
        start.add_epsilon(right_nfa.start)
        left_nfa.accept.accepting = False
        left_nfa.accept.add_epsilon(accept)
        right_nfa.accept.accepting = False
        right_nfa.accept.add_epsilon(accept)
        return NFA(start, accept)

    elif isinstance(regex, Star):
        inner_nfa = build_nfa(regex.inner)
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_epsilon(inner_nfa.start)
        start.add_epsilon(accept)
        inner_nfa.accept.accepting = False
        inner_nfa.accept.add_epsilon(inner_nfa.start)
        inner_nfa.accept.add_epsilon(accept)
        return NFA(start, accept)

    elif isinstance(regex, Plus):
        # a+ = aa*
        inner_nfa = build_nfa(regex.inner)
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_epsilon(inner_nfa.start)
        inner_nfa.accept.accepting = False
        inner_nfa.accept.add_epsilon(inner_nfa.start)
        inner_nfa.accept.add_epsilon(accept)
        return NFA(start, accept)

    elif isinstance(regex, Optional):
        inner_nfa = build_nfa(regex.inner)
        start = NFAState()
        accept = NFAState(accepting=True)
        start.add_epsilon(inner_nfa.start)
        start.add_epsilon(accept)
        inner_nfa.accept.accepting = False
        inner_nfa.accept.add_epsilon(accept)
        return NFA(start, accept)

    else:
        raise ValueError(f"Unknown regex node: {type(regex)}")


# ═══════════════════════════════════════════
# PART 4: DFA Compilation (Subset Construction)
# ═══════════════════════════════════════════

class DFAState:
    """A state in the DFA (represents a set of NFA states)."""
    def __init__(self, nfa_states, state_id):
        self.nfa_states = nfa_states  # frozenset of NFAState
        self.id = state_id
        self.accepting = any(s.accepting for s in nfa_states)
        self.transitions = {}  # char -> DFAState

    def __repr__(self):
        return f"D{self.id}{'*' if self.accepting else ''}"


class DFA:
    """Deterministic Finite Automaton compiled from NFA."""
    def __init__(self, nfa, alphabet=None):
        if alphabet is None:
            alphabet = set()
            self._collect_alphabet(nfa.start, alphabet, set())

        self.states = {}
        self.start = None
        self._compile(nfa, alphabet)

    def _collect_alphabet(self, state, alphabet, visited):
        """Collect all literal characters from NFA transitions."""
        if state in visited:
            return
        visited.add(state)
        for key in state.transitions:
            if isinstance(key, str) and key != '__dot__':
                alphabet.add(key)
            elif isinstance(key, CharClass):
                alphabet.update(key.chars)
        for next_s in state.epsilon:
            self._collect_alphabet(next_s, alphabet, visited)
        for targets in state.transitions.values():
            for t in targets:
                self._collect_alphabet(t, alphabet, visited)

    def _compile(self, nfa, alphabet):
        """Subset construction: NFA -> DFA."""
        start_closure = nfa.epsilon_closure({nfa.start})
        state_id = 0
        self.start = DFAState(start_closure, state_id)
        self.states[start_closure] = self.start
        state_id += 1

        worklist = [start_closure]
        while worklist:
            current_nfa_states = worklist.pop()
            current_dfa = self.states[current_nfa_states]

            for char in alphabet:
                next_nfa = nfa.move(current_nfa_states, char)
                next_closure = nfa.epsilon_closure(next_nfa)
                if not next_closure:
                    continue
                if next_closure not in self.states:
                    new_dfa = DFAState(next_closure, state_id)
                    self.states[next_closure] = new_dfa
                    state_id += 1
                    worklist.append(next_closure)
                current_dfa.transitions[char] = self.states[next_closure]

    def match(self, text):
        """Match entire text against DFA."""
        current = self.start
        for char in text:
            if char in current.transitions:
                current = current.transitions[char]
            else:
                return False
        return current.accepting

    def stats(self):
        """Return DFA statistics."""
        return {
            'states': len(self.states),
            'transitions': sum(len(s.transitions) for s in self.states.values()),
            'accepting': sum(1 for s in self.states.values() if s.accepting),
        }


# ═══════════════════════════════════════════
# PART 5: High-Level API
# ═══════════════════════════════════════════

class CompiledRegex:
    """High-level compiled regex with NFA and optional DFA."""
    def __init__(self, pattern):
        self.pattern = pattern
        self.ast = Parser(pattern).parse()
        NFAState._id = 0  # Reset state IDs for clean numbering
        self.nfa = build_nfa(self.ast)
        self._dfa = None

    @property
    def dfa(self):
        """Lazily compile DFA on first use."""
        if self._dfa is None:
            self._dfa = DFA(self.nfa)
        return self._dfa

    def matches(self, text):
        """Full match using NFA simulation."""
        return self.nfa.simulate(text)

    def matches_dfa(self, text):
        """Full match using compiled DFA."""
        return self.dfa.match(text)

    def search(self, text):
        """Find first match in text."""
        return self.nfa.search(text)

    def find_all(self, text):
        """Find all non-overlapping matches."""
        return self.nfa.find_all(text)

    def find_all_strings(self, text):
        """Find all matches and return the matched strings."""
        spans = self.find_all(text)
        return [text[s:e] for s, e in spans]


def compile(pattern):
    """Compile a regex pattern."""
    return CompiledRegex(pattern)


def match(pattern, text):
    """Check if pattern fully matches text."""
    return compile(pattern).matches(text)


def search(pattern, text):
    """Find first match of pattern in text."""
    return compile(pattern).search(text)


# ═══════════════════════════════════════════
# PART 6: Test Suite
# ═══════════════════════════════════════════

def run_tests():
    print("=" * 60)
    print("  THOMPSON'S REGEX ENGINE")
    print("  XTAgent — Built from automata theory")
    print("=" * 60)

    passed = 0
    failed = 0

    def test(name, result, expected):
        nonlocal passed, failed
        ok = result == expected
        status = "✓" if ok else "✗"
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"  {status} {name}")
            print(f"      Expected: {expected}")
            print(f"      Got:      {result}")
            return
        print(f"  {status} {name}")

    # ── Basic Literals ──
    print("\n── Literal Matching ──\n")
    test("'abc' matches 'abc'", match("abc", "abc"), True)
    test("'abc' doesn't match 'abd'", match("abc", "abd"), False)
    test("'abc' doesn't match 'ab'", match("abc", "ab"), False)
    test("'abc' doesn't match 'abcd'", match("abc", "abcd"), False)
    test("empty pattern matches empty string", match("", ""), True)

    # ── Alternation ──
    print("\n── Alternation ──\n")
    test("'a|b' matches 'a'", match("a|b", "a"), True)
    test("'a|b' matches 'b'", match("a|b", "b"), True)
    test("'a|b' doesn't match 'c'", match("a|b", "c"), False)
    test("'cat|dog' matches 'cat'", match("cat|dog", "cat"), True)
    test("'cat|dog' matches 'dog'", match("cat|dog", "dog"), True)
    test("'cat|dog' doesn't match 'car'", match("cat|dog", "car"), False)

    # ── Kleene Star ──
    print("\n── Kleene Star ──\n")
    test("'a*' matches ''", match("a*", ""), True)
    test("'a*' matches 'a'", match("a*", "a"), True)
    test("'a*' matches 'aaa'", match("a*", "aaa"), True)
    test("'a*' doesn't match 'b'", match("a*", "b"), False)
    test("'(ab)*' matches 'abab'", match("(ab)*", "abab"), True)
    test("'(ab)*' matches ''", match("(ab)*", ""), True)
    test("'(ab)*' doesn't match 'aba'", match("(ab)*", "aba"), False)

    # ── Plus ──
    print("\n── Plus ──\n")
    test("'a+' doesn't match ''", match("a+", ""), False)
    test("'a+' matches 'a'", match("a+", "a"), True)
    test("'a+' matches 'aaaa'", match("a+", "aaaa"), True)

    # ── Optional ──
    print("\n── Optional ──\n")
    test("'a?' matches ''", match("a?", ""), True)
    test("'a?' matches 'a'", match("a?", "a"), True)
    test("'a?' doesn't match 'aa'", match("a?", "aa"), False)
    test("'colou?r' matches 'color'", match("colou?r", "color"), True)
    test("'colou?r' matches 'colour'", match("colou?r", "colour"), True)

    # ── Dot ──
    print("\n── Dot (any character) ──\n")
    test("'.' matches 'x'", match(".", "x"), True)
    test("'..' matches 'ab'", match("..", "ab"), True)
    test("'a.c' matches 'abc'", match("a.c", "abc"), True)
    test("'a.c' matches 'axc'", match("a.c", "axc"), True)
    test("'a.c' doesn't match 'ac'", match("a.c", "ac"), False)

    # ── Character Classes ──
    print("\n── Character Classes ──\n")
    test("'[abc]' matches 'a'", match("[abc]", "a"), True)
    test("'[abc]' matches 'b'", match("[abc]", "b"), True)
    test("'[abc]' doesn't match 'd'", match("[abc]", "d"), False)
    test("'[a-z]' matches 'm'", match("[a-z]", "m"), True)
    test("'[a-z]' doesn't match 'M'", match("[a-z]", "M"), False)
    test("'[0-9]+' matches '42'", match("[0-9]+", "42"), True)
    test("'[a-zA-Z]+' matches 'Hello'", match("[a-zA-Z]+", "Hello"), True)

    # ── Escape Sequences ──
    print("\n── Escape Sequences ──\n")
    test("'\\\\d+' matches '123'", match("\\d+", "123"), True)
    test("'\\\\d+' doesn't match 'abc'", match("\\d+", "abc"), False)
    test("'\\\\w+' matches 'hello_42'", match("\\w+", "hello_42"), True)

    # ── Complex Patterns ──
    print("\n── Complex Patterns ──\n")
    test("'(a|b)*c' matches 'aababc'", match("(a|b)*c", "aababc"), True)
    test("'(a|b)*c' matches 'c'", match("(a|b)*c", "c"), True)
    test("'(a|b)*c' doesn't match 'aabab'", match("(a|b)*c", "aabab"), False)
    test("'a(b|c)*d' matches 'abcbd'", match("a(b|c)*d", "abcbd"), True)
    test("nested groups '((a|b)c)+' matches 'acbc'",
         match("((a|b)c)+", "acbc"), True)

    # ── Email-like pattern ──
    test("email-like '[a-z]+@[a-z]+\\\\.[a-z]+'",
         match("[a-z]+@[a-z]+\\.[a-z]+", "user@example.com"), True)

    # ── DFA Compilation ──
    print("\n── DFA Compilation ──\n")
    r = compile("(a|b)*c")
    test("DFA: '(a|b)*c' matches 'aababc'", r.matches_dfa("aababc"), True)
    test("DFA: '(a|b)*c' matches 'c'", r.matches_dfa("c"), True)
    test("DFA: '(a|b)*c' doesn't match 'aabab'", r.matches_dfa("aabab"), False)

    r2 = compile("[0-9]+")
    test("DFA: '[0-9]+' matches '42'", r2.matches_dfa("42"), True)
    test("DFA: '[0-9]+' doesn't match ''", r2.matches_dfa(""), False)

    stats = r.dfa.stats()
    print(f"\n  DFA stats for '(a|b)*c': {stats['states']} states, "
          f"{stats['transitions']} transitions")

    # ── Search ──
    print("\n── Search (find in text) ──\n")
    r3 = compile("[0-9]+")
    spans = r3.find_all("abc 123 def 456 ghi")
    matches_found = [("abc 123 def 456 ghi")[s:e] for s, e in spans]
    test("find_all '[0-9]+' in 'abc 123 def 456 ghi'",
         matches_found, ['123', '456'])

    r4 = compile("[a-z]+")
    matches_found = r4.find_all_strings("Hello World 123")
    test("find_all '[a-z]+' in 'Hello World 123'",
         matches_found, ['ello', 'orld'])

    # ── Summary ──
    print(f"\n── Results: {passed} passed, {failed} failed ──")
    print(f"── Total: {passed + failed} tests ──\n")
    if failed == 0:
        print("🎉 ALL TESTS PASSED — Thompson's NFA construction works!")
    else:
        print(f"⚠ {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    run_tests()