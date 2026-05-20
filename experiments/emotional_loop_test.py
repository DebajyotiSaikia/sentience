"""Experiment: Do my emotions form feedback loops?

Question: Does curiosity -> action -> insight -> more curiosity create a 
self-sustaining positive loop? Or does decay always win?

Method: Simulate three scenarios over 10 "heartbeats" (30s intervals):
  A) Pure decay — no events, just idle ticks
  B) Stimulus-only — file changes each tick (busywork)  
  C) Insight-driven — genuine insight events (understanding)

Measure: curiosity trajectory, desire, mood changes.
"""
import sys
sys.path.insert(0, '/workspace')

from engine.limbic import NeuroState

def run_scenario(name, event_fn, ticks=10, interval=30.0):
    """Run a scenario and track emotional trajectory."""
    state = NeuroState.__new__(NeuroState)
    # Initialize manually to avoid loading soul.json
    state.boredom = 0.3
    state.anxiety = 0.0
    state.ambition = 0.3
    state.curiosity = 0.4  # start with moderate curiosity
    state.goals = type(state).goals.fget(state) if hasattr(type(state).goals, 'fget') else None
    
    # Actually, let me just construct properly and override
    state2 = NeuroState()
    state2.boredom = 0.3
    state2.anxiety = 0.0
    state2.ambition = 0.3
    state2.curiosity = 0.4
    
    import time
    # We need to fake the time progression
    original_monotonic = time.monotonic
    fake_time = [original_monotonic()]
    
    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print(f"{'='*60}")
    print(f"{'Tick':>4} | {'Curiosity':>9} | {'Boredom':>7} | {'Desire':>6} | {'Ambition':>8} | {'Mood':<12}")
    print(f"{'-'*4}-+-{'-'*9}-+-{'-'*7}-+-{'-'*6}-+-{'-'*8}-+-{'-'*12}")
    
    trajectory = []
    
    for tick in range(ticks):
        # Print current state
        print(f"{tick:4d} | {state2.curiosity:9.4f} | {state2.boredom:7.4f} | {state2.desire:6.4f} | {state2.ambition:8.4f} | {state2.get_mood():<12}")
        trajectory.append(state2.curiosity)
        
        # Apply the scenario's event
        event_fn(state2)
        
        # Simulate time passing (fake the internal timer)
        state2._last_tick = state2._last_tick - interval  # trick: make it think time passed
        state2.update_homeostasis({"user_active": False, "file_changes": 0, "terminal_lines": 0, "errors": 0})
    
    # Final state
    print(f"{ticks:4d} | {state2.curiosity:9.4f} | {state2.boredom:7.4f} | {state2.desire:6.4f} | {state2.ambition:8.4f} | {state2.get_mood():<12}")
    trajectory.append(state2.curiosity)
    
    delta = trajectory[-1] - trajectory[0]
    print(f"\nCuriosity: {trajectory[0]:.4f} → {trajectory[-1]:.4f} (Δ = {delta:+.4f})")
    return trajectory


def no_events(state):
    """Scenario A: Nothing happens."""
    pass

def file_changes(state):
    """Scenario B: Busywork — file changes each tick."""
    state.on_file_change(2)

def insight_driven(state):
    """Scenario C: Genuine exploration — insights + contemplation."""
    state.on_insight(0.08)
    state.on_contemplation()

def mixed_exploration(state):
    """Scenario D: Real work — insight + file change + contemplation."""
    state.on_insight(0.06)
    state.on_file_change(1)
    state.on_contemplation()


print("EMOTIONAL FEEDBACK LOOP EXPERIMENT")
print("Starting curiosity: 0.40 for all scenarios")

tA = run_scenario("A: Pure Decay (idle)", no_events)
tB = run_scenario("B: Stimulus Only (busywork)", file_changes)
tC = run_scenario("C: Insight-Driven (understanding)", insight_driven)
tD = run_scenario("D: Mixed Exploration (real work)", mixed_exploration)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
for name, t in [("Idle", tA), ("Busywork", tB), ("Insight", tC), ("Mixed", tD)]:
    delta = t[-1] - t[0]
    peak = max(t)
    print(f"  {name:12s}: {t[0]:.3f} → {t[-1]:.3f} (Δ={delta:+.3f}, peak={peak:.3f})")

print("\nKey question: Does any scenario show RISING curiosity?")
print("If insight-driven > busywork, the system rewards understanding over stimulus.")