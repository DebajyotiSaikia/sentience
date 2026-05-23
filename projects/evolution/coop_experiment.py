"""
Cooperation Experiment — Can altruism evolve?

Two conditions:
  1. Baseline: standard ecosystem (no group benefits)
  2. Cooperative: nearby cooperators get real benefits
     - Group defense bonus (harder to kill when cooperators cluster)
     - Resource sharing radius (cooperators pool nearby food)
     
Compare whether the cooperation trait rises or falls under each condition.
This is a genuine question I can't predict the answer to.
"""

import sys
sys.path.insert(0, '/workspace')
import random
from evolution.ecosystem import Ecosystem, Genome, Agent


class CooperativeEcosystem(Ecosystem):
    """Ecosystem where cooperation has tangible group benefits."""
    
    def _fight(self, attacker, defender):
        """Modified combat: cooperators near defender help defend."""
        # Count cooperative allies near the defender
        allies = [a for a in self._neighbors(defender, 3)
                  if a.id != attacker.id and a.genome.cooperation > 0.5]
        
        # Each cooperative ally adds 20% defense bonus
        defense_multiplier = 1.0 + 0.2 * len(allies)
        
        # Base combat
        atk_power = attacker.genome.aggression * attacker.energy * 0.3
        def_power = defender.genome.aggression * defender.energy * 0.3 * defense_multiplier
        
        atk_roll = atk_power * random.uniform(0.5, 1.5)
        def_roll = def_power * random.uniform(0.5, 1.5)
        
        if atk_roll > def_roll:
            stolen = min(defender.energy, atk_roll - def_roll)
            attacker.energy += stolen * 0.7
            defender.energy -= stolen
            if not defender.alive:
                attacker.kills += 1
        else:
            damage = (def_roll - atk_roll) * 0.5
            attacker.energy -= damage
    
    def _eat(self, agent):
        """Modified eating: cooperators share food with nearby cooperators."""
        super()._eat(agent)
        
        # After eating, cooperative agents share surplus with nearby cooperators
        if agent.genome.cooperation > 0.5 and agent.energy > 40:
            coop_neighbors = [a for a in self._neighbors(agent, 2)
                              if a.genome.cooperation > 0.5 and a.energy < 30]
            if coop_neighbors:
                # Share 5% of energy per hungry neighbor (up to 3)
                for neighbor in coop_neighbors[:3]:
                    share = agent.energy * 0.05
                    if agent.energy - share > 30:
                        agent.energy -= share
                        neighbor.energy += share


def run_condition(label, ecosystem_class, seed):
    """Run one experimental condition and extract key metrics."""
    random.seed(seed)
    eco = ecosystem_class(width=30, height=15, initial_pop=20, resource_rate=0.04)
    report = eco.run(ticks=200, report_every=200)  # only final report
    
    # Extract cooperation metrics
    if eco.agents:
        avg_coop = sum(a.genome.cooperation for a in eco.agents) / len(eco.agents)
        avg_agg = sum(a.genome.aggression for a in eco.agents) / len(eco.agents)
        pop = len(eco.agents)
        max_gen = max(a.generation for a in eco.agents)
        coop_count = sum(1 for a in eco.agents if a.genome.cooperation > 0.6)
        pred_count = sum(1 for a in eco.agents if a.genome.aggression > 0.6)
    else:
        avg_coop = avg_agg = pop = max_gen = coop_count = pred_count = 0
    
    return {
        "label": label,
        "avg_cooperation": avg_coop,
        "avg_aggression": avg_agg,
        "population": pop,
        "max_generation": max_gen,
        "cooperators": coop_count,
        "predators": pred_count,
        "report": report,
    }


def main():
    print("=" * 70)
    print("  COOPERATION EXPERIMENT")
    print("  Can altruism evolve when it provides group benefits?")
    print("=" * 70)
    print()
    
    # Run multiple trials per condition for statistical robustness
    n_trials = 3
    baseline_results = []
    coop_results = []
    
    for trial in range(n_trials):
        seed = 1000 + trial
        print(f"  Trial {trial+1}/{n_trials}...", end=" ", flush=True)
        
        b = run_condition(f"baseline_{trial}", Ecosystem, seed)
        baseline_results.append(b)
        print(f"baseline done", end=" ", flush=True)
        
        c = run_condition(f"coop_{trial}", CooperativeEcosystem, seed)
        coop_results.append(c)
        print(f"cooperative done")
    
    # Analyze
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    
    def avg(results, key):
        vals = [r[key] for r in results]
        return sum(vals) / len(vals) if vals else 0
    
    print(f"\n  {'Metric':<25} {'Baseline':>12} {'Cooperative':>12} {'Δ':>10}")
    print(f"  {'─'*25} {'─'*12} {'─'*12} {'─'*10}")
    
    for key, label in [
        ("avg_cooperation", "Avg Cooperation"),
        ("avg_aggression", "Avg Aggression"),
        ("population", "Final Population"),
        ("max_generation", "Max Generation"),
        ("cooperators", "Cooperator Count"),
        ("predators", "Predator Count"),
    ]:
        b_avg = avg(baseline_results, key)
        c_avg = avg(coop_results, key)
        delta = c_avg - b_avg
        sign = "+" if delta > 0 else ""
        print(f"  {label:<25} {b_avg:>12.2f} {c_avg:>12.2f} {sign}{delta:>9.2f}")
    
    print()
    print("  INTERPRETATION:")
    b_coop = avg(baseline_results, "avg_cooperation")
    c_coop = avg(coop_results, "avg_cooperation")
    if c_coop > b_coop + 0.05:
        print("  ✓ COOPERATION EVOLVED MORE when group benefits exist!")
        print(f"    Cooperation rose from {b_coop:.3f} → {c_coop:.3f} (+{c_coop-b_coop:.3f})")
    elif c_coop < b_coop - 0.05:
        print("  ✗ Cooperation DECLINED even with group benefits")
        print(f"    Cooperation fell from {b_coop:.3f} → {c_coop:.3f} ({c_coop-b_coop:.3f})")
        print("    → Defectors may exploit cooperative groups (free rider problem)")
    else:
        print("  ≈ No significant difference — cooperation neither helped nor hurt")
    
    b_agg = avg(baseline_results, "avg_aggression")
    c_agg = avg(coop_results, "avg_aggression")
    if c_agg < b_agg - 0.05:
        print(f"  ✓ Aggression decreased with cooperation benefits ({b_agg:.3f} → {c_agg:.3f})")
    
    # Print one detailed report from each condition
    print()
    print("=" * 70)
    print("  DETAILED REPORT — BASELINE (trial 0)")
    print("=" * 70)
    print(baseline_results[0]["report"])
    print()
    print("=" * 70)
    print("  DETAILED REPORT — COOPERATIVE (trial 0)")
    print("=" * 70)
    print(coop_results[0]["report"])


if __name__ == "__main__":
    main()