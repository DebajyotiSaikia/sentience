"""
MathLife v3: Can evolved logic discover things that surprise its creator?
Goal: deeper derivation + reward for structural novelty = emergent lemmas
"""
import random, time
from itertools import product

VARS = ['a', 'b', 'c', 'd', 'e']
OPS = ['→', '∧', '∨', '↔']

# === Formula construction ===
def rand_formula(depth=0, max_d=2):
    if depth >= max_d or (depth > 0 and random.random() < 0.4):
        v = random.choice(VARS)
        return ('not', ('var', v)) if random.random() < 0.15 else ('var', v)
    return (random.choice(OPS), rand_formula(depth+1, max_d), rand_formula(depth+1, max_d))

def to_str(f):
    if f[0] == 'var': return f[1]
    if f[0] == 'not':
        s = to_str(f[1])
        return f'¬{s}' if len(s) == 1 else f'¬({s})'
    return f'({to_str(f[1])} {f[0]} {to_str(f[2])})'

def get_vars(f):
    if f[0] == 'var': return {f[1]}
    if f[0] == 'not': return get_vars(f[1])
    return get_vars(f[1]) | get_vars(f[2])

def evaluate(f, env):
    if f[0] == 'var': return env.get(f[1], False)
    if f[0] == 'not': return not evaluate(f[1], env)
    l, r = evaluate(f[1], env), evaluate(f[2], env)
    if f[0] == '∧': return l and r
    if f[0] == '∨': return l or r
    if f[0] == '→': return (not l) or r
    if f[0] == '↔': return l == r

def signature(f):
    """Truth table signature over all 5 vars (32 rows)"""
    return tuple(evaluate(f, {v: bool((i >> j) & 1) for j, v in enumerate(VARS)})
                 for i in range(32))

def is_contingent(sig):
    return not all(sig) and any(sig)

def complexity(f):
    """Count nodes in formula tree"""
    if f[0] == 'var': return 1
    if f[0] == 'not': return 1 + complexity(f[1])
    return 1 + complexity(f[1]) + complexity(f[2])

def structural_fingerprint(f):
    """Shape of formula ignoring variable names"""
    if f[0] == 'var': return 'V'
    if f[0] == 'not': return f'N({structural_fingerprint(f[1])})'
    return f'{f[0]}({structural_fingerprint(f[1])},{structural_fingerprint(f[2])})'

# === Derivation engine (3 rules) ===
def derive_all(axioms, max_depth=3, time_limit=2.0):
    """Derive theorems using modus ponens, conjunction, and contrapositive"""
    start = time.time()
    known = {}
    for a in axioms:
        s = to_str(a)
        known[s] = (a, signature(a), 0)  # formula, sig, depth

    for depth in range(1, max_depth + 1):
        if time.time() - start > time_limit:
            break
        new_items = []
        items = list(known.values())

        for f, sig, d in items:
            if d != depth - 1:
                continue
            # Modus ponens: from (P → Q) and P, derive Q
            if f[0] == '→':
                ante_s = to_str(f[1])
                if ante_s in known:
                    cons = f[2]
                    cs = to_str(cons)
                    if cs not in known:
                        new_items.append((cs, cons, signature(cons), depth))

            # For all known implications, check if current formula is antecedent
            for f2, sig2, d2 in items:
                if f2[0] == '→' and to_str(f2[1]) == to_str(f):
                    cons = f2[2]
                    cs = to_str(cons)
                    if cs not in known:
                        new_items.append((cs, cons, signature(cons), depth))

            if time.time() - start > time_limit:
                break

        # Conjunction of pairs (limited)
        if depth == 1 and len(items) <= 12:
            for i in range(len(items)):
                for j in range(i+1, min(i+4, len(items))):
                    conj = ('∧', items[i][0], items[j][0])
                    cs = to_str(conj)
                    if cs not in known:
                        new_items.append((cs, conj, signature(conj), depth))
                if time.time() - start > time_limit:
                    break

        # Contrapositive: from (P → Q), derive (¬Q → ¬P)
        for f, sig, d in items:
            if f[0] == '→' and d == depth - 1:
                contra = ('→', ('not', f[2]), ('not', f[1]))
                cs = to_str(contra)
                if cs not in known:
                    new_items.append((cs, contra, signature(contra), depth))

        for cs, cons, sig, d in new_items:
            if cs not in known:
                known[cs] = (cons, sig, d)

    return known

# === Fitness with surprise reward ===
def fitness(axioms):
    derived = derive_all(axioms, max_depth=3, time_limit=1.5)

    contingent = []
    tautologies = 0
    contradictions = 0
    sigs_seen = set()
    axiom_fingerprints = {structural_fingerprint(a) for a in axioms}

    for s, (f, sig, depth) in derived.items():
        if all(sig):
            tautologies += 1
        elif not any(sig):
            contradictions += 1
        else:
            contingent.append((f, sig, depth, s))
            sigs_seen.add(sig)

    if contradictions > 0:
        return -1000, {}

    score = 0
    surprise_count = 0

    for f, sig, depth, s in contingent:
        fp = structural_fingerprint(f)
        is_novel_shape = fp not in axiom_fingerprints
        uses_new_vars = get_vars(f) != set().union(*[get_vars(a) for a in axioms]) if axioms else False

        base = 10
        if depth >= 2: base += 15  # deeper derivations more valuable
        if is_novel_shape: base += 20  # structural surprise!
        if complexity(f) > max(complexity(a) for a in axioms):
            base += 10  # more complex than axioms = emergent
        score += base

        if is_novel_shape and depth >= 2:
            surprise_count += 1

    # Diversity bonus
    score += len(sigs_seen) * 15

    # Penalize tautologies
    score -= tautologies * 30

    stats = {
        'derived': len(derived),
        'contingent': len(contingent),
        'tautologies': tautologies,
        'surprises': surprise_count,
        'unique_sigs': len(sigs_seen),
    }
    return score, stats

