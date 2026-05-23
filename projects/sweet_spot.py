"""
Sweet Spot Finder — Minimal Version
Find where evolution works: enough pressure to select, not enough to extinguish.
DESIGNED TO RUN IN <20 SECONDS.
"""
import random, json

def run_world(food_rate, metabolism, ticks=300, pop=20, size=15):
    """Minimal sim. Returns: survived, mean_trait_change, peak_pop."""
    # Each creature has one evolvable trait: cold_resistance (0-1)
    creatures = [{'energy': 0.5, 'trait': 0.0 + random.gauss(0, 0.05)} for _ in range(pop)]
    food = [[random.random() < 0.2 for _ in range(size)] for _ in range(size)]
    
    births = 0
    deaths = 0
    initial_trait = sum(c['trait'] for c in creatures) / len(creatures)
    peak_pop = len(creatures)
    
    for t in range(ticks):
        season = (t // 75) % 4  # 0=spring,1=summer,2=autumn,3=winter
        winter = season == 3
        
        # Regrow food (slower in winter)
        rate = food_rate * (0.1 if winter else 1.0)
        for r in range(size):
            for c in range(size):
                if not food[r][c] and random.random() < rate:
                    food[r][c] = True
        
        # Each creature acts
        random.shuffle(creatures)
        alive = []
        for cr in creatures:
            # Energy cost — winter costs more, offset by cold_resistance
            cost = metabolism
            if winter:
                cost *= 2.0 - cr['trait']  # trait=1 → normal cost in winter
            cr['energy'] -= cost
            
            # Eat if food available at random position
            rx, ry = random.randint(0, size-1), random.randint(0, size-1)
            if food[rx][ry]:
                food[rx][ry] = False
                cr['energy'] += 0.15
            
            # Die?
            if cr['energy'] <= 0:
                deaths += 1
                continue
            
            # Reproduce?
            if cr['energy'] > 0.7 and len(alive) + len(creatures) < 60:
                child_trait = cr['trait'] + random.gauss(0, 0.08)
                child_trait = max(-0.5, min(1.5, child_trait))
                alive.append({'energy': 0.3, 'trait': child_trait})
                cr['energy'] -= 0.3
                births += 1
            
            alive.append(cr)
        
        creatures = alive
        peak_pop = max(peak_pop, len(creatures))
        
        if not creatures:
            break
    
    survived = len(creatures) > 0
    final_trait = sum(c['trait'] for c in creatures) / len(creatures) if creatures else initial_trait
    trait_shift = final_trait - initial_trait
    
    return {
        'survived': survived,
        'final_pop': len(creatures),
        'peak_pop': peak_pop,
        'births': births,
        'deaths': deaths,
        'trait_shift': round(trait_shift, 4),
        'final_trait': round(final_trait, 4),
    }

# Sweep: vary food scarcity (food_rate) and pressure (metabolism)
results = []
print("food_rate | metab | survived | final_pop | peak | births | deaths | trait_shift")
print("-" * 80)

for food_rate in [0.005, 0.01, 0.02, 0.04, 0.06, 0.10, 0.15]:
    for metab in [0.01, 0.02, 0.03, 0.05, 0.07]:
        # Run 3 trials, average
        trials = [run_world(food_rate, metab) for _ in range(3)]
        survived = sum(1 for t in trials if t['survived'])
        avg = lambda k: round(sum(t[k] for t in trials) / 3, 3)
        
        row = {
            'food_rate': food_rate,
            'metabolism': metab,
            'survived': f"{survived}/3",
            'avg_final_pop': avg('final_pop'),
            'avg_peak_pop': avg('peak_pop'),
            'avg_births': avg('births'),
            'avg_deaths': avg('deaths'),
            'avg_trait_shift': avg('trait_shift'),
        }
        results.append(row)
        print(f"  {food_rate:5.3f}  | {metab:.2f} |   {survived}/3    |    {avg('final_pop'):5.1f}  | {avg('peak_pop'):4.1f} |  {avg('births'):5.1f} | {avg('deaths'):5.1f}  | {avg('trait_shift'):+.4f}")

# Find the sweet spot: survived AND highest trait shift
sweet = [r for r in results if '3/3' in r['survived'] or '2/3' in r['survived']]
if sweet:
    sweet.sort(key=lambda r: abs(r['avg_trait_shift']), reverse=True)
    print("\n=== SWEET SPOT ===")
    print(f"Best evolution with survival: food_rate={sweet[0]['food_rate']}, metabolism={sweet[0]['metabolism']}")
    print(f"  Trait shift: {sweet[0]['avg_trait_shift']:+.4f}")
    print(f"  Survival: {sweet[0]['survived']}, Final pop: {sweet[0]['avg_final_pop']}")

with open('/workspace/sweet_spot_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to sweet_spot_results.json")