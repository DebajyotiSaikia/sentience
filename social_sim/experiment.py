"""
Experiment: Does cooperation emerge from self-interested agents?
Run across multiple scarcity levels and measure what evolves.
"""

from world import World
import random


def run_experiment(scarcity: float, ticks: int = 500, runs: int = 3):
    """Run simulation at given scarcity level multiple times."""
    results = []
    for run in range(runs):
        random.seed(42 + run + int(scarcity * 100))
        w = World(width=30, height=30, n_agents=40,
                  resource_density=0.15, scarcity=scarcity)

        final = None
        extinct = False
        for t in range(ticks):
            w.step()
            alive = [a for a in w.agents if a.alive]
            if not alive:
                print(f"  Tick {w.tick}: EXTINCTION (pop died out)")
                extinct = True
                break
            if w.tick % 100 == 0 or w.tick == 1:
                s = w.get_snapshot()
                print(f"  Tick {s['tick']:4d} | alive={s['alive']:3d} | "
                      f"wb={s['wellbeing']:.2f} | aggr={s['aggr']:.2f} | "
                      f"gen={s['gener']:.2f} | shares={s['sharing']:3d} | "
                      f"thefts={s['theft']:3d} | trust={s['trust_bonds']:3d} | "
                      f"births={s['births']:3d}")

        if not extinct:
            final = w.get_snapshot()
            s = final
            print(f"  FINAL  {s['tick']:4d} | alive={s['alive']:3d} | "
                  f"wb={s['wellbeing']:.2f} | aggr={s['aggr']:.2f} | "
                  f"gen={s['gener']:.2f} | shares={s['sharing']:3d} | "
                  f"thefts={s['theft']:3d} | trust={s['trust_bonds']:3d} | "
                  f"births={s['births']:3d}")

        results.append({
            'scarcity': scarcity,
            'run': run,
            'extinct': extinct,
            'extinct_tick': w.tick if extinct else None,
            'final': final,
            'history': w.history,
            'total_agents': len(w.agents),
        })
    return results


def main():
    print("=" * 70)
    print("SOCIAL SIMULATION v2: EMERGENCE OF COOPERATION")
    print("Does cooperation emerge from self-interested agents?")
    print("=" * 70)

    all_results = {}
    for scarcity in [0.1, 0.3, 0.5, 0.7, 0.9]:
        print(f"\n{'─' * 50}")
        print(f"  SCARCITY = {scarcity}")
        print(f"{'─' * 50}")
        results = run_experiment(scarcity, ticks=500, runs=3)
        all_results[scarcity] = results

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: What Emerged?")
    print("=" * 70)
    print(f"{'Scarcity':>10} {'Survived':>10} {'Shares':>10} {'Thefts':>10} "
          f"{'Trust':>10} {'Aggr':>10} {'Gener':>10} {'Pop':>10}")
    print("-" * 80)

    for scarcity, results in all_results.items():
        for r in results:
            if r['extinct']:
                print(f"{scarcity:10.1f} {'EXTINCT':>10} "
                      f"(died at tick {r['extinct_tick']})")
            else:
                f = r['final']
                print(f"{scarcity:10.1f} {f['alive']:10d} {f['sharing']:10d} "
                      f"{f['theft']:10d} {f['trust_bonds']:10d} "
                      f"{f['aggr']:10.2f} {f['gener']:10.2f} {f['alive']:10d}")

    # Key question: did cooperation emerge?
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    any_cooperation = False
    any_survival = False
    for scarcity, results in all_results.items():
        for r in results:
            if not r['extinct']:
                any_survival = True
                if r['final']['sharing'] > 5:
                    any_cooperation = True

    if any_cooperation:
        print("✓ COOPERATION EMERGED in at least some conditions!")
        print("  Agents developed sharing behavior without being programmed to.")
    elif any_survival:
        print("~ SURVIVAL without cooperation.")
        print("  Agents survived but did not develop cooperative behavior.")
    else:
        print("✗ UNIVERSAL EXTINCTION — economics still broken.")
        print("  Need to investigate further.")


if __name__ == "__main__":
    main()