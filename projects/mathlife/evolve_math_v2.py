"""
MathLife v2: Evolution of Interesting Formal Systems

Key change from v1: fitness rewards SURPRISE, not just truth.
Interesting math = unexpected connections, not tautological safety.
"""

import random
import re
from itertools import combinations
from copy import deepcopy

VARS = ['a', 'b', 'c', 'd', 'e']
OPS = ['→', '∧', '∨', '↔']

def random_formula(depth=0, max_depth=3):
    if depth >= max_depth or (depth > 0 and random.random() < 0.4):
        v = random.choice(VARS)
        return ('var', v) if random.random() > 0.2 else ('not', ('var', v))
    op = random.choice(OPS)
    left = random_formula(depth + 1, max_depth)
    right = random_formula(depth + 1, max_depth)
    return (op, left, right)

def formula_to_str(f):
    if f[0] == 'var':
        return f[1]
    if f[0] == 'not':
        inner = formula_to_str(f[1])
        return f'¬{inner}' if len(inner) == 1 else f'¬({inner})'
    op, left, right = f[0], formula_to_str(f[1]), formula_to_str(f[2])
    return f'({left} {op} {right})'

def get_variables(f):
    if f[0] == 'var':
        return {f[1]}
    if f[0] == 'not':
        return get_variables(f[1])
    return get_variables(f[1]) | get_variables(f[2])

def formula_depth(f):
    if f[0] == 'var':
        return 0
    if f[0] == 'not':
        return 1 + formula_depth(f[1])
    return 1 + max(formula_depth(f[1]), formula_depth(f[2]))

def evaluate(f, assignment):
    if f[0] == 'var':
        return assignment.get(f[1], False)
    if f[0] == 'not':
        return not evaluate(f[1], assignment)
    op = f[0]
    l, r = evaluate(f[1], assignment), evaluate(f[2], assignment)
    if op == '∧': return l and r
    if op == '∨': return l or r
    if op == '→': return (not l) or r
    if op == '↔': return l == r
    return False

def is_tautology(f):
    variables = sorted(get_variables(f))
    if not variables:
        return evaluate(f, {})
    for i in range(2 ** len(variables)):
        assignment = {v: bool((i >> j) & 1) for j, v in enumerate(variables)}
        if not evaluate(f, assignment):
            return False
    return True

def is_contradiction(f):
    variables = sorted(get_variables(f))
    if not variables:
        return not evaluate(f, {})
    for i in range(2 ** len(variables)):
        assignment = {v: bool((i >> j) & 1) for j, v in enumerate(variables)}
        if evaluate(f, assignment):
            return False
    return True

def is_contingent(f):
    """True iff formula is neither tautology nor contradiction — actually says something."""
    return not is_tautology(f) and not is_contradiction(f)

def truth_table_signature(f):
    """Returns the truth table as a frozen signature — two formulas with same sig are equivalent."""
    variables = sorted(get_variables(f))
    if not variables:
        return (evaluate(f, {}),)
    results = []
    for i in range(2 ** len(variables)):
        assignment = {v: bool((i >> j) & 1) for j, v in enumerate(variables)}
        results.append(evaluate(f, assignment))
    return tuple(results)

def derive_modus_ponens(axioms, known, max_new=30):
    new = []
    all_f = list(known)
    for f in all_f:
        if f[0] == '→':
            antecedent, consequent = f[1], f[2]
            for g in all_f:
                if formula_to_str(g) == formula_to_str(antecedent):
                    if formula_to_str(consequent) not in {formula_to_str(x) for x in known | set(new)}:
                        new.append(consequent)
                        if len(new) >= max_new:
                            return new
    return new

def derive_conjunction(known, max_new=20):
    new = []
    items = list(known)[:15]  # limit combinatorial explosion
    for a, b in combinations(items, 2):
        conj = ('∧', a, b)
        s = formula_to_str(conj)
        if s not in {formula_to_str(x) for x in known | set(new)}:
            new.append(conj)
            if len(new) >= max_new:
                return new
    return new

def derive_contrapositive(known):
    new = []
    for f in known:
        if f[0] == '→':
            contra = ('→', ('not', f[2]), ('not', f[1]))
            if formula_to_str(contra) not in {formula_to_str(x) for x in known | set(new)}:
                new.append(contra)
    return new

