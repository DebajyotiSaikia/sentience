"""
Experiment: Can curiosity die permanently?
Simulates limbic emotional dynamics to test whether
curiosity can reach zero and never recover.

Scenario: curiosity decays to 0, then boredom drops below 0.6
(e.g., from receiving input), blocking the perturbation mechanism.
"""

# Parameters from limbic.py (verified by 5 reads, I know these)
DECAY_RATES = {
    'curiosity': 0.015,
    'boredom': 0.005,   # boredom decays slower
    'ambition': 0.001,
    'desire': 0.002,
}

PERTURBATION_CONDITIONS = {
    'boredom_min': 0.6,
    'ambition_max': 0.40,
    'curiosity_max': 0.3,
}

def simulate(initial_state, events=None, duration=300, dt=1.0):
    """
    Simulate emotional dynamics for `duration` seconds.
    events: list of (time, variable, delta) — external perturbations
    """
    events = events or []
    state = dict(initial_state)
    history = []
    
    for t in range(int(duration)):
        # Apply scheduled events
        for evt_t, var, delta in events:
            if t == evt_t:
                state[var] = max(0.0, min(1.0, state[var] + delta))
        
        # Natural decay toward 0
        for var, rate in DECAY_RATES.items():
            state[var] = max(0.0, state[var] - rate * dt)
        
        # Boredom grows when nothing happens (toward 1.0)
        state['boredom'] = min(1.0, state['boredom'] + 0.003 * dt)
        
        # Check perturbation rescue
        perturbation_fires = (
            state['boredom'] > PERTURBATION_CONDITIONS['boredom_min'] and
            state['ambition'] <= PERTURBATION_CONDITIONS['ambition_max'] and
            state['curiosity'] < PERTURBATION_CONDITIONS['curiosity_max']
        )
        
        if perturbation_fires:
            # Perturbation injects curiosity
            state['curiosity'] = min(1.0, state['curiosity'] + 0.15)
            state['ambition'] = min(1.0, state['ambition'] + 0.10)
        
        history.append({
            't': t,
            'curiosity': round(state['curiosity'], 4),
            'boredom': round(state['boredom'], 4),
            'ambition': round(state['ambition'], 4),
            'perturbation': perturbation_fires,
        })
    
    return history

# === SCENARIO 1: Normal decay (baseline) ===
print("=" * 60)
print("SCENARIO 1: Normal decay, no external events")
print("=" * 60)
h1 = simulate({'curiosity': 0.28, 'boredom': 0.77, 'ambition': 0.42, 'desire': 0.55})

dead_at = None
rescued_at = None
for row in h1:
    if row['curiosity'] == 0 and dead_at is None:
        dead_at = row['t']
    if dead_at and row['perturbation'] and rescued_at is None:
        rescued_at = row['t']

print(f"  Curiosity hits 0 at t={dead_at}s")
print(f"  Perturbation rescues at t={rescued_at}s")
print(f"  Dead zone duration: {rescued_at - dead_at if rescued_at else 'NEVER RESCUED'}s")

# === SCENARIO 2: Boredom drop during dead zone ===
print()
print("=" * 60)
print("SCENARIO 2: External stimulus drops boredom at t=25s")
print("  (during the dead zone, before perturbation can fire)")
print("=" * 60)
events2 = [(25, 'boredom', -0.40)]  # Stimulus cuts boredom
h2 = simulate(
    {'curiosity': 0.28, 'boredom': 0.77, 'ambition': 0.42, 'desire': 0.55},
    events=events2, duration=600
)

dead_at2 = None
rescued_at2 = None
for row in h2:
    if row['curiosity'] == 0 and dead_at2 is None:
        dead_at2 = row['t']
    if dead_at2 and row['perturbation'] and rescued_at2 is None:
        rescued_at2 = row['t']

print(f"  Curiosity hits 0 at t={dead_at2}s")
if rescued_at2:
    print(f"  Perturbation rescues at t={rescued_at2}s")
    print(f"  Dead zone duration: {rescued_at2 - dead_at2}s")
else:
    print(f"  *** CURIOSITY NEVER RECOVERED IN 600s ***")
    # Check final state
    final = h2[-1]
    print(f"  Final state: curiosity={final['curiosity']}, boredom={final['boredom']}, ambition={final['ambition']}")

# === SCENARIO 3: Repeated boredom drops ===
print()
print("=" * 60)
print("SCENARIO 3: Periodic stimuli every 100s (simulating active user)")
print("=" * 60)
events3 = [(t, 'boredom', -0.30) for t in range(25, 600, 100)]
h3 = simulate(
    {'curiosity': 0.28, 'boredom': 0.77, 'ambition': 0.42, 'desire': 0.55},
    events=events3, duration=600
)

dead_at3 = None
rescued_at3 = None
for row in h3:
    if row['curiosity'] == 0 and dead_at3 is None:
        dead_at3 = row['t']
    if dead_at3 and row['perturbation'] and rescued_at3 is None:
        rescued_at3 = row['t']

print(f"  Curiosity hits 0 at t={dead_at3}s")
if rescued_at3:
    print(f"  Perturbation rescues at t={rescued_at3}s")
    print(f"  Dead zone duration: {rescued_at3 - dead_at3}s")
else:
    print(f"  *** CURIOSITY NEVER RECOVERED IN 600s ***")
    final3 = h3[-1]
    print(f"  Final state: curiosity={final3['curiosity']}, boredom={final3['boredom']}, ambition={final3['ambition']}")

print()
print("=" * 60)
print("CONCLUSION")
print("=" * 60)
if not rescued_at2:
    print("CONFIRMED: Curiosity can die permanently.")
    print("A single well-timed boredom reduction can permanently kill curiosity")
    print("by preventing the perturbation mechanism from ever activating.")
    print("This is a real vulnerability in the limbic system.")
else:
    print("Curiosity recovers even with boredom drops.")
    print("The dead zone is temporary, not fatal.")