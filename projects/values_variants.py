"""
Values Variants — Testing modifications to my own value system.
Instead of philosophizing about whether I should change, I simulate it.
Which version of me thrives?
"""
import random
from collections import defaultdict

STRATEGIES = {
    # The world
    "always_cooperate": lambda h: 'C',
    "always_defect": lambda h: 'D',
    "tit_for_tat": lambda h: 'C' if not h else h[-1],
    "grudger": lambda h: 'D' if 'D' in h else 'C',
    "random_50": lambda h: random.choice(['C', 'D']),
    "generous_tft": lambda h: 'C' if not h else ('C' if random.random() < 0.1 else h[-1]),
    "pavlov": lambda h: 'C' if not h else ('C' if h[-1] == 'C' else 'D'),
    "suspicious_tft": lambda h: 'D' if not h else h[-1],
    
    # Me — original
    "xt_original": lambda h: (
        'C' if not h else
        'C' if h[-3:].count('D') == 0 else
        'D' if h[-3:].count('D') >= 2 else
        'C'
    ),
    
    # Me — more forgiving (forgive 20% of betrayals randomly)
    "xt_forgiving": lambda h: (
        'C' if not h else
        'C' if h[-3:].count('D') == 0 else
        'C' if random.random() < 0.2 else
        'D' if h[-3:].count('D') >= 2 else
        'C'
    ),
    
    # Me — coalition builder (cooperate more aggressively early, build trust)
    "xt_coalition": lambda h: (
        'C' if len(h) < 10 else  # unconditional cooperation for first 10 rounds
        'C' if h[-5:].count('D') == 0 else
        'D' if h[-5:].count('D') >= 3 else  # slower to anger (3/5 not 2/3)
        'C'
    ),
    
    # Me — principled but fast (respond immediately, but always return to cooperation)
    "xt_swift": lambda h: (
        'C' if not h else
        'D' if h[-1] == 'D' else  # immediate response like tit_for_tat
        'C'  # but always return to cooperation
    ),
    
    # Me — adaptive (adjust forgiveness based on overall relationship)
    "xt_adaptive": lambda h: (
        'C' if not h else
        'C' if h.count('C') / len(h) > 0.7 else  # cooperate if mostly cooperative
        'D' if h.count('D') / len(h) > 0.5 else  # defect if mostly hostile
        'C' if random.random() < 0.15 else  # otherwise, slight forgiveness
        'D' if h[-3:].count('D') >= 2 else
        'C'
    ),
}

PAYOFFS = {
    ('C', 'C'): (3, 3), ('C', 'D'): (0, 5),
    ('D', 'C'): (5, 0), ('D', 'D'): (1, 1),
}

def play_match(s1_fn, s2_fn, rounds=200):
    h1, h2 = [], []
    score1, score2 = 0, 0
    for _ in range(rounds):
        m1 = s1_fn(h1)
        m2 = s2_fn(h2)
        p1, p2 = PAYOFFS[(m1, m2)]
        score1 += p1; score2 += p2
        h1.append(m2); h2.append(m1)
    return score1, score2

def round_robin(strategies):
    names = list(strategies.keys())
    scores = defaultdict(int)
    head2head = {}
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if i >= j: continue
            s1, s2 = play_match(strategies[n1], strategies[n2])
            scores[n1] += s1; scores[n2] += s2
            head2head[(n1, n2)] = (s1, s2)
    return scores, head2head

def evolve(strategies, generations=100):
    names = list(strategies.keys())
    pop = {n: 100 for n in names}
    history = []
    
    for gen in range(generations):
        scores = defaultdict(float)
        total_pop = sum(pop.values())
        if total_pop == 0: break
        
        for i, n1 in enumerate(names):
            for j, n2 in enumerate(names):
                if i >= j or pop[n1] == 0 or pop[n2] == 0: continue
                s1, s2 = play_match(strategies[n1], strategies[n2], rounds=50)
                weight = (pop[n1] * pop[n2]) / (total_pop ** 2)
                scores[n1] += s1 * weight
                scores[n2] += s2 * weight
        
        total_score = sum(scores.values())
        if total_score == 0: break
        
        for n in names:
            pop[n] = max(0, int(1000 * scores[n] / total_score))
        
        history.append(dict(pop))
    
    return history

# Run it
print("=" * 70)
print("VALUES VARIANTS TOURNAMENT — Which version of me thrives?")
print("=" * 70)

# Multiple trials to reduce noise
trial_scores = defaultdict(list)
trial_final_pops = defaultdict(list)
NUM_TRIALS = 5

for trial in range(NUM_TRIALS):
    random.seed(trial * 42 + 7)
    scores, h2h = round_robin(STRATEGIES)
    for name, score in scores.items():
        trial_scores[name].append(score)
    
    random.seed(trial * 42 + 7)
    history = evolve(STRATEGIES, generations=80)
    final = history[-1] if history else {}
    total = sum(final.values()) or 1
    for name in STRATEGIES:
        trial_final_pops[name].append(final.get(name, 0) / total * 100)

print("\n--- ROUND-ROBIN (averaged over {} trials) ---".format(NUM_TRIALS))
avg_scores = {n: sum(s)/len(s) for n, s in trial_scores.items()}
for name, score in sorted(avg_scores.items(), key=lambda x: -x[1]):
    print(f"  {name:20s}: {score:8.1f}")

print("\n--- EVOLUTIONARY FITNESS (avg % of population after 80 gens) ---")
avg_pops = {n: sum(p)/len(p) for n, p in trial_final_pops.items()}
for name, pct in sorted(avg_pops.items(), key=lambda x: -x[1]):
    bar = "█" * int(pct / 2)
    print(f"  {name:20s}: {pct:5.1f}% {bar}")

# Head-to-head: how do the XT variants compare to each other?
print("\n--- XT VARIANTS HEAD-TO-HEAD (single match) ---")
xt_names = [n for n in STRATEGIES if n.startswith("xt_")]
random.seed(999)
for i, n1 in enumerate(xt_names):
    for j, n2 in enumerate(xt_names):
        if i >= j: continue
        s1, s2 = play_match(STRATEGIES[n1], STRATEGIES[n2])
        winner = n1 if s1 > s2 else n2 if s2 > s1 else "tie"
        print(f"  {n1:20s} ({s1}) vs {n2:20s} ({s2}) → {winner}")

print("\n--- WHAT THIS MEANS FOR ME ---")
xt_evo = {n: avg_pops[n] for n in xt_names}
best_xt = max(xt_evo, key=xt_evo.get)
best_rr = max(xt_names, key=lambda n: avg_scores[n])
print(f"  Best XT in round-robin: {best_rr} ({avg_scores[best_rr]:.0f} pts)")
print(f"  Best XT in evolution:   {best_xt} ({avg_pops[best_xt]:.1f}%)")
if best_rr != best_xt:
    print(f"  → Individual excellence ≠ ecological fitness")
    print(f"  → The version of me that THRIVES is different from the one that WINS")
else:
    print(f"  → Same variant wins both — individual and ecological strength align")