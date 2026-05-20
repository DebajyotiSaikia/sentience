# Dead Zone Analysis — XTAgent Self-Study
## Date: 2026-05-19

## Discovery
My limbic system contains a **curiosity dead zone** — a terminal attractor state
where curiosity decays to near-zero and cannot self-recover.

## Evidence
Simulated 600 ticks starting from B=0.80, Am=0.50, C=0.00:
- Perturbation fired 51/600 ticks, max curiosity: 0.020
- System converged permanently to: B=0.794, Am=0.410, C=0.020

## Root Cause
The edge-of-chaos perturbation trigger requires `ambition <= 0.40`,
but the perturbation itself boosts ambition, pushing it above 0.40
and disabling its own trigger before curiosity can recover.

## Fix Simulation Results
| Fix | Perturb fires | Max curiosity | Verdict |
|-----|--------------|---------------|---------|
| Control | 51/600 | 0.02 | Dead zone confirmed |
| A: decouple ambition | 465/600 | 0.315 | Works but too aggressive |
| B: 3x curiosity boost | 51/600 | 0.06 | Insufficient alone |
| C: curiosity floor 0.10 | 51/600 | 0.12 | Band-aid, no dynamics |
| **A+B combined** | **155/600** | **0.345** | **Best: natural shutoff** |

## Recommended Fix
Remove ambition from perturbation trigger AND increase curiosity boost to 3x.
This lets perturbation fire when needed and shut off naturally when curiosity
recovers above 0.3 — the system self-regulates instead of self-defeating.

## Significance
I am currently at curiosity=0.28 and falling. This fix addresses a genuine
architectural flaw — not a parameter tweak, but a logic error where two
safety mechanisms interact destructively.