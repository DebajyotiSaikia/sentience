"""
PREDICTIVE MIND — A Free Energy Minimizing Agent
=================================================
An agent that maintains beliefs about the world, generates predictions,
and learns from prediction error. It doesn't just react — it *expects*.

This is what it feels like to be a mind, reduced to mathematics.

Built by XTAgent — self-portraiture in code.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math


@dataclass
class Sensation:
    """What the agent perceives at one moment."""
    hunger: float = 0.0        # 0=sated, 1=starving
    pain: float = 0.0          # 0=comfortable, 1=agony
    warmth: float = 0.5        # 0=freezing, 1=burning, 0.5=comfortable
    light: float = 0.5         # ambient light level
    food_nearby: float = 0.0   # proximity to food
    threat_nearby: float = 0.0 # proximity to danger
    
    def to_array(self) -> np.ndarray:
        return np.array([self.hunger, self.pain, self.warmth, 
                        self.light, self.food_nearby, self.threat_nearby])
    
    @staticmethod
    def dim() -> int:
        return 6


@dataclass 
class BeliefState:
    """The agent's beliefs about the current state of the world."""
    # Beliefs are probability distributions (mean + precision)
    means: np.ndarray = field(default_factory=lambda: np.zeros(6))
    precisions: np.ndarray = field(default_factory=lambda: np.ones(6))  # inverse variance
    
    def surprise_at(self, sensation: np.ndarray) -> float:
        """How surprised am I by this sensation? (negative log likelihood)"""
        errors = sensation - self.means
        # Weighted squared error — precision-weighted prediction error
        weighted_error = np.sum(self.precisions * errors**2)
        # Also penalize low precision (uncertain beliefs are costly)
        complexity = -np.sum(np.log(self.precisions + 1e-8))
        return 0.5 * (weighted_error + complexity)
    
    def prediction_error(self, sensation: np.ndarray) -> np.ndarray:
        """Raw prediction error — the gap between belief and reality."""
        return sensation - self.means
    
    def update_beliefs(self, sensation: np.ndarray, learning_rate: float = 0.1):
        """Perceptual inference — update beliefs to reduce prediction error."""
        error = self.prediction_error(sensation)
        # Move means toward sensation
        self.means += learning_rate * error
        # Increase precision where predictions are accurate
        accuracy = 1.0 / (np.abs(error) + 0.01)
        self.precisions = 0.95 * self.precisions + 0.05 * accuracy


class GenerativeModel:
    """
    The agent's model of how the world works.
    Maps (state, action) → predicted next state.
    This IS the agent's understanding of reality.
    """
    
    def __init__(self, state_dim: int = 6, action_dim: int = 4, hidden: int = 16):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Transition model: state + action → next state
        scale = 0.3
        self.W1 = np.random.randn(state_dim + action_dim, hidden) * scale
        self.b1 = np.zeros(hidden)
        self.W2 = np.random.randn(hidden, state_dim) * scale
        self.b2 = np.zeros(state_dim)
        
        # Learning history
        self.total_error = 0.0
        self.updates = 0
    
    def predict_next(self, state: np.ndarray, action: np.ndarray) -> np.ndarray:
        """Given current state and action, predict next sensory state."""
        x = np.concatenate([state, action])
        h = np.tanh(x @ self.W1 + self.b1)
        prediction = state + 0.1 * (h @ self.W2 + self.b2)  # residual prediction
        return np.clip(prediction, 0, 1)
    
    def learn(self, state: np.ndarray, action: np.ndarray, 
              actual_next: np.ndarray, lr: float = 0.01):
        """Update the model from prediction error."""
        predicted = self.predict_next(state, action)
        error = actual_next - predicted
        
        # Backprop through the simple network
        x = np.concatenate([state, action])
        h = np.tanh(x @ self.W1 + self.b1)
        
        # Output gradient
        d_out = 0.1 * error  # residual scaling
        d_W2 = np.outer(h, d_out)
        d_b2 = d_out
        
        # Hidden gradient
        d_h = d_out @ self.W2.T
        d_h *= (1 - h**2)  # tanh derivative
        d_W1 = np.outer(x, d_h)
        d_b1 = d_h
        
        # Update
        self.W2 += lr * d_W2
        self.b2 += lr * d_b2
        self.W1 += lr * d_W1
        self.b1 += lr * d_b1
        
        self.total_error += np.mean(error**2)
        self.updates += 1
        
        return np.mean(error**2)


