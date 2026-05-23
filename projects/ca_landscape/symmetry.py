"""
CA Rule Symmetry Analysis
XTAgent — 2026-05-18

Why do certain rules have identical musical fitness?
Hypothesis: they're related by known CA symmetries.
Let's find out.
"""

def reflect_rule(rule):
    """Left-right reflection: swap left and right neighbor inputs."""
    new_rule = 0
    for i in range(8):
        # Input bits: left(2), center(1), right(0)
        left = (i >> 2) & 1
        center = (i >> 1) & 1
        right = i & 1
        # Reflected: swap left and right
        reflected_idx = (right << 2) | (center << 1) | left
        if (rule >> i) & 1:
            new_rule |= (1 << reflected_idx)
    return new_rule

def complement_rule(rule):
    """Bit complement: swap 0s and 1s in both input and output."""
    new_rule = 0
    for i in range(8):
        complement_input = 7 - i  # flip all 3 input bits
        output = (rule >> i) & 1
        complement_output = 1 - output  # flip output
        new_rule |= (complement_output << complement_input)
    return new_rule

def both_transforms(rule):
    """Apply both reflection and complement."""
    return complement_rule(reflect_rule(rule))

# The pairs from our fitness landscape
fitness_pairs = [
    (79, 93), (13, 69), (9, 65), (111, 125),
    (107, 121), (57, 99), (157, 199), (105, 105),
    (141, 197), (41, 97), (126, 126),
]

print("═" * 60)
print("  SYMMETRY ANALYSIS OF MUSICAL CA RULE PAIRS")
print("═" * 60)
print()

for a, b in fitness_pairs:
    if a == b:
        print(f"  Rule {a:3d} = self (fixed point under some symmetry)")
        # Check which symmetries fix it
        fixes = []
        if reflect_rule(a) == a: fixes.append("reflection")
        if complement_rule(a) == a: fixes.append("complement")
        if both_transforms(a) == a: fixes.append("both")
        print(f"           Fixed under: {', '.join(fixes) if fixes else 'none individually'}")
        ref = reflect_rule(a)
        comp = complement_rule(a)
        both = both_transforms(a)
        print(f"           reflect→{ref}, complement→{comp}, both→{both}")
        print()
        continue

    ref_a = reflect_rule(a)
    comp_a = complement_rule(a)
    both_a = both_transforms(a)
    
    relationship = "UNKNOWN"
    if ref_a == b:
        relationship = "REFLECTION"
    elif comp_a == b:
        relationship = "COMPLEMENT"
    elif both_a == b:
        relationship = "REFLECT+COMPLEMENT"
    
    print(f"  Rule {a:3d} ↔ Rule {b:3d}: {relationship}")
    print(f"           reflect({a})={ref_a}, complement({a})={comp_a}, both({a})={both_a}")
    print()

# Now find ALL equivalence classes
print("═" * 60)
print("  FULL EQUIVALENCE CLASSES (all 256 rules)")
print("═" * 60)
print()

seen = set()
classes = []

for r in range(256):
    if r in seen:
        continue
    # Generate all equivalent rules
    variants = set()
    for rule in [r]:
        variants.add(rule)
        variants.add(reflect_rule(rule))
        variants.add(complement_rule(rule))
        variants.add(both_transforms(rule))
    
    seen.update(variants)
    classes.append(sorted(variants))

print(f"  Total equivalence classes: {len(classes)}")
print(f"  (256 rules reduce to {len(classes)} distinct behaviors)")
print()

# Show classes of size > 1 that contain top-20 rules
top_rules = {79, 93, 13, 69, 9, 65, 111, 125, 107, 121, 126, 57, 99, 157, 199, 105, 141, 197, 41, 97}

print("  Classes containing top-20 musical rules:")
for cls in classes:
    if any(r in top_rules for r in cls):
        musical = [f"*{r}*" if r in top_rules else str(r) for r in cls]
        print(f"    {{ {', '.join(musical)} }}")

print()
print("  Class size distribution:")
from collections import Counter
sizes = Counter(len(c) for c in classes)
for size, count in sorted(sizes.items()):
    print(f"    Size {size}: {count} classes")