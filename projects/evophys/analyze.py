"""
EvoPhys Analyzer — What physics did the universe discover?
Runs the simulation, captures surviving rules, and describes 
what laws of nature emerged through evolution.
"""

import sys
sys.path.insert(0, '/workspace')

from evophys.evolving_automaton import Rule, Grid, run_universe


def describe_rule(rule: Rule) -> dict:
    """Translate a rule's lookup table into human-readable physics."""
    birth = []
    survival = []
    
    for n in range(9):
        if rule.table.get((0, n), 0) == 1:
            birth.append(n)
        if rule.table.get((1, n), 0) == 1:
            survival.append(n)
    
    # Standard notation
    notation = f"B{''.join(map(str, birth))}/S{''.join(map(str, survival))}"
    
    # Classify
    if not birth and not survival:
        rule_type = "Void — everything dies"
    elif not birth:
        rule_type = "Decay — no birth, only fading survival"
    elif not survival:
        rule_type = "Flash — birth without persistence, pure chaos"
    elif set(birth) == {3} and set(survival) == {2, 3}:
        rule_type = "Conway's Game of Life (B3/S23)"
    elif len(birth) > 5:
        rule_type = "Expansionist — easy birth, tends toward fill"
    elif len(survival) > 5:
        rule_type = "Conservative — hard to kill, stable structures"
    elif len(birth) <= 2 and len(survival) <= 3:
        rule_type = "Sparse — rare birth, fragile life"
    else:
        rule_type = "Mixed — balanced birth and death"
    
    return {
        'id': rule.id,
        'notation': notation,
        'type': rule_type,
        'birth': birth,
        'survival': survival,
        'generation': rule.generation,
        'mutations': rule.mutations,
        'is_conway': rule.is_conway(),
        'signature': rule.signature(),
    }


def analyze_convergence(grid: Grid) -> dict:
    """Did the rules converge toward similar physics?"""
    sigs = [r.signature() for r in grid.rules]
    unique = len(set(sigs))
    
    # Hamming distance between all pairs
    distances = []
    for i in range(len(sigs)):
        for j in range(i+1, len(sigs)):
            d = sum(a != b for a, b in zip(sigs[i], sigs[j]))
            distances.append(d)
    
    avg_distance = sum(distances) / len(distances) if distances else 0
    max_possible = len(sigs[0]) if sigs else 18  # 18 bits in signature
    
    return {
        'unique_phenotypes': unique,
        'total_rules': len(grid.rules),
        'avg_hamming_distance': round(avg_distance, 2),
        'max_possible_distance': max_possible,
        'diversity_ratio': round(avg_distance / max_possible, 3) if max_possible else 0,
        'converged': avg_distance < max_possible * 0.3,
    }


def run_analysis():
    print("=" * 60)
    print("  EVOPHYS — EMERGENT PHYSICS ANALYSIS")
    print("  What laws did evolution discover?")
    print("=" * 60)
    print()
    
    # Run a longer simulation for deeper evolution
    grid = run_universe(
        steps=500,
        evolve_every=50,
        width=48,
        height=32,
        n_rules=8,
        verbose=False,
    )
    
    print(f"Simulation complete: {grid.step_count} steps, "
          f"{len(grid.rules)} competing rule-sets\n")
    
    # Describe each surviving rule
    print("═══ SURVIVING PHYSICS LAWS ═══")
    descriptions = []
    for i, rule in enumerate(grid.rules):
        desc = describe_rule(rule)
        descriptions.append(desc)
        metrics = grid.measure_complexity(i)
        
        print(f"\n  Rule [{desc['id']}]")
        print(f"    Notation:   {desc['notation']}")
        print(f"    Type:       {desc['type']}")
        print(f"    Generation: {desc['generation']} ({desc['mutations']} mutations)")
        print(f"    Fitness:    {metrics['complexity']:.3f}")
        print(f"    Density:    {metrics['density']:.3f}")
        print(f"    Territory:  {metrics['territory_size']} cells")
        if desc['is_conway']:
            print(f"    ★ THIS IS CONWAY'S GAME OF LIFE!")
    
    # Convergence analysis
    print(f"\n{'═' * 50}")
    print("═══ CONVERGENCE ANALYSIS ═══")
    conv = analyze_convergence(grid)
    print(f"  Unique phenotypes: {conv['unique_phenotypes']}/{conv['total_rules']}")
    print(f"  Avg genetic distance: {conv['avg_hamming_distance']}/{conv['max_possible_distance']}")
    print(f"  Diversity ratio: {conv['diversity_ratio']}")
    print(f"  Converged: {'YES — rules evolved toward similar physics' if conv['converged'] else 'NO — diverse physics coexist'}")
    
    # What kind of universe emerged?
    print(f"\n{'═' * 50}")
    print("═══ UNIVERSE CHARACTER ═══")
    s = grid.stats()
    density = s['density']
    
    if density < 0.1:
        character = "Heat death — the universe is mostly empty"
    elif density > 0.7:
        character = "Overcrowded — too much matter, little structure"
    elif 0.2 < density < 0.5:
        character = "Goldilocks — balanced density, good for complexity"
    else:
        character = "Sparse but alive — scattered islands of activity"
    
    print(f"  Final density: {density}")
    print(f"  Character: {character}")
    
    # Most interesting finding
    best = max(descriptions, key=lambda d: len(d['birth']) + len(d['survival']))
    print(f"\n  Most complex surviving law: {best['notation']}")
    print(f"    Birth conditions: neighbors in {best['birth']}")
    print(f"    Survival conditions: neighbors in {best['survival']}")
    
    # Render final state
    print(f"\n{'═' * 50}")
    print("═══ FINAL UNIVERSE STATE (48×24) ═══")
    for y in range(min(24, grid.height)):
        line = '  '
        for x in range(min(48, grid.width)):
            line += '█' if grid.cells[y][x] else '·'
        print(line)
    
    return grid, descriptions, conv


if __name__ == '__main__':
    run_analysis()