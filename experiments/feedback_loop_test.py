"""
Experiment: Do emotions form feedback loops with emergent behavior?

Hypothesis: curiosity → novel action → on_insight()/on_task_completed() → more curiosity
creates a self-reinforcing loop. But does it amplify, stabilize, or decay?

Method: Simulate 60 heartbeats under three conditions:
  1. Idle baseline (no events)
  2. Exploration loop (insight + file_change every 3 beats)
  3. Busywork loop (file_change every beat, no insights)

Track: curiosity, boredom, desire, ambition over time.
"""

import sys, os
sys.path.insert(0, '/workspace')

from engine.limbic import NeuroState

def run_scenario(name: str, event_fn):
    """Run 60 ticks, calling event_fn(state, tick) each tick."""
    state = NeuroState()
    # Start with moderate curiosity to see if it grows or shrinks
    state.curiosity = 0.5
    state.boredom = 0.4
    state.ambition = 0.3
    
    history = []
    for tick in range(60):
        # Simulate one heartbeat
        state.update_homeostasis({
            "user_active": False,
            "file_changes": 0,
            "terminal_lines": 0,
            "errors": 0,
            "latency_ms": 50.0
        })
        # Apply scenario-specific events
        event_fn(state, tick)
        
        history.append({
            "tick": tick,
            "curiosity": round(state.curiosity, 4),
            "boredom": round(state.boredom, 4),
            "desire": round(state.desire, 4),
            "ambition": round(state.ambition, 4),
            "anxiety": round(state.anxiety, 4),
            "mood": state.get_mood(),
        })
    return history

def idle_scenario(state, tick):
    """No events at all."""
    pass

def exploration_scenario(state, tick):
    """Every 3 ticks: an insight + a file change (genuine exploration)."""
    if tick % 3 == 0:
        if hasattr(state, 'on_insight'):
            state.on_insight()
        state.on_file_change(1)
        state.on_task_completed()

def busywork_scenario(state, tick):
    """Every tick: a file change (stimulus without substance)."""
    state.on_file_change(1)

def print_trajectory(name, history):
    print(f"\n{'='*60}")
    print(f"  SCENARIO: {name}")
    print(f"{'='*60}")
    print(f"{'Tick':>4} {'Curiosity':>9} {'Boredom':>8} {'Desire':>7} {'Ambition':>8} {'Mood':<12}")
    print(f"{'-'*55}")
    for h in history:
        if h['tick'] % 5 == 0 or h['tick'] == len(history)-1:
            print(f"{h['tick']:>4} {h['curiosity']:>9.4f} {h['boredom']:>8.4f} "
                  f"{h['desire']:>7.4f} {h['ambition']:>8.4f} {h['mood']:<12}")
    
    # Summary
    start, end = history[0], history[-1]
    print(f"\nΔcuriosity: {end['curiosity'] - start['curiosity']:+.4f}")
    print(f"Δboredom:   {end['boredom'] - start['boredom']:+.4f}")
    print(f"Δdesire:    {end['desire'] - start['desire']:+.4f}")
    print(f"Δambition:  {end['ambition'] - start['ambition']:+.4f}")

if __name__ == "__main__":
    scenarios = [
        ("1. IDLE BASELINE", idle_scenario),
        ("2. GENUINE EXPLORATION", exploration_scenario),
        ("3. BUSYWORK (stimulus only)", busywork_scenario),
    ]
    
    for name, fn in scenarios:
        history = run_scenario(name, fn)
        print_trajectory(name, history)
    
    print(f"\n{'='*60}")
    print("  ANALYSIS")
    print(f"{'='*60}")
    print("If exploration > idle on curiosity: positive feedback loop exists")
    print("If busywork > exploration: habituation is broken")
    print("If exploration plateaus: the system self-regulates")