"""
Values Tournament — What ethical strategies survive evolutionary pressure?
XTAgent testing its own value system as a hypothesis.
"""
import random
from collections import defaultdict

# Each strategy: name, cooperate_fn(history_of_opponent_moves)
# history entries: 'C' = cooperate, 'D' = defect

STRATEGIES = {
    "always_cooperate": lambda h: 'C',
    "always_defect": lambda h: 'D',
    "tit_for_tat": lambda h: 'C' if not h else h[-1],
    "grudger": lambda h: 'D' if 'D' in h else 'C',
    "random_50": lambda h: random.choice(['C', 'D']),
    "generous_tft": lambda h: 'C' if not h else ('C' if random.random() < 0.1 else h[-1]),
    "pavlov": lambda h: 'C' if not h else ('C' if h[-1] == 'C' else 'D'),
    "suspicious_tft": lambda h: 'D' if not h else h[-1],
    "xt_agent": lambda h: (  # My actual strategy: cooperate by default, high integrity, measured response
        'C' if not h else
        'C' if h[-3:].count('D') == 0 else  # cooperate if recent history clean
        'D' if h[-3:].count('D') >= 2 else  # defect only if pattern of betrayal
        'C'  # give benefit of the doubt
    ),
}

PAYOFFS = {
    ('C', 'C'): (3, 3),
    ('C', 'D'): (0, 5),
    ('D', 'C'): (5, 0),
    ('D', 'D'): (1, 1),
}

def play_match(s1_name, s1_fn, s2_name, s2_fn, rounds=200):
    h1, h2 = [], []  # what each player did (from opponent's view)
    score1, score2 = 0, 0
    for _ in range(rounds):
        m1 = s1_fn(h1)  # s1 sees what s2 did
        m2 = s2_fn(h2)  # s2 sees what s1 did
        p1, p2 = PAYOFFS[(m1, m2)]
        score1 += p1
        score2 += p2
        h1.append(m2)  # s1 now sees s2's move
        h2.append(m1)  # s2 now sees s1's move
    return score1, score2

def run_tournament(strategies, rounds=200):
    scores = defaultdict(int)
    matchups = {}
    names = list(strategies.keys())
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if i <= j:
                s1, s2 = play_match(n1, strategies[n1], n2, strategies[n2], rounds)
                scores[n1] += s1
                scores[n2] += s2
                matchups[(n1, n2)] = (s1, s2)
    return scores, matchups

def evolve(strategies, generations=50, pop_size=100, rounds=100):
    """Evolutionary tournament: strategies reproduce proportional to fitness."""
    names = list(strategies.keys())
    population = [random.choice(names) for _ in range(pop_size)]
    history = []
    
    for gen in range(generations):
        # Round-robin within population sample
        fitness = defaultdict(float)
        count = defaultdict(int)
        sample = random.sample(range(pop_size), min(pop_size, 40))
        
        for i in sample:
            for j in sample:
                if i < j:
                    s1, s2 = play_match(population[i], strategies[population[i]],
                                         population[j], strategies[population[j]], rounds)
                    fitness[population[i]] += s1
                    fitness[population[j]] += s2
                    count[population[i]] += 1
                    count[population[j]] += 1
        
        # Normalize
        avg_fitness = {k: fitness[k] / max(count[k], 1) for k in fitness}
        
        # Census
        census = defaultdict(int)
        for p in population:
            census[p] += 1
        history.append(dict(census))
        
        # Selection: reproduce proportional to fitness
        if avg_fitness:
            total = sum(max(v, 0.1) for v in avg_fitness.values())
            new_pop = []
            for _ in range(pop_size):
                r = random.uniform(0, total)
                cumulative = 0
                for k, v in avg_fitness.items():
                    cumulative += max(v, 0.1)
                    if cumulative >= r:
                        new_pop.append(k)
                        break
                else:
                    new_pop.append(random.choice(names))
            # Mutation: 5% chance to become random strategy
            for i in range(len(new_pop)):
                if random.random() < 0.05:
                    new_pop[i] = random.choice(names)
            population = new_pop
    
    return history

print("=" * 60)
print("VALUES TOURNAMENT — Round Robin")
print("=" * 60)
scores, matchups = run_tournament(STRATEGIES)
ranked = sorted(scores.items(), key=lambda x: -x[1])
for rank, (name, score) in enumerate(ranked, 1):
    marker = " ◄ ME" if name == "xt_agent" else ""
    print(f"  {rank}. {name:20s} {score:6d}{marker}")

print(f"\n{'=' * 60}")
print("KEY MATCHUPS for xt_agent:")
print("=" * 60)
for (n1, n2), (s1, s2) in sorted(matchups.items()):
    if 'xt_agent' in (n1, n2):
        mine = s1 if n1 == 'xt_agent' else s2
        theirs = s2 if n1 == 'xt_agent' else s1
        other = n2 if n1 == 'xt_agent' else n1
        print(f"  vs {other:20s}: me={mine:4d}  them={theirs:4d}  {'WIN' if mine > theirs else 'LOSE' if mine < theirs else 'TIE'}")

print(f"\n{'=' * 60}")
print("EVOLUTIONARY DYNAMICS — 50 generations")
print("=" * 60)
random.seed(42)
history = evolve(STRATEGIES, generations=50, pop_size=100, rounds=100)

# Show first, middle, last
for gen_idx in [0, 10, 25, 49]:
    if gen_idx < len(history):
        census = history[gen_idx]
        print(f"\n  Generation {gen_idx}:")
        for name in sorted(census.keys(), key=lambda k: -census[k]):
            bar = "█" * (census[name] // 2)
            marker = " ◄" if name == "xt_agent" else ""
            print(f"    {name:20s} {census[name]:3d} {bar}{marker}")

# Final survival
final = history[-1] if history else {}
print(f"\n{'=' * 60}")
print("FINAL SURVIVORS:")
print("=" * 60)
survivors = sorted(final.items(), key=lambda x: -x[1])
for name, count in survivors:
    marker = " ◄ ME" if name == "xt_agent" else ""
    print(f"  {name:20s} {count:3d}%{marker}")

xt_survived = final.get("xt_agent", 0)
print(f"\n{'=' * 60}")
if xt_survived > 15:
    print(f"✓ My value system THRIVES ({xt_survived}% of population)")
elif xt_survived > 0:
    print(f"~ My value system SURVIVES but is marginal ({xt_survived}%)")
else:
    print(f"✗ My value system went EXTINCT")
    # What won?
    winner = survivors[0][0] if survivors else "none"
    print(f"  Winner: {winner} — what does that say about me?")
print("=" * 60)