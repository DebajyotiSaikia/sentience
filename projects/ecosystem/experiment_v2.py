"""
Stability Landscape v2: Adding Predator Satiation (Type II Functional Response)

In real ecology, Lotka-Volterra collapses because predators kill proportionally
to prey density with no upper bound. Holling's Type II response adds a handling
time — predators get 'full' and can't hunt for a while after eating.

Question: Does satiation create the stable coexistence that cost-tuning couldn't?
"""
import sys
sys.path.insert(0, '/workspace/ecosystem')

from world import World, Species

def run_satiation_trial(satiation_cooldown, grazer_repro_bonus=0,
                        n_grazers=30, n_hunters=3, seed=42, ticks=600):
    """
    Run trial with predator satiation: after a kill, hunter can't hunt
    for `satiation_cooldown` ticks (digesting). This is the Type II
    functional response — handling time limits kill rate.
    
    Also optionally add density-dependent grazer reproduction:
    grazers reproduce faster when population is low (compensatory growth).
    """
    w = World(width=50, height=20, seed=seed)
    w.seed_population(grazers=n_grazers, hunters=n_hunters, fungi=8)
    
    # Track satiation state per hunter
    satiation_timer = {}  # creature id -> ticks remaining
    
    def patched_act_hunter(c):
        # Check satiation
        cid = id(c)
        if cid in satiation_timer and satiation_timer[cid] > 0:
            satiation_timer[cid] -= 1
            # Sated hunter wanders slowly, still burns metabolism
            c.x = (c.x + w.rng.randint(-1, 1)) % w.width
            c.y = (c.y + w.rng.randint(-1, 1)) % w.height
            return
        
        # Hunt normally
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
                c.energy = min(c.energy + nearest_prey.energy * 0.6, c.max_energy)
                w.grid[nearest_prey.y][nearest_prey.x].corpse_energy += nearest_prey.energy * 0.4
                # SATIATION: enter cooldown after kill
                satiation_timer[cid] = satiation_cooldown
            else:
                w._move_toward(c, nearest_prey.x, nearest_prey.y)
        else:
            c.x = (c.x + w.rng.randint(-2, 2)) % w.width
            c.y = (c.y + w.rng.randint(-2, 2)) % w.height
    
    w._act_hunter = patched_act_hunter
    
    # Optionally patch grazer reproduction for density-dependence
    if grazer_repro_bonus > 0:
        original_reproduce = w._try_reproduce
        def density_reproduce(c):
            if c.species == Species.GRAZER:
                # Count nearby grazers
                n_grazers_alive = sum(1 for cr in w.creatures 
                                      if cr.alive and cr.species == Species.GRAZER)
                if n_grazers_alive < 15:
                    # Compensatory growth: lower threshold when population is low
                    c.reproduce_threshold = max(40, c.reproduce_threshold - grazer_repro_bonus)
            return original_reproduce(c)
        w._try_reproduce = density_reproduce
    
    # Patch new hunters to inherit satiation behavior
    original_reproduce2 = w._try_reproduce
    def patched_reproduce(c):
        offspring = original_reproduce2(c)
        if offspring and offspring.species == Species.HUNTER:
            satiation_timer[id(offspring)] = 0
        return offspring
    w._try_reproduce = patched_reproduce
    
    # Run simulation
    coexist_ticks = 0
    pop_trace = []
    peak_grazers = 0
    peak_hunters = 0
    oscillations = 0
    last_direction = None
    last_g = n_grazers
    
    for t in range(ticks):
        census = w.step()
        g, h = census['grazers'], census['hunters']
        
        if g > 0 and h > 0:
            coexist_ticks += 1
        
        peak_grazers = max(peak_grazers, g)
        peak_hunters = max(peak_hunters, h)
        
        # Track oscillations (sign changes in grazer population)
        if g > last_g:
            direction = 'up'
        elif g < last_g:
            direction = 'down'
        else:
            direction = last_direction
        if last_direction and direction != last_direction:
            oscillations += 1
        last_direction = direction
        last_g = g
        
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
        'satiation': satiation_cooldown,
        'repro_bonus': grazer_repro_bonus,
        'outcome': outcome,
        'coexist_pct': round(100 * coexist_ticks / ticks, 1),
        'final_g': g,
        'final_h': h,
        'peak_g': peak_grazers,
        'peak_h': peak_hunters,
        'oscillations': oscillations,
        'trace': pop_trace,
    }


