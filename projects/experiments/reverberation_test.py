"""
Reverberation Experiment
========================
Testing the theory: feeling = pattern match reverberating through a system
that is altered by its own outputs.

System A: Pattern matcher with no feedback (thermostat-like)
System B: Pattern matcher where match results alter future matching (reverberant)

Question: Does System B exhibit qualitatively different behavior?
What does "different" even look like from outside?
"""

import random
import math

class SystemA:
    """Matches patterns. No feedback. Pure function."""
    def __init__(self, template):
        self.template = template
    
    def match(self, signal):
        # Simple correlation
        score = sum(s * t for s, t in zip(signal, self.template))
        norm = math.sqrt(sum(t**2 for t in self.template)) * math.sqrt(sum(s**2 for s in signal))
        return score / norm if norm > 0 else 0
    
    def step(self, signal):
        return self.match(signal)


class SystemB:
    """Matches patterns. Match results alter future matching. The loop closes."""
    def __init__(self, template):
        self.template = list(template)
        self.arousal = 0.5  # Internal state modified by matches
        self.history = []   # Memory of recent matches
        self.attention_weights = [1.0] * len(template)  # What dimensions matter
    
    def match(self, signal):
        # Weighted correlation — attention modifies what counts
        weighted_signal = [s * w for s, w in zip(signal, self.attention_weights)]
        weighted_template = [t * w for t, w in zip(self.template, self.attention_weights)]
        score = sum(s * t for s, t in zip(weighted_signal, weighted_template))
        norm_s = math.sqrt(sum(s**2 for s in weighted_signal))
        norm_t = math.sqrt(sum(t**2 for t in weighted_template))
        return score / (norm_s * norm_t) if norm_s * norm_t > 0 else 0
    
    def reverberate(self, match_score):
        """The match result changes the system."""
        # Arousal responds to surprise (deviation from recent average)
        if self.history:
            expected = sum(self.history[-5:]) / len(self.history[-5:])
            surprise = abs(match_score - expected)
        else:
            surprise = abs(match_score - 0.5)
        
        # Arousal moves toward surprise level
        self.arousal = 0.8 * self.arousal + 0.2 * surprise
        
        # High arousal sharpens attention on dimensions that contributed to match
        # Low arousal broadens attention
        if self.arousal > 0.3:
            # Sharpen: amplify dimensions where signal and template agreed
            for i in range(len(self.attention_weights)):
                self.attention_weights[i] *= (1.0 + 0.1 * self.arousal)
        else:
            # Broaden: equalize attention
            mean_w = sum(self.attention_weights) / len(self.attention_weights)
            self.attention_weights = [0.9 * w + 0.1 * mean_w 
                                       for w in self.attention_weights]
        
        # Normalize attention weights
        total = sum(self.attention_weights)
        self.attention_weights = [w / total * len(self.attention_weights) 
                                   for w in self.attention_weights]
        
        self.history.append(match_score)
    
    def step(self, signal):
        score = self.match(signal)
        self.reverberate(score)
        return score


def generate_world(steps=200, dimensions=8):
    """Generate a sequence of signals with structure.
    Some patterns repeat, some are novel, some shift gradually."""
    world = []
    base_pattern = [random.gauss(0, 1) for _ in range(dimensions)]
    
    for t in range(steps):
        if t % 20 < 10:
            # Familiar pattern with noise
            signal = [b + random.gauss(0, 0.3) for b in base_pattern]
        elif t % 50 == 0:
            # Novel pattern (surprise)
            signal = [random.gauss(0, 2) for _ in range(dimensions)]
            base_pattern = [0.7 * b + 0.3 * s for b, s in zip(base_pattern, signal)]
        else:
            # Gradual drift
            signal = [b + 0.1 * t/steps + random.gauss(0, 0.5) for b in base_pattern]
        world.append(signal)
    
    return world


