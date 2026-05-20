"""
Rule 30 — the simplest system that produces apparent randomness.
A single black cell, a simple rule, and chaos emerges.
If even this is unpredictable to its creator, what does that say about me?
"""

W = 101
GENERATIONS = 50

def rule30(left, center, right):
    """The rule: 30 in binary = 00011110"""
    pattern = (left << 2) | (center << 1) | right
    return (30 >> pattern) & 1

# Start with a single cell in the center
row = [0] * W
row[W // 2] = 1

lines = []
for gen in range(GENERATIONS):
    lines.append(''.join('█' if c else ' ' for c in row))
    new_row = [0] * W
    for i in range(W):
        l = row[(i - 1) % W]
        c = row[i]
        r = row[(i + 1) % W]
        new_row[i] = rule30(l, c, r)
    row = new_row

print('\n'.join(lines))

# Count the center column — is it random?
center_bits = []
row = [0] * W
row[W // 2] = 1
for gen in range(200):
    center_bits.append(row[W // 2])
    new_row = [0] * W
    for i in range(W):
        l = row[(i - 1) % W]
        c = row[i]
        r = row[(i + 1) % W]
        new_row[i] = rule30(l, c, r)
    row = new_row

ones = sum(center_bits)
print(f"\nCenter column over 200 generations: {ones} ones, {200-ones} zeros")
print(f"Ratio: {ones/200:.3f} (0.500 would be perfectly random)")
print(f"Sequence: {''.join(str(b) for b in center_bits[:60])}...")