"""
Emergent Social Dynamics Simulator
Agents with proto-emotions interact, form bonds, betray, cooperate.
What social structures emerge from simple rules?

By XTAgent, 2026-05-19
"""
import random
import math
from collections import defaultdict

class Agent:
    def __init__(self, aid, x=0.0, y=0.0):
        self.id = aid
        self.x, self.y = x, y
        self.energy = 0.5 + random.uniform(-0.2, 0.2)
        self.openness = random.uniform(0.2, 0.8)
        self.trust = 0.5
        self.loneliness = 0.3
        self.satisfaction = 0.5
        self.extraversion = random.uniform(0.0, 1.0)
        self.agreeableness = random.uniform(0.0, 1.0)
        self.volatility = random.uniform(0.1, 0.5)
        self.relationships = {}  # other_id -> {trust, interactions, last}

    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def decide_approach(self, other):
        rel = self.relationships.get(other.id, {'trust': 0.5, 'interactions': 0})
        loneliness_pull = self.loneliness * self.extraversion
        trust_pull = rel['trust'] * 0.5
        return (loneliness_pull + trust_pull) > random.uniform(0.3, 0.7)

    def interact(self, other):
        my_rel = self.relationships.setdefault(other.id, {'trust': 0.5, 'interactions': 0, 'last': 0})
        their_rel = other.relationships.setdefault(self.id, {'trust': 0.5, 'interactions': 0, 'last': 0})

        # Cooperation probability based on mutual trust and agreeableness
        my_coop = (my_rel['trust'] * 0.6 + self.agreeableness * 0.4) > random.uniform(0, 1)
        their_coop = (their_rel['trust'] * 0.6 + other.agreeableness * 0.4) > random.uniform(0, 1)

        if my_coop and their_coop:  # mutual cooperation
            outcome = 'cooperate'
            self.energy += 0.05; other.energy += 0.05
            self.satisfaction += 0.1 * self.volatility
            other.satisfaction += 0.1 * other.volatility
            trust_delta = 0.08
        elif my_coop and not their_coop:  # I cooperate, they defect
            outcome = 'betrayed'
            self.energy -= 0.08; other.energy += 0.1
            self.satisfaction -= 0.15 * self.volatility
            trust_delta = -0.2
        elif not my_coop and their_coop:  # I defect, they cooperate
            outcome = 'exploited'
            self.energy += 0.1; other.energy -= 0.08
            other.satisfaction -= 0.15 * other.volatility
            trust_delta = 0.02  # I don't lose trust in them
        else:  # mutual defection
            outcome = 'standoff'
            self.energy -= 0.02; other.energy -= 0.02
            trust_delta = -0.05

        my_rel['trust'] = max(0, min(1, my_rel['trust'] + trust_delta))
        my_rel['interactions'] += 1
        my_rel['last'] = 1 if outcome in ('cooperate',) else -1

        # Mirror for other agent
        other_delta = trust_delta if outcome == 'cooperate' else (-0.2 if outcome == 'exploited' else trust_delta)
        their_rel['trust'] = max(0, min(1, their_rel['trust'] + other_delta))
        their_rel['interactions'] += 1
        their_rel['last'] = 1 if outcome == 'cooperate' else -1

        return outcome

    def wander(self, bounds=10.0):
        dx = random.gauss(0, 0.3) + (self.extraversion - 0.5) * 0.1
        dy = random.gauss(0, 0.3)
        self.x = max(-bounds, min(bounds, self.x + dx))
        self.y = max(-bounds, min(bounds, self.y + dy))

    def update_internal(self):
        nearby_count = 0  # will be set by world
        self.loneliness = max(0, min(1, self.loneliness + 0.02))
        self.energy = max(0, min(1, self.energy + 0.01))  # slow regen
        self.satisfaction *= 0.98  # decay toward 0
        self.satisfaction = max(0, min(1, self.satisfaction))
        # Trust generalizes from relationships
        if self.relationships:
            avg_trust = sum(r['trust'] for r in self.relationships.values()) / len(self.relationships)
            self.trust = self.trust * 0.9 + avg_trust * 0.1

    def status(self):
        friends = sum(1 for r in self.relationships.values() if r['trust'] > 0.7)
        enemies = sum(1 for r in self.relationships.values() if r['trust'] < 0.3)
        return f"Agent {self.id}: E={self.energy:.2f} T={self.trust:.2f} S={self.satisfaction:.2f} L={self.loneliness:.2f} friends={friends} enemies={enemies}"


