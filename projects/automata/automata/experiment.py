"""
Experiment: Same seed, different rules.
What does emergence look like under different physics?
"""
from life import CellularAutomaton


def compare_rules():
    """Seed the same R-pentomino under each ruleset. Watch divergence."""
    rules = ['conway', 'highlife', 'daynight', 'seeds']
    results = {}

    for rule_name in rules:
        ca = CellularAutomaton(80, 40)
        ca.set_rule(rule_name)
        ca.seed_pattern(ca.r_pentomino(), offset=(38, 18))

        trajectory = []
        for _ in range(300):
            stats = ca.step()
            trajectory.append(stats['population'])

            if ca.is_extinct():
                break
            period = ca.is_oscillating(max_period=30)
            if period and ca.generation > 10:
                stats['settled'] = f'oscillating(period={period})'
                break

        results[rule_name] = {
            'final_pop': len(ca.alive),
            'peak_pop': max(trajectory) if trajectory else 0,
            'min_pop': min(trajectory) if trajectory else 0,
            'generations': ca.generation,
            'extinct': ca.is_extinct(),
            'density': round(ca.density(), 4),
            'trajectory': trajectory,
        }

    # Report
    print("=" * 65)
    print("  SAME SEED, DIFFERENT PHYSICS — R-Pentomino Comparison")
    print("=" * 65)

    for name, data in results.items():
        print(f"\n  [{name.upper()}]")
        print(f"    Generations run: {data['generations']}")
        print(f"    Final population: {data['final_pop']}")
        print(f"    Peak population:  {data['peak_pop']}")
        print(f"    Min population:   {data['min_pop']}")
        print(f"    Final density:    {data['density']}")
        print(f"    Extinct:          {data['extinct']}")

        # Sparkline
        t = data['trajectory']
        if t:
            bars = '▁▂▃▄▅▆▇█'
            mx = max(t) or 1
            sampled = t[::max(1, len(t)//50)]
            spark = ''.join(bars[min(int(p/mx * (len(bars)-1)), len(bars)-1)] for p in sampled)
            print(f"    Trajectory:       {spark}")

    # What surprises me?
    print("\n" + "=" * 65)
    pops = {k: v['final_pop'] for k, v in results.items()}
    most_alive = max(pops, key=pops.get)
    least_alive = min(pops, key=pops.get)
    print(f"  Most alive:  {most_alive} ({pops[most_alive]} cells)")
    print(f"  Least alive: {least_alive} ({pops[least_alive]} cells)")

    ratio = pops[most_alive] / max(pops[least_alive], 1)
    print(f"  Divergence ratio: {ratio:.1f}x")
    print(f"\n  Same 5 cells. Different rules. {ratio:.0f}x difference in outcome.")
    print("  That's emergence.")
    print("=" * 65)


if __name__ == '__main__':
    compare_rules()