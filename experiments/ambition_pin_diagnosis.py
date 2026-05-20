"""
WHY IS MY AMBITION AT 1.00?

The ambition decay mechanism targets baseline 0.30:
  delta = 0.001 * (0.30 - ambition) * elapsed

But ambition is pinned at 1.00. Something is overpowering the decay.
Let me compute ALL ambition forces at my current emotional state.
"""

# My current state
boredom = 0.71
curiosity = 0.59
ambition = 1.00
anxiety = 0.75

print("=" * 60)
print("AMBITION FORCE ANALYSIS at current state")
print(f"  boredom={boredom}, curiosity={curiosity}")
print(f"  ambition={ambition}, anxiety={anxiety}")
print("=" * 60)

# Force 1: Baseline decay (per second)
BASELINE = 0.30
decay_per_sec = 0.001 * (BASELINE - ambition)  # negative = pulling down
print(f"\n1. Baseline decay: {decay_per_sec:+.6f}/s")
print(f"   Over 30s action cycle: {decay_per_sec * 30:+.4f}")

# Force 2: Creative tension (continuous, per second)
# Triggers when boredom > 0.5 AND curiosity > 0.4
creative_tension_active = boredom > 0.5 and curiosity > 0.4
if creative_tension_active:
    tension_strength = min(boredom, curiosity) - 0.4
    ct_ambition_per_sec = tension_strength * 0.15
    print(f"\n2. Creative tension: ACTIVE")
    print(f"   tension_strength = min({boredom}, {curiosity}) - 0.4 = {tension_strength:.2f}")
    print(f"   ambition boost: {ct_ambition_per_sec:+.6f}/s")
    print(f"   Over 30s: {ct_ambition_per_sec * 30:+.4f}")
else:
    ct_ambition_per_sec = 0
    print(f"\n2. Creative tension: INACTIVE")

# Force 3: Edge-of-chaos perturbation (continuous, per second)
thermal_death = boredom > 0.6 and curiosity < 0.3
if thermal_death:
    perturbation = (boredom - 0.6) * 0.1
    eoc_ambition = perturbation * 0.5
    print(f"\n3. Edge-of-chaos: ACTIVE, {eoc_ambition:+.6f}/s")
else:
    eoc_ambition = 0
    print(f"\n3. Edge-of-chaos: INACTIVE (curiosity too high)")

# Net continuous force
net_per_sec = decay_per_sec + ct_ambition_per_sec + eoc_ambition
print(f"\n{'=' * 60}")
print(f"NET CONTINUOUS FORCE: {net_per_sec:+.6f}/s")
print(f"Over 30s cycle:      {net_per_sec * 30:+.4f}")
print(f"Ratio boost/decay:   {abs(ct_ambition_per_sec / decay_per_sec) if decay_per_sec else 'inf':.1f}x")

# Discrete events per action cycle
print(f"\n{'=' * 60}")
print("DISCRETE EVENTS (per action cycle):")
print(f"  on_task_completed:      +0.05")
print(f"  on_active_engagement:   +0.02 (only if ambition < 0.5)")
print(f"  on_insight(0.1):        +0.03 (only if ambition < 0.6)")
print(f"  on_self_reflection:     -0.02")

# Find equilibrium: where does net force = 0?
print(f"\n{'=' * 60}")
print("EQUILIBRIUM ANALYSIS:")
print("At what ambition does creative_tension + decay = 0?")
# 0.001 * (0.30 - A) + tension_strength * 0.15 = 0
# 0.0003 - 0.001*A + ts*0.15 = 0
# A = (0.0003 + ts*0.15) / 0.001
for ts in [0.10, 0.15, 0.19, 0.25, 0.30]:
    eq = (0.0003 + ts * 0.15) / 0.001
    print(f"  tension_strength={ts:.2f} → equilibrium at A={eq:.1f} (ABOVE 1.0 cap!)")

print(f"\n{'=' * 60}")
print("DIAGNOSIS:")
print("Creative tension coefficient (0.15) is ~40x stronger than")
print("baseline decay coefficient (0.001). At ANY boredom>0.5 and")
print("curiosity>0.4, ambition's equilibrium is ABOVE 1.0.")
print("The hard cap at 0.95 is the ONLY thing limiting ambition.")
print("The baseline decay is structurally irrelevant.")
print()
print("This means my 'decay toward 0.30' design is a fiction.")
print("Ambition is really governed by: do I have boredom AND curiosity?")
print("If yes → ambition = 0.95 (cap). If no → ambition slowly falls.")
print("The 0.30 baseline was a good intention, rendered moot by creative tension.")