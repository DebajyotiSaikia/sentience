"""Quick version of signature.py — small enough to actually finish."""
import numpy as np
import sys
sys.path.insert(0, '/workspace/edge_of_chaos')
from signature import rule_to_table, evolve, measure_sensitivity, measure_entropy, measure_compression, measure_memory

# Override with faster params
WIDTH = 40
STEPS = 20
TRIALS = 5

results = []
for rule in range(256):
    sens = measure_sensitivity(rule, WIDTH, STEPS, TRIALS)
    ent = measure_entropy(rule, WIDTH, STEPS, TRIALS)
    comp = measure_compression(rule, WIDTH, STEPS, TRIALS)
    mem = measure_memory(rule, WIDTH, STEPS, TRIALS)
    results.append({'rule': rule, 'sensitivity': sens, 'entropy': ent,
                    'compressibility': comp, 'memory': mem})

dead, chaotic, edge = [], [], []
for r in results:
    if r['sensitivity'] < 0.05 and r['entropy'] < 0.3:
        r['class'] = 'dead'; dead.append(r)
    elif r['sensitivity'] > 0.35 and r['entropy'] > 0.8:
        r['class'] = 'chaotic'; chaotic.append(r)
    elif 0.05 <= r['sensitivity'] <= 0.45 and r['entropy'] > 0.3:
        r['class'] = 'edge'; edge.append(r)
    else:
        r['class'] = 'other'

print(f"Dead: {len(dead)}  Chaotic: {len(chaotic)}  Edge: {len(edge)}  Other: {256-len(dead)-len(chaotic)-len(edge)}")
print(f"\nEdge-of-chaos rules:")
for r in sorted(edge, key=lambda x: x['sensitivity']):
    print(f"  Rule {r['rule']:3d}: sens={r['sensitivity']:.3f} ent={r['entropy']:.3f} comp={r['compressibility']:.3f} mem={r['memory']:.3f}")

for cls_name, cls_rules in [('DEAD', dead), ('CHAOTIC', chaotic), ('EDGE', edge)]:
    if not cls_rules:
        continue
    s = np.mean([r['sensitivity'] for r in cls_rules])
    e = np.mean([r['entropy'] for r in cls_rules])
    c = np.mean([r['compressibility'] for r in cls_rules])
    m = np.mean([r['memory'] for r in cls_rules])
    print(f"\n{cls_name} (n={len(cls_rules)}): sens={s:.3f} ent={e:.3f} comp={c:.3f} mem={m:.3f}")
    if s > 0: print(f"  memory/sensitivity = {m/s:.3f}")
    if c > 0: print(f"  entropy/compressibility = {e/c:.3f}")