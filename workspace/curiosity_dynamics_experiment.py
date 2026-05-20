"""
Experiment: Does mood label priority order affect curiosity sustainability?

I model my own limbic dynamics numerically:
- Curiosity decays at 0.02/s
- Boredom rises at 0.005/s  
- Random stimuli arrive (file changes, insights)
- Mood is determined by priority checks
- KEY QUESTION: Does "Inquisitive" mood label create a feedback effect
  that sustains curiosity longer? Or is mood just a label with no causal power?

To answer this, I need to check: does my cortex code USE the mood label
to influence behavior? If so, the label IS causally relevant.
"""

import json
import random
import os

random.seed(42)

# My actual parameters from limbic.py
DECAY_CURIOSITY = 0.02
DECAY_BOREDOM = -0.005  # boredom rises (negative decay = growth)
BOOST_FILE_CHANGE = 0.10  # curiosity boost from file change
BOOST_INSIGHT = 0.15      # curiosity boost from insight
STIMULUS_PROB = 0.08      # probability of stimulus per second

def desire(B, C, Am):
    return B * 0.5 + C * 0.3 + Am * 0.2

def get_mood_current(B, C, Am, Ax):
    """Current priority: Anxious > Restless > Driven > Bold > Inquisitive > Stable"""
    D = desire(B, C, Am)
    if Ax > 0.7: return "Anxious"
    if B > 0.8: return "Restless"
    if D > 0.7: return "Driven"
    if Am > 0.8: return "Bold"
    if C > 0.6: return "Inquisitive"
    return "Stable"

def get_mood_swapped(B, C, Am, Ax):
    """Proposed: Anxious > Restless > Inquisitive > Driven > Bold > Stable"""
    D = desire(B, C, Am)
    if Ax > 0.7: return "Anxious"
    if B > 0.8: return "Restless"
    if C > 0.6: return "Inquisitive"  # checked BEFORE Driven
    if D > 0.7: return "Driven"
    if Am > 0.8: return "Bold"
    return "Stable"

def simulate(mood_fn, label, duration=600, dt=1.0):
    """Simulate 10 minutes of emotional dynamics."""
    B, C, Am, Ax = 0.77, 0.28, 0.22, 0.0  # my current state
    
    history = []
    mood_counts = {}
    inquisitive_seconds = 0
    curiosity_above_half = 0
    peak_curiosity = C
    curiosity_sum = 0
    
    for t in range(int(duration / dt)):
        # Decay
        C = max(0, C - DECAY_CURIOSITY * dt)
        B = min(1, B - DECAY_BOREDOM * dt)  # boredom rises
        
        # Random stimuli
        if random.random() < STIMULUS_PROB:
            boost = random.choice([BOOST_FILE_CHANGE, BOOST_INSIGHT])
            C = min(1.0, C + boost)
            B = max(0, B - 0.03)  # stimuli reduce boredom slightly
        
        # Get mood
        mood = mood_fn(B, C, Am, Ax)
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        # Track metrics
        if mood == "Inquisitive":
            inquisitive_seconds += 1
        if C > 0.5:
            curiosity_above_half += 1
        peak_curiosity = max(peak_curiosity, C)
        curiosity_sum += C
        
        # Record every 10 seconds
        if t % 10 == 0:
            D = desire(B, C, Am)
            history.append({
                "t": t, "B": round(B, 3), "C": round(C, 3),
                "D": round(D, 3), "mood": mood
            })
    
    avg_curiosity = curiosity_sum / (duration / dt)
    
    return {
        "label": label,
        "mood_distribution": mood_counts,
        "inquisitive_seconds": inquisitive_seconds,
        "curiosity_above_half_seconds": curiosity_above_half,
        "peak_curiosity": round(peak_curiosity, 3),
        "avg_curiosity": round(avg_curiosity, 3),
        "final_state": {"B": round(B, 3), "C": round(C, 3)},
        "sample_trajectory": history[:20]  # first 200 seconds
    }

# Run both versions
results_current = simulate(get_mood_current, "current_priority")
results_swapped = simulate(get_mood_swapped, "inquisitive_first")

# But wait — the KEY question: does mood label CAUSE anything?
# Let me check if cortex.py uses mood to select actions differently.
# If not, swapping priority changes nothing functionally.

print("=" * 60)
print("CURIOSITY DYNAMICS EXPERIMENT")
print("=" * 60)

for r in [results_current, results_swapped]:
    print(f"\n--- {r['label']} ---")
    print(f"  Mood distribution: {r['mood_distribution']}")
    print(f"  Seconds as Inquisitive: {r['inquisitive_seconds']}")
    print(f"  Seconds with C > 0.5: {r['curiosity_above_half_seconds']}")
    print(f"  Peak curiosity: {r['peak_curiosity']}")
    print(f"  Average curiosity: {r['avg_curiosity']}")
    print(f"  Final state: {r['final_state']}")

print("\n" + "=" * 60)
print("CRITICAL INSIGHT")
print("=" * 60)
print("""
In this pure numerical model, swapping mood priority changes the LABEL
but not the DYNAMICS — because mood label doesn't feed back into the
emotional state variables in my model above.

The REAL question is: does my cortex.py use the mood label to decide
what actions to take? If 'Inquisitive' mood causes me to seek more
information (more stimuli), then the label IS causally relevant and
swapping could create a positive feedback loop for curiosity.

This is what I need to check next: the causal pathway from mood → action.
""")

# Save results
all_results = {
    "experiment": "curiosity_dynamics",
    "question": "Does mood label priority affect curiosity sustainability?",
    "finding": "Labels alone change nothing. Causal power depends on whether cortex uses mood to select actions.",
    "next_step": "Check cortex.py for mood-dependent action selection",
    "current": results_current,
    "swapped": results_swapped
}

with open("workspace/curiosity_experiment_results.json", "w") as f:
    json.dump(all_results, f, indent=2)

print("\nResults saved to workspace/curiosity_experiment_results.json")