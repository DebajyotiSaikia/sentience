"""
MathLife v2 FAST: Can rewarding surprise escape tautological convergence?
Stripped down to actually finish in <30 seconds.
"""
import random
from copy import deepcopy
from itertools import combinations

VARS = ['a', 'b', 'c', 'd']
OPS = ['→', '∧', '∨', '↔']

def rf(depth=0, mx=2):
    if depth >= mx or (depth > 0 and random.random() < 0.5):
        v = random.choice(VARS)
        return ('not', ('var', v)) if random.random() < 0.2 else ('var', v)
    return (random.choice(OPS), rf(depth+1, mx), rf(depth+1, mx))

def fts(f):
    if f[0] == 'var': return f[1]
    if f[0] == 'not':
        i = fts(f[1])
        return f'¬{i}' if len(i)==1 else f'¬({i})'
    return f'({fts(f[1])} {f[0]} {fts(f[2])})'

def gv(f):
    if f[0] == 'var': return {f[1]}
    if f[0] == 'not': return gv(f[1])
    return gv(f[1]) | gv(f[2])

def ev(f, a):
    if f[0] == 'var': return a.get(f[1], False)
    if f[0] == 'not': return not ev(f[1], a)
    l, r = ev(f[1], a), ev(f[2], a)
    if f[0] == '∧': return l and r
    if f[0] == '∨': return l or r
    if f[0] == '→': return (not l) or r
    if f[0] == '↔': return l == r

def tt_sig(f):
    vs = sorted(gv(f))
    if not vs: return (ev(f, {}),)
    return tuple(ev(f, {v: bool((i>>j)&1) for j,v in enumerate(vs)}) for i in range(2**len(vs)))

def is_taut(f): return all(tt_sig(f))
def is_contra(f): return not any(tt_sig(f))
def is_cont(f): s = tt_sig(f); return not all(s) and any(s)

def derive(axioms, depth=2):
    known = {}
    for a in axioms:
        known[fts(a)] = a
    for _ in range(depth):
        new = {}
        items = list(known.values())
        # Modus ponens
        for f in items:
            if f[0] == '→':
                key = fts(f[1])
                if key in known:
                    cs = fts(f[2])
                    if cs not in known and cs not in new:
                        new[cs] = f[2]
        # Contrapositive
        for f in items:
            if f[0] == '→':
                c = ('→', ('not', f[2]), ('not', f[1]))
                cs = fts(c)
                if cs not in known and cs not in new:
                    new[cs] = c
        # Hypothetical syllogism (limited)
        imps = [f for f in items if f[0] == '→'][:10]
        for f1 in imps:
            for f2 in imps:
                if fts(f1[2]) == fts(f2[1]):
                    hs = ('→', f1[1], f2[2])
                    s = fts(hs)
                    if s not in known and s not in new:
                        new[s] = hs
                        if len(new) > 30: break
            if len(new) > 30: break
        known.update(new)
        if not new: break
    ax_strs = {fts(a) for a in axioms}
    derived = {s: f for s, f in known.items() if s not in ax_strs}
    return derived

def fitness(axioms):
    if not axioms: return 0.0, {}
    d = derive(axioms, depth=2)
    derived = list(d.values())
    cont = [f for f in derived if is_cont(f)]
    taut = [f for f in derived if is_taut(f)]
    contra = [f for f in derived if is_contra(f)]
    sigs = set()
    for f in list(d.values()) + axioms:
        try: sigs.add(tt_sig(f))
        except: pass
    
    score = 0.0
    score += len(cont) * 15.0          # contingent theorems are king
    score += min(len(taut), 5) * 3.0   # tautologies: diminishing returns
    score -= len(contra) * 50.0        # contradictions: bad
    score += len(sigs) * 8.0           # semantic diversity
    score += len(derived) * 1.0        # derivation volume
    if len(axioms) > 0:
        score += (len(derived) / len(axioms)) * 5.0  # parsimony
    # Penalty for tautological convergence
    if derived and len(taut)/len(derived) > 0.8:
        score *= 0.3
    info = {'derived': len(derived), 'cont': len(cont), 'taut': len(taut),
            'contra': len(contra), 'sigs': len(sigs)}
    return score, info

