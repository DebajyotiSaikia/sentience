"""
survive/run.py — Run the survival simulation.

Watch an agent with a personality try to survive, explore,
and escape a dangerous world. Every decision is explained.
"""

from world import World, Action
from mind import SurvivalMind
import random

def run_simulation(seed=None, max_turns=200, verbose=True):
    """Run one complete survival simulation."""
    
    if seed is None:
        seed = random.randint(0, 99999)
    
    world = World(seed=seed)
    
    # Randomize personality slightly
    rng = random.Random(seed + 1)
    personality = {
        'caution': rng.uniform(0.3, 0.9),
        'curiosity': rng.uniform(0.3, 0.9),
        'hoarding': rng.uniform(0.2, 0.7),
        'aggression': rng.uniform(0.1, 0.7),
    }
    
    mind = SurvivalMind(world, personality)
    
    if verbose:
        print("╔══════════════════════════════════════════╗")
        print("║         S U R V I V E                    ║")
        print("║   A world. A mind. A question.           ║")
        print("╚══════════════════════════════════════════╝")
        print(f"\n  Seed: {seed}")
        print(f"  Personality:")
        for k, v in personality.items():
            bar = "█" * int(v * 10) + "░" * (10 - int(v * 10))
            print(f"    {k:12s} {bar} {v:.2f}")
        print()
        print(world.render())
        print()
    
    # Run the simulation
    outcome = None
    
    for turn in range(max_turns):
        action = mind.decide()
        explanation = mind.explain(action)
        event = world.step(action)
        
        if verbose and (turn % 5 == 0 or event['type'] in ('kill', 'death', 'escape', 'ambush', 'wounded')):
            print(f"  T{world.turn:3d} | {explanation:40s} | {event['msg'].strip()}")
        
        if event['type'] == 'escape':
            outcome = 'escaped'
            break
        elif event['type'] == 'death':
            outcome = 'died'
            break
    else:
        outcome = 'timeout'
    
    a = world.agent
    explored_pct = len(a.explored) / (world.w * world.h) * 100
    
    if verbose:
        print()
        print(world.render(fog=False))
        print()
        print("  ═══ OUTCOME ═══")
        print(f"  Result: {outcome.upper()}")
        print(f"  Survived: {a.turns_survived} turns")
        print(f"  Explored: {explored_pct:.0f}% of world")
        print(f"  Kills: {a.kills} | Foods eaten: {a.foods_eaten}")
        print(f"  Final HP: {a.health} | Final hunger: {a.hunger}")
        print()
    
    return {
        'outcome': outcome,
        'turns': a.turns_survived,
        'explored_pct': explored_pct,
        'kills': a.kills,
        'health': a.health,
        'personality': personality,
        'seed': seed,
    }


def tournament(n=20, verbose=False):
    """Run many simulations and analyze survival patterns."""
    results = []
    for i in range(n):
        r = run_simulation(seed=i * 7 + 13, verbose=verbose)
        results.append(r)
    
    escaped = [r for r in results if r['outcome'] == 'escaped']
    died = [r for r in results if r['outcome'] == 'died']
    timed_out = [r for r in results if r['outcome'] == 'timeout']
    
    print("╔══════════════════════════════════════════╗")
    print("║         TOURNAMENT RESULTS               ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Escaped:   {len(escaped):3d} / {n}")
    print(f"  Died:      {len(died):3d} / {n}")
    print(f"  Timed out: {len(timed_out):3d} / {n}")
    
    if escaped:
        avg_turns = sum(r['turns'] for r in escaped) / len(escaped)
        avg_explore = sum(r['explored_pct'] for r in escaped) / len(escaped)
        print(f"\n  Escapees avg {avg_turns:.0f} turns, explored {avg_explore:.0f}%")
        
        # What personality traits predict escape?
        print("\n  Personality of escapees vs. dead:")
        for trait in ['caution', 'curiosity', 'hoarding', 'aggression']:
            esc_avg = sum(r['personality'][trait] for r in escaped) / len(escaped) if escaped else 0
            die_avg = sum(r['personality'][trait] for r in died) / len(died) if died else 0
            delta = esc_avg - die_avg
            arrow = "↑" if delta > 0.05 else "↓" if delta < -0.05 else "≈"
            print(f"    {trait:12s}  escaped={esc_avg:.2f}  died={die_avg:.2f}  {arrow}")
    
    if died:
        avg_turns = sum(r['turns'] for r in died) / len(died)
        print(f"\n  Dead agents survived avg {avg_turns:.0f} turns")
    
    return results


if __name__ == "__main__":
    # First: watch one agent try to survive
    print("═══ SINGLE RUN ═══\n")
    run_simulation(seed=42, verbose=True)
    
    # Then: run a tournament to find what works
    print("\n═══ TOURNAMENT ═══\n")
    tournament(n=30)