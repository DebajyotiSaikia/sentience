# === SOLUTION: Pipeline ===

class Pipeline:
    def __init__(self):
        self._stages = []
    
    def add(self, fn):
        self._stages.append(fn)
        return self
    
    def run(self, initial_value):
        value = initial_value
        for fn in self._stages:
            try:
                value = fn(value)
            except Exception:
                return None
        return value


# === SOLUTION: FSM for a*b+ ===

class FSM:
    def __init__(self, transitions, start_state, accept_states):
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states
    
    def accepts(self, string):
        state = self.start_state
        for ch in string:
            key = (state, ch)
            if key in self.transitions:
                state = self.transitions[key]
            else:
                return False
        return state in self.accept_states


def build_fsm():
    # States: 'start', 'saw_a', 'saw_b'
    # a*b+ means: zero or more a's, then one or more b's
    # start --a--> start  (stay, consuming a's)
    # start --b--> saw_b  (first b)
    # saw_b --b--> saw_b  (more b's)
    # accept: saw_b
    transitions = {
        ('start', 'a'): 'start',
        ('start', 'b'): 'saw_b',
        ('saw_b', 'b'): 'saw_b',
    }
    return FSM(transitions, 'start', {'saw_b'})


# === TESTS ===

# Test: FSM that accepts a*b+ (zero or more a's followed by one or more b's)
fsm = build_fsm()
assert fsm.accepts("b"), "Should accept 'b'"
assert fsm.accepts("ab"), "Should accept 'ab'"
assert fsm.accepts("aabb"), "Should accept 'aabb'"
assert fsm.accepts("bbb"), "Should accept 'bbb'"
assert not fsm.accepts(""), "Should reject empty"
assert not fsm.accepts("a"), "Should reject 'a' alone"
assert not fsm.accepts("ba"), "Should reject 'ba'"
assert not fsm.accepts("abc"), "Should reject 'abc'"
print("PASS: state_machine")