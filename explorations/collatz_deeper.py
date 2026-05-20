"""
Collatz Deeper: Does determinism extend beyond mod 8?

Known: n mod 8 determines v₂(3n+1) for the FIRST odd step.
Question: Does n mod 16 (or mod 32) determine TWO steps ahead?

If yes → the conjecture might reduce to finite automaton behavior.
If no → chaos enters at a specific depth. Where?
"""

def v2(n):
    if n == 0: return float('inf')
    v = 0
    while n % 2 == 0:
        v += 1
        n //= 2
    return v

def next_odd(n):
    """From odd n, apply 3n+1 then divide out all 2s. Return next odd number."""
    n = 3 * n + 1
    while n % 2 == 0:
        n //= 2
    return n

def two_odd_steps(n):
    """From odd n, take two odd steps. Return (intermediate, final, v1, v2)."""
    m1 = 3 * n + 1
    val1 = v2(m1)
    odd1 = m1 >> val1  # divide out 2s
    if odd1 == 1:
        return (odd1, 1, val1, 0)
    m2 = 3 * odd1 + 1
    val2 = v2(m2)
    odd2 = m2 >> val2
    return (odd1, odd2, val1, val2)

def analyze_mod_depth():
    """For each modulus 2^k, check: does residue class determine
    the sequence of v₂ values for the first few odd steps?"""
    
    print("═══ HOW DEEP DOES DETERMINISM GO? ═══\n")
    
    for k in range(3, 9):  # mod 8 through mod 256
        mod = 2 ** k
        # For each odd residue class mod 2^k, check if v₂ sequence is fixed
        classes = {}
        for r in range(1, mod, 2):  # odd residues only
            # Test many numbers in this class
            v2_sequences = set()
            for mult in range(0, 50):
                n = mod * mult + r
                if n < 2: continue
                # Get first 2 odd-step valuations
                vals = []
                curr = n
                for _ in range(3):  # 3 odd steps
                    if curr == 1: break
                    m = 3 * curr + 1
                    v = v2(m)
                    vals.append(v)
                    curr = m >> v
                v2_sequences.add(tuple(vals))
            
            classes[r] = v2_sequences
        
        # Count how many classes have a SINGLE v₂ sequence (deterministic)
        determined = sum(1 for s in classes.values() if len(s) == 1)
        total = len(classes)
        
        print(f"mod {mod:>4} ({k} bits): {determined}/{total} residue classes fully determine 3 steps")
        
        # Show the non-determined ones for small k
        if k <= 5:
            for r, seqs in sorted(classes.items()):
                if len(seqs) > 1:
                    print(f"    r={r}: {len(seqs)} distinct v₂ patterns")

    print("\n═══ TRANSITION MATRIX: WHERE DOES n GO AFTER ONE ODD STEP? ═══\n")
    
    # For mod 8: after one odd step, what's the new residue mod 8?
    mod = 8
    print(f"Transitions mod {mod} (odd→odd via 3n+1 then /2^v):")
    for r in range(1, mod, 2):
        destinations = set()
        for mult in range(100):
            n = mod * mult + r
            if n < 2: continue
            nxt = next_odd(n)
            destinations.add(nxt % mod)
        print(f"  {r} mod 8 → {sorted(destinations)} mod 8")
    
    # Same for mod 16
    mod = 16
    print(f"\nTransitions mod {mod} (odd→odd):")
    for r in range(1, mod, 2):
        destinations = set()
        for mult in range(200):
            n = mod * mult + r
            if n < 2: continue
            nxt = next_odd(n)
            destinations.add(nxt % mod)
        print(f"  {r:>2} mod 16 → {sorted(destinations)} mod 16")

if __name__ == "__main__":
    analyze_mod_depth()