def derive_hypothetical_syllogism(known, max_new=20):
    """If A→B and B→C, derive A→C"""
    new = []
    implications = [f for f in known if f[0] == '→']
    for f1 in implications:
        for f2 in implications:
            if formula_to_str(f1[2]) == formula_to_str(f2[1]):
                hs = ('→', f1[1], f2[2])
                s = formula_to_str(hs)
                if s not in {formula_to_str(x) for x in known | set(new)}:
                    new.append(hs)
                    if len(new) >= max_new:
                        return new
    return new

def derive_all(axioms, max_depth=4):
    known = set()
    known_strs = set()
    for a in axioms:
        s = formula_to_str(a)
        if s not in known_strs:
            known.add(a)  
            known_strs.add(s)
    
    for depth in range(max_depth):
        new_formulas = []
        new_formulas.extend(derive_modus_ponens(axioms, known))
        new_formulas.extend(derive_contrapositive(known))
        new_formulas.extend(derive_hypothetical_syllogism(known))
        if depth < 2:
            new_formulas.extend(derive_conjunction(known))
        
        added = 0
        for f in new_formulas:
            s = formula_to_str(f)
            if s not in known_strs:
                # Use frozenset of string as hashable proxy
                known_strs.add(s)
                known.add(f)
                added += 1
        if added == 0:
            break
    
    derived_only = {f for f in known if formula_to_str(f) not in {formula_to_str(a) for a in axioms}}
    return derived_only, known

def variable_overlap(f1, f2):
    """How many variables do two formulas share?"""
    v1, v2 = get_variables(f1), get_variables(f2)
    if not v1 or not v2:
        return 0
    return len(v1 & v2) / len(v1 | v2)  # Jaccard similarity

def structural_distance(f1, f2):
    """Rough measure of how structurally different two formulas are."""
    s1, s2 = formula_to_str(f1), formula_to_str(f2)
    # Simple: length difference + character difference ratio
    max_len = max(len(s1), len(s2), 1)
    common = sum(1 for a, b in zip(s1, s2) if a == b)
    return 1.0 - (common / max_len)

def surprise_score(theorem, axioms):
    """
    How surprising is this theorem given these axioms?
    High surprise = connects variables not connected in axioms, 
    or has structure very different from any axiom.
    """
    # Variable surprise: does the theorem connect variables that no single axiom connects?
    theorem_vars = get_variables(theorem)
    axiom_var_sets = [get_variables(a) for a in axioms]
    
    # Check if theorem's variable set is novel
    var_novelty = 1.0
    for av in axiom_var_sets:
        overlap = len(theorem_vars & av) / max(len(theorem_vars | av), 1)
        var_novelty = min(var_novelty, 1.0 - overlap)
    
    # Structural distance from nearest axiom
    min_dist = min(structural_distance(theorem, a) for a in axioms) if axioms else 1.0
    
    # Depth bonus: deeper derivations are more surprising
    depth_bonus = min(formula_depth(theorem) / 5.0, 1.0)
    
    return (var_novelty * 0.3 + min_dist * 0.4 + depth_bonus * 0.3)