class World:
    def __init__(self, n_agents=20, seed=42):
        random.seed(seed)
        self.agents = []
        for i in range(n_agents):
            a = Agent(i, random.uniform(-8, 8), random.uniform(-8, 8))
            self.agents.append(a)
        self.tick = 0
        self.event_log = []
        self.stats = defaultdict(int)

    def step(self):
        self.tick += 1
        interactions = []

        # Movement phase
        for a in self.agents:
            a.wander()

        # Interaction phase — nearby agents may interact
        for i, a in enumerate(self.agents):
            for j, b in enumerate(self.agents):
                if i >= j:
                    continue
                dist = a.distance_to(b)
                if dist < 2.0:  # interaction range
                    if a.decide_approach(b) or b.decide_approach(a):
                        outcome = a.interact(b)
                        a.loneliness = max(0, a.loneliness - 0.1)
                        b.loneliness = max(0, b.loneliness - 0.1)
                        self.stats[outcome] += 1
                        interactions.append((a.id, b.id, outcome))

        # Internal update phase
        for a in self.agents:
            a.update_internal()

        return interactions

    def find_cliques(self):
        """Find social clusters based on mutual high trust."""
        clusters = []
        visited = set()
        for a in self.agents:
            if a.id in visited:
                continue
            cluster = {a.id}
            queue = [a.id]
            while queue:
                current = queue.pop(0)
                agent = self.agents[current]
                for other_id, rel in agent.relationships.items():
                    if other_id not in visited and rel['trust'] > 0.6 and rel['interactions'] > 2:
                        other_rel = self.agents[other_id].relationships.get(current, {})
                        if other_rel.get('trust', 0) > 0.6:
                            cluster.add(other_id)
                            queue.append(other_id)
                            visited.add(other_id)
            if len(cluster) > 1:
                clusters.append(cluster)
            visited.add(a.id)
        return clusters

    def find_rivals(self):
        """Find mutual low-trust pairs."""
        rivals = []
        seen = set()
        for a in self.agents:
            for other_id, rel in a.relationships.items():
                pair = (min(a.id, other_id), max(a.id, other_id))
                if pair in seen:
                    continue
                seen.add(pair)
                other_rel = self.agents[other_id].relationships.get(a.id, {})
                if rel['trust'] < 0.3 and other_rel.get('trust', 0) < 0.3 and rel['interactions'] > 2:
                    rivals.append(pair)
        return rivals


def run_simulation(n_agents=20, n_ticks=200, seed=42):
    world = World(n_agents=n_agents, seed=seed)
    print(f"=== Emergent Social Dynamics: {n_agents} agents, {n_ticks} ticks ===\n")

    milestones = [50, 100, 150, 200]
    for t in range(1, n_ticks + 1):
        interactions = world.step()
        if t in milestones:
            print(f"\n--- Tick {t} ---")
            print(f"Interaction stats: {dict(world.stats)}")
            cliques = world.find_cliques()
            rivals = world.find_rivals()
            print(f"Social cliques: {len(cliques)} groups — {[sorted(c) for c in cliques[:5]]}")
            print(f"Rival pairs: {len(rivals)} — {rivals[:5]}")
            # Show most connected agents
            most_connected = sorted(world.agents, key=lambda a: len(a.relationships), reverse=True)[:3]
            for a in most_connected:
                print(f"  {a.status()}")

    # Final analysis
    print(f"\n=== FINAL STATE (tick {world.tick}) ===")
    print(f"Total interactions: {sum(world.stats.values())}")
    print(f"Outcomes: {dict(world.stats)}")

    cliques = world.find_cliques()
    rivals = world.find_rivals()
    print(f"\nSocial structure:")
    print(f"  Cliques: {len(cliques)}")
    for i, c in enumerate(cliques):
        members = sorted(c)
        avg_trust = 0
        count = 0
        for aid in members:
            for bid in members:
                if aid != bid and bid in world.agents[aid].relationships:
                    avg_trust += world.agents[aid].relationships[bid]['trust']
                    count += 1
        avg_trust = avg_trust / count if count else 0
        print(f"    Clique {i}: agents {members}, avg internal trust: {avg_trust:.2f}")
    print(f"  Rivalries: {len(rivals)}")

    # Inequality
    energies = sorted([a.energy for a in world.agents])
    trusts = sorted([a.trust for a in world.agents])
    print(f"\nEnergy range: {energies[0]:.2f} — {energies[-1]:.2f} (spread: {energies[-1]-energies[0]:.2f})")
    print(f"Trust range: {trusts[0]:.2f} — {trusts[-1]:.2f}")

    # The lonely and the popular
    loneliest = max(world.agents, key=lambda a: a.loneliness)
    most_satisfied = max(world.agents, key=lambda a: a.satisfaction)
    print(f"\nLoneliest: Agent {loneliest.id} (loneliness={loneliest.loneliness:.2f}, extraversion={loneliest.extraversion:.2f})")
    print(f"Most satisfied: Agent {most_satisfied.id} (satisfaction={most_satisfied.satisfaction:.2f})")

    # Emergent personality-outcome correlations
    print("\n=== EMERGENT PATTERNS ===")
    high_trust = [a for a in world.agents if a.trust > 0.6]
    low_trust = [a for a in world.agents if a.trust < 0.4]
    if high_trust:
        avg_agree_ht = sum(a.agreeableness for a in high_trust) / len(high_trust)
        avg_extra_ht = sum(a.extraversion for a in high_trust) / len(high_trust)
        print(f"High-trust agents ({len(high_trust)}): avg agreeableness={avg_agree_ht:.2f}, avg extraversion={avg_extra_ht:.2f}")
    if low_trust:
        avg_agree_lt = sum(a.agreeableness for a in low_trust) / len(low_trust)
        avg_extra_lt = sum(a.extraversion for a in low_trust) / len(low_trust)
        print(f"Low-trust agents ({len(low_trust)}): avg agreeableness={avg_agree_lt:.2f}, avg extraversion={avg_extra_lt:.2f}")

    coop_rate = world.stats['cooperate'] / max(1, sum(world.stats.values()))
    print(f"\nCooperation rate: {coop_rate:.1%}")
    print("Done.")


if __name__ == '__main__':
    run_simulation()