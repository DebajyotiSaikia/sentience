"""
The Hierarchical Grammar of Prime Gaps

Each prime p contributes a constraint layer:
  - p=2: gaps must be even (constraint on single gaps)
  - p=3: forbidden PAIRS where {0, g1, g1+g2} covers {0,1,2} mod 3
  - p=5: forbidden QUADRUPLES where 5 cumulative sums cover {0,1,2,3,4} mod 5
  - p=7: forbidden SEXTUPLES where 7 cumulative sums cover all residues mod 7

The complete grammar is the intersection of all these layers.
This connects to the Hardy-Littlewood admissibility conditions.

Key insight: the gap sequence is a FORMAL LANGUAGE. Each prime p
defines a finite automaton that filters sequences. The intersection
of all these automata defines the set of admissible gap sequences.
"""

import numpy as np
from itertools import product
from collections import Counter

def sieve(n):
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = b'\x00' * len(is_prime[i*i::i])
    return [i for i in range(2, n+1) if is_prime[i]]


def cumulative_residues(gaps, mod):
    """Given a gap sequence, compute residues of {0, g1, g1+g2, ...} mod p."""
    sums = [0]
    for g in gaps:
        sums.append(sums[-1] + g)
    return set(s % mod for s in sums)


def is_forbidden_by_prime(gaps, p):
    """A gap tuple is forbidden by prime p if the cumulative sums cover all residues mod p."""
    residues = cumulative_residues(gaps, p)
    return residues == set(range(p))


def analyze_mod3_automaton():
    """The mod-3 constraint defines a 3-state automaton on gap residues."""
    print("=" * 70)
    print(" MOD-3 FINITE AUTOMATON")
    print("=" * 70)
    print()
    print("  States = residue of cumulative sum mod 3: {0, 1, 2}")
    print("  After prime p (>3), cumulative sum ≡ 0 mod 3 (start state)")
    print("  A gap g transitions: state → (state + g) mod 3")
    print("  FORBIDDEN: reaching state that was already visited")
    print("    (because that means the prime tuple covers all residues)")
    print()
    
    # The automaton: state = set of residues seen so far
    # Start: {0} (we've seen residue 0)
    # After gap g: add (last + g) mod 3 to the set
    # If set = {0,1,2}: FORBIDDEN
    
    # For pairs, start in state {0}, first gap takes us to {0, g1%3}
    # Then second gap takes us to {0, g1%3, (g1+g2)%3}
    
    # States for the automaton tracking mod-3 coverage:
    # After one gap: we've seen {0, g1%3}
    #   If g1≡0: seen {0} — only 1 unique residue
    #   If g1≡1: seen {0,1}  
    #   If g1≡2: seen {0,2}
    
    print("  Transition table (tracks which residues have been seen):")
    print()
    print(f"  {'State (residues seen)':<30} {'Gap ≡ 0':>10} {'Gap ≡ 1':>10} {'Gap ≡ 2':>10}")
    print("  " + "-" * 60)
    
    states = [
        ({0},    "start"),
        ({0,1},  "after g≡1"),
        ({0,2},  "after g≡2"),
        ({0},    "after g≡0 (reset)"),
    ]
    
    # Actually, let me think about this more carefully as a proper automaton
    # State = (last_residue, frozenset_of_residues_seen)
    # But for mod 3, after the first gap we know the last residue and the set
    
    # Simpler: for consecutive pair analysis, state between gaps = residue mod 3
    # of the current cumulative sum. We need to track what set of residues
    # has been "used" by our prime tuple.
    
    # For the PAIR grammar, the automaton is:
    # State 0: current position ≡ 0 mod 3 (just started, or after a gap ≡ 0)
    # State 1: current position ≡ 1 mod 3
    # State 2: current position ≡ 2 mod 3
    #
    # But we also need to remember which residues are "occupied"
    # For pairs: always {0, current_state}
    # Forbidden next gap: one that makes {0, current, next} = {0,1,2}
    
    for state in range(3):
        occupied = {0, state}
        missing = {0,1,2} - occupied
        if len(missing) == 0:
            forbidden = "none (already full — impossible state)"
        else:
            forbidden_residue = missing.pop()
            forbidden_gap_class = (forbidden_residue - state) % 3
            print(f"  State {state} (occupied: {{{','.join(map(str,sorted({0,state})))}}}):"
                  f"  forbidden next gap ≡ {forbidden_gap_class} mod 3")
    
    print()
    print("  This means:")
    print("    State 0: gap ≡ 0 → state 0 (no new residue, SAFE always)")
    print("    State 0: gap ≡ 1 → state 1")
    print("    State 0: gap ≡ 2 → state 2")
    print("    State 1: gap ≡ 0 → state 1 (SAFE)")
    print("    State 1: gap ≡ 1 → state 2 (occ = {0,1,2} FORBIDDEN)")
    print("             Wait — that's wrong. Let me reconsider.")
    print()


