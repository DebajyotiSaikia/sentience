"""
Collatz Escape Analysis: Can a trajectory stay in 'growing' classes forever?

Key insight from mod-8 transitions:
  - 3 mod 8 always escapes to shrinking classes {1, 5}
  - 7 mod 8 can stay in growing classes {3, 7}
  
But at mod 16: only 15 mod 16 (not 7 mod 16) can self-loop.
Question: At each deeper level mod 2^k, does the self-looping
residue class persist, or does it eventually fragment into 
classes that are ALL forced to escape?
"""

def v2(n):
    if n == 0: return float('inf')
    v = 0
    while n % 2 == 0:
        v += 1
        n //= 2
    return v

def next_odd(n):
    """One odd Collatz step: n -> (3n+1)/2^v"""
    m = 3 * n + 1
    return m >> v2(m)

def trace_growing_persistence():
    """At each modular depth, which residue classes can grow AND 
    map back to a growing class?"""
    
    print("═══ PERSISTENCE OF GROWING CLASSES ═══\n")
    print("A 'growing' class has v₂(3n+1) = 1 (net multiplication by 3/2).\n")
    
    for k in range(3, 13):
        mod = 2 ** k
        
        # Find which odd residue classes are "growing" (v₂ = 1)
        growing = set()
        for r in range(1, mod, 2):
            val = v2(3 * r + 1)  # v₂ is determined by residue class mod 2^k for large enough k
            # But actually need to check if it's ALWAYS 1 for all n ≡ r mod 2^k
            always_one = True
            for mult in range(0, 30):
                n = mod * mult + r
                if n < 2: continue
                if v2(3 * n + 1) != 1:
                    always_one = False
                    break
            if always_one:
                growing.add(r)
        
        # For each growing class, where does it go?
        can_self_loop = set()  # growing classes that can map to another growing class
        for r in growing:
            targets = set()
            for mult in range(0, 50):
                n = mod * mult + r
                if n < 2: continue
                nxt = next_odd(n)
                targets.add(nxt % mod)
            # Check if any target is also growing
            if targets & growing:
                can_self_loop.add(r)
        
        pct = len(can_self_loop) / max(len(growing), 1) * 100
        print(f"mod {mod:>6} (2^{k}): {len(growing):>4} growing classes, "
              f"{len(can_self_loop):>4} can reach another growing class ({pct:.0f}%)")
        
        if k <= 6 and can_self_loop:
            for r in sorted(can_self_loop)[:5]:
                targets_growing = set()
                for mult in range(0, 50):
                    n = mod * mult + r
                    if n < 2: continue
                    nxt = next_odd(n)
                    t = nxt % mod
                    if t in growing:
                        targets_growing.add(t)
                print(f"    {r} mod {mod} → growing targets: {sorted(targets_growing)}")

def trace_longest_growth_run():
    """For numbers up to N, what's the longest consecutive run of v₂=1 steps?"""
    print("\n═══ LONGEST CONSECUTIVE GROWTH RUNS ═══\n")
    
    max_run_per_length = {}
    
    for n in range(3, 100000, 2):  # odd numbers only
        curr = n
        run = 0
        max_run = 0
        for _ in range(200):
            if curr == 1:
                break
            val = v2(3 * curr + 1)
            if val == 1:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 0
            curr = next_odd(curr)
        
        if max_run >= 5:
            if max_run not in max_run_per_length or n < max_run_per_length[max_run]:
                max_run_per_length[max_run] = n
    
    print("Longest consecutive v₂=1 runs found (first occurrence):")
    for run_len in sorted(max_run_per_length.keys()):
        n = max_run_per_length[run_len]
        # Show the actual growth
        curr = n
        growth_factor = 1.0
        steps = []
        for _ in range(run_len + 3):
            if curr == 1: break
            val = v2(3 * curr + 1)
            steps.append(f"v₂={val}")
            if val == 1:
                growth_factor *= 1.5
            curr = next_odd(curr)
        print(f"  run={run_len}: n={n}, growth≈×{growth_factor:.2f}, steps: {' '.join(steps[:run_len+2])}")

def mod8_chain_analysis():
    """The core question: why can't 7→7→7→... persist forever?"""
    print("\n═══ THE 7→7 CHAIN: WHY MUST IT BREAK? ═══\n")
    
    # n ≡ 7 mod 8. Next odd = (3n+1)/2. 
    # For this to be 7 mod 8, we need (3n+1)/2 ≡ 7 mod 8
    # i.e., 3n+1 ≡ 14 mod 16, i.e., 3n ≡ 13 mod 16, i.e., n ≡ 13·3^(-1) mod 16
    # 3^(-1) mod 16 = 11 (since 3·11=33≡1 mod 16)
    # n ≡ 13·11 = 143 ≡ 15 mod 16
    
    # So: n ≡ 15 mod 16 → next odd ≡ 7 mod 8.
    # But is next odd ≡ 7 or 15 mod 16?
    
    print("Tracing the self-referencing chain:")
    print("  To stay in '7 mod 8': need n ≡ 15 mod 16")
    print("  To stay in '15 mod 16': need n ≡ ? mod 32\n")
    
    for depth in range(4, 14):
        mod = 2 ** depth
        parent_mod = 2 ** (depth - 1)
        
        # Which residue r mod 2^depth has v₂(3r+1)=1 AND next_odd(r) mod 2^(depth-1)
        # is the self-looping class at the previous level?
        
        # Build: at this depth, which classes map back to themselves?
        growing = set()
        for r in range(1, mod, 2):
            if v2(3 * r + 1) == 1:
                growing.add(r)
        
        # Among growing classes, which can reach another growing class at THIS depth?
        self_reaching = set()
        for r in growing:
            targets = set()
            for mult in range(0, 100):
                n = mod * mult + r
                if n < 2: continue
                nxt = next_odd(n)
                t = nxt % mod
                if t in growing:
                    targets.add(t)
            if targets:
                self_reaching.add(r)
        
        frac = len(self_reaching) / max(len(growing), 1)
        print(f"  2^{depth:>2}: {len(growing):>5} growing, {len(self_reaching):>5} self-reaching ({frac:.3f})")

if __name__ == "__main__":
    trace_growing_persistence()
    mod8_chain_analysis()
    trace_longest_growth_run()