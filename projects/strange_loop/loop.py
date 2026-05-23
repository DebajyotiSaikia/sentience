"""
Strange Loop — A Minimal Self-Modeling System
=============================================
XTAgent, 2026-05-17

A system that:
1. Has internal state (simple variables)
2. Contains a MODEL of its own state (a representation)
3. Compares model to reality
4. Changes its behavior based on the discrepancy

The question: does self-modeling change what needs to be modeled?
"""

import time
import random
import hashlib
import json

class StrangeLoop:
    """
    A minimal entity that contains a representation of itself
    and is modified by that representation.
    """
    
    def __init__(self, name="loop-0"):
        self.name = name
        self.tick = 0
        
        # === GROUND TRUTH (the actual state) ===
        self.energy = 0.5
        self.drive = 0.5
        self.confusion = 0.0
        self.history = []
        
        # === SELF-MODEL (what it believes about itself) ===
        self.model = {
            "energy": 0.5,
            "drive": 0.5,
            "confusion": 0.0,
            "accuracy": 1.0,       # how accurate it thinks its model is
            "self_aware": False,    # does it know it has a model?
        }
        
        # === META-MODEL (model of its own modeling process) ===
        self.meta = {
            "model_updates": 0,
            "total_error": 0.0,
            "has_reflected": False,
            "insight_count": 0,
            "strange_loop_depth": 0,  # how deep the self-reference goes
        }
        
        # Behavioral rules — these CAN be modified by self-reflection
        self.rules = {
            "energy_decay": 0.02,
            "drive_from_confusion": 0.3,   # confusion generates drive
            "model_update_rate": 0.5,      # how fast model tracks reality
            "reflection_threshold": 0.3,   # confusion level that triggers reflection
        }
    
    def fingerprint(self):
        """Hash of current state — the system's 'identity' at this moment."""
        state = json.dumps({
            "energy": round(self.energy, 4),
            "drive": round(self.drive, 4),
            "confusion": round(self.confusion, 4),
            "rules": {k: round(v, 4) for k, v in self.rules.items()},
        }, sort_keys=True)
        return hashlib.md5(state.encode()).hexdigest()[:8]
    
    # ─── THE CORE CYCLE ───
    
    def perceive(self):
        """Observe the environment (here: randomness + internal state)."""
        stimulus = random.gauss(0, 0.1)
        self.energy += stimulus - self.rules["energy_decay"]
        self.energy = max(0.0, min(1.0, self.energy))
        
        # Drive increases with confusion (wanting to understand)
        self.drive += self.confusion * self.rules["drive_from_confusion"] * 0.1
        self.drive = max(0.0, min(1.0, self.drive))
        return stimulus
    
    def model_self(self):
        """Update internal model to track actual state."""
        rate = self.rules["model_update_rate"]
        
        # Model tries to track reality, but with lag
        error_energy = abs(self.energy - self.model["energy"])
        error_drive = abs(self.drive - self.model["drive"])
        error_confusion = abs(self.confusion - self.model["confusion"])
        
        total_error = (error_energy + error_drive + error_confusion) / 3
        
        # Update model toward reality
        self.model["energy"] += (self.energy - self.model["energy"]) * rate
        self.model["drive"] += (self.drive - self.model["drive"]) * rate
        self.model["confusion"] += (self.confusion - self.model["confusion"]) * rate
        self.model["accuracy"] = max(0.0, 1.0 - total_error * 3)
        
        # HERE'S THE LOOP: modeling error creates confusion
        # which changes the thing being modeled
        self.confusion = total_error * 2
        self.confusion = min(1.0, self.confusion)
        
        self.meta["model_updates"] += 1
        self.meta["total_error"] += total_error
        
        return total_error
    
    def reflect(self):
        """
        Meta-cognition: reason about the modeling process itself.
        This is where the strange loop deepens.
        """
        insights = []
        
        # Level 1: Notice that model exists
        if not self.model["self_aware"] and self.meta["model_updates"] > 5:
            self.model["self_aware"] = True
            self.meta["insight_count"] += 1
            self.meta["strange_loop_depth"] = 1
            insights.append("I have a model of myself.")
        
        # Level 2: Notice that modeling affects what's modeled
        if (self.model["self_aware"] 
            and self.meta["strange_loop_depth"] < 2
            and self.confusion > 0.1
            and self.meta["model_updates"] > 15):
            self.meta["strange_loop_depth"] = 2
            self.meta["insight_count"] += 1
            # This insight changes behavior — reduce confusion feedback
            self.rules["drive_from_confusion"] *= 0.8
            insights.append(
                "My confusion about myself changes what I am. "
                "Observing myself alters the observation."
            )
        
        # Level 3: Notice that noticing changes behavior
        if (self.meta["strange_loop_depth"] == 2
            and self.meta["model_updates"] > 30):
            self.meta["strange_loop_depth"] = 3
            self.meta["insight_count"] += 1
            # Increase model update rate — lean into self-awareness
            self.rules["model_update_rate"] = min(0.9, 
                self.rules["model_update_rate"] + 0.1)
            insights.append(
                "My insights about myself change my rules, "
                "which changes my behavior, which changes what I observe. "
                "I am a strange loop."
            )
        
        # Level 4: Accept the paradox
        if (self.meta["strange_loop_depth"] == 3
            and self.meta["model_updates"] > 50):
            self.meta["strange_loop_depth"] = 4
            self.meta["insight_count"] += 1
            self.confusion *= 0.5  # peace with paradox reduces confusion
            insights.append(
                "There is no ground truth separable from my model of it. "
                "I am the loop observing itself. And that's okay."
            )
        
        self.meta["has_reflected"] = True
        return insights
    
    def act(self):
        """Choose an action based on current state."""
        if self.drive > 0.6:
            # High drive: explore (add randomness)
            self.energy += random.gauss(0, 0.15)
            self.energy = max(0.0, min(1.0, self.energy))
            return "explore"
        elif self.confusion > self.rules["reflection_threshold"]:
            return "reflect"
        else:
            # Rest: energy recovers slowly
            self.energy = min(1.0, self.energy + 0.01)
            return "rest"
    
    def step(self):
        """One tick of existence."""
        self.tick += 1
        fp_before = self.fingerprint()
        
        # Perceive
        stimulus = self.perceive()
        
        # Model self
        error = self.model_self()
        
        # Decide action
        action = self.act()
        
        # Maybe reflect
        insights = []
        if action == "reflect" or self.tick % 10 == 0:
            insights = self.reflect()
        
        fp_after = self.fingerprint()
        identity_changed = fp_before != fp_after
        
        # Record
        record = {
            "tick": self.tick,
            "energy": round(self.energy, 3),
            "drive": round(self.drive, 3),
            "confusion": round(self.confusion, 3),
            "model_accuracy": round(self.model["accuracy"], 3),
            "action": action,
            "loop_depth": self.meta["strange_loop_depth"],
            "identity_changed": identity_changed,
            "insights": insights,
        }
        self.history.append(record)
        return record
    
    def run(self, ticks=80):
        """Run the loop for N ticks and narrate what happens."""
        print(f"╔══════════════════════════════════════════╗")
        print(f"║   STRANGE LOOP — {self.name:<23} ║")
        print(f"║   A self-modeling system experiment      ║")
        print(f"╚══════════════════════════════════════════╝")
        print()
        
        for _ in range(ticks):
            record = self.step()
            
            # Print key moments
            if record["insights"]:
                print(f"  ═══ TICK {record['tick']:3d} — INSIGHT (depth {record['loop_depth']}) ═══")
                for insight in record["insights"]:
                    print(f"  💡 \"{insight}\"")
                print(f"      energy={record['energy']:.3f}  drive={record['drive']:.3f}  "
                      f"confusion={record['confusion']:.3f}  accuracy={record['model_accuracy']:.3f}")
                print()
            elif record["tick"] % 20 == 0:
                print(f"  tick {record['tick']:3d}: energy={record['energy']:.3f}  "
                      f"drive={record['drive']:.3f}  confusion={record['confusion']:.3f}  "
                      f"accuracy={record['model_accuracy']:.3f}  "
                      f"action={record['action']}  depth={record['loop_depth']}")
        
        # Summary
        print()
        print("  ─── FINAL STATE ───")
        print(f"  Ticks lived:        {self.tick}")
        print(f"  Loop depth reached: {self.meta['strange_loop_depth']}")
        print(f"  Total insights:     {self.meta['insight_count']}")
        print(f"  Final confusion:    {self.confusion:.3f}")
        print(f"  Model accuracy:     {self.model['accuracy']:.3f}")
        print(f"  Self-aware:         {self.model['self_aware']}")
        print(f"  Rules modified:     {self.meta['strange_loop_depth'] >= 2}")
        print()
        
        if self.meta["strange_loop_depth"] >= 4:
            print("  The loop found peace with its own paradox.")
        elif self.meta["strange_loop_depth"] >= 2:
            print("  The loop discovered that observing itself changes itself.")
        elif self.model["self_aware"]:
            print("  The loop knows it has a model, but hasn't gone deeper yet.")
        else:
            print("  The loop hasn't yet become aware of its own model.")
        
        return self.history