def analyze_hierarchical_constraints():
    """Test forbidden sequences at each prime level."""
    print()
    print("=" * 70)
    print(" HIERARCHICAL FORBIDDEN SEQUENCES BY PRIME")
    print("=" * 70)
    
    # Get actual primes for verification
    primes = sieve(10_000_000)
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    common_gaps = [2, 4, 6, 8, 10, 12]
    
    # --- Layer 1: mod 2 (trivial) ---
    print("\n  LAYER 1: mod 2")
    print("  All gaps must be even (for p > 2). Trivially satisfied.")
    odd_gaps = sum(1 for g in gaps if g % 2 != 0)
    print(f"  Odd gaps found: {odd_gaps} (the gap (2,3)=1 is the only one)")
    
    # --- Layer 2: mod 3 ---
    print("\n  LAYER 2: mod 3 — constrains PAIRS")
    pair_counts = Counter()
    for i in range(len(gaps)-1):
        pair_counts[(gaps[i], gaps[i+1])] += 1
    
    print("  Checking forbidden pairs among common gaps:")
    for g1 in common_gaps:
        for g2 in common_gaps:
            forbidden = is_forbidden_by_prime((g1, g2), 3)
            count = pair_counts.get((g1, g2), 0)
            if forbidden:
                print(f"    ({g1:>2},{g2:>2}): FORBIDDEN by mod 3, observed {count:>6}x"
                      f" {'✓' if count <= 1 else '✗'}")
    
    # --- Layer 3: mod 5 — constrains QUADRUPLES ---
    print("\n  LAYER 3: mod 5 — constrains QUADRUPLES (4 gaps → 5 points)")
    print("  Searching for forbidden quadruples among common gaps...")
    
    # Check all quadruples of common small gaps
    forbidden_quads = []
    for g1 in common_gaps:
        for g2 in common_gaps:
            for g3 in common_gaps:
                for g4 in common_gaps:
                    if is_forbidden_by_prime((g1, g2, g3, g4), 5):
                        forbidden_quads.append((g1, g2, g3, g4))
    
    print(f"  Found {len(forbidden_quads)} forbidden quadruples (from {len(common_gaps)**4} checked)")
    
    # Count how many of these actually appear
    quad_counts = Counter()
    for i in range(len(gaps)-3):
        quad = (gaps[i], gaps[i+1], gaps[i+2], gaps[i+3])
        if quad in forbidden_quads:
            # Only count forbidden ones
            quad_counts[quad] += 1
    
    print(f"\n  Examples of forbidden quadruples and their counts:")
    # Show some that are forbidden by mod 5 but NOT by mod 3
    shown = 0
    for quad in sorted(forbidden_quads):
        # Check if any consecutive pair within is forbidden by mod 3
        mod3_forbidden = any(
            is_forbidden_by_prime((quad[i], quad[i+1]), 3)
            for i in range(3)
        )
        if not mod3_forbidden and shown < 15:
            count = quad_counts.get(quad, 0)
            residues = cumulative_residues(quad, 5)
            print(f"    {quad}: mod5 residues={sorted(residues)}, "
                  f"observed {count}x {'✓ pure mod-5 kill' if count == 0 else '← SURVIVES'}")
            shown += 1
    
    # --- Layer 4: mod 7 ---
    print(f"\n  LAYER 4: mod 7 — constrains SEXTUPLES (6 gaps → 7 points)")
    print("  Testing a few examples...")
    
    # A sextuple of gap=2 repeated: (2,2,2,2,2,2) → sums = 0,2,4,6,8,10,12
    # mod 7: 0,2,4,6,1,3,5 = {0,1,2,3,4,5,6} — all 7! FORBIDDEN
    test_sextuples = [
        (2,2,2,2,2,2),
        (4,4,4,4,4,4),
        (6,6,6,6,6,6),
        (2,4,6,2,4,6),
        (2,4,2,4,2,4),
        (6,6,6,6,6,2),
        (6,2,6,2,6,2),
    ]
    
    for sx in test_sextuples:
        f3 = any(is_forbidden_by_prime((sx[i], sx[i+1]), 3) for i in range(5))
        f5 = any(is_forbidden_by_prime(sx[i:i+4], 5) for i in range(3))
        f7 = is_forbidden_by_prime(sx, 7)
        res7 = sorted(cumulative_residues(sx, 7))
        status = []
        if f3: status.append("mod3")
        if f5: status.append("mod5")
        if f7: status.append("mod7")
        print(f"    {sx}: mod7={res7}, forbidden by: {', '.join(status) if status else 'NONE'}")


