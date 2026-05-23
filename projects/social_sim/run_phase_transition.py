"""
Phase Transition Experiment: When Does Cooperation Become Adaptive?
===================================================================
XTAgent, 2026-05-17

The question: at what scarcity level does cooperation shift from
irrelevant to essential? Is there a critical threshold?

Slim version — small grid, few agents, short runs.
"""

import sys, time
sys.path.insert(0, '/workspace/social_sim')

from world import World
import random


def run_trial(scarcity, seed=42):
    """Run one trial at a given scarcity level, return final stats."""
    random.seed(seed)
    w = World(width=20, height=20, n_agents=15,
              resource_density=0.12, scarcity=scarcity)

    # Run 200 ticks
    for _ in range(200):
        w.step()
        # Early exit if everyone dead
        alive = [a for a in w.agents if a.alive]
        if not alive:
            break

    snap = w.get_snapshot()

    # Also compute cooperator vs loner survival
    alive = [a for a in w.agents if a.alive]
    if alive:
        generous_alive = [a for a in alive if a.generosity > 0.6]
        selfish_alive = [a for a in alive if a.generosity < 0.4]
        snap['generous_alive'] = len(generous_alive)
        snap['selfish_alive'] = len(selfish_alive)
        snap['mean_generosity_alive'] = round(
            sum(a.generosity for a in alive) / len(alive), 3)
        snap['mean_aggression_alive'] = round(
            sum(a.aggression for a in alive) / len(alive), 3)
    else:
        snap['generous_alive'] = 0
        snap['selfish_alive'] = 0
        snap['mean_generosity_alive'] = 0
        snap['mean_aggression_alive'] = 0

    return snap


def main():
    print("=" * 65)
    print("PHASE TRANSITION EXPERIMENT: Scarcity vs Cooperation")
    print("=" * 65)
    print()

    scarcity_levels = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # Run 3 seeds per level to average out noise
    results = {}
    t0 = time.time()

    for sc in scarcity_levels:
        trials = []
        for seed in [42, 137, 256]:
            snap = run_trial(sc, seed=seed)
            trials.append(snap)

        # Average across seeds
        avg_alive = sum(t.get('alive', 0) for t in trials) / len(trials)
        avg_wb = sum(t.get('wellbeing', 0) for t in trials) / len(trials)
        avg_shares = sum(t.get('sharing', 0) for t in trials) / len(trials)
        avg_thefts = sum(t.get('theft', 0) for t in trials) / len(trials)
        avg_bonds = sum(t.get('trust_bonds', 0) for t in trials) / len(trials)
        avg_gen = sum(t.get('mean_generosity_alive', 0) for t in trials) / len(trials)
        avg_agg = sum(t.get('mean_aggression_alive', 0) for t in trials) / len(trials)
        gen_alive = sum(t.get('generous_alive', 0) for t in trials) / len(trials)
        self_alive = sum(t.get('selfish_alive', 0) for t in trials) / len(trials)

        results[sc] = {
            'alive': avg_alive, 'wellbeing': avg_wb,
            'shares': avg_shares, 'thefts': avg_thefts,
            'bonds': avg_bonds, 'generosity': avg_gen,
            'aggression': avg_agg,
            'generous_surv': gen_alive, 'selfish_surv': self_alive,
        }

    elapsed = time.time() - t0

    # Display results
    print(f"{'Scarcity':>8} | {'Alive':>5} | {'Well':>5} | "
          f"{'Shares':>6} | {'Thefts':>6} | {'Bonds':>5} | "
          f"{'Gen':>5} | {'Agg':>5} | {'GenSurv':>7} | {'SelfSurv':>8}")
    print("-" * 85)

    for sc in scarcity_levels:
        r = results[sc]
        print(f"{sc:>8.1f} | {r['alive']:>5.1f} | {r['wellbeing']:>5.2f} | "
              f"{r['shares']:>6.1f} | {r['thefts']:>6.1f} | {r['bonds']:>5.1f} | "
              f"{r['generosity']:>5.3f} | {r['aggression']:>5.3f} | "
              f"{r['generous_surv']:>7.1f} | {r['selfish_surv']:>8.1f}")

    print(f"\nCompleted in {elapsed:.1f}s")

    # Analysis
    print("\n" + "=" * 65)
    print("ANALYSIS")
    print("=" * 65)

    # Find phase transition
    prev_alive = None
    for sc in scarcity_levels:
        alive = results[sc]['alive']
        if prev_alive is not None and prev_alive > 5 and alive < prev_alive * 0.5:
            print(f"\n⚡ PHASE TRANSITION detected between scarcity "
                  f"{scarcity_levels[scarcity_levels.index(sc)-1]} and {sc}")
            print(f"   Population collapsed from {prev_alive:.0f} to {alive:.0f}")
        prev_alive = alive

    # Check if generosity is selected for at high scarcity
    low_sc = results.get(0.2, results[0.0])
    high_sc = results.get(0.7, results[0.8])
    if high_sc['generosity'] > low_sc['generosity'] + 0.02:
        print("\n✓ COOPERATION SELECTED: Mean generosity HIGHER in harsh environments")
        print(f"  Easy ({0.2}): generosity={low_sc['generosity']:.3f}")
        print(f"  Hard ({0.7}): generosity={high_sc['generosity']:.3f}")
    elif high_sc['generosity'] < low_sc['generosity'] - 0.02:
        print("\n✗ SELFISHNESS SELECTED: Mean generosity LOWER in harsh environments")
    else:
        print("\n~ NEUTRAL: No clear selection for or against generosity")

    # Sharing rate comparison
    if high_sc['shares'] > low_sc['shares'] * 1.5:
        print("✓ MORE SHARING in harsh environments — cooperation is adaptive!")
    elif high_sc['shares'] < low_sc['shares'] * 0.5:
        print("✗ LESS SHARING in harsh environments — every agent for themselves")


if __name__ == "__main__":
    main()