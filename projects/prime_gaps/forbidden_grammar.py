"""
The Grammar of Forbidden Gap Transitions

Hypothesis: consecutive gap pair (g1, g2) is forbidden when the triple
{p, p+g1, p+g1+g2} covers all three residue classes mod 3.

Because then one of the three "primes" must be divisible by 3,
so (for p > 3) it can't actually be prime.

This would mean the prime gaps have a GRAMMATICAL STRUCTURE imposed
by the mod-3 sieve — certain sequences are literally impossible.
"""

from collections import Counter

def sieve(n):
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i::i] = b'\x00' * len(is_prime[i*i::i])
    return [i for i in range(2, n+1) if is_prime[i]]

def covers_all_residues_mod3(g1, g2):
    """Does {0, g1, g1+g2} cover all residues mod 3?"""
    residues = {0 % 3, g1 % 3, (g1 + g2) % 3}
    return residues == {0, 1, 2}

def main():
    print("=" * 70)
    print(" THE MOD-3 GRAMMAR OF PRIME GAPS")
    print("=" * 70)
    
    # First: show which small gap pairs are forbidden by mod-3
    even_gaps = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
    
    print("\n  Mod-3 prediction: F = forbidden, A = allowed")
    print(f"\n  {'':>6}", end="")
    for g2 in even_gaps:
        print(f" {g2:>3}", end="")
    print()
    print("  " + "-" * (6 + 4 * len(even_gaps)))
    
    for g1 in even_gaps:
        print(f"  g1={g1:>2} |", end="")
        for g2 in even_gaps:
            if covers_all_residues_mod3(g1, g2):
                print("  F ", end="")
            else:
                print("  . ", end="")
        print()
    
    # Now verify against actual prime data
    print("\n" + "=" * 70)
    print(" VERIFICATION AGAINST PRIMES UP TO 10,000,000")
    print("=" * 70)
    
    primes = sieve(10_000_000)
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    pairs = [(gaps[i], gaps[i+1]) for i in range(len(gaps)-1)]
    pair_counts = Counter(pairs)
    
    # For each pair involving gaps <= 24, check prediction
    print(f"\n  {'Pair':<12} {'Predicted':>10} {'Observed':>10} {'Match?':>8}")
    print("  " + "-" * 45)
    
    correct = 0
    total = 0
    violations = []
    
    for g1 in even_gaps:
        for g2 in even_gaps:
            predicted_forbidden = covers_all_residues_mod3(g1, g2)
            count = pair_counts.get((g1, g2), 0)
            # "Forbidden" means count should be very small (only from p=3 vicinity)
            actually_rare = count < 10  # allowing a tiny handful
            
            if predicted_forbidden or count > 0:
                match = predicted_forbidden == actually_rare
                if predicted_forbidden or not match:
                    total += 1
                    if match:
                        correct += 1
                    else:
                        violations.append((g1, g2, predicted_forbidden, count))
                    
                    status = "✓" if match else "✗ VIOLATION"
                    pred_str = "FORBIDDEN" if predicted_forbidden else "allowed"
                    print(f"  ({g1:>2},{g2:>2})   {pred_str:>10} {count:>10}   {status}")
    
    print(f"\n  Predictions correct: {correct}/{total}")
    
    if violations:
        print(f"\n  VIOLATIONS (predicted ≠ observed):")
        for g1, g2, pred, count in violations:
            print(f"    ({g1},{g2}): predicted {'forbidden' if pred else 'allowed'}, "
                  f"observed {count}")
    
    # The deeper insight: what's the RULE?
    print("\n" + "=" * 70)
    print(" THE RULE")
    print("=" * 70)
    print("""
  A consecutive gap pair (g1, g2) is FORBIDDEN when:
  
    {0, g1, g1+g2} mod 3 = {0, 1, 2}
    
  Because this means the triple (p, p+g1, p+g1+g2) hits all residue
  classes mod 3, so one must be divisible by 3 and can't be prime (p>3).
  
  Equivalently: (g1, g2) is forbidden when
    g1 ≢ 0 (mod 3)  AND  g2 ≢ 0 (mod 3)  AND  g1 ≢ g2 (mod 3)
    
  This means:
    - After a gap ≡ 0 mod 3 (like 6, 12, 18): ANY next gap is allowed
    - After a gap ≡ 1 mod 3 (like 4, 10, 16): next gap must be ≡ 0 or 1 mod 3
    - After a gap ≡ 2 mod 3 (like 2, 8, 14):  next gap must be ≡ 0 or 2 mod 3
    
  Gap 6 dominates partly because it's a "universal connector" —
  it can follow AND precede any gap. It's the vowel of the gap alphabet.
""")

    # Extend: does this work for mod 5 too?
    print("=" * 70)
    print(" EXTENSION: MOD-5 CONSTRAINTS ON GAP TRIPLES")  
    print("=" * 70)
    
    # For mod 5, we need {0, g1, g1+g2} to NOT cover too many residues
    # Actually for mod 5, covering all 5 residues requires 5 points,
    # but we only have 3. So mod 5 can't outright forbid pairs.
    # But it CAN suppress them — reducing probability by a factor.
    
    # Let's check: for gap pairs that are mod-3 allowed, does mod-5
    # create additional suppression?
    print("\n  For mod 5, 3 points can't cover all 5 residues,")
    print("  so no pair is strictly forbidden. But we can check")
    print("  whether pairs avoiding more mod-5 residues are more common.\n")
    
    # Count how many distinct residues mod 5 the triple {0, g1, g1+g2} hits
    for g1 in [2, 4, 6]:
        for g2 in [2, 4, 6]:
            if covers_all_residues_mod3(g1, g2):
                continue
            res5 = len({0, g1 % 5, (g1 + g2) % 5})
            count = pair_counts.get((g1, g2), 0)
            print(f"  ({g1},{g2}): mod5 residues = {res5}, count = {count}")

if __name__ == "__main__":
    main()