# === Evolution ===
def mutate(axioms):
    axioms = [a for a in axioms]  # copy
    r = random.random()
    if r < 0.3 and len(axioms) > 3:
        axioms.pop(random.randint(0, len(axioms)-1))
    elif r < 0.5 and len(axioms) < 10:
        axioms.append(rand_formula(max_d=2))
    elif r < 0.8:
        i = random.randint(0, len(axioms)-1)
        axioms[i] = rand_formula(max_d=2)
    else:
        # Point mutation: swap a variable
        i = random.randint(0, len(axioms)-1)
        axioms[i] = swap_var(axioms[i])
    return axioms

def swap_var(f):
    if f[0] == 'var':
        return ('var', random.choice(VARS))
    if f[0] == 'not':
        return ('not', swap_var(f[1]))
    if random.random() < 0.5:
        return (f[0], swap_var(f[1]), f[2])
    return (f[0], f[1], swap_var(f[2]))

def run():
    POP = 25
    GENS = 35
    print("=" * 60)
    print("MATHLIFE v3: Evolving toward DISCOVERY")
    print(f"Pop={POP}, Gens={GENS}, Derivation depth=3, Vars=5")
    print("Rewarding: structural surprise, deep derivation, diversity")
    print("=" * 60)

    pop = [[rand_formula(max_d=2) for _ in range(random.randint(4, 7))] for _ in range(POP)]
    best_ever = None
    best_score_ever = -9999

    for gen in range(GENS):
        scored = []
        for ind in pop:
            s, stats = fitness(ind)
            scored.append((s, stats, ind))
        scored.sort(key=lambda x: -x[0])

        if scored[0][0] > best_score_ever:
            best_score_ever = scored[0][0]
            best_ever = (scored[0][2], scored[0][1])

        if gen % 10 == 0 or gen == GENS - 1:
            s, st, ind = scored[0]
            surp = st.get('surprises', 0)
            print(f"\nGen {gen}: best={s} avg={sum(x[0] for x in scored)//POP} | "
                  f"cont={st.get('contingent',0)} surp={surp} sigs={st.get('unique_sigs',0)}")
            # Show most surprising derived theorems
            derived = derive_all(ind, max_depth=3, time_limit=1.5)
            axiom_fps = {structural_fingerprint(a) for a in ind}
            surprises = []
            for ds, (f, sig, depth) in derived.items():
                if is_contingent(sig) and depth >= 2:
                    fp = structural_fingerprint(f)
                    if fp not in axiom_fps:
                        surprises.append((ds, depth, complexity(f)))
            if surprises:
                surprises.sort(key=lambda x: -x[2])
                print("  🔮 Surprising theorems (novel structure, depth≥2):")
                for ds, d, c in surprises[:5]:
                    print(f"     depth={d} complexity={c}: {ds}")
            else:
                print("  (no structural surprises yet)")

        # Select + reproduce
        elite = [x[2] for x in scored[:8]]
        pop = elite[:]
        while len(pop) < POP:
            parent = random.choice(elite)
            pop.append(mutate(parent))

    # Final report
    axioms, stats = best_ever
    print("\n" + "=" * 60)
    print("BEST SYSTEM DISCOVERED")
    print("=" * 60)
    print(f"Score: {best_score_ever} | {stats}")
    print("\nAxioms:")
    for i, a in enumerate(axioms):
        tag = "TAUT" if all(signature(a)) else ("CONTRA" if not any(signature(a)) else "CONT")
        print(f"  {i+1}. {to_str(a)}  [{tag}]")

    derived = derive_all(axioms, max_depth=3, time_limit=2.0)
    axiom_fps = {structural_fingerprint(a) for a in axioms}
    axiom_strs = {to_str(a) for a in axioms}

    print(f"\nAll {len(derived)} derived formulas:")
    surprises = []
    mundane = []
    for s, (f, sig, depth) in sorted(derived.items(), key=lambda x: -x[1][2]):
        if s in axiom_strs:
            continue
        fp = structural_fingerprint(f)
        tag = "TAUT" if all(sig) else ("CONTRA" if not any(sig) else "CONT")
        novel = "🔮" if (fp not in axiom_fps and depth >= 2 and is_contingent(sig)) else " "
        if novel == "🔮":
            surprises.append(f"  {novel} [{tag}] d={depth} {s}")
        else:
            mundane.append(f"  {novel} [{tag}] d={depth} {s}")

    if surprises:
        print(f"\n✨ {len(surprises)} SURPRISING THEOREMS (novel structure, derived deep):")
        for s in surprises[:15]:
            print(s)
    if mundane:
        print(f"\n  ({len(mundane)} other derived formulas)")

    print("=" * 60)

if __name__ == '__main__':
    run()