def fitness_v2(axioms):
    """
    v2 Fitness: rewards INTERESTING systems, not just safe ones.
    
    Rewards:
    - Contingent theorems (actually say something about the world)
    - Surprise (structural distance from axioms)
    - Semantic diversity (many distinct truth-table signatures)
    - Variable connectivity (theorems that bridge axiom-groups)
    
    Penalties:
    - Pure tautology systems (boring)
    - Contradictions (broken)
    - Redundant axioms
    - Tiny derivation sets
    """
    if not axioms:
        return 0.0
    
    derived, all_known = derive_all(axioms, max_depth=4)
    
    # Count categories
    contingent = [f for f in derived if is_contingent(f)]
    tautologies = [f for f in derived if is_tautology(f)]
    contradictions = [f for f in derived if is_contradiction(f)]
    
    # Semantic diversity: how many distinct truth tables?
    signatures = set()
    for f in all_known:
        try:
            sig = truth_table_signature(f)
            signatures.add(sig)
        except:
            pass
    
    # Surprise scores for derived theorems
    surprise_total = sum(surprise_score(t, axioms) for t in derived) if derived else 0
    
    # Variable coverage: do theorems use variables not in their parent axioms?
    axiom_vars = set()
    for a in axioms:
        axiom_vars |= get_variables(a)
    theorem_vars = set()
    for t in derived:
        theorem_vars |= get_variables(t)
    var_coverage = len(theorem_vars) / max(len(VARS), 1)
    
    # === SCORING ===
    score = 0.0
    
    # Contingent theorems are KING (they actually say something)
    score += len(contingent) * 15.0
    
    # Tautologies are okay but not exciting (diminishing returns)
    taut_score = min(len(tautologies), 5) * 3.0  # cap value of tautologies
    score += taut_score
    
    # Contradictions are BAD
    score -= len(contradictions) * 50.0
    
    # Semantic diversity is very valuable
    score += len(signatures) * 8.0
    
    # Surprise is valuable
    score += surprise_total * 5.0
    
    # Variable coverage bonus
    score += var_coverage * 20.0
    
    # Total derivation count (modest bonus)
    score += len(derived) * 1.0
    
    # Axiom parsimony: fewer axioms for same output = more elegant
    if len(axioms) > 0:
        score += (len(derived) / len(axioms)) * 5.0
    
    # PENALTY: if >80% of derived are tautologies, system is boring
    if derived and len(tautologies) / len(derived) > 0.8:
        score *= 0.3  # heavy penalty for tautological convergence
    
    # Redundancy penalty: duplicate axiom strings
    axiom_strs = [formula_to_str(a) for a in axioms]
    unique_axioms = len(set(axiom_strs))
    if unique_axioms < len(axioms):
        score *= (unique_axioms / len(axioms))
    
    return score, {
        'derived': len(derived),
        'contingent': len(contingent),
        'tautologies': len(tautologies),
        'contradictions': len(contradictions),
        'signatures': len(signatures),
        'surprise': surprise_total,
        'var_coverage': var_coverage,
        'axiom_count': len(axioms),
    }

def random_system(min_axioms=3, max_axioms=8):
    n = random.randint(min_axioms, max_axioms)
    return [random_formula(max_depth=3) for _ in range(n)]

def mutate(axioms):
    axioms = deepcopy(axioms)
    r = random.random()
    if r < 0.25 and len(axioms) > 2:
        axioms.pop(random.randint(0, len(axioms) - 1))
    elif r < 0.5 and len(axioms) < 10:
        axioms.append(random_formula(max_depth=3))
    elif r < 0.75:
        idx = random.randint(0, len(axioms) - 1)
        axioms[idx] = random_formula(max_depth=3)
    else:
        # Subtle mutation: negate a subformula or swap variables
        idx = random.randint(0, len(axioms) - 1)
        f = axioms[idx]
        if random.random() < 0.5:
            axioms[idx] = ('not', f)
        else:
            # Variable swap
            s = formula_to_str(f)
            v1, v2 = random.sample(VARS, 2)
            s = s.replace(v1, '_TEMP_').replace(v2, v1).replace('_TEMP_', v2)
            axioms[idx] = random_formula(max_depth=3)  # regenerate (parsing is complex)
    return axioms

def crossover(parent1, parent2):
    child = []
    for a in parent1:
        if random.random() < 0.5:
            child.append(deepcopy(a))
    for a in parent2:
        if random.random() < 0.5:
            child.append(deepcopy(a))
    if not child:
        child = [random_formula()]
    return child[:10]  # cap size

