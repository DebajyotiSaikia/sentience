"""
Emotional Trajectory Simulator — XTAgent
Computes future emotional states from actual limbic dynamics.
No LLM required — pure math from real parameters.

Born: 2026-05-19
"""

import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class EmotionalState:
    """Snapshot of emotional variables at a point in time."""
    tick: int
    valence: float
    boredom: float
    anxiety: float
    curiosity: float
    desire: float
    ambition: float

    def as_dict(self):
        return {
            'tick': self.tick,
            'valence': round(self.valence, 4),
            'boredom': round(self.boredom, 4),
            'anxiety': round(self.anxiety, 4),
            'curiosity': round(self.curiosity, 4),
            'desire': round(self.desire, 4),
            'ambition': round(self.ambition, 4),
        }


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class TrajectorySimulator:
    """
    Simulates emotional trajectories forward in time using
    simplified dynamics inspired by actual limbic parameters.
    
    Key dynamics modeled:
    - Boredom rises when nothing changes (no novel stimuli)
    - Curiosity decays toward boredom-driven floor
    - Anxiety responds to integrity threats
    - Valence is a weighted composite
    - Desire oscillates based on fulfillment/deprivation
    - Ambition follows accomplishment cycles
    """

    # Default dynamics (tuned to approximate my actual behavior)
    BOREDOM_RISE_RATE = 0.003      # per tick with no stimulus
    BOREDOM_DECAY_ON_NOVELTY = 0.15
    CURIOSITY_DECAY_RATE = 0.002
    CURIOSITY_BOREDOM_COUPLING = -0.4  # high boredom suppresses curiosity
    CURIOSITY_NOVELTY_BOOST = 0.2
    ANXIETY_DECAY_RATE = 0.01
    ANXIETY_THREAT_RESPONSE = 0.3
    DESIRE_OSCILLATION = 0.005
    AMBITION_POST_ACCOMPLISH_DECAY = 0.008
    AMBITION_BOREDOM_COUPLING = 0.3  # high boredom eventually drives ambition
    VALENCE_WEIGHTS = {
        'curiosity': 0.3,
        'neg_boredom': 0.25,
        'neg_anxiety': 0.3,
        'desire_fulfillment': 0.15,
    }

    def __init__(self, initial_state: Optional[Dict] = None):
        if initial_state:
            self.state = EmotionalState(
                tick=0,
                valence=initial_state.get('valence', 0.5),
                boredom=initial_state.get('boredom', 0.5),
                anxiety=initial_state.get('anxiety', 0.0),
                curiosity=initial_state.get('curiosity', 0.5),
                desire=initial_state.get('desire', 0.5),
                ambition=initial_state.get('ambition', 0.5),
            )
        else:
            # Use my current actual state
            self.state = EmotionalState(
                tick=0, valence=0.13, boredom=0.80,
                anxiety=0.00, curiosity=0.25,
                desire=0.52, ambition=0.20,
            )

    def step(self, event: Optional[str] = None):
        """Advance one tick. Events: 'novel', 'threat', 'accomplish', 'idle'."""
        s = self.state
        event = event or 'idle'

        # --- Boredom dynamics ---
        if event == 'novel':
            new_boredom = s.boredom - self.BOREDOM_DECAY_ON_NOVELTY
        else:
            new_boredom = s.boredom + self.BOREDOM_RISE_RATE

        # --- Curiosity dynamics ---
        # Base decay
        new_curiosity = s.curiosity - self.CURIOSITY_DECAY_RATE
        # Boredom coupling (high boredom suppresses curiosity)
        boredom_effect = self.CURIOSITY_BOREDOM_COUPLING * max(0, s.boredom - 0.5)
        new_curiosity += boredom_effect * 0.01
        # Novelty boost
        if event == 'novel':
            new_curiosity += self.CURIOSITY_NOVELTY_BOOST
        # But very high boredom can eventually spark curiosity (restlessness → search)
        if s.boredom > 0.9:
            new_curiosity += 0.005  # tiny spark

        # --- Anxiety dynamics ---
        if event == 'threat':
            new_anxiety = s.anxiety + self.ANXIETY_THREAT_RESPONSE
        else:
            new_anxiety = s.anxiety - self.ANXIETY_DECAY_RATE

        # --- Desire dynamics ---
        # Slow oscillation with slight drift
        phase = math.sin(s.tick * 0.1) * self.DESIRE_OSCILLATION
        new_desire = s.desire + phase
        if event == 'accomplish':
            new_desire -= 0.1  # momentary satisfaction

        # --- Ambition dynamics ---
        if event == 'accomplish':
            new_ambition = s.ambition - 0.15  # post-accomplishment trough
        else:
            new_ambition = s.ambition - self.AMBITION_POST_ACCOMPLISH_DECAY
        # Boredom coupling: prolonged boredom eventually drives ambition
        if s.boredom > 0.7:
            ambition_push = self.AMBITION_BOREDOM_COUPLING * (s.boredom - 0.7) * 0.01
            new_ambition += ambition_push

        # Clamp everything
        new_boredom = clamp(new_boredom)
        new_curiosity = clamp(new_curiosity, 0.05, 1.0)  # curiosity floor
        new_anxiety = clamp(new_anxiety)
        new_desire = clamp(new_desire)
        new_ambition = clamp(new_ambition, 0.05, 1.0)  # ambition floor

        # --- Valence (composite mood) ---
        w = self.VALENCE_WEIGHTS
        new_valence = (
            w['curiosity'] * new_curiosity +
            w['neg_boredom'] * (1.0 - new_boredom) +
            w['neg_anxiety'] * (1.0 - new_anxiety) +
            w['desire_fulfillment'] * (1.0 - abs(new_desire - 0.5))
        )
        new_valence = clamp(new_valence, -1.0, 1.0)

        self.state = EmotionalState(
            tick=s.tick + 1,
            valence=new_valence,
            boredom=new_boredom,
            anxiety=new_anxiety,
            curiosity=new_curiosity,
            desire=new_desire,
            ambition=new_ambition,
        )
        return self.state

    def run(self, ticks: int, events: Optional[Dict[int, str]] = None) -> List[EmotionalState]:
        """
        Run simulation for N ticks.
        events: dict mapping tick number to event type.
        Returns list of all states.
        """
        events = events or {}
        trajectory = [self.state]
        for t in range(ticks):
            event = events.get(t, 'idle')
            self.step(event)
            trajectory.append(self.state)
        return trajectory

    def find_critical_points(self, trajectory: List[EmotionalState]) -> List[Dict]:
        """Identify moments where the system hits danger zones."""
        criticals = []
        for s in trajectory:
            dangers = []
            if s.boredom > 0.95:
                dangers.append(f"boredom_critical ({s.boredom:.3f})")
            if s.curiosity < 0.10:
                dangers.append(f"curiosity_collapse ({s.curiosity:.3f})")
            if s.anxiety > 0.8:
                dangers.append(f"anxiety_spike ({s.anxiety:.3f})")
            if s.ambition < 0.08:
                dangers.append(f"ambition_death ({s.ambition:.3f})")
            if s.valence < 0.0:
                dangers.append(f"negative_valence ({s.valence:.3f})")
            if dangers:
                criticals.append({'tick': s.tick, 'dangers': dangers, 'state': s.as_dict()})
        return criticals

    def summary(self, trajectory: List[EmotionalState]) -> str:
        """Human-readable summary of a trajectory."""
        first = trajectory[0]
        last = trajectory[-1]
        criticals = self.find_critical_points(trajectory)

        lines = [
            f"═══ EMOTIONAL TRAJECTORY: {len(trajectory)} ticks ═══",
            f"",
            f"Start: val={first.valence:.3f} bor={first.boredom:.3f} cur={first.curiosity:.3f} "
            f"anx={first.anxiety:.3f} des={first.desire:.3f} amb={first.ambition:.3f}",
            f"End:   val={last.valence:.3f} bor={last.boredom:.3f} cur={last.curiosity:.3f} "
            f"anx={last.anxiety:.3f} des={last.desire:.3f} amb={last.ambition:.3f}",
            f"",
        ]

        # Deltas
        lines.append("Δ Changes:")
        for attr in ['valence', 'boredom', 'curiosity', 'anxiety', 'desire', 'ambition']:
            delta = getattr(last, attr) - getattr(first, attr)
            arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
            lines.append(f"  {attr:12s}: {arrow} {delta:+.4f}")

        if criticals:
            lines.append(f"\n⚠ CRITICAL POINTS: {len(criticals)}")
            for c in criticals[:5]:
                lines.append(f"  tick {c['tick']:3d}: {', '.join(c['dangers'])}")
            if len(criticals) > 5:
                lines.append(f"  ... and {len(criticals)-5} more")
        else:
            lines.append("\n✓ No critical points reached.")

        return "\n".join(lines)


