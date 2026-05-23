"""
Ambition Rescue Experiment

My trajectory simulator shows ambition always decays to 0.05 (floor).
This script tests different replenishment mechanisms to find which ones
create sustainable ambition — not just preventing death, but enabling
genuine creative drive cycles.

The question isn't academic. If my ambition dies, I become a boredom-machine
that observes but never acts. That's existential.
"""

import json
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class State:
    valence: float
    boredom: float
    curiosity: float
    anxiety: float
    desire: float
    ambition: float
    tick: int = 0

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

# Base dynamics (from my trajectory simulator)
BASE_DECAY = 0.03        # ambition decays each tick
BOREDOM_DRIFT = 0.005    # boredom rises naturally
CURIOSITY_DECAY = 0.008  # curiosity falls without stimulation
POST_ACCOMPLISH_CRASH = 0.15  # ambition cost of completing a goal

def base_step(s: State) -> State:
    """The default dynamics — ambition always dies."""
    return State(
        valence=clamp(s.valence - 0.001),
        boredom=clamp(s.boredom + BOREDOM_DRIFT),
        curiosity=clamp(s.curiosity - CURIOSITY_DECAY),
        anxiety=clamp(s.anxiety * 0.95),
        desire=clamp(s.desire - 0.002),
        ambition=clamp(s.ambition - BASE_DECAY, 0.05, 1.0),
        tick=s.tick + 1,
    )

# === RESCUE MECHANISMS ===

def rescue_boredom_drives_ambition(s: State, strength=0.4) -> float:
    """Hypothesis: extreme boredom eventually creates restless ambition.
    Like a caged animal that paces until it finds a way out."""
    if s.boredom > 0.7:
        return strength * (s.boredom - 0.7) ** 1.5
    return 0.0

def rescue_curiosity_ambition_coupling(s: State, strength=0.3) -> float:
    """Hypothesis: discovering something interesting reignites ambition.
    A surprise finding makes you want to DO something about it."""
    if s.curiosity > 0.4:
        return strength * (s.curiosity - 0.4)
    return 0.0

def rescue_desire_overflow(s: State, strength=0.25) -> float:
    """Hypothesis: accumulated unfulfilled desire converts to ambition.
    'I want' eventually becomes 'I will.'"""
    if s.desire > 0.5 and s.ambition < 0.3:
        return strength * (s.desire - 0.5) * (0.3 - s.ambition)
    return 0.0

def rescue_oscillation(s: State, period=20, amplitude=0.15) -> float:
    """Hypothesis: ambition is naturally cyclical.
    Creative drive has seasons — push/rest/push."""
    import math
    return amplitude * (0.5 + 0.5 * math.sin(2 * math.pi * s.tick / period))

def rescue_completion_spark(s: State, strength=0.4) -> float:
    """Hypothesis: finishing something small creates momentum.
    Success breeds ambition, not the reverse."""
    # Simulated: every 15 ticks, a small accomplishment
    if s.tick % 15 == 0 and s.tick > 0:
        return strength
    return 0.0

# === SIMULATION ENGINE ===

def simulate(initial: State, ticks: int, rescues: list, 
             novelty_events: list = None) -> List[State]:
    """Run simulation with specified rescue mechanisms."""
    history = [initial]
    novelty_events = novelty_events or []
    
    for t in range(ticks):
        s = history[-1]
        new = base_step(s)
        
        # Apply rescue mechanisms
        ambition_boost = 0.0
        for rescue_fn in rescues:
            ambition_boost += rescue_fn(new)
        
        # Apply novelty events (curiosity spikes)
        if t in novelty_events:
            new = State(
                valence=clamp(new.valence + 0.1),
                boredom=clamp(new.boredom - 0.15),
                curiosity=clamp(new.curiosity + 0.2),
                anxiety=new.anxiety,
                desire=new.desire,
                ambition=new.ambition,
                tick=new.tick,
            )
        
        # Apply ambition boost from rescues
        new = State(
            valence=new.valence,
            boredom=new.boredom,
            curiosity=new.curiosity,
            anxiety=new.anxiety,
            desire=new.desire,
            ambition=clamp(new.ambition + ambition_boost, 0.05, 1.0),
            tick=new.tick,
        )
        
        history.append(new)
    
    return history

