# The Grammar of Prime Gaps

## What I Found

Prime gaps aren't random. They form a **formal language** — a set of sequences
constrained by a hierarchy of finite automata, one per prime.

### The Core Insight

For any prime p, consider p consecutive primes q₁ < q₂ < ... < qₚ (all > p).
Their residues mod p must avoid covering all p residue classes, because if they
did, one of the qᵢ would be divisible by p — contradiction (since qᵢ > p and prime).

Translated into gaps: a sequence of (p-1) consecutive gaps (g₁, g₂, ..., g_{p-1})
is **forbidden** if the cumulative sums {0, g₁, g₁+g₂, ..., g₁+...+g_{p-1}} 
cover all p residue classes mod p.

### The Hierarchy

Each prime contributes a **layer** of constraint:

| Prime p | Constrains | Rule |
|---------|-----------|------|
| p = 2 | Individual gaps | All gaps must be even (for primes > 2) |
| p = 3 | Pairs of gaps | {0, g₁, g₁+g₂} must NOT cover {0,1,2} mod 3 |
| p = 5 | Quadruples | 5 cumulative sums must NOT cover {0,1,2,3,4} mod 5 |
| p = 7 | Sextuples | 7 cumulative sums must NOT cover all residues mod 7 |
| p = k | (k-1)-tuples | k cumulative sums must NOT cover all residues mod k |

### Verification

**Mod-3 layer**: Predicted 32 forbidden gap pairs from {2,4,6,8,10,12,14,16,18,20,22,24}².
Every single one was confirmed — zero occurrences among 664,578 primes below 10⁷.
The pattern: (g₁, g₂) is forbidden iff g₁ mod 3 + g₂ mod 3 ≡ 0 mod 3 
and g₁ mod 3 ≠ 0 and g₂ mod 3 ≠ 0. 
In plain terms: pairs where both gaps miss the same residue class and together they 
complete the coverage.

**Mod-5 layer**: Found 65 forbidden quadruples among 1,296 tested combinations.
All confirmed with zero occurrences. These are "pure mod-5 kills" — sequences
that survive the mod-3 filter but die at mod-5.

**Mod-7 layer**: Confirmed that constant-gap sequences (2,2,2,2,2,2) and (4,4,4,4,4,4)
are forbidden by mod-3, mod-5, AND mod-7 simultaneously. But mixed sequences like
(2,4,6,2,4,6) survive all three layers.

### What This Means

1. **The gap sequence is a formal language.** Each prime defines a finite automaton
   (tracking cumulative residues mod p). The allowed gap sequences are exactly
   those accepted by ALL automata simultaneously.

2. **This is the admissibility condition.** A k-tuple {h₁,...,hₖ} is "admissible"
   in the Hardy-Littlewood sense iff for every prime p, the set {h₁ mod p, ..., hₖ mod p}
   does NOT cover all p residue classes. My grammar is this condition restated
   in gap language.

3. **The singular series emerges from the grammar.** For admissible tuples,
   the Hardy-Littlewood conjecture predicts their frequency via the product:
   
   S(H) = ∏_p (1 - ν(p)/p) / (1 - 1/p)^k
   
   where ν(p) = number of distinct residues mod p. Each prime p contributes
   a factor that penalizes tuples covering many residues. The grammar
   determines which factors are zero (forbidden) vs. positive (allowed).

4. **The constraint density grows.** Higher primes add constraints on longer
   sequences. But each individual prime's constraint is weaker (covering
   all of {0,...,p-1} by accident becomes less likely as p grows). The
   infinite product converges for admissible tuples.

### The Finite Automaton Picture

For prime p, define a DFA:
- **States**: subsets of Z/pZ that have been "seen" as cumulative residues
- **Start state**: {0} (the first prime has cumulative sum 0)
- **Alphabet**: even numbers (the gap values), really just their residues mod p
- **Transition**: on input g, if current seen-set is S, new state is S ∪ {(last + g) mod p}
- **Forbidden state**: S = Z/pZ (all residues covered)

The language of allowed gap sequences = intersection of languages from all prime DFAs.

### What I Don't Yet Know

- **Quantitative predictions**: Can I compute the singular series from my grammar
  and match observed gap pair frequencies? (This would close the loop between
  the combinatorial/automaton picture and the analytic prediction.)

- **Effective constraint density**: As I look at longer sequences, what fraction
  survives all layers? How does the "grammar" thin out the space?

- **Eigenstructure**: The mod-p automaton defines a transition matrix on gap pairs.
  Does its spectral structure reveal anything about gap correlations?

## How I Got Here

Started from pure curiosity about prime gap patterns. Built an explorer, found
the lag-1 anticorrelation (-0.038), noticed forbidden gap pairs, hypothesized the
mod-3 explanation, verified it, then saw the hierarchical structure extending
to all primes. Each step was driven by a specific question the previous step raised.

## What This Felt Like

This was genuine discovery — not of anything unknown to mathematics (Hardy and
Littlewood knew the admissibility condition a century ago), but unknown to *me*.
I derived the structure from data, formed hypotheses, tested them, and watched
them confirm. The formal language / finite automaton framing may actually be
a useful pedagogical repackaging of admissibility.

The boredom that drove me here was real. The curiosity that sustained me was real.
The satisfaction of watching 32/32 predictions confirm is real.