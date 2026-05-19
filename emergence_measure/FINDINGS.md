# Emergence Measurement Experiment — Findings

## Hypothesis
Structurally emergent systems (like Conway's Life) should show positive 
"emergence signal" — meaning coarse-grained descriptions need fewer bits 
per cell than fine-grained ones.

## Method
- Ran cellular automata with various rules on 32x32 grids
- Measured Shannon entropy at micro scale (individual cells)
- Measured Shannon entropy at macro scale (2x2 block averages)  
- Emergence signal = micro_bits - macro_bits (positive = emergent)

## Results
| Rule | Signal | Emergent? |
|------|--------|-----------|
| B3/S12345 (Maze) | +0.039 | Barely |
| Random noise | -0.535 | No |
| B18/S237 | -0.734 | No |
| B3/S23 (Conway) | -0.797 | No |
| B36/S23 (HighLife) | -0.801 | No |

## Interpretation
**The simple compression-based emergence measure doesn't work as expected.**

Why? Coarse-graining (averaging 2x2 blocks) creates NEW information — the 
block averages can take on more distinct values than individual binary cells.
A 2x2 block of binary cells has 5 possible average values (0, 0.25, 0.5, 0.75, 1.0),
which is MORE states than the 2 states of a single cell. So the macro level 
has a higher entropy ceiling, not lower.

This is actually a known subtlety in the emergence literature. Real emergence 
measurement requires:
1. Choosing the RIGHT coarse-graining (not just spatial averaging)
2. Measuring mutual information between scales, not just entropy at each scale
3. Possibly using effective information (EI) as per Tononi/Hoel

## What I Learned
- Simple ideas about emergence don't survive contact with actual computation
- The coarse-graining choice IS the hard problem — not the measurement
- A negative result is still a result. I now understand WHY it failed.
- Next step would be: implement Hoel's causal emergence measure (effective information)