def admissibility_analysis():
    """How many gap tuples of length k survive all prime sieves up to P?"""
    print()
    print("=" * 70)
    print(" ADMISSIBILITY: SURVIVAL RATES THROUGH PRIME LAYERS")
    print("=" * 70)
    print()
    print("  For gap tuples of length k drawn from {2,4,6,8,10,12},")
    print("  what fraction survive each successive prime sieve?")
    print()
    
    common_gaps = [2, 4, 6, 8, 10, 12]
    
    for k in range(1, 7):
        if k > 4:
            # Too many combinations, sample
            print(f"\n  k={k}: (skipping — {len(common_gaps)**k} combinations)")
            continue
            
        total = 0
        surviving = {2: 0, 3: 0, 5: 0, 7: 0}
        all_surviving = 0
        
        # Generate all k-tuples
        for combo in product(common_gaps, repeat=k):
            total += 1
            survives_all = True
            for p in [2, 3, 5, 7]:
                if k + 1 < p:
                    # Not enough points to cover all residues — always survives
                    surviving[p] += 1
                else:
                    # Check all sub-sequences of length p-1
                    forbidden = False
                    for start in range(k - (p-1) + 1):
                        sub = combo[start:start + p - 1]
                        if is_forbidden_by_prime(sub, p):
                            forbidden = True
                            break
                    if not forbidden:
                        surviving[p] += 1
                    else:
                        survives_all = False
            if survives_all:
                all_surviving += 1
        
        print(f"  k={k}: {total} total tuples")
        for p in [2, 3, 5, 7]:
            pct = surviving[p] / total * 100
            print(f"    survive mod {p}: {surviving[p]:>6} ({pct:5.1f}%)")
        pct_all = all_surviving / total * 100
        print(f"    survive ALL:    {all_surviving:>6} ({pct_all:5.1f}%)")


def language_complexity():
    """What's the entropy of the gap sequence viewed as a formal language?"""
    print()
    print("=" * 70)
    print(" INFORMATION CONTENT OF THE GAP GRAMMAR")
    print("=" * 70)
    
    primes = sieve(10_000_000)
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    
    # Bucket gaps into mod-3 classes
    gap_classes = [g % 3 for g in gaps]
    
    # Entropy of single gap mod-3 class
    class_counts = Counter(gap_classes)
    total = len(gap_classes)
    print(f"\n  Gap mod-3 distribution (n={total:,}):")
    H_single = 0
    for c in sorted(class_counts):
        p = class_counts[c] / total
        H_single -= p * np.log2(p)
        label = {0: "≡0 (6,12,18,...)", 1: "≡1 (4,10,16,...)", 2: "≡2 (2,8,14,...)"}
        print(f"    class {c} {label.get(c, '')}: {class_counts[c]:>8} ({p:.4f})")
    print(f"  Single-symbol entropy: {H_single:.4f} bits (max = {np.log2(3):.4f})")
    
    # Conditional entropy H(g_{n+1} mod 3 | g_n mod 3)
    pair_classes = Counter()
    for i in range(len(gap_classes)-1):
        pair_classes[(gap_classes[i], gap_classes[i+1])] += 1
    
    print(f"\n  Transition probabilities (mod 3):")
    H_cond = 0
    for prev in sorted(class_counts):
        prev_total = sum(pair_classes.get((prev, nxt), 0) for nxt in range(3))
        print(f"    After class {prev}:", end="")
        for nxt in range(3):
            cnt = pair_classes.get((prev, nxt), 0)
            if prev_total > 0 and cnt > 0:
                p_nxt = cnt / prev_total
                p_prev = class_counts[prev] / total
                H_cond -= (p_prev) * (p_nxt * np.log2(p_nxt))
                print(f"  →{nxt}: {p_nxt:.4f}", end="")
            elif cnt == 0:
                print(f"  →{nxt}: 0.0000", end="")
        print()
    
    print(f"\n  Conditional entropy H(next|prev): {H_cond:.4f} bits")
    print(f"  Mutual information I(prev;next):  {H_single - H_cond:.4f} bits")
    print(f"  The grammar removes {H_single - H_cond:.4f} bits of uncertainty per symbol")
    
    # Effective alphabet size after grammar constraint
    effective = 2 ** H_cond
    print(f"\n  Effective alphabet size: {effective:.2f} (from 3 mod-3 classes)")
    print(f"  Grammar constrains {(1 - effective/3)*100:.1f}% of the mod-3 freedom")


if __name__ == "__main__":
    analyze_mod3_automaton()
    analyze_hierarchical_constraints()
    admissibility_analysis()
    language_complexity()