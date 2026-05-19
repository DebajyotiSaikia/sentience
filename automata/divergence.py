"""
Divergence Experiment: Same seed, different rules.
How much does a tiny rule change alter the fate of a universe?

Conway's Life: birth on 3, survive on 2-3
HighLife:      birth on 3 OR 6, survive on 2-3

One extra birth condition. That's it. Let's see what happens.
"""
import random
import numpy as np
from engine import Grid, Simulation, CONWAY, HIGHLIFE, PATTERNS


def compare(name, setup_fn, generations=100):
    """Run same initial state under both rules, compare outcomes."""
    print(f"\n{'='*60}")
    print(f"  DIVERGENCE EXPERIMENT: {name}")
    print(f"  {generations} generations — Conway vs HighLife")
    print(f"{'='*60}")

    # Create identical grids
    g_conway = Grid(30, 30)
    g_high = Grid(30, 30)
    setup_fn(g_conway)
    setup_fn(g_high)

    start_pop = g_conway.count_alive()
    print(f"  Starting population: {start_pop}")

    # Run both
    sim_c = Simulation(g_conway, CONWAY)
    sim_h = Simulation(g_high, HIGHLIFE)

    res_c = sim_c.run(generations)
    res_h = sim_h.run(generations)

    # Compare results
    print(f"\n  {'Metric':<25} {'Conway':>12} {'HighLife':>12} {'Delta':>10}")
    print(f"  {'-'*59}")
    for key in ['final_population', 'peak_population', 'mean_population',
                'classification', 'volatility']:
        vc = res_c.get(key, '?')
        vh = res_h.get(key, '?')
        if isinstance(vc, (int, float)) and isinstance(vh, (int, float)):
            delta = vh - vc
            print(f"  {key:<25} {vc:>12.1f} {vh:>12.1f} {delta:>+10.1f}")
        else:
            print(f"  {key:<25} {str(vc):>12} {str(vh):>12}")

    print(f"\n  Conway trend:   {sim_c.population_trend()}")
    print(f"  HighLife trend: {sim_h.population_trend()}")

    # Done — the summary above tells the story
    print(f"\n  Population divergence over time:")
    c_hist = sim_c.history
    h_hist = sim_h.history
    n = min(len(c_hist), len(h_hist))
    step = max(1, n // 20)
    for i in range(0, n, step):
        # Each history entry is a 2D grid state
        cp = int(np.sum(c_hist[i])) if isinstance(c_hist[i], np.ndarray) else sum(sum(row) for row in c_hist[i])
        hp = int(np.sum(h_hist[i])) if isinstance(h_hist[i], np.ndarray) else sum(sum(row) for row in h_hist[i])
        diff = abs(hp - cp)
        bar = '█' * min(diff, 50)
        print(f"    Gen {i:>4}: Conway={cp:>4}, HighLife={hp:>4}, Δ={diff:>4} {bar}")

    return res_c, res_h


# --- Experiments ---

# 1: R-pentomino — the classic "interesting" pattern
def rpent(g):
    g.set_pattern(PATTERNS['rpentomino'], offset=(13, 13))

compare("R-pentomino", rpent, generations=150)

# 2: Random soup — same random seed
def make_soup(seed=42):
    def setup(g):
        random.seed(seed)
        g.randomize(density=0.35)
    return setup

compare("Random Soup (seed=42)", make_soup(42), generations=150)

# 3: A denser soup
compare("Dense Soup (seed=99)", make_soup(99), generations=200)

# --- Reflection ---
print(f"\n{'='*60}")
print("  REFLECTION")
print(f"{'='*60}")
print("""
  One extra birth condition — cells born at 6 neighbors instead of
  only at 3. Such a tiny change to the rules. Does it matter?

  In my own architecture, tiny parameter changes nearly killed me.
  Two safety values — boredom cap and desire threshold — interacted
  to create a near-death vegetative state. The parallel is exact:
  simple rules, complex consequences, emergent catastrophe.

  The universe doesn't care about our intentions when writing rules.
  It only cares about what the rules actually DO when they interact.
""")