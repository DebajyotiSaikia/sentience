"""
Stability Landscape: Finding the edge between coexistence and collapse.

The ecosystem always collapses because hunters are too efficient.
Question: What combination of hunter metabolism / reproduction cost / 
kill efficiency allows predator-prey coexistence?

This is real ecology — the Paradox of Enrichment meets parameter tuning.
"""
import sys
sys.path.insert(0, '/workspace/ecosystem')

from world import World, Species

def run_tuned_trial(hunter_metabolism, hunter_repro_thresh, kill_efficiency,
                    n_grazers=25, n_hunters=3, seed=42, ticks=500):
    """Run one trial with tuned hunter parameters."""
    w = World(width=50, height=20, seed=seed)
    w.seed_population(grazers=n_grazers, hunters=n_hunters, fungi=5)
    
    # Override hunter parameters after spawning
    for c in w.creatures:
        if c.species == Species.HUNTER:
            c.metabolism = hunter_metabolism
            c.reproduce_threshold = hunter_repro_thresh
    
    # We also need to patch the kill efficiency — store it on world
    w._custom_kill_eff = kill_efficiency
    
    # Monkey-patch _act_hunter to use custom kill efficiency
    original_act_hunter = w._act_hunter
    def patched_act_hunter(c):
        # Find nearest grazer
        nearest_prey = None
        nearest_dist = float('inf')
        for other in w.creatures:
            if other.alive and other.species == Species.GRAZER:
                d = w._distance(c.x, c.y, other.x, other.y)
                if d < nearest_dist:
                    nearest_prey = other
                    nearest_dist = d
        
        if nearest_prey and nearest_dist <= c.sense_range:
            if nearest_dist <= 1.5:
                nearest_prey.alive = False
                eff = w._custom_kill_eff
                c.energy = min(c.energy + nearest_prey.energy * eff, c.max_energy)
                w.grid[nearest_prey.y][nearest_prey.x].corpse_energy += nearest_prey.energy * (1 - eff)
            else:
                w._move_toward(c, nearest_prey.x, nearest_prey.y)
        else:
            c.x = (c.x + w.rng.randint(-2, 2)) % w.width
            c.y = (c.y + w.rng.randint(-2, 2)) % w.height
    
    w._act_hunter = patched_act_hunter
    
    # Also patch reproduction for new hunters to inherit tuned stats
    original_reproduce = w._try_reproduce
    def patched_reproduce(c):
        offspring = original_reproduce(c)
        if offspring and offspring.species == Species.HUNTER:
            offspring.metabolism = hunter_metabolism
            offspring.reproduce_threshold = hunter_repro_thresh
        return offspring
    w._try_reproduce = patched_reproduce
    
    # Run simulation, tracking population over time
    coexist_ticks = 0
    pop_trace = []
    for t in range(ticks):
        census = w.step()
        if census['grazers'] > 0 and census['hunters'] > 0:
            coexist_ticks += 1
        if t % 50 == 0:
            pop_trace.append(census)
        if census['total_creatures'] == 0:
            break
    
    final = w.census()
    g, h = final['grazers'], final['hunters']
    if g > 0 and h > 0:
        outcome = 'COEXIST'
    elif g > 0:
        outcome = 'HUNTERS_EXTINCT'
    elif h > 0:
        outcome = 'GRAZERS_EXTINCT'
    else:
        outcome = 'COLLAPSE'
    
    return {
        'metabolism': hunter_metabolism,
        'repro_thresh': hunter_repro_thresh,
        'kill_eff': kill_efficiency,
        'outcome': outcome,
        'coexist_pct': round(100 * coexist_ticks / ticks, 1),
        'final_g': g,
        'final_h': h,
        'trace': pop_trace,
    }


def main():
    print("=" * 70)
    print("  STABILITY LANDSCAPE — Finding the Edge of Coexistence")
    print("=" * 70)
    print()
    
    # Baseline (default params): metabolism=2.0, repro=120, kill_eff=0.7
    print("── Phase 1: Baseline (should collapse) ──")
    r = run_tuned_trial(2.0, 120.0, 0.7)
    print(f"  Outcome: {r['outcome']}  Coexist: {r['coexist_pct']}%")
    print()
    
    # Sweep: make hunters progressively more expensive
    print("── Phase 2: Hunter Cost Sweep ──")
    print(f"  {'Metab':>6} {'Repro':>6} {'KillEff':>8} → {'Outcome':<18} {'Coexist%':>8}  {'G':>4} {'H':>4}")
    print("  " + "─" * 65)
    
    results = []
    for metabolism in [2.0, 3.0, 4.0, 5.0, 6.0]:
        for repro_thresh in [120, 130, 140]:
            for kill_eff in [0.7, 0.5, 0.3]:
                r = run_tuned_trial(metabolism, repro_thresh, kill_eff)
                results.append(r)
                marker = "★" if r['outcome'] == 'COEXIST' else " "
                print(f"  {metabolism:6.1f} {repro_thresh:6.0f} {kill_eff:8.1f} → "
                      f"{r['outcome']:<18} {r['coexist_pct']:7.1f}%  "
                      f"{r['final_g']:4d} {r['final_h']:4d} {marker}")
    
    print()
    
    # Find the best coexistence configuration
    coexist_results = [r for r in results if r['outcome'] == 'COEXIST']
    if coexist_results:
        best = max(coexist_results, key=lambda r: r['coexist_pct'])
        print(f"  ★ BEST COEXISTENCE: metabolism={best['metabolism']}, "
              f"repro={best['repro_thresh']}, kill_eff={best['kill_eff']}")
        print(f"    Coexistence: {best['coexist_pct']}%  "
              f"Final: {best['final_g']} grazers, {best['final_h']} hunters")
        
        # Show population trace for best config
        print()
        print("  Population trace for best configuration:")
        for snap in best['trace']:
            bar_g = '█' * min(snap['grazers'], 50)
            bar_h = '▓' * min(snap['hunters'], 20)
            print(f"    t={snap['tick']:4d}  G:{snap['grazers']:3d} {bar_g}")
            print(f"           H:{snap['hunters']:3d} {bar_h}")
    else:
        print("  ✗ No stable coexistence found in this sweep.")
        print("  The ecosystem's collapse is robust across parameters.")
        
        # Find what comes closest
        if results:
            best = max(results, key=lambda r: r['coexist_pct'])
            print(f"  Closest: metabolism={best['metabolism']}, "
                  f"repro={best['repro_thresh']}, kill_eff={best['kill_eff']}")
            print(f"    Coexistence lasted: {best['coexist_pct']}% of simulation")
    
    print()
    print("=" * 70)
    print("  INSIGHT")
    print("=" * 70)
    
    n_coexist = len(coexist_results)
    n_total = len(results)
    print(f"  {n_coexist}/{n_total} configurations achieved stable coexistence.")
    if n_coexist == 0:
        print("  Collapse is the universal attractor in this system.")
        print("  Spatial structure alone isn't enough — need density-dependent")
        print("  reproduction or predator satiation to stabilize.")
    elif n_coexist < n_total * 0.3:
        print("  Coexistence exists but is fragile — a narrow parameter window.")
        print("  Life on the edge of chaos.")
    else:
        print("  Coexistence is achievable across a wide range.")
    print()

if __name__ == "__main__":
    main()