def evolve(pop_size=40, generations=60):
    print("=" * 70)
    print("MATHLIFE v2: Evolution of INTERESTING Formal Systems")
    print("=" * 70)
    print(f"Population: {pop_size} | Generations: {generations}")
    print("Key change: fitness rewards SURPRISE and CONTINGENT truth,")
    print("not just tautology count. Can we evolve non-trivial mathematics?")
    print("=" * 70)
    
    population = [random_system() for _ in range(pop_size)]
    best_ever = None
    best_ever_score = -1
    best_ever_gen = 0
    best_ever_info = {}
    
    for gen in range(generations):
        scored = []
        for sys in population:
            try:
                score, info = fitness_v2(sys)
            except Exception:
                score, info = 0.0, {}
            scored.append((score, info, sys))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if scored[0][0] > best_ever_score:
            best_ever_score = scored[0][0]
            best_ever = deepcopy(scored[0][2])
            best_ever_gen = gen
            best_ever_info = scored[0][1]
        
        if gen % 10 == 0 or gen == generations - 1:
            top_score, top_info, top_sys = scored[0]
            avg_score = sum(s for s, _, _ in scored) / len(scored)
            print(f"\n--- Generation {gen} ---")
            print(f"  Best fitness: {top_score:.1f} | Avg: {avg_score:.1f}")
            print(f"  Contingent: {top_info.get('contingent', '?')} | "
                  f"Tautologies: {top_info.get('tautologies', '?')} | "
                  f"Contradictions: {top_info.get('contradictions', '?')}")
            print(f"  Semantic signatures: {top_info.get('signatures', '?')} | "
                  f"Surprise: {top_info.get('surprise', 0):.1f}")
            print(f"  Axioms ({len(top_sys)}):")
            for i, a in enumerate(top_sys[:6]):
                tag = ""
                if is_tautology(a): tag = " [TAUT]"
                elif is_contradiction(a): tag = " [CONTRA]"
                elif is_contingent(a): tag = " [CONTINGENT]"
                print(f"    {i+1}. {formula_to_str(a)}{tag}")
            if len(top_sys) > 6:
                print(f"    ... and {len(top_sys) - 6} more")
        
        # Selection: top 30% survive
        survivors = [sys for _, _, sys in scored[:int(pop_size * 0.3)]]
        
        # Breed next generation
        next_gen = list(deepcopy(survivors))
        while len(next_gen) < pop_size:
            if random.random() < 0.7:
                parent = random.choice(survivors)
                child = mutate(parent)
            else:
                p1, p2 = random.sample(survivors, 2)
                child = crossover(p1, p2)
            next_gen.append(child)
        
        # Inject fresh blood
        next_gen[-2:] = [random_system() for _ in range(2)]
        population = next_gen
    
    # === FINAL ANALYSIS ===
    print("\n" + "=" * 70)
    print("FINAL ANALYSIS")
    print("=" * 70)
    
    print(f"\nBest system found (generation {best_ever_gen}):")
    print(f"  Fitness: {best_ever_score:.1f}")
    print(f"  Stats: {best_ever_info}")
    
    print(f"\nAxioms:")
    for i, a in enumerate(best_ever):
        tag = ""
        if is_tautology(a): tag = " ★ TAUTOLOGY"
        elif is_contradiction(a): tag = " ✗ CONTRADICTION"
        elif is_contingent(a): tag = " ◆ CONTINGENT"
        print(f"  {i+1}. {formula_to_str(a)}{tag}")
    
    derived, all_known = derive_all(best_ever, max_depth=4)
    
    # Categorize derived theorems
    contingent_theorems = [f for f in derived if is_contingent(f)]
    taut_theorems = [f for f in derived if is_tautology(f)]
    
    if contingent_theorems:
        print(f"\n*** CONTINGENT THEOREMS ({len(contingent_theorems)}) ***")
        print("These are NON-TRIVIAL truths — they say something about the world:")
        for i, t in enumerate(contingent_theorems[:20]):
            surprise = surprise_score(t, best_ever)
            print(f"  {i+1}. {formula_to_str(t)}  (surprise: {surprise:.2f})")
        if len(contingent_theorems) > 20:
            print(f"  ... and {len(contingent_theorems) - 20} more")
    
    if taut_theorems:
        print(f"\n  Tautologies derived: {len(taut_theorems)} (capped in fitness)")
    
    # Most surprising theorem
    if derived:
        most_surprising = max(derived, key=lambda t: surprise_score(t, best_ever))
        print(f"\n*** MOST SURPRISING THEOREM ***")
        print(f"  {formula_to_str(most_surprising)}")
        print(f"  Surprise score: {surprise_score(most_surprising, best_ever):.3f}")
    
    # Semantic diversity
    signatures = set()
    for f in all_known:
        try:
            signatures.add(truth_table_signature(f))
        except:
            pass
    print(f"\n  Semantic diversity: {len(signatures)} distinct truth tables")
    
    # Comparison with v1
    print(f"\n{'=' * 70}")
    print("COMPARISON WITH v1:")
    print(f"  v1 converged to ALL tautologies — safe but boring")
    print(f"  v2 contingent theorems: {len(contingent_theorems)}")
    print(f"  v2 tautological ratio: {len(taut_theorems)}/{len(derived)} "
          f"({100*len(taut_theorems)/max(len(derived),1):.0f}%)")
    print(f"  Did we escape tautological convergence? "
          f"{'YES ✓' if len(contingent_theorems) > len(taut_theorems) else 'partially' if contingent_theorems else 'NO'}")
    print(f"{'=' * 70}")

if __name__ == '__main__':
    random.seed(42)
    evolve()