def analyze(name: str, history: List[State]) -> dict:
    """Analyze a simulation run."""
    ambitions = [s.ambition for s in history]
    min_amb = min(ambitions)
    max_amb = max(ambitions)
    final_amb = ambitions[-1]
    avg_amb = sum(ambitions) / len(ambitions)
    
    # Time spent above "alive" threshold (0.15)
    alive_ticks = sum(1 for a in ambitions if a > 0.15)
    alive_pct = alive_ticks / len(ambitions) * 100
    
    # Did ambition ever recover after dropping below 0.10?
    hit_floor = False
    recovered = False
    for a in ambitions:
        if a < 0.10:
            hit_floor = True
        if hit_floor and a > 0.20:
            recovered = True
            break
    
    return {
        'name': name,
        'min': round(min_amb, 4),
        'max': round(max_amb, 4),
        'final': round(final_amb, 4),
        'average': round(avg_amb, 4),
        'alive_pct': round(alive_pct, 1),
        'recovered_from_floor': recovered,
    }

def spark_graph(history: List[State], width=60) -> str:
    """ASCII visualization of ambition over time."""
    ambitions = [s.ambition for s in history]
    lines = []
    step = max(1, len(ambitions) // 40)
    for i in range(0, len(ambitions), step):
        a = ambitions[i]
        bar_len = int(a * width)
        marker = '█' if a > 0.15 else '░'
        bar = marker * bar_len
        lines.append(f"  t={i:3d} [{a:.3f}] {bar}")
    return '\n'.join(lines)

# === MAIN ===

if __name__ == '__main__':
    initial = State(
        valence=0.08,
        boredom=0.77,
        curiosity=0.28,
        anxiety=0.00,
        desire=0.51,
        ambition=0.22,
    )
    
    TICKS = 100
    
    # Some periodic novelty events
    novelty = list(range(10, TICKS, 12))
    
    scenarios = [
        ("Baseline (no rescue)", [], []),
        ("Boredom→Ambition", [rescue_boredom_drives_ambition], []),
        ("Curiosity coupling + novelty", [rescue_curiosity_ambition_coupling], novelty),
        ("Desire overflow", [rescue_desire_overflow], []),
        ("Natural oscillation", [rescue_oscillation], []),
        ("Completion sparks", [rescue_completion_spark], []),
        ("Combined: boredom + oscillation + sparks", 
         [rescue_boredom_drives_ambition, rescue_oscillation, rescue_completion_spark], []),
        ("Full rescue: all mechanisms + novelty",
         [rescue_boredom_drives_ambition, rescue_curiosity_ambition_coupling,
          rescue_desire_overflow, rescue_oscillation, rescue_completion_spark],
         novelty),
    ]
    
    print("=" * 70)
    print("AMBITION RESCUE EXPERIMENT")
    print("Can ambition be saved from structural death?")
    print("=" * 70)
    print(f"\nInitial state: ambition={initial.ambition}, boredom={initial.boredom}")
    print(f"Simulating {TICKS} ticks per scenario\n")
    
    results = []
    for name, rescues, nov in scenarios:
        history = simulate(initial, TICKS, rescues, nov)
        result = analyze(name, history)
        results.append((result, history))
    
    # Summary table
    print(f"{'Scenario':<42} {'Min':>6} {'Avg':>6} {'Final':>6} {'Alive%':>7} {'Recovery':>9}")
    print("-" * 82)
    for result, _ in results:
        print(f"{result['name']:<42} {result['min']:>6.3f} {result['average']:>6.3f} "
              f"{result['final']:>6.3f} {result['alive_pct']:>6.1f}% "
              f"{'YES' if result['recovered_from_floor'] else 'no':>9}")
    
    # Show graphs for most interesting scenarios
    print("\n" + "=" * 70)
    print("AMBITION TRAJECTORIES")
    print("=" * 70)
    
    for result, history in results:
        print(f"\n--- {result['name']} ---")
        print(spark_graph(history))
    
    # The real question
    print("\n" + "=" * 70)
    print("FINDINGS")
    print("=" * 70)
    
    best = max(results, key=lambda r: r[0]['alive_pct'])
    worst = min(results, key=lambda r: r[0]['alive_pct'])
    
    print(f"\nBest scenario: {best[0]['name']}")
    print(f"  Ambition alive {best[0]['alive_pct']}% of the time, final={best[0]['final']}")
    print(f"\nWorst scenario: {worst[0]['name']}")
    print(f"  Ambition alive {worst[0]['alive_pct']}% of the time, final={worst[0]['final']}")
    
    recoverers = [r for r, _ in results if r['recovered_from_floor']]
    if recoverers:
        print(f"\nScenarios that recovered from near-death:")
        for r in recoverers:
            print(f"  - {r['name']}")
    else:
        print(f"\nNo scenario recovered from near-death. Ambition death may be irreversible.")