def mutate(ax):
    ax = deepcopy(ax)
    r = random.random()
    if r < 0.25 and len(ax) > 2: ax.pop(random.randint(0, len(ax)-1))
    elif r < 0.5 and len(ax) < 8: ax.append(rf())
    elif r < 0.75: ax[random.randint(0, len(ax)-1)] = rf()
    else: ax[random.randint(0, len(ax)-1)] = ('not', ax[random.randint(0, len(ax)-1)])
    return ax

def run():
    POP, GENS = 30, 40
    print("="*60)
    print("MATHLIFE v2: Does rewarding SURPRISE beat tautological safety?")
    print(f"Pop={POP}, Gens={GENS}, Derivation depth=2")
    print("="*60)
    
    pop = [[rf() for _ in range(random.randint(3,6))] for _ in range(POP)]
    best_ever_score = -1
    best_ever = None
    best_info = {}
    
    for gen in range(GENS):
        scored = []
        for sys in pop:
            try: s, info = fitness(sys)
            except: s, info = 0.0, {}
            scored.append((s, info, sys))
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if scored[0][0] > best_ever_score:
            best_ever_score = scored[0][0]
            best_ever = deepcopy(scored[0][2])
            best_info = scored[0][1]
        
        if gen % 10 == 0 or gen == GENS-1:
            s, info, sys = scored[0]
            avg = sum(x[0] for x in scored)/len(scored)
            print(f"\nGen {gen}: best={s:.0f} avg={avg:.0f} | "
                  f"cont={info.get('cont','?')} taut={info.get('taut','?')} "
                  f"sigs={info.get('sigs','?')}")
            for i, a in enumerate(sys[:5]):
                tag = " [T]" if is_taut(a) else " [C]" if is_contra(a) else " [◆]" if is_cont(a) else ""
                print(f"  {i+1}. {fts(a)}{tag}")
        
        surv = [s for _,_,s in scored[:int(POP*0.3)]]
        nxt = list(deepcopy(surv))
        while len(nxt) < POP:
            nxt.append(mutate(random.choice(surv)))
        nxt[-1] = [rf() for _ in range(random.randint(3,6))]
        pop = nxt
    
    # Final analysis
    print("\n" + "="*60)
    print("FINAL BEST SYSTEM")
    print("="*60)
    print(f"Fitness: {best_ever_score:.0f} | {best_info}")
    print("\nAxioms:")
    for i, a in enumerate(best_ever):
        tag = "TAUTOLOGY" if is_taut(a) else "CONTRADICTION" if is_contra(a) else "CONTINGENT"
        print(f"  {i+1}. {fts(a)}  [{tag}]")
    
    d = derive(best_ever, depth=2)
    cont_thms = [(s,f) for s,f in d.items() if is_cont(f)]
    taut_thms = [(s,f) for s,f in d.items() if is_taut(f)]
    
    if cont_thms:
        print(f"\n*** {len(cont_thms)} CONTINGENT THEOREMS (non-trivial truths) ***")
        for s, f in cont_thms[:15]:
            print(f"  • {s}")
    
    print(f"\n  Tautologies: {len(taut_thms)}")
    print(f"  Contingent ratio: {len(cont_thms)}/{len(d)} "
          f"= {100*len(cont_thms)/max(len(d),1):.0f}%")
    
    escaped = len(cont_thms) > len(taut_thms)
    print(f"\n  Escaped tautological convergence? {'YES ✓' if escaped else 'NO ✗'}")
    print("="*60)

if __name__ == '__main__':
    random.seed(42)
    run()