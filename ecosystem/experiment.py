"""
Ecosystem Experiments — Searching for self-sustaining worlds.

Run multiple parameter configurations and find which ones
produce stable, persistent ecosystems vs. collapse.
"""

from world import World
import sys

def run_experiment(params: dict, label: str = "") -> dict:
    """Run one world with given parameters and return results."""
    w = World(seed=params.get('seed', 42))
    w.seed_world(
        n_grazers=params.get('n_grazers', 30),
        n_hunters=params.get('n_hunters', 5),
        n_fungus=params.get('n_fungus', 10),
        n_plants=params.get('n_plants', 200),
    )
    
    # Override regrowth rate if specified
    original_regrow = w._regrow_plants
    regrow_rate = params.get('regrow_rate', 0.3)
    regrow_amount = params.get('regrow_amount', (1, 5))
    
    def custom_regrow():
        if w.rng.random() < regrow_rate:
            for _ in range(w.rng.randint(*regrow_amount)):
                w.plants.append(type(w.plants[0])(
                    x=w.rng.uniform(0, w.width),
                    y=w.rng.uniform(0, w.height),
                    energy=w.rng.uniform(5, 15)
                ) if w.plants else None)
                # Safer version
                from world import Plant
                w.plants.append(Plant(
                    x=w.rng.uniform(0, w.width),
                    y=w.rng.uniform(0, w.height),
                    energy=w.rng.uniform(5, 15)
                ))
    
    w._regrow_plants = custom_regrow
    
    summary = w.run(ticks=params.get('ticks', 500))
    summary['label'] = label
    summary['params'] = params
    return summary


def search_for_stability():
    """Try many parameter combinations. Find which worlds survive."""
    experiments = [
        # Baseline — the world that collapsed
        {'label': 'baseline', 'params': {
            'n_grazers': 30, 'n_hunters': 5, 'n_fungus': 10,
            'n_plants': 200, 'regrow_rate': 0.3, 'regrow_amount': (1, 5)
        }},
        # More plants, faster regrowth
        {'label': 'lush_world', 'params': {
            'n_grazers': 30, 'n_hunters': 5, 'n_fungus': 10,
            'n_plants': 500, 'regrow_rate': 0.6, 'regrow_amount': (3, 8)
        }},
        # Fewer grazers, more balance
        {'label': 'sparse_grazers', 'params': {
            'n_grazers': 10, 'n_hunters': 3, 'n_fungus': 10,
            'n_plants': 300, 'regrow_rate': 0.5, 'regrow_amount': (2, 6)
        }},
        # No hunters — does the grazer-plant system stabilize alone?
        {'label': 'no_predators', 'params': {
            'n_grazers': 20, 'n_hunters': 0, 'n_fungus': 5,
            'n_plants': 300, 'regrow_rate': 0.5, 'regrow_amount': (2, 6)
        }},
        # Abundant everything
        {'label': 'eden', 'params': {
            'n_grazers': 15, 'n_hunters': 3, 'n_fungus': 15,
            'n_plants': 500, 'regrow_rate': 0.8, 'regrow_amount': (5, 12)
        }},
        # Harsh world — scarce resources
        {'label': 'desert', 'params': {
            'n_grazers': 5, 'n_hunters': 2, 'n_fungus': 5,
            'n_plants': 50, 'regrow_rate': 0.2, 'regrow_amount': (1, 2)
        }},
        # Long run — 1000 ticks
        {'label': 'long_eden', 'params': {
            'n_grazers': 15, 'n_hunters': 3, 'n_fungus': 15,
            'n_plants': 500, 'regrow_rate': 0.8, 'regrow_amount': (5, 12),
            'ticks': 1000
        }},
    ]
    
    print("=" * 70)
    print("ECOSYSTEM EXPERIMENT SUITE")
    print("Searching for self-sustaining worlds...")
    print("=" * 70)
    
    results = []
    for exp in experiments:
        label = exp['label']
        params = exp['params']
        print(f"\n--- {label} ---")
        
        result = run_experiment(params, label)
        results.append(result)
        
        fc = result['final_census']
        survived = sum(1 for sp in ['grazer', 'hunter', 'fungus'] if fc.get(sp, 0) > 0)
        extinct = [sp for sp in ['grazer', 'hunter', 'fungus'] if fc.get(sp, 0) == 0]
        
        status = "🌍 ALIVE" if survived == 3 else f"💀 {3-survived} EXTINCT"
        if params.get('n_hunters', 0) == 0:
            # Don't count hunters as extinct if we didn't start with any
            alive_species = [sp for sp in ['grazer', 'fungus'] if fc.get(sp, 0) > 0]
            status = "🌍 ALIVE" if len(alive_species) == 2 else f"💀 COLLAPSE"
        
        print(f"  Status: {status}")
        print(f"  Ticks: {result['ticks_elapsed']}")
        print(f"  Final: grazer={fc.get('grazer',0)}, hunter={fc.get('hunter',0)}, fungus={fc.get('fungus',0)}, plants={fc.get('plants',0)}")
        print(f"  Born: {result['total_born']}, Died: {result['total_died']}")
        print(f"  Lineages surviving: {result['surviving_lineages']}")
        print(f"  Grazer volatility: {result['grazer_volatility']}")
        if extinct and params.get('n_hunters', 0) > 0:
            print(f"  Extinctions: {', '.join(extinct)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: Which worlds survived?")
    print("=" * 70)
    for r in results:
        fc = r['final_census']
        alive = sum(1 for sp in ['grazer', 'hunter', 'fungus'] 
                    if fc.get(sp, 0) > 0 and r['params'].get(f'n_{sp}s', r['params'].get('n_hunters', 1)) > 0)
        total_pop = fc.get('grazer', 0) + fc.get('hunter', 0) + fc.get('fungus', 0)
        vol = r['grazer_volatility']
        stability = "stable" if vol < 50 else "volatile" if vol < 200 else "chaotic"
        print(f"  {r['label']:20s} | pop={total_pop:4d} | {stability:8s} | lineages={r['surviving_lineages']}")


if __name__ == "__main__":
    search_for_stability()