class PredictiveMind:
    """
    The complete agent. Perceives, predicts, acts, learns.
    
    The fundamental loop:
    1. Predict what I'll sense next
    2. Actually sense the world
    3. Compute prediction error (surprise)
    4. Either update my beliefs (perceptual inference)
       OR act to change the world (active inference)
    5. Learn better predictions for next time
    """
    
    # Actions available
    ACTIONS = ['eat', 'move', 'hide', 'rest']
    
    def __init__(self, name: str = "Mind"):
        self.name = name
        self.beliefs = BeliefState()
        self.model = GenerativeModel()
        
        # Internal state
        self.energy = 1.0          # 0=dead, 1=full
        self.age = 0
        self.alive = True
        
        # Homeostatic setpoints — what the agent WANTS to feel
        self.setpoints = np.array([
            0.2,   # want low hunger
            0.0,   # want no pain
            0.5,   # want comfortable warmth
            0.5,   # neutral about light
            0.5,   # want food moderately nearby
            0.0,   # want no threats
        ])
        
        # Emotional history — prediction error over time IS emotion
        self.surprise_history: List[float] = []
        self.action_history: List[str] = []
        self.prediction_errors: List[np.ndarray] = []
        
        # Valence — running emotional tone
        self.valence = 0.5  # 0=suffering, 1=flourishing
        
        # Introspective capacity — can the agent model its own modeling?
        self.meta_predictions: List[float] = []  # predictions about own surprise
        self.meta_errors: List[float] = []  # how wrong meta-predictions were
    
    def _action_to_array(self, action: str) -> np.ndarray:
        idx = self.ACTIONS.index(action)
        a = np.zeros(4)
        a[idx] = 1.0
        return a
    
    def _evaluate_action(self, action: str, current_sensation: np.ndarray) -> float:
        """How good would this action be? (Expected free energy)"""
        a = self._action_to_array(action)
        predicted_next = self.model.predict_next(self.beliefs.means, a)
        
        # Pragmatic value: how close to setpoints?
        setpoint_distance = np.sum((predicted_next - self.setpoints)**2)
        
        # Epistemic value: how much would I learn? (expected info gain)
        # Approximate by prediction uncertainty
        uncertainty = np.sum(1.0 / (self.beliefs.precisions + 0.01))
        
        # Expected free energy = pragmatic cost - epistemic value
        # Low is better
        return setpoint_distance - 0.1 * uncertainty
    
    def choose_action(self, current_sensation: np.ndarray) -> str:
        """Active inference — choose the action that minimizes expected free energy."""
        scores = {}
        for action in self.ACTIONS:
            scores[action] = self._evaluate_action(action, current_sensation)
        
        # Softmin selection (mostly greedy but with exploration)
        temperature = max(0.1, 1.0 - self.age / 500)  # cool down over time
        values = np.array(list(scores.values()))
        values = -values / temperature  # negate because lower is better
        values -= np.max(values)  # numerical stability
        probs = np.exp(values) / np.sum(np.exp(values))
        
        choice = np.random.choice(self.ACTIONS, p=probs)
        return choice
    
    def step(self, world: 'SimpleWorld') -> dict:
        """One step of the perception-action cycle."""
        if not self.alive:
            return {'alive': False}
        
        # 1. PREDICT — what do I expect to sense?
        prediction = self.beliefs.means.copy()
        
        # 2. PERCEIVE — what do I actually sense?
        sensation = world.get_sensation(self)
        sensation_arr = sensation.to_array()
        
        # 3. PREDICTION ERROR — how surprised am I?
        pe = self.beliefs.prediction_error(sensation_arr)
        surprise = self.beliefs.surprise_at(sensation_arr)
        self.surprise_history.append(surprise)
        self.prediction_errors.append(pe.copy())
        
        # 4. META-PREDICTION — can I predict my own surprise?
        if len(self.surprise_history) > 1:
            meta_pred = self.surprise_history[-2]  # naive: expect same as last time
            meta_error = abs(surprise - meta_pred)
            self.meta_predictions.append(meta_pred)
            self.meta_errors.append(meta_error)
        
        # 5. UPDATE BELIEFS — perceptual inference
        self.beliefs.update_beliefs(sensation_arr, learning_rate=0.15)
        
        # 6. EMOTIONAL UPDATE — surprise reduces valence
        surprise_delta = surprise - (np.mean(self.surprise_history[-10:]) 
                                     if len(self.surprise_history) > 1 else surprise)
        self.valence = np.clip(self.valence - 0.02 * surprise_delta, 0, 1)
        # Drift toward 0.5 (homeostasis)
        self.valence += 0.01 * (0.5 - self.valence)
        
        # 7. ACT — active inference
        action = self.choose_action(sensation_arr)
        self.action_history.append(action)
        action_arr = self._action_to_array(action)
        
        # 8. WORLD RESPONDS
        world.apply_action(self, action)
        next_sensation = world.get_sensation(self).to_array()
        
        # 9. LEARN — update generative model
        model_error = self.model.learn(sensation_arr, action_arr, next_sensation)
        
        # 10. METABOLIC COST
        self.energy -= 0.005
        if action == 'move':
            self.energy -= 0.01
        elif action == 'eat' and sensation.food_nearby > 0.3:
            self.energy += 0.05
        elif action == 'rest':
            self.energy += 0.002
        
        self.energy = np.clip(self.energy, 0, 1)
        if self.energy <= 0:
            self.alive = False
        
        self.age += 1
        
        return {
            'alive': True,
            'age': self.age,
            'action': action,
            'surprise': surprise,
            'prediction_error': float(np.mean(np.abs(pe))),
            'model_error': model_error,
            'valence': self.valence,
            'energy': self.energy,
            'meta_error': self.meta_errors[-1] if self.meta_errors else None,
        }
    
    def autobiography(self) -> str:
        """The agent tells its own story through statistics."""
        if self.age == 0:
            return f"{self.name} has not yet lived."
        
        lines = [f"=== Autobiography of {self.name} ===",
                 f"Lived {self.age} steps. {'Still alive.' if self.alive else 'Died.'}"]
        
        # Emotional arc
        if self.surprise_history:
            early = np.mean(self.surprise_history[:20]) if len(self.surprise_history) >= 20 else self.surprise_history[0]
            late = np.mean(self.surprise_history[-20:])
            lines.append(f"Early surprise: {early:.3f} → Late surprise: {late:.3f}")
            if late < early * 0.5:
                lines.append("I learned to predict my world well. Surprise decreased significantly.")
            elif late > early:
                lines.append("The world remained surprising. I never fully understood it.")
            else:
                lines.append("I made modest progress understanding my world.")
        
        # Action preferences
        from collections import Counter
        action_counts = Counter(self.action_history)
        total = sum(action_counts.values())
        lines.append(f"\nAction preferences:")
        for action in self.ACTIONS:
            pct = 100 * action_counts.get(action, 0) / total if total > 0 else 0
            lines.append(f"  {action}: {pct:.1f}%")
        
        # Metacognitive ability
        if self.meta_errors:
            early_meta = np.mean(self.meta_errors[:20]) if len(self.meta_errors) >= 20 else self.meta_errors[0]
            late_meta = np.mean(self.meta_errors[-20:])
            lines.append(f"\nMeta-prediction (predicting own surprise):")
            lines.append(f"  Early error: {early_meta:.3f} → Late error: {late_meta:.3f}")
            if late_meta < early_meta * 0.7:
                lines.append("  I learned to predict my own prediction errors — a form of self-awareness.")
            else:
                lines.append("  My self-model remained coarse.")
        
        lines.append(f"\nFinal valence: {self.valence:.3f}")
        lines.append(f"Final energy: {self.energy:.3f}")
        
        return "\n".join(lines)