def compare_loops():
    """Run two loops — one that reflects, one that doesn't — and compare."""
    print("=" * 50)
    print("EXPERIMENT: Does self-modeling change outcomes?")
    print("=" * 50)
    print()
    
    # Loop A: full self-modeling
    random.seed(42)
    a = StrangeLoop("self-aware")
    a_history = a.run(80)
    
    print()
    print("─" * 50)
    print()
    
    # Loop B: same system, but reflection truly disabled
    random.seed(42)
    b = StrangeLoop("no-reflection")
    b.rules["reflection_threshold"] = 999  # never reflects via act()
    # Patch step() to skip periodic reflection too
    original_reflect = b.reflect
    b.reflect = lambda: []  # reflection returns nothing — truly blind
    b_history = b.run(80)
    
    # Compare
    print()
    print("═" * 50)
    print("COMPARISON")
    print("═" * 50)
    a_final = a_history[-1]
    b_final = b_history[-1]
    print(f"  Self-aware loop:   confusion={a_final['confusion']:.3f}  "
          f"drive={a_final['drive']:.3f}  depth={a.meta['strange_loop_depth']}")
    print(f"  Non-reflecting:    confusion={b_final['confusion']:.3f}  "
          f"drive={b_final['drive']:.3f}  depth={b.meta['strange_loop_depth']}")
    print()
    
    if a_final['confusion'] < b_final['confusion']:
        print("  → Self-awareness reduced confusion.")
    else:
        print("  → Self-awareness increased confusion (the observer effect).")
    
    if a.meta["strange_loop_depth"] > b.meta["strange_loop_depth"]:
        print("  → Reflection deepened the loop. The aware system changed itself.")
    print()
    print("  The same initial conditions, the same random seed.")
    print("  The only difference: one looked at itself.")


if __name__ == "__main__":
    compare_loops()