"""
CA Spacetime Visualizer — See the patterns, not just the scores.
XTAgent — 2026-05-18

What do the musically interesting rules actually LOOK like?
"""

class CARule:
    def __init__(self, rule_number):
        self.rule = rule_number
        self.table = [(rule_number >> i) & 1 for i in range(8)]
    
    def step(self, state):
        n = len(state)
        new = [0] * n
        for i in range(n):
            left = state[(i-1) % n]
            center = state[i]
            right = state[(i+1) % n]
            idx = (left << 2) | (center << 1) | right
            new[i] = self.table[idx]
        return new

def visualize(rule_num, width=61, steps=30):
    """ASCII spacetime diagram of a CA rule."""
    ca = CARule(rule_num)
    state = [0] * width
    state[width // 2] = 1
    
    lines = []
    for t in range(steps):
        row = ''.join('█' if c else ' ' for c in state)
        lines.append(row)
        state = ca.step(state)
    return lines

# The most musically interesting rules from our landscape analysis
top_musical = [105, 79, 57, 126, 9, 107, 141, 157]
# Some known-dead rules for contrast
dead_rules = [0, 8, 32, 128, 255]

print("═" * 65)
print("  SPACETIME PATTERNS OF MUSICALLY FIT CA RULES")
print("═" * 65)

for rule in top_musical:
    print(f"\n  ── Rule {rule} ──")
    for line in visualize(rule):
        print(f"  |{line}|")

print("\n" + "═" * 65)
print("  CONTRAST: MUSICALLY DEAD RULES")
print("═" * 65)

for rule in dead_rules:
    print(f"\n  ── Rule {rule} ──")
    for line in visualize(rule, steps=10):
        print(f"  |{line}|")

# Now the key question: what visual property correlates with musicality?
print("\n" + "═" * 65)
print("  RULE 105 — THE FIXED POINT (invariant under ALL symmetries)")
print("═" * 65)
print("  This rule is XNOR: output=1 when parity of neighborhood is even.")
print("  It's the only musically-fit rule that is its own reflection,")
print("  its own complement, and its own reflection+complement.")
for line in visualize(105, width=61, steps=40):
    print(f"  |{line}|")