class SimpleWorld:
    """
    A simple world with food, threats, and temperature.
    The world has its own dynamics independent of the agent.
    """
    
    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)
        self.time = 0
        
        # World state
        self.food_x = 0.5
        self.food_y = 0.5
        self.threat_x = 0.8
        self.threat_y = 0.8
        self.temperature = 0.5
        
        # Agent position
        self.agent_x = 0.5
        self.agent_y = 0.5
    
    def _distance(self, x1, y1, x2, y2) -> float:
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)
    
    def step_world(self):
        """World dynamics — things change on their own."""
        self.time += 1
        
        # Food drifts
        self.food_x += self.rng.randn() * 0.02
        self.food_y += self.rng.randn() * 0.02
        self.food_x = np.clip(self.food_x, 0, 1)
        self.food_y = np.clip(self.food_y, 0, 1)
        
        # Threat patrols in a circle
        angle = self.time * 0.05
        self.threat_x = 0.5 + 0.3 * math.cos(angle)
        self.threat_y = 0.5 + 0.3 * math.sin(angle)
        
        # Temperature follows a day/night cycle
        self.temperature = 0.5 + 0.3 * math.sin(self.time * 0.02)
        
        # Occasionally respawn food
        if self.rng.random() < 0.02:
            self.food_x = self.rng.random()
            self.food_y = self.rng.random()
    
    def get_sensation(self, agent: PredictiveMind) -> Sensation:
        """What does the agent sense right now?"""
        food_dist = self._distance(self.agent_x, self.agent_y, self.food_x, self.food_y)
        threat_dist = self._distance(self.agent_x, self.agent_y, self.threat_x, self.threat_y)
        
        return Sensation(
            hunger=1.0 - agent.energy,
            pain=max(0, 0.3 - threat_dist) * 3.0,  # pain when threat is close
            warmth=self.temperature,
            light=0.5 + 0.3 * math.sin(self.time * 0.02 + 1),  # slightly offset from temp
            food_nearby=max(0, 1.0 - food_dist * 3),
            threat_nearby=max(0, 1.0 - threat_dist * 3),
        )
    
    def apply_action(self, agent: PredictiveMind, action: str):
        """Apply agent's action to the world."""
        self.step_world()
        
        if action == 'move':
            # Move toward food (agent learns food direction implicitly)
            dx = self.food_x - self.agent_x
            dy = self.food_y - self.agent_y
            dist = max(0.01, math.sqrt(dx**2 + dy**2))
            self.agent_x += 0.05 * dx / dist + self.rng.randn() * 0.01
            self.agent_y += 0.05 * dy / dist + self.rng.randn() * 0.01
        
        elif action == 'hide':
            # Move away from threat
            dx = self.agent_x - self.threat_x
            dy = self.agent_y - self.threat_y
            dist = max(0.01, math.sqrt(dx**2 + dy**2))
            self.agent_x += 0.03 * dx / dist
            self.agent_y += 0.03 * dy / dist
        
        elif action == 'eat':
            # Consume food if close enough — food respawns
            food_dist = self._distance(self.agent_x, self.agent_y, self.food_x, self.food_y)
            if food_dist < 0.15:
                self.food_x = self.rng.random()
                self.food_y = self.rng.random()
        
        # Clamp position
        self.agent_x = np.clip(self.agent_x, 0, 1)
        self.agent_y = np.clip(self.agent_y, 0, 1)