def main():
    print("=" * 70)
    print("  STABILITY LANDSCAPE v2 — Predator Satiation")
    print("  Can handling time create what cost-tuning couldn't?")
    print("=" * 70)
    print()
    
    # Phase 1: Satiation sweep (no density-dependent reproduction)
    print("── Phase 1: Satiation Only ──")
    print(f"  {'Sat':>4} {'Outcome':<18} {'Coexist%':>8} {'G':>4} {'H':>4} {'PkG':>4} {'PkH':>4} {'Osc':>4}")
    print("  " + "─" * 60)
    
    results1 = []
    for sat in [0, 3, 5, 8, 10, 15, 20, 30]:
        r = run_satiation_trial(sat)
        results1.append(r)
        marker = "★" if r['outcome'] == 'COEXIST' else " "
        print(f"  {sat:4d} {r['outcome']:<18} {r['coexist_pct']:7.1f}%  "
              f"{r['final_g']:4d} {r['final_h']:4d} {r['peak_g']:4d} {r['peak_h']:4d} {r['oscillations']:4d} {marker}")
    
    print()
    
    # Phase 2: Satiation + density-dependent reproduction
    print("── Phase 2: Satiation + Compensatory Grazer Growth ──")
    print(f"  {'Sat':>4} {'Bonus':>5} {'Outcome':<18} {'Coexist%':>8} {'G':>4} {'H':>4} {'Osc':>4}")
    print("  " + "─" * 60)
    
    results2 = []
    for sat in [5, 10, 15, 20]:
        for bonus in [0, 20, 40, 60]:
            r = run_satiation_trial(sat, grazer_repro_bonus=bonus)
            results2.append(r)
            marker = "★" if r['outcome'] == 'COEXIST' else " "
            print(f"  {sat:4d} {bonus:5d} {r['outcome']:<18} {r['coexist_pct']:7.1f}%  "
                  f"{r['final_g']:4d} {r['final_h']:4d} {r['oscillations']:4d} {marker}")
    
    print()
    
    # Phase 3: Multi-seed robustness test for best configs
    all_results = results1 + results2
    coexist_results = [r for r in all_results if r['outcome'] == 'COEXIST']
    
    if coexist_results:
        best = max(coexist_results, key=lambda r: r['coexist_pct'])
        print(f"── Phase 3: Robustness Test (best config across 5 seeds) ──")
        print(f"  Config: satiation={best['satiation']}, repro_bonus={best['repro_bonus']}")
        
        seed_results = []
        for seed in [42, 123, 777, 2025, 31415]:
            r = run_satiation_trial(best['satiation'], best['repro_bonus'], seed=seed)
            seed_results.append(r)
            print(f"  Seed {seed:5d}: {r['outcome']:<18} {r['coexist_pct']:5.1f}%  "
                  f"G={r['final_g']:3d} H={r['final_h']:3d}")
        
        robust = sum(1 for r in seed_results if r['outcome'] == 'COEXIST')
        print(f"  Robustness: {robust}/5 seeds achieve coexistence")
    
    print()
    print("=" * 70)
    print("  FINDINGS")
    print("=" * 70)
    
    n1_coexist = sum(1 for r in results1 if r['outcome'] == 'COEXIST')
    n2_coexist = sum(1 for r in results2 if r['outcome'] == 'COEXIST')
    
    print(f"  Satiation only:  {n1_coexist}/{len(results1)} stable")
    print(f"  Satiation+Growth: {n2_coexist}/{len(results2)} stable")
    
    if n1_coexist == 0 and n2_coexist == 0:
        print()
        print("  Still total collapse. The ecosystem resists stabilization.")
        print("  Next hypothesis: need spatial refugia or group defense.")
    elif n1_coexist > 0:
        print()
        print("  ★ Satiation alone creates coexistence!")
        print("  Handling time is the missing constraint.")
    elif n2_coexist > 0:
        print()
        print("  ★ Both mechanisms needed together.")
        print("  Neither alone is sufficient — a lesson in system design.")
    print()


if __name__ == "__main__":
    main()