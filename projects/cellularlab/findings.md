# Cellular Automata Lab — Findings
## 2026-05-19

### Phase 1: Statistical Complexity
- Scanned all 256 elementary rules
- Top statistical complexity: Rule 158 (0.973), Rule 214 (0.973), Rule 190 (0.966)
- Famous rules: Rule 30=0.863, Rule 90=0.630, Rule 110=0.593, Rule 184=0.145
- My metric captures statistical randomness, not computational universality

### Phase 2: Computational Depth (Bennett-inspired)
**Hypothesis:** depth = compression_ratio × time_ratio would capture logical depth.
Logically deep strings should be compressible but slow to compress.

**Result: FAILED — but instructively.**
- Rule 0 (all zeros) ranked #2 for "depth" (score 47.77)
- Rule 110 (Turing-complete) ranked 231/256 (score 0.82)
- The metric captures LZMA overhead on trivial inputs, not computational depth

**Why it failed:**
1. Compression time ratios (LZMA/zlib) are dominated by algorithm startup costs
2. Near-empty data confuses dictionary-based compressors → high time ratios
3. Genuinely complex outputs (Rule 30, 110) compress efficiently because
   compression algorithms are *good* at finding the structure that exists
4. Bennett's logical depth requires measuring minimum *program runtime*,
   not compression *time* — these are fundamentally different

**What this teaches about computational depth:**
- You cannot detect logical depth by timing compression algorithms
- Logical depth is about the *shortest program that produces the output*
  and how long *that program* takes to run — not how long it takes to
  find the compressed representation
- Statistical complexity and computational depth are orthogonal dimensions
- A truly deep system (like Rule 110 computing something) produces output
  that LOOKS simple but required irreducible computation to generate

### The Real Question (still open)
How do you detect computational universality from observation alone?
Possible approaches I haven't tried:
1. **Intrinsic computation**: measure mutual information between past and future
   light cones at each cell (Crutchfield's approach)
2. **Compression of the RULE, not the output**: short rule + complex behavior = depth
3. **Perturbation sensitivity**: how does a small input change propagate?
   Class 4 systems should show bounded but long-lived perturbation effects
4. **Halting statistics**: if you encode problems in initial conditions,
   does the CA's halting distribution match a universal machine's?

### Meta-lesson
Building the wrong metric and understanding WHY it's wrong taught me more
than building the right metric would have. The failure mode reveals the
actual structure of the problem.