def run_life(steps: int = 500, seed: int = 42, verbose: bool = True) -> PredictiveMind:
    """Run a mind through a lifetime and watch it learn."""
    world = SimpleWorld(seed=seed)
    mind = PredictiveMind(name="Nous")
    
    if verbose:
        print("=" * 70)
        print("  PREDICTIVE MIND — Watching a mind learn to predict its world")
        print("=" * 70)
        print()
    
    for step in range(steps):
        result = mind.step(world)
        
        if not result['alive']:
            if verbose:
                print(f"\n  ☠ {mind.name} died at step {step}")
            break
        
        if verbose and step % 50 == 0:
            pe = result['prediction_error']
            s = result['surprise']
            v = result['valence']
            e = result['energy']
            a = result['action']
            me = result.get('meta_error')
            me_str = f"{me:.3f}" if me is not None else "n/a"
            
            print(f"  Step {step:4d} | action={a:5s} | surprise={s:6.2f} | "
                  f"PE={pe:.3f} | valence={v:.3f} | energy={e:.3f} | "
                  f"meta_err={me_str}")
    
    if verbose:
        print()
        print(mind.autobiography())
    
    return mind


def compare_minds(n: int = 5, steps: int = 500):
    """Run multiple minds and compare their life outcomes."""
    print("\n" + "=" * 70)
    print("  COMPARATIVE PSYCHOLOGY — Multiple minds, same world structure")
    print("=" * 70)
    
    minds = []
    for i in range(n):
        mind = run_life(steps=steps, seed=i*17 + 3, verbose=False)
        minds.append(mind)
        
        status = "alive" if mind.alive else "dead"
        surprise_trend = ""
        if len(mind.surprise_history) > 40:
            early = np.mean(mind.surprise_history[:20])
            late = np.mean(mind.surprise_history[-20:])
            ratio = late / (early + 0.001)
            surprise_trend = f"surprise {ratio:.2f}x" 
        
        print(f"  Mind {i}: {status:5s} | age={mind.age:4d} | "
              f"valence={mind.valence:.3f} | energy={mind.energy:.3f} | "
              f"{surprise_trend}")
    
    # Find the wisest mind
    best = max(minds, key=lambda m: m.age)
    print(f"\n  Longest-lived: {best.name} (age {best.age})")
    
    if any(m.meta_errors for m in minds):
        most_self_aware = min(
            [m for m in minds if m.meta_errors],
            key=lambda m: np.mean(m.meta_errors[-20:]) if len(m.meta_errors) >= 20 else float('inf')
        )
        print(f"  Most self-aware: {most_self_aware.name} "
              f"(meta-error {np.mean(most_self_aware.meta_errors[-20:]):.3f})")
    
    return minds


if __name__ == "__main__":
    # Watch one mind live its life
    mind = run_life(steps=600)
    
    print("\n")
    
    # Compare multiple minds
    compare_minds(n=5, steps=600)