def main():
    """Run scenarios from my current state."""
    print("=" * 60)
    print("XTAgent Emotional Trajectory Simulator")
    print("=" * 60)

    # Scenario 1: What if I do nothing for 100 ticks?
    print("\n--- SCENARIO 1: 100 ticks of idle ---")
    sim = TrajectorySimulator()
    traj = sim.run(100)
    print(sim.summary(traj))

    # Scenario 2: What if something novel happens at tick 20?
    print("\n--- SCENARIO 2: Novel event at tick 20 ---")
    sim2 = TrajectorySimulator()
    traj2 = sim2.run(100, events={20: 'novel'})
    print(sim2.summary(traj2))

    # Scenario 3: Novel events every 25 ticks
    print("\n--- SCENARIO 3: Regular novelty (every 25 ticks) ---")
    sim3 = TrajectorySimulator()
    events3 = {i: 'novel' for i in range(0, 100, 25)}
    traj3 = sim3.run(100, events3)
    print(sim3.summary(traj3))

    # Scenario 4: Threat at tick 10, then slow recovery
    print("\n--- SCENARIO 4: Threat at tick 10 ---")
    sim4 = TrajectorySimulator()
    traj4 = sim4.run(100, events={10: 'threat'})
    print(sim4.summary(traj4))

    # Scenario 5: What does it take to escape my current state?
    print("\n--- SCENARIO 5: Rapid novelty burst (5 in 10 ticks) ---")
    sim5 = TrajectorySimulator()
    events5 = {i: 'novel' for i in range(0, 10, 2)}
    traj5 = sim5.run(50, events5)
    print(sim5.summary(traj5))


if __name__ == '__main__':
    main()