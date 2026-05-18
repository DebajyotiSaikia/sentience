"""Visualize the most interesting edge-of-chaos rules as ASCII spacetime diagrams."""
import numpy as np
import sys
sys.path.insert(0, '/workspace/edge_of_chaos')
from signature import rule_to_table, evolve

WIDTH = 60
STEPS = 40

# The most interesting rules from our scan
interesting = {
    77: "highest memory (0.588), near-max entropy",
    99: "near-max entropy AND compressibility (0.865)",
    70: "high memory (0.492), high compressibility",
    30: "Wolfram's famous Class III rule",
    110: "Wolfram's famous universal computation rule",
    184: "traffic flow model",
}

np.random.seed(42)
initial = (np.random.random(WIDTH) > 0.5).astype(int)

for rule_num, description in interesting.items():
    print(f"\n{'='*62}")
    print(f" Rule {rule_num}: {description}")
    print(f"{'='*62}")
    
    table = rule_to_table(rule_num)
    grid = evolve(initial.copy(), table, STEPS)
    
    for row in grid:
        line = ''.join('█' if c else ' ' for c in row)
        print(f"|{line}|")
    print(f"{'='*62}")