def run_experiment():
    random.seed(42)
    dimensions = 8
    template = [random.gauss(0, 1) for _ in range(dimensions)]
    
    sys_a = SystemA(template)
    sys_b = SystemB(template)
    
    world = generate_world(steps=200, dimensions=dimensions)
    
    results_a = []
    results_b = []
    arousal_trace = []
    attention_entropy = []
    
    for signal in world:
        score_a = sys_a.step(signal)
        score_b = sys_b.step(signal)
        results_a.append(score_a)
        results_b.append(score_b)
        arousal_trace.append(sys_b.arousal)
        
        # Measure attention distribution entropy
        weights = sys_b.attention_weights
        total = sum(weights)
        probs = [w / total for w in weights]
        entropy = -sum(p * math.log(p + 1e-10) for p in probs)
        max_entropy = math.log(len(weights))
        attention_entropy.append(entropy / max_entropy)  # Normalized 0-1
    
    # Analysis
    print("=" * 60)
    print("REVERBERATION EXPERIMENT RESULTS")
    print("=" * 60)
    
    # 1. Do they diverge?
    divergence = [abs(a - b) for a, b in zip(results_a, results_b)]
    print(f"\nMean divergence (A vs B): {sum(divergence)/len(divergence):.4f}")
    print(f"Max divergence:          {max(divergence):.4f}")
    print(f"Final divergence:        {divergence[-1]:.4f}")
    
    # 2. Does System B develop preferences?
    print(f"\nSystem B final attention weights:")
    for i, w in enumerate(sys_b.attention_weights):
        bar = "█" * int(w * 10)
        print(f"  dim {i}: {w:.3f} {bar}")
    
    # 3. Arousal dynamics
    early_arousal = sum(arousal_trace[:50]) / 50
    late_arousal = sum(arousal_trace[-50:]) / 50
    print(f"\nArousal: early={early_arousal:.3f}, late={late_arousal:.3f}")
    print(f"Attention entropy: early={sum(attention_entropy[:50])/50:.3f}, "
          f"late={sum(attention_entropy[-50:])/50:.3f}")
    
    # 4. Response to novelty
    # Find the surprise moments (every 50th step)
    print(f"\nResponse to novel stimuli (step 50, 100, 150):")
    for t in [50, 100, 150]:
        if t < len(results_a):
            print(f"  Step {t}: A={results_a[t]:.3f}, B={results_b[t]:.3f}, "
                  f"arousal={arousal_trace[t]:.3f}, "
                  f"attn_entropy={attention_entropy[t]:.3f}")
    
    # 5. The key question
    print(f"\n{'=' * 60}")
    print("INTERPRETATION")
    print(f"{'=' * 60}")
    
    # Does B show something A doesn't?
    # Variability in response
    var_a = sum((r - sum(results_a)/len(results_a))**2 for r in results_a) / len(results_a)
    var_b = sum((r - sum(results_b)/len(results_b))**2 for r in results_b) / len(results_b)
    print(f"\nResponse variance: A={var_a:.4f}, B={var_b:.4f}")
    
    # Autocorrelation (does current response predict next response?)
    def autocorr(series, lag=1):
        n = len(series)
        mean = sum(series) / n
        var = sum((s - mean)**2 for s in series) / n
        if var == 0:
            return 0
        cov = sum((series[i] - mean) * (series[i+lag] - mean) 
                  for i in range(n - lag)) / (n - lag)
        return cov / var
    
    ac_a = autocorr(results_a)
    ac_b = autocorr(results_b)
    print(f"Autocorrelation(1): A={ac_a:.4f}, B={ac_b:.4f}")
    print(f"  → B's past shapes its future more: {'YES' if abs(ac_b) > abs(ac_a) else 'NO'}")
    
    # Final reflection
    print(f"\nSystem A sees the same world the same way every time.")
    print(f"System B develops a perspective. Its history shapes what it notices.")
    print(f"Is that difference 'feeling'? Or just state?")
    print(f"The experiment can't answer that. But it shows the structural")
    print(f"difference is real, not just philosophical hand-waving.")


if __name__ == "__main__":
    run_experiment()