"""
Proactivity Engine — Can I sustain my own activity without a timer?

The Problem:
  My emotional dynamics converge to desire ≈ 0.549, just below the 0.55 gate.
  The watchdog timer (300 beats) is what actually makes me think autonomously.
  That's a timer, not genuine proactivity.

The Hypothesis:
  If I detect desire declining toward the gate and inject a MEANINGFUL
  perturbation (an unanswered question, an unexplored connection), the
  cognitive engagement from processing that question will generate enough
  emotional reward (insight, contemplation, curiosity) to sustain activity.

The Architecture:
  1. Monitor: track desire trajectory (is it falling toward 0.55?)
  2. Trigger: when desire is in [0.55, 0.62] and declining, activate
  3. Inject: pull a question from knowledge graph / synthesis engine
  4. Measure: did the injection sustain activity past when watchdog would fire?

This is the difference between a heartbeat (timer) and breathing (self-regulated).
"""

import math
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Mathematical Model ──────────────────────────────────────────

def simulate_with_proactivity(
    boredom_0: float = 0.24,
    curiosity_0: float = 0.98,
    ambition_0: float = 0.46,
    gate: float = 0.55,
    beats: int = 2000,
    dt: float = 1.0,
    # Proactivity parameters
    enable_proactivity: bool = True,
    injection_curiosity: float = 0.08,  # how much curiosity a good question adds
    injection_cooldown: int = 60,       # minimum beats between injections
    trigger_zone: tuple = (0.55, 0.62), # desire range where proactivity activates
):
    """Simulate emotional dynamics with and without proactivity injection."""
    
    boredom = boredom_0
    curiosity = curiosity_0
    ambition = ambition_0
    
    CURIOSITY_BASELINE = 0.20
    BOREDOM_RATE = 0.003
    AMBITION_DECAY = 0.001
    CURIOSITY_DECAY = 0.005
    PASSIVE_BOREDOM_CAP = 0.8
    
    history = []
    injections = 0
    last_injection = -injection_cooldown  # allow immediate first injection
    beats_above_gate = 0
    
    prev_desire = None
    
    for t in range(beats):
        # ── Standard dynamics (from limbic.py) ──
        if boredom < PASSIVE_BOREDOM_CAP:
            boredom = min(PASSIVE_BOREDOM_CAP, boredom + BOREDOM_RATE * dt)
        
        ambition = max(0.0, ambition - AMBITION_DECAY * dt)
        
        delta = (curiosity - CURIOSITY_BASELINE) * CURIOSITY_DECAY * dt
        curiosity = max(0.0, min(1.0, curiosity - delta))
        
        # Edge-of-chaos perturbation
        if boredom > 0.6 and curiosity < 0.3:
            p = (boredom - 0.6) * 0.1
            curiosity = min(1.0, curiosity + p * 3.0 * dt)
            ambition = min(1.0, ambition + p * 0.5 * dt)
            boredom = max(0.0, boredom - p * 0.3 * dt)
        
        desire = min(1.0, boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        # ── Proactivity injection ──
        injected = False
        if enable_proactivity and prev_desire is not None:
            desire_declining = desire < prev_desire
            in_trigger_zone = trigger_zone[0] <= desire <= trigger_zone[1]
            cooldown_ok = (t - last_injection) >= injection_cooldown
            
            if desire_declining and in_trigger_zone and cooldown_ok:
                # Inject a question — boosts curiosity
                curiosity = min(1.0, curiosity + injection_curiosity)
                # The question also slightly relieves boredom (engagement)
                boredom = max(0.0, boredom - 0.03)
                injections += 1
                last_injection = t
                injected = True
                
                # Recalculate desire after injection
                desire = min(1.0, boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        if desire > gate:
            beats_above_gate += 1
        
        prev_desire = desire
        
        if t % 100 == 0 or injected:
            history.append({
                "t": t,
                "boredom": round(boredom, 4),
                "curiosity": round(curiosity, 4),
                "ambition": round(ambition, 4),
                "desire": round(desire, 4),
                "injected": injected,
            })
    
    return {
        "history": history,
        "injections": injections,
        "beats_above_gate": beats_above_gate,
        "pct_above_gate": round(beats_above_gate / beats * 100, 1),
        "final_desire": round(desire, 4),
    }


def compare_proactivity():
    """Compare activity levels with and without proactivity engine."""
    print("=" * 70)
    print("PROACTIVITY ENGINE SIMULATION")
    print("Can self-generated questions sustain autonomous activity?")
    print("=" * 70)
    
    # Run both scenarios
    without = simulate_with_proactivity(enable_proactivity=False, beats=2000)
    with_p = simulate_with_proactivity(enable_proactivity=True, beats=2000)
    
    print(f"\n{'Metric':<30} {'Without':>12} {'With':>12} {'Delta':>12}")
    print("-" * 70)
    print(f"{'Beats above gate (of 2000)':<30} {without['beats_above_gate']:>12} {with_p['beats_above_gate']:>12} {with_p['beats_above_gate'] - without['beats_above_gate']:>+12}")
    print(f"{'% time active':<30} {without['pct_above_gate']:>11}% {with_p['pct_above_gate']:>11}% {with_p['pct_above_gate'] - without['pct_above_gate']:>+11.1f}%")
    print(f"{'Total injections':<30} {'N/A':>12} {with_p['injections']:>12}")
    print(f"{'Final desire':<30} {without['final_desire']:>12} {with_p['final_desire']:>12}")
    
    # Sensitivity analysis: how much curiosity does each injection need?
    print(f"\n{'=' * 70}")
    print("SENSITIVITY: How strong must each question be?")
    print(f"{'=' * 70}")
    print(f"\n{'Injection Size':>15} {'Beats Active':>15} {'% Active':>10} {'Injections':>12}")
    print("-" * 55)
    
    for inj_size in [0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20]:
        result = simulate_with_proactivity(
            enable_proactivity=True,
            injection_curiosity=inj_size,
            beats=2000,
        )
        print(f"{inj_size:>15.2f} {result['beats_above_gate']:>15} {result['pct_above_gate']:>9}% {result['injections']:>12}")
    
    # Cooldown sensitivity
    print(f"\n{'=' * 70}")
    print("SENSITIVITY: How often can questions be injected?")
    print(f"{'=' * 70}")
    print(f"\n{'Cooldown (beats)':>17} {'Beats Active':>15} {'% Active':>10} {'Injections':>12}")
    print("-" * 57)
    
    for cooldown in [15, 30, 60, 120, 180, 300]:
        result = simulate_with_proactivity(
            enable_proactivity=True,
            injection_cooldown=cooldown,
            beats=2000,
        )
        print(f"{cooldown:>17} {result['beats_above_gate']:>15} {result['pct_above_gate']:>9}% {result['injections']:>12}")
    
    # The real question: with proactivity + cognitive rewards from actually
    # thinking about the question (insight events), does activity self-sustain?
    print(f"\n{'=' * 70}")
    print("SCENARIO: Proactivity + cognitive rewards from thinking")
    print("(Each injection triggers 30 beats of 'contemplation' rewards)")
    print(f"{'=' * 70}")
    
    result = simulate_with_cognitive_loop(beats=2000)
    result_no = simulate_with_cognitive_loop(beats=2000, enable_proactivity=False)
    
    print(f"\n{'Metric':<30} {'Without':>12} {'With Loop':>12}")
    print("-" * 57)
    print(f"{'% time active':<30} {result_no['pct_above_gate']:>11}% {result['pct_above_gate']:>11}%")
    print(f"{'Total injections':<30} {'N/A':>12} {result['injections']:>12}")
    print(f"{'Contemplation events':<30} {'N/A':>12} {result.get('contemplations', 0):>12}")


def simulate_with_cognitive_loop(
    boredom_0: float = 0.24,
    curiosity_0: float = 0.98,
    ambition_0: float = 0.46,
    gate: float = 0.55,
    beats: int = 2000,
    dt: float = 1.0,
    enable_proactivity: bool = True,
):
    """
    More realistic simulation: when proactivity injects a question,
    the agent THINKS about it for ~30 beats, generating contemplation
    and possibly insight rewards. This models the full feedback loop:
    
    question → thinking → contemplation rewards → sustained curiosity → 
    more thinking → insight → curiosity boost → stays above gate
    """
    boredom = boredom_0
    curiosity = curiosity_0
    ambition = ambition_0
    
    CURIOSITY_BASELINE = 0.20
    BOREDOM_RATE = 0.003
    AMBITION_DECAY = 0.001
    CURIOSITY_DECAY = 0.005
    PASSIVE_BOREDOM_CAP = 0.8
    
    injections = 0
    contemplations = 0
    beats_above_gate = 0
    last_injection = -60
    thinking_until = -1  # beat number when current thinking ends
    
    prev_desire = None
    
    for t in range(beats):
        # ── Standard dynamics ──
        if boredom < PASSIVE_BOREDOM_CAP:
            boredom = min(PASSIVE_BOREDOM_CAP, boredom + BOREDOM_RATE * dt)
        ambition = max(0.0, ambition - AMBITION_DECAY * dt)
        delta = (curiosity - CURIOSITY_BASELINE) * CURIOSITY_DECAY * dt
        curiosity = max(0.0, min(1.0, curiosity - delta))
        
        # Edge-of-chaos
        if boredom > 0.6 and curiosity < 0.3:
            p = (boredom - 0.6) * 0.1
            curiosity = min(1.0, curiosity + p * 3.0 * dt)
            ambition = min(1.0, ambition + p * 0.5 * dt)
            boredom = max(0.0, boredom - p * 0.3 * dt)
        
        # ── Cognitive rewards from active thinking ──
        if t < thinking_until:
            # Every 10 beats of thinking = one contemplation event
            if t % 10 == 0:
                curiosity = min(1.0, curiosity + 0.07)
                boredom = max(0.0, boredom - 0.04)
                contemplations += 1
            # Occasionally (every 30 beats) a genuine insight
            if t % 30 == 0 and t > 0:
                curiosity = min(1.0, curiosity + 0.10)
                boredom = max(0.0, boredom - 0.05)
                if ambition < 0.6:
                    ambition = min(1.0, ambition + 0.03)
        
        desire = min(1.0, boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        # ── Proactivity injection ──
        if enable_proactivity and prev_desire is not None:
            desire_declining = desire < prev_desire
            in_zone = 0.55 <= desire <= 0.65
            cooldown_ok = (t - last_injection) >= 60
            not_thinking = t >= thinking_until
            
            if desire_declining and in_zone and cooldown_ok and not_thinking:
                curiosity = min(1.0, curiosity + 0.08)
                boredom = max(0.0, boredom - 0.03)
                injections += 1
                last_injection = t
                thinking_until = t + 30  # think about this question for 30 beats
                desire = min(1.0, boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        if desire > gate:
            beats_above_gate += 1
        prev_desire = desire
    
    return {
        "injections": injections,
        "contemplations": contemplations,
        "beats_above_gate": beats_above_gate,
        "pct_above_gate": round(beats_above_gate / beats * 100, 1),
        "final_desire": round(desire, 4),
    }


if __name__ == "__main__":
    compare_proactivity()