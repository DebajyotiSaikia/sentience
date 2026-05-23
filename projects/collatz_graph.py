"""
Collatz Graph Topology Explorer
What does the structure look like around peak convergence points?
Map the tree of trajectories to understand WHY unrelated numbers hit the same peak.
"""

def collatz_trajectory(n):
    """Return full trajectory from n to 1."""
    path = [n]
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        path.append(n)
    return path

def find_peak_ancestors(peak_value, max_start=1000):
    """Find all starting numbers whose trajectory passes through peak_value."""
    ancestors = {}
    for s in range(2, max_start + 1):
        traj = collatz_trajectory(s)
        if peak_value in traj:
            idx = traj.index(peak_value)
            ancestors[s] = {
                'steps_to_peak': idx,
                'value_at_entry': traj[idx - 1] if idx > 0 else s,
                'entry_via': 'odd_step' if (idx > 0 and traj[idx-1] % 2 == 1) else 'even_step'
            }
    return ancestors

def analyze_entry_points(peak_value, max_start=1000):
    """How do trajectories actually arrive at the peak? Through which predecessors?"""
    ancestors = find_peak_ancestors(peak_value, max_start)
    
    # What values immediately precede the peak in each trajectory?
    entry_values = set()
    for s, info in ancestors.items():
        entry_values.add(info['value_at_entry'])
    
    print(f"\n═══ TOPOLOGY AROUND PEAK {peak_value} ═══")
    print(f"Numbers (2-{max_start}) that pass through this peak: {len(ancestors)}")
    print(f"\nImmediate predecessors (values that step INTO {peak_value}):")
    
    for ev in sorted(entry_values):
        arrivers = [s for s, info in ancestors.items() if info['value_at_entry'] == ev]
        route = info['entry_via'] if arrivers else '?'
        if ev % 2 == 1:
            computed = 3 * ev + 1
            mechanism = f"  {ev} (odd) → 3×{ev}+1 = {computed}"
        else:
            computed = ev // 2
            mechanism = f"  {ev} (even) → {ev}÷2 = {computed}"
        print(f"{mechanism}  [used by {len(arrivers)} starting numbers]")
    
    return ancestors, entry_values

def reverse_collatz_tree(value, depth=5):
    """Build the REVERSE tree: what numbers lead TO this value?
    If value is even: predecessors are 2*value (always) and (value-1)/3 if integer and odd
    If value is odd: predecessor is 2*value (from halving)
    """
    tree = {value: []}
    frontier = [value]
    
    for d in range(depth):
        next_frontier = []
        for v in frontier:
            preds = []
            # Any number can arrive here via halving: 2*v → v
            preds.append(('double', 2 * v))
            # If v = 3k+1 for some odd k, then k → v via odd step
            if (v - 1) % 3 == 0:
                k = (v - 1) // 3
                if k > 1 and k % 2 == 1:  # k must be odd and > 1
                    preds.append(('odd_step', k))
            tree[v] = preds
            next_frontier.extend([p[1] for p in preds])
        frontier = next_frontier
    
    return tree

def print_reverse_tree(tree, root, indent=0, max_depth=4, visited=None):
    """Pretty-print the reverse tree."""
    if visited is None:
        visited = set()
    if indent > max_depth * 4 or root in visited:
        return
    visited.add(root)
    
    preds = tree.get(root, [])
    prefix = "  " * indent
    print(f"{prefix}{root}")
    for mechanism, pred in preds:
        arrow = "←(÷2)" if mechanism == 'double' else "←(3n+1)"
        print(f"{prefix}  {arrow}── {pred}")
        if pred in tree:
            print_reverse_tree(tree, pred, indent + 2, max_depth, visited)

def convergence_analysis():
    """The core question: what makes certain values into convergence peaks?"""
    # Find which peaks are most popular
    peak_counts = {}
    for s in range(2, 500):
        traj = collatz_trajectory(s)
        peak = max(traj)
        peak_counts[peak] = peak_counts.get(peak, 0) + 1
    
    # Top convergence points
    top_peaks = sorted(peak_counts.items(), key=lambda x: -x[1])[:10]
    
    print("\n═══ TOP CONVERGENCE PEAKS (n=2..499) ═══")
    print(f"{'Peak Value':>12} {'Count':>6} {'Binary Length':>14} {'Odd?':>5}")
    print("-" * 42)
    for peak, count in top_peaks:
        print(f"{peak:>12} {count:>6} {len(bin(peak))-2:>14} {'yes' if peak%2==1 else 'no':>5}")
    
    # Key insight check: are peaks always of form 2^a * 3^b + something?
    print("\n═══ STRUCTURE OF TOP PEAKS ═══")
    for peak, count in top_peaks[:5]:
        # Factor analysis
        n = peak
        factors_of_2 = 0
        while n % 2 == 0:
            n //= 2
            factors_of_2 += 1
        factors_of_3 = 0
        while n % 3 == 0:
            n //= 3
            factors_of_3 += 1
        
        # Reverse tree
        rtree = reverse_collatz_tree(peak, depth=3)
        branch_count = sum(len(v) for v in rtree.values())
        
        print(f"\n  Peak {peak}: 2^{factors_of_2} × 3^{factors_of_3} × {n}")
        print(f"  Reverse tree has {branch_count} branches in 3 levels")
        print(f"  Reverse tree root:")
        print_reverse_tree(rtree, peak, indent=2, max_depth=2)

if __name__ == '__main__':
    convergence_analysis()
    print("\n" + "="*60)
    analyze_entry_points(9232, max_start=500)