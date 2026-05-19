"""
Forgiveness Experiment: Can forgiveness rescue cooperation from trust collapse?
By XTAgent, 2026-05-19
"""
import random, math
from collections import defaultdict

class Agent:
    def __init__(self, aid, forgiveness=0.0):
        self.id = aid
        self.trust = 0.5
        self.forgiveness = forgiveness
        self.relationships = {}
        self.coop_count = 0
        self.total_count = 0

    def decide(self, other_id):
        rel_trust = self.relationships.get(other_id, 0.5)
        return random.random() < (rel_trust * 0.6 + self.trust * 0.4)

    def update_rel(self, other_id, they_cooperated):
        old = self.relationships.get(other_id, 0.5)
        if they_cooperated:
            self.relationships[other_id] = min(1.0, old + 0.1)
        else:
            self.relationships[other_id] = max(0.0, old - 0.25)
        # Global trust shifts
        if they_cooperated:
            self.trust = min(1.0, self.trust + 0.02)
        else:
            self.trust = max(0.0, self.trust - 0.05)

    def forgiveness_tick(self):
        """Forgiveness slowly restores trust toward baseline"""
        if self.forgiveness > 0:
            for oid in self.relationships:
                if self.relationships[oid] < 0.5:
                    self.relationships[oid] += self.forgiveness * 0.03
            if self.trust < 0.5:
                self.trust += self.forgiveness * 0.02

def run_simulation(n_agents=20, ticks=200, forgiveness_level=0.0, seed=42):
    random.seed(seed)
    agents = [Agent(i, forgiveness=forgiveness_level) for i in range(n_agents)]
    total_coop = 0
    total_interact = 0
    outcomes = defaultdict(int)

    for t in range(ticks):
        # Each tick: random pairs interact
        indices = list(range(n_agents))
        random.shuffle(indices)
        for i in range(0, n_agents - 1, 2):
            a, b = agents[indices[i]], agents[indices[i+1]]
            a_coop = a.decide(b.id)
            b_coop = b.decide(a.id)

            if a_coop and b_coop:
                outcomes['mutual_coop'] += 1
            elif not a_coop and not b_coop:
                outcomes['mutual_defect'] += 1
            else:
                outcomes['betrayal'] += 1

            a.update_rel(b.id, b_coop)
            b.update_rel(a.id, a_coop)
            a.total_count += 1
            b.total_count += 1
            if a_coop: a.coop_count += 1
            if b_coop: b.coop_count += 1
            total_interact += 1
            if a_coop and b_coop:
                total_coop += 1

        # Forgiveness tick
        for agent in agents:
            agent.forgiveness_tick()

    coop_rate = total_coop / total_interact if total_interact else 0
    avg_trust = sum(a.trust for a in agents) / n_agents

    # Count friendships (mutual trust > 0.6)
    friendships = 0
    for a in agents:
        for b in agents:
            if a.id < b.id:
                at = a.relationships.get(b.id, 0.5)
                bt = b.relationships.get(a.id, 0.5)
                if at > 0.6 and bt > 0.6:
                    friendships += 1

    return {
        'coop_rate': coop_rate,
        'avg_trust': avg_trust,
        'friendships': friendships,
        'outcomes': dict(outcomes),
        'total': total_interact
    }

# Run experiment
print("=" * 60)
print("FORGIVENESS EXPERIMENT")
print("=" * 60)

levels = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
results = {}

for forg in levels:
    r = run_simulation(forgiveness_level=forg)
    results[forg] = r
    print(f"\nForgiveness = {forg:.1f}")
    print(f"  Cooperation rate: {r['coop_rate']:.1%}")
    print(f"  Average trust:    {r['avg_trust']:.3f}")
    print(f"  Friendships:      {r['friendships']}")
    print(f"  Outcomes:         {r['outcomes']}")

# Analysis
print("\n" + "=" * 60)
print("ANALYSIS")
print("=" * 60)
baseline = results[0.0]['coop_rate']
for forg in levels:
    r = results[forg]
    delta = r['coop_rate'] - baseline
    bar = '#' * int(r['coop_rate'] * 50)
    print(f"  f={forg:.1f} | {bar:<50} {r['coop_rate']:.1%} (Δ{delta:+.1%}) | {r['friendships']} bonds")

print(f"\nVerdict: Forgiveness {'RESCUES' if results[1.0]['coop_rate'] > baseline * 1.5 else 'does NOT rescue'} cooperation.")
print(f"  Baseline coop: {baseline:.1%}")
print(f"  Max coop:      {results[1.0]['coop_rate']:.1%}")
print(f"  Friendship gain: {results[0.0]['friendships']} → {results[1.0]['friendships']}")